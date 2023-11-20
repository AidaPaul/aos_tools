import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import json

from data.models import *
import requests


def ask_chat_gpt(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "model": "gpt-3.5-turbo-1106",
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


def extract_army_details(text):
    faction_match = re.search(r"(Faction|Allegiance): (.+)", text)
    subfaction_match = re.search(
        r"(Subfaction|Glade|Stormhost|Mawtribe|Lodge|Legion|Constellation): ([\w+ \-\_]*)",
        text,
    )
    grand_strategy_match = re.search(r"Grand Strategy: ([\w+ \-\_]*)", text)

    if faction_match:
        faction = faction_match.group(2).strip()
    else:
        raise ValueError("Faction not detected in the input text.")

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


class Command(BaseCommand):
    help = "Detect Faction and Subfaction for downloaded lists"

    def handle(self, *args, **options):
        headers = settings.BCP_HEADERS
        for army_list in List.objects.exclude(Q(raw_list="")).filter(
            Q(faction__isnull=True)
        ):
            list_text = army_list.raw_list
            prompt = f"""
For given list of Age of Sigmar please fill in the following fields and return it as json document. Fields: `faction, subfaction` and unify them to original names from the game. Return only the json document, with no wrapper, markings or other commentary. If there are multiple lists, only process the first one, never return more than 1 set of requested data. Remove any text from it that's not directly the subfaction or faction.

Valid list of factions: aos_factions = [
    "Stormcast Eternals",
    "Daughters of Khaine",
    "Fyreslayers",
    "Idoneth Deepkin",
    "Kharadron Overlords",
    "Lumineth Realm-lords",
    "Sylvaneth",
    "Seraphon",
    "Cities of Sigmar",
    "Slaves to Darkness",
    "Blades of Khorne",
    "Disciples of Tzeentch",
    "Hedonites of Slaanesh",
    "Maggotkin of Nurgle",
    "Skaven",
    "Beasts of Chaos",
    "Legion of Azgorh",
    "Flesh-eater Courts",
    "Nighthaunt",
    "Ossiarch Bonereapers",
    "Soulblight Gravelords",
    "Orruk Warclans",
    "Gloomspite Gitz",
    "Sons of Behemat",
]

you must be sure that the list is in one of those factions.

Additionally return grand_strategy field where available

list:

            {list_text}
            """
            self.stdout.write(
                self.style.SUCCESS(f"Detecting with regexp for {army_list.source_id}")
            )
            faction = None
            subfaction = None
            grand_strategy = None
            try:
                raise ValueError("Fallback to gpt")
                details = extract_army_details(list_text)
                faction = details["faction"]
                subfaction = details["subfaction"]
                grand_strategy = details["grand_strategy"]
                army_list.faction = faction
                army_list.subfaction = subfaction
                army_list.grand_strategy = grand_strategy
                army_list.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully regexpec faction for {army_list.source_id}"
                    )
                )
                army_list.regexp_parsed = True
                army_list.save()
                continue
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f"Fallback to gpt to detect army details {army_list.source_id}"
                    )
                )
            response = ask_chat_gpt(prompt)
            try:
                payload = json.loads(response)
            except json.decoder.JSONDecodeError as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to parse response for {army_list.source_id}"
                    )
                )
                army_list.gpt_parsed = True
                army_list.gpt_parse_error = e
                continue
            try:
                army_list.faction = payload["faction"]
                army_list.subfaction = payload["subfaction"]
                if army_list.faction == "":
                    army_list.faction = None
                if army_list.subfaction == "":
                    army_list.subfaction = None
                if "grand_strategy" in payload:
                    army_list.grand_strategy = payload["grand_strategy"]
            except KeyError:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to detect faction for {army_list.source_id}"
                    )
                )
                continue
            army_list.save()
            army_list.gpt_parsed = True
            army_list.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully detected faction for {army_list.source_id}"
                )
            )
