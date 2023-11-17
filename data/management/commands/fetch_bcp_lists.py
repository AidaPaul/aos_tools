from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from data.models import *
import requests


class Command(BaseCommand):
    help = "Fetch events from BCP"

    def handle(self, *args, **options):
        headers = settings.BCP_HEADERS
        for participant in Participant.objects.filter(
            Q(army_source_id__isnull=False) & Q(event__source=BCP)
        ):
            url = f"https://prod-api.bestcoastpairings.com/armylists/{participant.army_source_id}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to fetch data for {participant.army_source_id}, code: {response.status_code} body response: {response.text}"
                    )
                )
                continue
            data = response.json()
            list_dict = {
                "source_json": data,
                "participant": participant,
                "player_created_at": data["created_at"],
                "player_updated_at": data["updated_at"],
                "raw_list": data["armyListText"],
            }
            List.objects.update_or_create(
                source_id=participant.army_source_id, defaults=list_dict
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully fetched data for {participant.army_source_id}"
                )
            )
