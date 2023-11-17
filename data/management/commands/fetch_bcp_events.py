from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from data.models import Event, BCP
import requests


class Command(BaseCommand):
    help = "Fetch events from BCP"

    def handle(self, *args, **options):
        month = 1
        year = 2023
        limit = 100
        headers = settings.BCP_HEADERS
        while month <= 12:
            url = f"https://prod-api.bestcoastpairings.com/events?limit={limit}&startDate={year}-{month:02d}-01T00%3A00%3A00Z&endDate={year}-{month:02d}-31T00%3A00%3A00Z&sortKey=eventDate&sortAscending=true&gameType=4"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise CommandError(
                    f"Failed to fetch data for {year}-{month:02d}, code: {response.status_code} body response: {response.text}"
                )
            data = response.json()
            for event in data["data"]:
                event_dict = {
                    "source": BCP,
                    "source_id": event["id"],
                    "source_json": event,
                    "name": event["name"],
                    "start_date": event["eventDate"],
                    "end_date": event["eventEndDate"],
                    "rounds": event["numberOfRounds"],
                }
                if "numTickets" in event:
                    event_dict["players_count"] = event["numTickets"]
                if "pointsValue" in event:
                    event_dict["points_limit"] = event["pointsValue"]
                Event.objects.update_or_create(
                    source=BCP, source_id=event["id"], defaults=event_dict
                )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully fetched data for {year}-{month:02d}")
            )
            month += 1
