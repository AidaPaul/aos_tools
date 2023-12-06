import requests
from celery import shared_task
from django.conf import settings

from data.models import List

headers = settings.BCP_HEADERS

from celery.contrib import rdb

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Count

from data.models import *
import requests


@shared_task
def fetch_list(list_id: int):
    current_list = List.objects.get(id=list_id)
    url = f"https://prod-api.bestcoastpairings.com/armylists/{current_list.source_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data for {current_list.name}, code: {response.status_code} body response: {response.text}"
        )
    data = response.json()
    current_list.source_json = data
    if "armyListText" in data:
        current_list.raw_list = data["armyListText"]
    current_list.save()
    return True


@shared_task()
def fetch_pairings_for_event(event_id: int):
    event = Event.objects.get(id=event_id)
    round = 0
    max_rounds = event.rounds
    if max_rounds is None:
        return
    while round <= max_rounds:
        round += 1
        url = f"https://prod-api.bestcoastpairings.com/pairings?limit=100&eventId={event.source_id}&round={round}&pairingType=Pairing&expand%5B%5D=player1&expand%5B%5D=player2&expand%5B%5D=player1Game&expand%5B%5D=player2Game"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch data for {event.name}, code: {response.status_code} body response: {response.text}"
            )
        data = response.json()
        player1 = None
        player2 = None
        for pairing in data["data"]:
            if len(pairing["player1"]) == 0 or len(pairing["player2"]) == 0:
                continue
            pairing_dict = {
                "source_id": pairing["id"],
                "source_json": pairing,
                "event": event,
                "round": round,
            }
            for player in ["player1", "player2"]:
                player_dict = {
                    "source": BCP,
                    "source_json": pairing[player],
                }
                if "id" in pairing[player]:
                    player_dict["source_id"] = pairing[player]["id"]
                else:
                    raise Exception(
                        f"Failed to fetch data for {event.name}, no player id in pairing"
                    )
                player_instance = Player.objects.update_or_create(
                    source=BCP,
                    source_id=pairing[player]["id"],
                    defaults=player_dict,
                )[0]
                participant_dict = {
                    "event": event,
                    "player": player_instance,
                    "source_json": pairing[player],
                }
                if "armyListObjectId" in pairing[player]:
                    participant_dict["army_source_id"] = pairing[player][
                        "armyListObjectId"
                    ]
                if "armyId" in pairing[player]:
                    participant_dict["army_id"] = pairing[player]["armyId"]
                participant_instance = Participant.objects.update_or_create(
                    event=event,
                    player=player_instance,
                    defaults=participant_dict,
                )[0]
                if player == "player1":
                    player1 = participant_instance
                else:
                    player2 = participant_instance
            pairing_dict["player1"] = player1
            pairing_dict["player2"] = player2
            if "gamePoints" in pairing["player1Game"]:
                pairing_dict["player1_score"] = pairing["player1Game"]["gamePoints"]
            if "gamePoints" in pairing["player2Game"]:
                pairing_dict["player2_score"] = pairing["player2Game"]["gamePoints"]
            if "gameResult" in pairing["player1Game"]:
                pairing_dict["player1_result"] = pairing["player1Game"]["gameResult"]
            if "gameResult" in pairing["player2Game"]:
                pairing_dict["player2_result"] = pairing["player2Game"]["gameResult"]
            if "armyListObjectId" in pairing["player1"]:
                pairing_dict["player1_list"] = List.objects.update_or_create(
                    source_id=pairing["player1"]["armyListObjectId"],
                    defaults={
                        "source_json": pairing["player1"],
                        "participant": player1,
                    },
                )[0]
            if "armyListObjectId" in pairing["player2"]:
                pairing_dict["player2_list"] = List.objects.update_or_create(
                    source_id=pairing["player2"]["armyListObjectId"],
                    defaults={
                        "source_json": pairing["player2"],
                        "participant": player2,
                    },
                )[0]
            try:
                Pairing.objects.update_or_create(
                    source_id=pairing["id"], defaults=pairing_dict
                )
            except Exception as e:
                continue
        return True
