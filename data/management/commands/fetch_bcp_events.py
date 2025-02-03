from copy import copy
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from data.models import Event, BCP, W40K, BOLT_ACTION, AOS, OLD_WORLD, \
    KINGS_OF_WAR, SPEARHEAD


class Command(BaseCommand):
    help = "Fetch events from BCP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--game_type",
            type=int,
            required=True,
            help="Game type to fetch events for (e.g., 1 for 40k, 4 for AOS)",
        )
        parser.add_argument(
            "--month",
            type=int,
            default=1,
            help="Starting month for fetching events (1-12)",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=2025,
            help="Starting year for fetching events",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Number of events to fetch per request",
        )

    def handle(self, *args, **options):
        month = options["month"]
        year = options["year"]
        limit = options["limit"]
        headers = settings.BCP_HEADERS
        game_type = options["game_type"]

        # Validate month value
        if not 1 <= month <= 12:
            raise CommandError("Month must be between 1 and 12.")

        # Build the initial URL
        url = (
            f"https://newprod-api.bestcoastpairings.com/v1/events"
            f"?limit={limit}"
            f"&startDate={year}-{month:02d}-01T00:00:00Z"
            f"&endDate={year + 1}-{month:02d}-01T00:00:00Z"
            f"&sortKey=eventDate"
            f"&sortAscending=true"
            f"&gameType={game_type}"
        )
        base_url = copy(url)

        # Initialize variables for pagination
        last_key = None

        while True:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise CommandError(
                    f"Failed to fetch data: {response.status_code} - {response.text}"
                )

            data = response.json()
            events = data.get("data", [])

            for event in events:
                # Build the event dictionary
                event_dict = {
                    "source": BCP,
                    "source_id": event.get("id"),
                    "source_json": event,
                    "name": event.get("name", "Unnamed Event"),
                    "start_date": event.get("eventDate"),
                    "end_date": event.get("eventEndDate"),
                }

                # Map the game_type
                if game_type == 1:
                    event_dict["game_type"] = W40K
                elif game_type == 4:
                    event_dict["game_type"] = AOS
                elif game_type == 11:
                    event_dict["game_type"] = BOLT_ACTION
                elif game_type == 89:
                    event_dict["game_type"] = OLD_WORLD
                elif game_type == 16:
                    event_dict["game_type"] = KINGS_OF_WAR
                elif game_type == 96:
                    event_dict["game_type"] = SPEARHEAD
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Unknown game type {game_type} for event {event_dict['name']}"
                        )
                    )
                    event_dict["game_type"] = None

                # Optional fields
                if "numberOfRounds" in event:
                    event_dict["rounds"] = event["numberOfRounds"]
                if "numTickets" in event:
                    event_dict["players_count"] = event["numTickets"]
                if "pointsValue" in event:
                    event_dict["points_limit"] = event["pointsValue"]

                # Update or create the Event object
                event_obj, created = Event.objects.update_or_create(
                    source=BCP,
                    source_id=event_dict["source_id"],
                    defaults=event_dict,
                )

                action = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{action} event '{event_obj.name}' with ID {event_obj.source_id}"
                    )
                )

            # Check for pagination
            next_key = data.get("nextKey")
            if not next_key or next_key == last_key:
                self.stdout.write(self.style.SUCCESS("Finished fetching data."))
                break

            last_key = next_key
            url = f"{base_url}&nextKey={next_key}"
            self.stdout.write(
                self.style.SUCCESS(f"Fetching next batch with nextKey: {next_key}")
            )
