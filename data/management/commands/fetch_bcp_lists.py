from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from data.models import *
import requests


class Command(BaseCommand):
    help = "Fetch events from BCP"

    def handle(self, *args, **options):
        headers = settings.BCP_HEADERS
        for list in List.objects.filter(
            Q(source_id__isnull=False) & Q(raw_list__isnull=True)
        ):
            url = f"https://prod-api.bestcoastpairings.com/armylists/{list.source_id}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to fetch data for {list.source_id}, code: {response.status_code} body response: {response.text}"
                    )
                )
                continue
            data = response.json()
            list.source_json = data
            if "armyListText" in data:
                list.raw_list = data["armyListText"]
            list.save()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully fetched data for {list.source_id}")
            )
