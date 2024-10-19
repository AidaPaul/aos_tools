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
    GHB_2024,
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

            # Create players, participants, and lists
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

            # Now we create pairings
            for player in event["players"]:
                for result in player["matchupResults"]:
                    if result["outcome"] == "UNPAIRED" or result["againstPlayerId"] is None:
                        continue
                    round_number, round_scenario = event_rounds[result["roundId"]]
                    # Ensure both player IDs are not None
                    if player['id'] is None or result['againstPlayerId'] is None:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Missing player ID in result: {result} for event {event_instance}"
                            )
                        )
                        continue
                    # Generate a unique source_id regardless of player order
                    player_ids = sorted([player['id'], result['againstPlayerId']])

                    # Check if the pairing already exists
                    source_id = f"{event_instance.id}_{round_number}_{player_ids[0]}_{player_ids[1]}"
                    if Pairing.objects.filter(source_id=source_id).exists():
                        continue

                    try:
                        player1 = Participant.objects.get(
                            event=event_instance,
                            player=Player.objects.get(
                                source=ECKSEN, source_id=player_ids[0]
                            ),
                        )
                    except Player.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Player {player_ids[0]} not found for event {event_instance}"
                            )
                        )
                        continue

                    try:
                        player2 = Participant.objects.get(
                            event=event_instance,
                            player=Player.objects.get(
                                source=ECKSEN, source_id=player_ids[1]
                            ),
                        )
                    except Player.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Player {player_ids[1]} not found for event {event_instance}"
                            )
                        )
                        continue

                    # Determine the outcome from the perspective of player1
                    if player['id'] == player_ids[0]:
                        # Current player is player1
                        outcome = result["outcome"]
                    else:
                        # Current player is player2, find outcome from opponent's data
                        opponent_player = next(
                            (p for p in event["players"] if p["id"] == result["againstPlayerId"]), None
                        )
                        if opponent_player is None:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Opponent player {result['againstPlayerId']} not found for event {event_instance}"
                                )
                            )
                            continue
                        opponent_result = next(
                            (r for r in opponent_player["matchupResults"]
                             if r["againstPlayerId"] == player['id'] and r["roundId"] == result["roundId"]), None
                        )
                        if opponent_result is None:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"No matching result for players {player_ids[0]} and {player_ids[1]} in round {round_number} of event {event_instance}"
                                )
                            )
                            continue
                        outcome = opponent_result["outcome"]

                    # Determine winner, loser, and is_draw
                    if outcome == "WIN":
                        is_draw = False
                        winner = player1
                        loser = player2
                    elif outcome == "LOSS":
                        is_draw = False
                        winner = player2
                        loser = player1
                    elif outcome == "DRAW":
                        is_draw = True
                        winner = None
                        loser = None
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Unexpected outcome '{outcome}' for players {player_ids[0]} and {player_ids[1]} in event {event_instance}"
                            )
                        )
                        continue

                    # Get lists
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
                        player1_list = None

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
                        player2_list = None

                    pairing_dict = {
                        "source_id": source_id,
                        "source_json": result,
                        "event": event_instance,
                        "round": round_number,
                        "winner": winner,
                        "loser": loser,
                        "is_draw": is_draw,
                        "winner_list": player1_list if winner == player1 else player2_list if winner == player2 else None,
                        "loser_list": player1_list if loser == player1 else player2_list if loser == player2 else None,
                        "scenario": round_scenario["name"] if round_scenario else None,
                    }

                    # Create or update the pairing
                    Pairing.objects.update_or_create(
                        source_id=source_id, defaults=pairing_dict
                    )

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
        self.stdout.write(self.style.SUCCESS("Finished fetching events"))