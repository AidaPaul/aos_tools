from copy import copy

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import time

from data.models import Event, BCP, W40K, BOLT_ACTION, AOS, OLD_WORLD, \
    KINGS_OF_WAR


class Command(BaseCommand):
    help = "Refresh BCP token"

    def handle(self, *args, **options):
        # do this every 5 minutes until command stops
        while True:
            headers = settings.BCP_HEADERS
            url = "https://newprod-api.bestcoastpairings.com/v1/users/refreshtokens"
            body = {
                "refreshToken": settings.BCP_REFRESH_TOKEN
            }
            response = requests.post(url, json=body, headers=headers)
            if response.status_code != 200:
                raise CommandError(
                    f"Failed to refresh token, code: {response.status_code} body response: {response.text}"
                )
            data = response.json()
            headers["Authorization"] = f"Bearer {data['accessToken']}"
            settings.BCP_HEADERS = headers
            self.stdout.write(self.style.SUCCESS("Successfully refreshed token"))
            time.sleep(300)
