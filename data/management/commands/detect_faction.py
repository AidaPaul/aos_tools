import json
import re

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DataError
from django.db.models import Q, F

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


def regexp_army_details_aos(text):
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


def extract_faction_details_for_aos(army_list_id: int):
    army_list = List.objects.get(id=army_list_id)
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
    try:
        details = regexp_army_details_aos(list_text)
        faction = details["faction"]
        if "\t" in faction:
            faction = faction.split("\t")[0]
        if " - " in faction:
            faction = faction.split(" - ")[0]
        subfaction = details["subfaction"]
        grand_strategy = details["grand_strategy"]
        army_list.faction = faction
        army_list.subfaction = subfaction
        army_list.grand_strategy = grand_strategy
        army_list.save()
        print(
            f"Detected faction: {faction} and subfaction: {subfaction} for {army_list.source_id} using regex"
        )
        army_list.regexp_parsed = True
        army_list.save()
        return True
    except (ValueError, DataError) as e:
        print(
            f"Failed to detect faction for {army_list.source_id} error: {e} using regex"
        )
    response = ask_chat_gpt(prompt)
    payload = None
    try:
        payload = json.loads(response.replace("```", "").replace("json", ""))
    except json.decoder.JSONDecodeError as e:
        print(f"Failed to decode json for {army_list.source_id} error: {e}")
        army_list.gpt_parsed = True
        army_list.gpt_parse_error = e
        return False
    try:
        army_list.faction = payload["faction"]
        army_list.subfaction = payload["subfaction"]
        if army_list.faction == "":
            army_list.faction = None
        if army_list.subfaction == "":
            army_list.subfaction = None
        if "grand_strategy" in payload:
            army_list.grand_strategy = payload["grand_strategy"]
    except KeyError as e:
        print(
            f"Failed to detect faction for {army_list.source_id} error: {e} using gpt"
        )
    try:
        army_list.save()
        army_list.gpt_parsed = True
        army_list.save()
    except DataError as e:
        print(f"Failed to save faction for {army_list.source_id} error: {e}")
    print(
        f"Detected faction: {army_list.faction} and subfaction: {army_list.subfaction} for {army_list.source_id} using gpt"
    )
    return True


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

    def handle(self, *args, **options):
        army_lists = (
            List.objects.exclude(Q(raw_list=""))
            .filter(Q(faction__isnull=True))
            .annotate(event_date=F("participant__event__start_date"))
            .annotate(game_type=F("participant__event__game_type"))
            .filter(game_type__in=[W40K])
            .filter(event_date__gte="2023-07-01")
            .filter(~Q(raw_list="") | ~Q(raw_list__isnull=True))
        )
        self.stdout.write(f"Detecting for {army_lists.count()} lists")
        for army_list in army_lists:
            if army_list.game_type == AOS:
                extract_faction_details_for_aos(army_list.id)
            elif army_list.game_type == W40K:
                extract_faction_details_for_40k(army_list.id)
        print(failed_factions)
