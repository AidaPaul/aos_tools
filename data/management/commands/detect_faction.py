import json
import re

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q, F
from redis import DataError

from data.models import *

failed_factions = {}


def ask_chat_gpt(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "model": "gpt-4o-mini",
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    }

    success = False
    while success is False:
        try:
            response = requests.post(
                url, data=json.dumps(payload), headers=headers, timeout=10
            )
            success = True
        except requests.exceptions.Timeout:
            pass
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")
        return data["choices"][0]["message"]["content"].strip()
    else:
        raise ValueError(
            f"Request failed with status code {response.status_code} and {response.text}"
        )


def regexp_army_details_aos(text):
    faction_match = re.search(r"(Faction|Allegiance): (.+)", text)
    subfaction_match = re.search(
        r"(Subfaction|Glade|Stormhost|Mawtribe|Lodge|Legion|Constellation|Slaughterhost|Slaughterhosts|Tribe|Temple|Warclan|Host of Chaos|Enclave|Army Type|Lineage|Procession|City|Grand Court|Great Nation|Greatfray|Sky Port|Change Coven|Glade|Host|Option): ([\w+ \-\_]*)",
        text,
    )
    grand_strategy_match = re.search(r"Grand Strategy: ([\w+ \-\_]*)", text)

    if faction_match:
        faction = faction_match.group(2).strip()
    else:
        raise ValueError("Faction not detected in the input text.")

    if faction == "Nurgle":
        faction = "Maggotkin of Nurgle"
    elif faction == "Khorne":
        faction = "Blades of Khorne"
    elif faction == "Slaanesh":
        faction = "Hedonites of Slaanesh"
    elif faction == "Tzeentch":
        faction = "Disciples of Tzeentch"
    elif "Soulblight Gravelords" in faction:
        faction = "Soulblight Gravelords"

    if faction not in aos_factions:
        raise ValueError(f"Faction {faction} not recognized.")

    if subfaction_match:
        subfaction = subfaction_match.group(2).strip()
    else:
        raise ValueError("Subfaction not detected in the input text.")

    if grand_strategy_match:
        grant_strategy = grand_strategy_match.group(1).strip()
    else:
        grant_strategy = None

    return {
        "faction": faction,
        "subfaction": subfaction,
        "grand_strategy": grant_strategy,
    }


def extract_faction_details_for_40k(id):
    army_list = List.objects.get(id=id)
    list_text = army_list.raw_list
    list_text = list_text.replace("’", "'")
    faction_in_text = next(
        (faction for faction in w40k_factions if faction.lower() in list_text.lower()),
        None,
    )
    if not faction_in_text:
        if "Adeptas Sororitas".lower() in list_text.lower():
            faction_in_text = "Adepta Sororitas"
        elif "Chaos Demons".lower() in list_text.lower():
            faction_in_text = "Chaos Daemons"
        elif "Termaguants".lower() in list_text.lower():
            faction_in_text = "Tyranids"
        elif "IG" in list_text:
            faction_in_text = "Astra Militarum"
        elif "Genestealer Cult".lower() in list_text.lower():
            faction_in_text = "Genestealer Cults"
        else:
            faction_in_text = next(
                (
                    faction
                    for faction in w40k_marines
                    if faction.lower() in list_text.lower()
                ),
                None,
            )
            if faction_in_text:
                faction_in_text = "Space Marines"
    if not faction_in_text:
        print(
            f"Failed to detect faction for {army_list.source_id} using text, assigning from user selection"
        )
        if "armyName" in army_list.source_json:
            selected_army = army_list.source_json["armyName"]
            if selected_army in w40k_factions:
                faction_in_text = selected_army
            elif selected_army in w40k_marines:
                faction_in_text = "Space Marines"
            elif selected_army in w40k_chaos_space_marines:
                faction_in_text = "Chaos Space Marines"
            elif selected_army in w40k_dark_angel:
                faction_in_text = "Dark Angels"
            elif "Astra Militarum".lower() == selected_army.lower():
                faction_in_text = "Astra Militarum"
            elif "GeneStealer Cult".lower() == selected_army.lower():
                faction_in_text = "Genestealer Cults"
            else:
                if selected_army not in failed_factions:
                    failed_factions[selected_army] = 1
                else:
                    failed_factions[selected_army] += 1
                faction_in_text = None
    if faction_in_text:
        army_list.faction = faction_in_text
        army_list.save()
        print(
            f"Detected faction: {faction_in_text} for {army_list.source_id} using text"
        )
        return True
    else:
        print(f"Failed to detect faction for {army_list.source_id} using text")



class Command(BaseCommand):
    help = "Detect Faction and Subfaction for downloaded lists"

    def add_arguments(self, parser):
        parser.add_argument(
            '--celery',
            action='store_true',
            help="Use Celery to process faction extraction asynchronously."
        )

    def handle(self, *args, **options):
        from data.tasks import (extract_faction_details_for_aos,
                                extract_faction_details_for_spearhead)
        use_celery = options['celery']

        army_lists = (
            List.objects.exclude(Q(raw_list=""))
            .filter(Q(faction__isnull=True))
            .annotate(event_date=F("participant__event__start_date"))
            .annotate(game_type=F("participant__event__game_type"))
            .filter(event_date__gte="2024-07-01")
            .exclude(gpt_parsed=True)
            .filter(~Q(raw_list="") | ~Q(raw_list__isnull=True))
        )

        self.stdout.write(f"Detecting for {army_lists.count()} lists")

        job_count = 0
        for army_list in army_lists:
            if army_list.game_type == AOS:
                if use_celery:
                    extract_faction_details_for_aos.delay(army_list.id)  # Asynchronous Celery task
                else:
                    extract_faction_details_for_aos(army_list.id)  # Synchronous function call
            elif army_list.game_type == SPEARHEAD:
                if use_celery:
                    extract_faction_details_for_spearhead.delay(army_list.id)  # Asynchronous Celery task
                else:
                    extract_faction_details_for_spearhead(army_list.id)  # Synchronous function call
            elif army_list.game_type == W40K:
                if use_celery:
                    extract_faction_details_for_40k.delay(army_list.id)  # Asynchronous Celery task
                else:
                    extract_faction_details_for_40k(army_list.id)  # Synchronous function call

            job_count += 1

        self.stdout.write(f"Total jobs created: {job_count}")
        self.stdout.write("All jobs dispatched.")