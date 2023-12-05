import requests
from celery import shared_task
from django.conf import settings

from data.models import List

headers = settings.BCP_HEADERS

from celery.contrib import rdb


@shared_task
def fetch_list(list_id: int):
    current_list = List.objects.get(id=list_id)
    url = f"https://prod-api.bestcoastpairings.com/armylists/{current_list.source_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data for {current_list.name}, code: {response.status_code} body response: {response.text}"
        )
    data = response.json()
    current_list.source_json = data
    if "armyListText" in data:
        current_list.raw_list = data["armyListText"]
    current_list.save()
    return True
