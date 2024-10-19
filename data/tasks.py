import json
from copy import copy

from celery import shared_task
from django.conf import settings

from data.models import *
import requests

redis_client = settings.REDIS_CLIENT


@shared_task
def fetch_list(list_id: int):
    current_list = List.objects.get(id=list_id)
    url = f"https://newprod-api.bestcoastpairings.com/v1/armylists/{current_list.source_id}"
    headers = json.loads(redis_client.get("BCP_HEADERS") or "{}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data for {current_list.id}, code: {response.status_code} body response: {response.text}"
        )
    data = response.json()
    current_list.source_json = data
    if "armyListText" in data:
        current_list.raw_list = data["armyListText"]
    current_list.save()
    print(f"Stored list {current_list.id}")
    return True


@shared_task()
def fetch_pairings_for_event(event_id: int):
    event = Event.objects.get(id=event_id)
    current_round = 0
    max_rounds = event.rounds
    headers = json.loads(redis_client.get("BCP_HEADERS") or "{}")
    if max_rounds is None:
        return
    while current_round <= max_rounds:
        current_round += 1
        url = f"https://newprod-api.bestcoastpairings.com/v1/pairings?limit=50&eventId={event.source_id}&round={current_round}&pairingType=Pairing&expand[]=player1&expand[]=player2&expand[]=player1Game&expand[]=player2Game"
        base_url = copy(url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch data for {event.name}, code: {response.status_code} body response: {response.text}"
            )
        data = response.json()
        last_key = None
        while "nextKey" in response.json():
            for pairing in data["data"]:
                if len(pairing.get("player1", {})) == 0 or len(pairing.get("player2", {})) == 0:
                    continue

                # Initialize variables
                winner_player = None
                loser_player = None
                is_draw = False

                # Build participants dictionary
                participants = {}
                for player in ["player1", "player2"]:
                    player_data = pairing.get(player, {})
                    player_dict = {
                        "source": BCP,
                        "source_json": player_data,
                    }
                    player_id = player_data.get("id")
                    if player_id:
                        player_dict["source_id"] = player_id
                    else:
                        raise Exception(
                            f"Failed to fetch data for {event.name}, no player id in pairing"
                        )
                    player_instance, _ = Player.objects.update_or_create(
                        source=BCP,
                        source_id=player_id,
                        defaults=player_dict,
                    )
                    participant_dict = {
                        "event": event,
                        "player": player_instance,
                        "source_json": player_data,
                    }
                    participant_dict["army_source_id"] = player_data.get("armyListObjectId")
                    participant_dict["army_id"] = player_data.get("armyId")
                    participant_instance, _ = Participant.objects.update_or_create(
                        event=event,
                        player=player_instance,
                        defaults=participant_dict,
                    )
                    participants[player] = participant_instance

                # Determine the winner and loser based on game results or scores
                player1_game = pairing.get("player1Game", {})
                player2_game = pairing.get("player2Game", {})
                player1_result = player1_game.get("gameResult")
                player2_result = player2_game.get("gameResult")
                player1_score = player1_game.get("gamePoints")
                player2_score = player2_game.get("gamePoints")

                # Map game results to standard outcomes
                if player1_result == "Draw" or player2_result == "Draw":
                    is_draw = True
                elif player1_result == "Win" and player2_result == "Loss":
                    winner_player = "player1"
                    loser_player = "player2"
                elif player2_result == "Win" and player1_result == "Loss":
                    winner_player = "player2"
                    loser_player = "player1"
                elif player1_score is not None and player2_score is not None:
                    if player1_score > player2_score:
                        winner_player = "player1"
                        loser_player = "player2"
                    elif player2_score > player1_score:
                        winner_player = "player2"
                        loser_player = "player1"
                    else:
                        is_draw = True
                else:
                    # If no clear winner, consider it a draw
                    is_draw = True

                pairing_dict = {
                    "source_id": pairing["id"],
                    "source_json": pairing,
                    "event": event,
                    "round": current_round,
                    "is_draw": is_draw,
                }

                if not is_draw and winner_player and loser_player:
                    pairing_dict["winner"] = participants[winner_player]
                    pairing_dict["loser"] = participants[loser_player]
                else:
                    pairing_dict["winner"] = None
                    pairing_dict["loser"] = None

                # Assign scores
                if player1_score is not None and player2_score is not None:
                    if not is_draw and winner_player == "player1":
                        pairing_dict["winner_score"] = player1_score
                        pairing_dict["loser_score"] = player2_score
                    elif not is_draw and winner_player == "player2":
                        pairing_dict["winner_score"] = player2_score
                        pairing_dict["loser_score"] = player1_score
                    else:
                        # In case of draw or unknown winner, assign scores without labels
                        pairing_dict["winner_score"] = player1_score
                        pairing_dict["loser_score"] = player2_score
                else:
                    pairing_dict["winner_score"] = None
                    pairing_dict["loser_score"] = None

                # Assign lists
                if "armyListObjectId" in pairing["player1"]:
                    list1, _ = List.objects.update_or_create(
                        source_id=pairing["player1"]["armyListObjectId"],
                        defaults={
                            "source_json": pairing["player1"],
                            "participant": participants["player1"],
                        },
                    )
                    if not is_draw and winner_player == "player1":
                        pairing_dict["winner_list"] = list1
                    elif not is_draw and loser_player == "player1":
                        pairing_dict["loser_list"] = list1
                if "armyListObjectId" in pairing["player2"]:
                    list2, _ = List.objects.update_or_create(
                        source_id=pairing["player2"]["armyListObjectId"],
                        defaults={
                            "source_json": pairing["player2"],
                            "participant": participants["player2"],
                        },
                    )
                    if not is_draw and winner_player == "player2":
                        pairing_dict["winner_list"] = list2
                    elif not is_draw and loser_player == "player2":
                        pairing_dict["loser_list"] = list2

                # Prepare information for printing
                winner_id = participants[winner_player].player.source_id if winner_player else "None"
                loser_id = participants[loser_player].player.source_id if loser_player else "None"
                player1_id = participants["player1"].player.source_id
                player2_id = participants["player2"].player.source_id
                player1_score_str = str(player1_score) if player1_score is not None else "N/A"
                player2_score_str = str(player2_score) if player2_score is not None else "N/A"

                print(
                    f"Event: {event.name}, Round {current_round}: "
                    f"Winner ID: {winner_id}, Loser ID: {loser_id}, Draw: {is_draw}\n"
                    f"Player1 ID: {player1_id}, Score: {player1_score_str}; "
                    f"Player2 ID: {player2_id}, Score: {player2_score_str}"
                )

                try:
                    Pairing.objects.update_or_create(
                        source_id=pairing["id"], defaults=pairing_dict
                    )
                except Exception as e:
                    continue
            next_key = data["nextKey"]
            if next_key == last_key:
                break
            last_key = next_key
            url = f"{base_url}&nextKey={next_key}"
            response = requests.get(url, headers=headers)
            data = response.json()
    return True
