import openpyxl
from django.conf import settings
from django.core.management.base import BaseCommand
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from data.models import (
    Event,
    Pairing,
    List,
    Participant,
    Player,
    ECKSEN,
    GHB_2022S1,
    GHB_2021,
    GHB_2022S2,
    GHB_2023,
    WIN,
    LOSS,
    DRAW, GHB_2024,
)

fetch_all_query = """
query TournamentResultsBySystem($gamingSystemId: Int) {
  tournamentResultsBySystem(gamingSystemId: $gamingSystemId) {
    id
    name
    players {
      name
      id
      placing
      playerList {
        faction
        list
        factionId
      }
      tournamentId
      matchupResults {
        againstPlayerId
        outcome
        roundId
      }
    }
    rounds {
      id
      number
      scenario {
        id
        name
      }
    }
    gamingSystem {
      name
      id
      edition
    }
    date
  }
}
"""


class Command(BaseCommand):
    help = "Fetch events from Ecksen"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from_date",
            type=str,
            help="Fetch events from this date",
        )

    def handle(self, *args, **options):
        transport = AIOHTTPTransport(url=settings.ECKSEN_ENDPOINT)
        client = Client(transport=transport, fetch_schema_from_transport=False)

        query = gql(fetch_all_query)
        response = client.execute(query, variable_values={"gamingSystemId": 1})
        for event in response["tournamentResultsBySystem"]:
            event_dict = {
                "source": ECKSEN,
                "source_id": event["id"],
                "source_json": event,
                "name": event["name"],
                "rounds": len(event["rounds"]),
                "players_count": len(event["players"]),
                "start_date": f"{event['date']}T00:00:00+02:00",
            }
            if event["gamingSystem"]["edition"] == "GH21":
                event_dict["season"] = GHB_2021
            elif event["gamingSystem"]["edition"] == "GH22":
                event_dict["season"] = GHB_2022S1
            elif event["gamingSystem"]["edition"] == "GH22 s2":
                event_dict["season"] = GHB_2022S2
            elif event["gamingSystem"]["edition"] == "GH23-24":
                event_dict["season"] = GHB_2023
            elif event["gamingSystem"]["edition"] == "GH24-25":
                event_dict["season"] = GHB_2024
            else:
                raise Exception(
                    f"Unknown season: {event['gamingSystem']['edition']} for event {event}"
                )

            if Event.objects.filter(source=ECKSEN, source_id=event["id"]).exists():
                continue

            event_instance, created = Event.objects.update_or_create(
                source=ECKSEN, source_id=event["id"], defaults=event_dict
            )

            # Create players, participants and lists
            for player in event["players"]:
                player_dict = {
                    "source": ECKSEN,
                    "source_id": player["id"],
                    "source_json": player,
                }
                Player.objects.update_or_create(
                    source=ECKSEN, source_id=player["id"], defaults=player_dict
                )
                participant_dict = {
                    "event": event_instance,
                    "player": Player.objects.get(source=ECKSEN, source_id=player["id"]),
                    "source_json": player,
                }
                player_part = Participant.objects.update_or_create(
                    event=event_instance,
                    player=Player.objects.get(source=ECKSEN, source_id=player["id"]),
                    defaults=participant_dict,
                )
                List.objects.update_or_create(
                    participant=player_part[0],
                    source_json=player["playerList"],
                    raw_list=player["playerList"]["list"],
                    source_id=f"{player_part[0].id}_{event_instance.id}",
                )

            event_rounds = {}
            for round_instance in event["rounds"]:
                event_rounds[round_instance["id"]] = [
                    round_instance["number"],
                    round_instance["scenario"],
                ]

            # And now we create pairings
            for player in event["players"]:
                for result in player["matchupResults"]:
                    if result["outcome"] == "UNPAIRED":
                        continue
                    round_number, round_scenario = event_rounds[result["roundId"]]
                    pairing_dict = {
                        "source_id": f"{player['id']}_{result['againstPlayerId']}",
                        "source_json": result,
                        "event": event_instance,
                        "round": round_number,
                    }
                    if result["outcome"] == "WIN":
                        pairing_dict["player1_result"] = WIN
                        pairing_dict["player2_result"] = LOSS
                    elif result["outcome"] == "LOSS":
                        pairing_dict["player1_result"] = LOSS
                        pairing_dict["player2_result"] = WIN
                    elif result["outcome"] == "DRAW":
                        pairing_dict["player1_result"] = DRAW
                        pairing_dict["player2_result"] = DRAW
                    try:
                        player1 = Participant.objects.get(
                            event=event_instance,
                            player=Player.objects.get(
                                source=ECKSEN, source_id=player["id"]
                            ),
                        )
                    except Player.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Player {player['id']} not found for event {event_instance}"
                            )
                        )
                        continue

                    try:
                        player2 = Participant.objects.get(
                            event=event_instance,
                            player=Player.objects.get(
                                source=ECKSEN, source_id=result["againstPlayerId"]
                            ),
                        )
                    except Player.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Player {result['againstPlayerId']} not found for event {event_instance}"
                            )
                        )
                        continue

                    # Check if that pairing already exists from the other side
                    if Pairing.objects.filter(
                        source_id=f"{event_instance.id}_{round_number}_{result['againstPlayerId']}_{player['id']}"
                    ).exists():
                        continue
                    source_id = f"{event_instance.id}_{round_number}_{player['id']}_{result['againstPlayerId']}"
                    try:
                        player1_list = List.objects.get(
                            source_id=f"{player1.id}_{event_instance.id}"
                        )
                    except List.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"List for player {player1} not found for event {event_instance}"
                            )
                        )
                        continue
                    try:
                        player2_list = List.objects.get(
                            source_id=f"{player2.id}_{event_instance.id}"
                        )
                    except List.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"List for player {player2} not found for event {event_instance}"
                            )
                        )
                        continue

                    pairing_dict["player1"] = player1
                    pairing_dict["player2"] = player2
                    pairing_dict["player1_list"] = player1_list
                    pairing_dict["player2_list"] = player2_list
                    if Pairing.objects.filter(source_id=source_id).exists():
                        Pairing.objects.filter(source_id=source_id).update(
                            **pairing_dict
                        )
                    else:
                        pairing_dict["source_id"] = source_id
                        Pairing.objects.create(**pairing_dict)
            event_instance = Event.objects.get(source=ECKSEN, source_id=event["id"])
            pairings = Pairing.objects.filter(event=event_instance)
            participants = Participant.objects.filter(event=event_instance)
            expected_pairings = int(len(participants) * event_instance.rounds / 2)
            if len(pairings) != expected_pairings:
                self.stdout.write(
                    self.style.ERROR(
                        f"For event {event_instance} expected {expected_pairings} pairings, found {len(pairings)} instead"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Event {event_instance} has {len(pairings)} pairings as expected"
                    )
                )
