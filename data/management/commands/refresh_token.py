import json
from copy import copy

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import time

from data.models import Event, BCP, W40K, BOLT_ACTION, AOS, OLD_WORLD, KINGS_OF_WAR


class Command(BaseCommand):
    help = "Refresh BCP token"

    def handle(self, *args, **options):
        redis_client = settings.REDIS_CLIENT

        while True:
            headers = settings.BCP_HEADERS
            url = "https://newprod-api.bestcoastpairings.com/v1/users/refreshtokens"
            body = {"refreshToken": settings.BCP_REFRESH_TOKEN}
            response = requests.post(url, json=body, headers=headers)
            if response.status_code != 200:
                raise CommandError(
                    f"Failed to refresh token, code: {response.status_code} body response: {response.text}"
                )
            data = response.json()
            bcp_headers = settings.BCP_HEADERS
            bcp_headers["Authorization"] = f"Bearer {data['accessToken']}"
            redis_client.set("BCP_HEADERS", json.dumps(headers))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully refreshed token, new token: {data['accessToken']}"
                )
            )
            time.sleep(60)
