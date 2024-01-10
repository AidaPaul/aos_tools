from django.core.management.base import BaseCommand

from data.models import *
from data.tasks import fetch_pairings_for_event


class Command(BaseCommand):
    help = "Fetch pairings for events from BCP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--celery",
            action="store_true",
            dest="celery",
            default=False,
            help="Use celery to fetch lists",
        )

    def handle(self, *args, **options):
        events = (
            Event.objects.filter(source=BCP)
            # .filter(game_type__in=[W40K])
            .filter(start_date__gte="2024-01-01")
        )
        self.stdout.write(f"Fetching data for {events.count()} events")
        tasks = []
        for event in events:
            if options["celery"]:
                tasks.append(fetch_pairings_for_event.delay(event.id))
            else:
                fetch_pairings_for_event(event.id)

        if options["celery"]:
            self.stdout.write(f"Started {len(tasks)} tasks")
        else:
            self.stdout.write(f"Finished fetching pairings")
