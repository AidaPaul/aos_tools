from copy import copy

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data.models import *


class Command(BaseCommand):
    help = "Fetch event lists from BCP"

    def handle(self, *args, **options):
        headers = settings.BCP_HEADERS
        # for event in Event.objects.filter(source=BCP).filter(start_date__gte="2024-01-16"):
        for event in Event.objects.filter(id=14479):
            url = f"https://prod-api.bestcoastpairings.com/players?limit=100&eventId={event.source_id}&expand%5B%5D=army&expand%5B%5D=subFaction&expand%5B%5D=character&expand%5B%5D=team&expand%5B%5D=user"
            base_url = copy(url)
            response = requests.get(url, headers=headers)
            last_key = None
            next_key = None
            data = response.json()
            while "nextKey" in response.json():
                for player in data["data"]:
                    player_dict = {
                        "source": BCP,
                        "source_id": player["id"],
                        "source_json": player,
                    }
                    army_source_id = None
                    if "armyListObjectId" in player:
                        army_source_id = player["armyListObjectId"]
                    army_id = None
                    if "army" in player and "id" in player["army"]:
                        army_id = player["army"]["id"]
                    if "armyId" in player:
                        army_id = player["armyId"]
                    Player.objects.update_or_create(
                        source=BCP, source_id=player["id"], defaults=player_dict
                    )
                    participant_dict = {
                        "event": event,
                        "player": Player.objects.get(source=BCP, source_id=player["id"]),
                        "source_json": player,
                        "army_source_id": army_source_id,
                        "army_id": army_id,
                    }
                    player_part = Participant.objects.update_or_create(
                        event=event,
                        player=Player.objects.get(source=BCP, source_id=player["id"]),
                        defaults=participant_dict,
                    )
                    if 'army_source_id' in participant_dict and participant_dict['army_source_id'] is not None:
                        List.objects.update_or_create(
                            participant=player_part[0],
                            source_json={},
                            raw_list="",
                            source_id=participant_dict['army_source_id'],
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Successfully created empty list for {player}"
                            )
                        )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully fetched data for {player}"
                        )
                    )
                next_key = data["nextKey"]
                if next_key == last_key:
                    self.stdout.write(self.style.SUCCESS(f"Finished fetching data"))
                    break
                last_key = next_key
                self.stdout.write(self.style.SUCCESS(f"Fetching data for {event.name} with key {next_key}"))
                url = f"{base_url}&nextKey={next_key}"
                response = requests.get(url, headers=headers)
                data = response.json()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully fetched data for {event.name}")
            )
