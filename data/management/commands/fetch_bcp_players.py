from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from data.models import *
import requests


class Command(BaseCommand):
    help = "Fetch event lists from BCP"

    def handle(self, *args, **options):
        headers = settings.BCP_HEADERS
        for event in Event.objects.filter(source=BCP):
            url = f"https://prod-api.bestcoastpairings.com/players?limit=100&eventId={event.source_id}&expand%5B%5D=army&expand%5B%5D=subFaction&expand%5B%5D=character&expand%5B%5D=team&expand%5B%5D=user"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to fetch data for {event.name}, code: {response.status_code} body response: {response.text}"
                    )
                )
                continue
            data = response.json()
            for player in data["data"]:
                player_dict = {
                    "source": BCP,
                    "source_id": player["id"],
                    "source_json": player,
                }
                army_id = None
                if "armyListObjectId" in player:
                    army_id = player["armyListObjectId"]
                Player.objects.update_or_create(
                    source=BCP, source_id=player["id"], defaults=player_dict
                )
                participant_dict = {
                    "event": event,
                    "player": Player.objects.get(source=BCP, source_id=player["id"]),
                    "source_json": player,
                    "army_source_id": army_id,
                }
                Participant.objects.update_or_create(
                    event=event,
                    player=Player.objects.get(source=BCP, source_id=player["id"]),
                    defaults=participant_dict,
                )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully fetched data for {event.name}")
            )
