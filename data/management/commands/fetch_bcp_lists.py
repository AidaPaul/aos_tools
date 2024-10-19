import datetime

from django.core.management.base import BaseCommand
from django.db.models import Q

from data.models import *
from data.tasks import fetch_list
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = "Fetch events from BCP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--celery",
            action="store_true",
            dest="celery",
            default=False,
            help="Use celery to fetch lists",
        )

    def handle(self, *args, **options):
        date_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)

        lists = List.objects.filter(
            Q(source_id__isnull=False) & (Q(raw_list__isnull=True) | Q(raw_list=""))
        ).filter(participant__event__start_date__gte=date_month_ago)

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
            self.stdout.write(f"Finished fetching lists")
