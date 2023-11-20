import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DataError
from django.db.models import Q
import json

from data.models import *
import requests


class Command(BaseCommand):
    help = "Detect GHB for events for downloaded lists"

    def handle(self, *args, **options):
        for event in Event.objects.filter(season__isnull=True):
            grand_strategies = []
            for list in List.objects.filter(participant__event=event):
                if list.grand_strategy and list.grand_strategy not in grand_strategies:
                    grand_strategies.append(list.grand_strategy)
            if len(grand_strategies) == 0:
                continue
            # check if any of the grandstrategies match _STRATEGIES constants
            season_consts = [
                GHB_2022S1_STRATEGIES,
                GHB_2022S2_STRATEGIES,
                GHB_2023_STRATEGIES,
            ]

            for season in season_consts:
                # see if any of the grand strategies match
                for grand_strategy in grand_strategies:
                    if grand_strategy in season:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Detected {grand_strategy} in {event.name}"
                            )
                        )
                        if season == GHB_2022S1_STRATEGIES:
                            event.season = GHB_2022S1
                        elif season == GHB_2022S2_STRATEGIES:
                            event.season = GHB_2022S2
                        elif season == GHB_2023_STRATEGIES:
                            event.season = GHB_2023
                        event.save()
                        break
            if not event.season:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to detect season for {event.name} with grand strategies {grand_strategies}"
                    )
                )
