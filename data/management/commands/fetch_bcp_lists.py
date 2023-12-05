import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from data.tasks import fetch_list

from data.models import *
import requests


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
        lists = List.objects.filter(
            Q(source_id__isnull=False) & (Q(raw_list__isnull=True) | Q(raw_list=""))
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
            self.stdout.write(f"Finished fetching lists")
