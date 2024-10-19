import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from data.models import List
from data.tasks import fetch_list

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Fetch lists from BCP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--celery",
            action="store_true",
            dest="celery",
            default=False,
            help="Use Celery to fetch lists",
        )

    def handle(self, *args, **options):
        date_month_ago = timezone.now() - timedelta(days=30)

        lists = List.objects.filter(
            source_id__isnull=False
        ).filter(
            Q(raw_list__isnull=True) | Q(raw_list__exact="")
        ).filter(
            participant__event__start_date__gte=date_month_ago
        )

        self.stdout.write(f"Fetching data for {lists.count()} lists")
        tasks = []
        for current_list in lists:
            if options["celery"]:
                tasks.append(fetch_list.delay(current_list.id))
            else:
                fetch_list(current_list.id)

        if options["celery"]:
            self.stdout.write(f"Started {len(tasks)} tasks")
        else:
            self.stdout.write("Finished fetching lists")
