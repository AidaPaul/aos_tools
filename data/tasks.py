import json
from copy import copy

from celery import shared_task
from django.conf import settings
from django.db import DataError

from data.management.commands.detect_faction import regexp_army_details_aos, \
    ask_chat_gpt
from data.models import *
import requests

from data.models import List, aos_factions, aos_subfactions

redis_client = settings.REDIS_CLIENT


@shared_task
def fetch_list(list_id: int):
    current_list = List.objects.get(id=list_id)
    url = f"https://newprod-api.bestcoastpairings.com/v1/armylists/{current_list.source_id}"
    headers = json.loads(redis_client.get("BCP_HEADERS") or "{}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data for {current_list.id}, code: {response.status_code} body response: {response.text}"
        )
    data = response.json()
    current_list.source_json = data
    if "armyListText" in data:
        current_list.raw_list = data["armyListText"]
    current_list.save()
    print(f"Stored list {current_list.id}")
    return True


@shared_task()
def fetch_pairings_for_event(event_id: int):
    event = Event.objects.get(id=event_id)
    current_round = 0
    max_rounds = event.rounds
    headers = json.loads(redis_client.get("BCP_HEADERS") or "{}")
    if max_rounds is None:
        return
    while current_round <= max_rounds:
        current_round += 1
        url = f"https://newprod-api.bestcoastpairings.com/v1/pairings?limit=500&eventId={event.source_id}&round={current_round}&pairingType=Pairing&expand[]=player1&expand[]=player2&expand[]=player1Game&expand[]=player2Game"
        base_url = copy(url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch data for {event.name}, code: {response.status_code} body response: {response.text}"
            )
        data = response.json()
        last_key = None
        while "nextKey" in response.json():
            for pairing in data["data"]:
                if len(pairing.get("player1", {})) == 0 or len(pairing.get("player2", {})) == 0:
                    continue

                # Initialize variables
                winner_player = None
                loser_player = None
                is_draw = False

                # Build participants dictionary
                participants = {}
                for player in ["player1", "player2"]:
                    player_data = pairing.get(player, {})
                    player_dict = {
                        "source": BCP,
                        "source_json": player_data,
                    }
                    player_id = player_data.get("id")
                    if player_id:
                        player_dict["source_id"] = player_id
                    else:
                        raise Exception(
                            f"Failed to fetch data for {event.name}, no player id in pairing"
                        )
                    player_instance, _ = Player.objects.update_or_create(
                        source=BCP,
                        source_id=player_id,
                        defaults=player_dict,
                    )
                    participant_dict = {
                        "event": event,
                        "player": player_instance,
                        "source_json": player_data,
                    }
                    participant_dict["army_source_id"] = player_data.get("armyListObjectId")
                    participant_dict["army_id"] = player_data.get("armyId")
                    participant_instance, _ = Participant.objects.update_or_create(
                        event=event,
                        player=player_instance,
                        defaults=participant_dict,
                    )
                    participants[player] = participant_instance

                # Determine the winner and loser based on game results or scores
                player1_game = pairing.get("player1Game", {})
                player2_game = pairing.get("player2Game", {})
                player1_result = player1_game.get("gameResult")
                player2_result = player2_game.get("gameResult")
                player1_score = player1_game.get("gamePoints")
                player2_score = player2_game.get("gamePoints")

                # Map game results to standard outcomes
                if player1_result == "Draw" or player2_result == "Draw":
                    is_draw = True
                elif player1_result == "Win" and player2_result == "Loss":
                    winner_player = "player1"
                    loser_player = "player2"
                elif player2_result == "Win" and player1_result == "Loss":
                    winner_player = "player2"
                    loser_player = "player1"
                elif player1_score is not None and player2_score is not None:
                    if player1_score > player2_score:
                        winner_player = "player1"
                        loser_player = "player2"
                    elif player2_score > player1_score:
                        winner_player = "player2"
                        loser_player = "player1"
                    else:
                        is_draw = True
                else:
                    # If no clear winner, consider it a draw
                    is_draw = True

                pairing_dict = {
                    "source_id": pairing["id"],
                    "source_json": pairing,
                    "event": event,
                    "round": current_round,
                    "is_draw": is_draw,
                }

                if not is_draw and winner_player and loser_player:
                    pairing_dict["winner"] = participants[winner_player]
                    pairing_dict["loser"] = participants[loser_player]
                else:
                    pairing_dict["winner"] = None
                    pairing_dict["loser"] = None

                # Assign scores
                if player1_score is not None and player2_score is not None:
                    if not is_draw and winner_player == "player1":
                        pairing_dict["winner_score"] = player1_score
                        pairing_dict["loser_score"] = player2_score
                    elif not is_draw and winner_player == "player2":
                        pairing_dict["winner_score"] = player2_score
                        pairing_dict["loser_score"] = player1_score
                    else:
                        # In case of draw or unknown winner, assign scores without labels
                        pairing_dict["winner_score"] = player1_score
                        pairing_dict["loser_score"] = player2_score
                else:
                    pairing_dict["winner_score"] = None
                    pairing_dict["loser_score"] = None

                # Assign lists
                if "armyListObjectId" in pairing["player1"]:
                    list1, _ = List.objects.update_or_create(
                        source_id=pairing["player1"]["armyListObjectId"],
                        defaults={
                            "source_json": pairing["player1"],
                            "participant": participants["player1"],
                        },
                    )
                    if not is_draw and winner_player == "player1":
                        pairing_dict["winner_list"] = list1
                    elif not is_draw and loser_player == "player1":
                        pairing_dict["loser_list"] = list1
                if "armyListObjectId" in pairing["player2"]:
                    list2, _ = List.objects.update_or_create(
                        source_id=pairing["player2"]["armyListObjectId"],
                        defaults={
                            "source_json": pairing["player2"],
                            "participant": participants["player2"],
                        },
                    )
                    if not is_draw and winner_player == "player2":
                        pairing_dict["winner_list"] = list2
                    elif not is_draw and loser_player == "player2":
                        pairing_dict["loser_list"] = list2

                # Prepare information for printing
                winner_id = participants[winner_player].player.source_id if winner_player else "None"
                loser_id = participants[loser_player].player.source_id if loser_player else "None"
                player1_id = participants["player1"].player.source_id
                player2_id = participants["player2"].player.source_id
                player1_score_str = str(player1_score) if player1_score is not None else "N/A"
                player2_score_str = str(player2_score) if player2_score is not None else "N/A"

                print(
                    f"Event: {event.name}, Round {current_round}: "
                    f"Winner ID: {winner_id}, Loser ID: {loser_id}, Draw: {is_draw}\n"
                    f"Player1 ID: {player1_id}, Score: {player1_score_str}; "
                    f"Player2 ID: {player2_id}, Score: {player2_score_str}"
                )

                try:
                    Pairing.objects.update_or_create(
                        source_id=pairing["id"], defaults=pairing_dict
                    )
                except Exception as e:
                    continue
            next_key = data["nextKey"]
            if next_key == last_key:
                break
            last_key = next_key
            url = f"{base_url}&nextKey={next_key}"
            response = requests.get(url, headers=headers)
            data = response.json()
    return True


@shared_task
def extract_faction_details_for_aos(army_list_id: int):
    army_list = List.objects.get(id=army_list_id)
    list_text = army_list.raw_list
    prompt = f"""
    For given list of Age of Sigmar please fill in the following fields and return it as json document: {{"faction": string,"subfaction": string,"drops: int, "points": int,"manifestation_lore": string,"prayer_lore": string,"spell_lore": string}}
    
    Return only the json document, with no wrapper, markings or other commentary. If there are multiple lists, only process the first one, never return more than 1 set of requested data. Remove any text from it that's not directly the subfaction or faction.

    Valid list of factions: aos_factions = [
        "Beasts of Chaos",
        "Blades of Khorne",
        "Bonesplitterz",
        "Cities of Sigmar",
        "Daughters of Khaine",
        "Disciples of Tzeentch",
        "Flesh-Eater Courts",
        "Fyreslayers",
        "Gloomspite Gitz",
        "Hedonites of Slaanesh",
        "Idoneth Deepkin",
        "Ironjawz",
        "Kharadron Overlords",
        "Kruleboyz",
        "Lumineth Realm-lords",
        "Maggotkin of Nurgle",
        "Nighthaunt",
        "Ogor Mawtribes",
        "Ossiarch Bonereapers",
        "Seraphon",
        "Skaven",
        "Slaves to Darkness",
        "Sons of Behemat",
        "Soulblight Gravelords",
        "Stormcast Eternals",
        "Sylvaneth",
    ]
    
    Valid list of subfactions: aos_subfactions = [
        "Fortress-City Defenders",
        "Collegiate Arcane Expedition",
        "Dawnbringer Crusade",
        "Ironweld Guild Army",
        "Scáthcoven",
        "Shadow Patrol",
        "Cauldron Guard",
        "Slaughter Troupe",
        "Scales of Vulcatrix",
        "Forge Brethren",
        "Warrior Kinband",
        "Lords of the Lodge",
        "Akhelian Beastmasters",
        "Soul-raid Ambushers",
        "Isharann Council",
        "Namarti Corps",
        "Endrineers Guild Expeditionary Force",
        "Iron Sky Attack Squadron",
        "Grundcorps Wing",
        "Aether-runners",
        "Vanari Battlehost",
        "Alarith Temple",
        "Scinari Council",
        "Hurakan Temple",
        "Thunderhead Host",
        "Lightning Echelon",
        "Vanguard Wing",
        "Sentinels of the Bleak Citadels",
        "Eternal Starhost",
        "Shadowstrike Starhost",
        "Sunclaw Starhost",
        "Thunderquake Starhost",
        "Lords of the Clan",
        "Outcasts",
        "Free Spirits",
        "Forest Folk",
        "Death Battle formations",
        "Cannibal Court",
        "Ghoul Patrol",
        "Lords of the Manor",
        "Royal Menagerie",
        "Vanishing Phantasms",
        "Hunters of the Accursed",
        "Death Stalkers",
        "Procession of Death",
        "Mortisan Council",
        "Mortek Phalanx",
        "Kavalos Lance",
        "Mortek Ballistari",
        "Legion of Shyish",
        "Deathstench Drove",
        "Bacchanal of Blood",
        "Deathmarch",
        "Marauding Brayherd",
        "Hungering Warherd",
        "Almighty Beastherd",
        "Thunderscorn Stormherd",
        "Depraved Carnival",
        "Epicurean Revellers",
        "Seeker Cavalcade",
        "Supreme Sybarites",
        "Khornate Legion",
        "Brass Stampede",
        "Murder Host",
        "Bloodbound Warhorde",
        "Tallyband of Nurgle",
        "Plague Cyst",
        "Nurgle’s Menagerie",
        "Affliction Cyst",
        "Despoilers",
        "Darkoath Horde",
        "Godsworn Warband",
        "Legion of Chaos",
        "Claw-Horde",
        "Fleshmeld Menargerie",
        "Virulent Procession",
        "Warpog Convocation",
        "Arcanite Cabal",
        "Tzaangor Coven",
        "Change Host",
        "Wyrdflame Host",
        "Kunnin' Rukk",
        "Snaga Rukk",
        "Brutal Rukk",
        "Kop Rukk",
        "Squigalanch",
        "Moonclan Skrap",
        "Troggherd",
        "Spiderfang Stalktribe",
        "Prophets of the Gulping God",
        "Heralds of the Everwinter",
        "Beast Handlers",
        "Blackpowder Fanatics",
        "Ironfist",
        "Weirdfist",
        "Ironjawz Brawl",
        "Grunta Stampede",
        "Kruleboyz Klaw",
        "Middul Finga",
        "Light Finga",
        "Trophy Finga",
        "Taker Tribe",
        "Breaker Tribe",
        "Stomper Tribe",
        "Boss Tribe",
    ]
    
    and valid manifestation lores = [
        "Manifestations of Tzeentch",
        "Manifestations of Malevolence",
        "Judgements of Khorne",
        "Manifestations of Depravity",
        "Manifestations of Doom",
        "Bestial Manifestations",
        "Chthonic Sorceries",
        "Manifested Insanity",
        "Horrors of the Necropolis",
        "Dank Manifestations",
        "Manifestations of Hysh",
        "Magmic Invocations",
        "Manifestations of Khaine",
        "Manifestations of the Deepwood",
        "Manifestations of the Storm",
        "Krondspine Incarnate",
        "Morbid Conjuration",
        "Primal Energy",
        "Aetherwrought Machineries",
        "Forbidden Power",
        "Twilit Sorceries",
    ]


    Ignore how the faction in the list is written, just match it to the closest faction in the
    above and return that faction if there is a match (typos and shorthand are expected). If the faction is not in the list, return "False", if the subfaction is not in the list of subfactions, return "False".

    Additionally calculate number of drops, each regiment (defined explicitly as regiment, not a unit belonging to it) or auxiliary troop in a list counts as one drop. Points usually are noted above unit in parenthesis, but it's not a given.
    
    If available also extract manifestation, spell and player lore, but if it's not available simply put down false instead of guessing

    list:

                {list_text}
                """
    # try:
    #     details = regexp_army_details_aos(list_text)
    #     faction = details["faction"]
    #     if "\t" in faction:
    #         faction = faction.split("\t")[0]
    #     if " - " in faction:
    #         faction = faction.split(" - ")[0]
    #     subfaction = details["subfaction"]
    #     grand_strategy = details["grand_strategy"]
    #     army_list.manifestation_lores = details.get("manifestation_lore", None)
    #     army_list.prayer_lores = details.get("prayer_lore", None)
    #     army_list.spell_lores = details.get("spell_lore", None)
    #     army_list.drops = details.get("drops", None)
    #     army_list.points = details.get("points", None)
    #     army_list.faction = faction
    #     army_list.subfaction = subfaction
    #     army_list.grand_strategy = grand_strategy
    #     army_list.save()
    #     print(
    #         f"Detected faction: {faction} and subfaction: {subfaction} for {army_list.source_id} using regex"
    #     )
    #     army_list.regexp_parsed = True
    #     army_list.save()
    #     return True
    # except (ValueError, DataError) as e:
    #     print(
    #         f"Failed to detect faction for {army_list.source_id} error: {e} using regex"
    #     )
    response = ask_chat_gpt(prompt)
    try:
        payload = json.loads(response.replace("```", "").replace("json", ""))
    except json.decoder.JSONDecodeError as e:
        print(f"Failed to decode json for {army_list.source_id} error: {e}")
        army_list.gpt_parsed = True
        army_list.gpt_parse_error = e
        return False
    try:
        if payload["faction"] not in aos_factions:
            print(f"Faction {payload['faction']} not recognized.")
            payload["faction"] = None
        army_list.faction = payload["faction"]
        if payload["subfaction"] not in aos_subfactions:
            print(f"Subfaction {payload['subfaction']} not recognized.")
            payload["subfaction"] = None
        army_list.subfaction = payload["subfaction"]
        army_list.manifestation_lore = payload.get("manifestation_lore", None)
        army_list.prayer_lore = payload.get("prayer_lore", None)
        army_list.spell_lore = payload.get("spell_lore", None)
        army_list.drops = payload.get("drops", None)
        army_list.points = payload.get("points", None)
        if type(army_list.points) != int:
            army_list.points = None
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
        army_list.gpt_parsed = True
        army_list.gpt_parse_error = e
        army_list.save()
    try:
        army_list.save()
        army_list.gpt_parsed = True
        army_list.save()
    except DataError as e:
        print(f"Failed to save faction for {army_list.source_id} error: {e}")
        army_list.gpt_parsed = True
        army_list.gpt_parse_error = e
        army_list.save()
    print(
        f"Detected faction: {army_list.faction} and subfaction: {army_list.subfaction} for {army_list.source_id} using gpt"
    )
    return True

@shared_task
def extract_faction_details_for_spearhead(army_list_id: int):
    army_list = List.objects.get(id=army_list_id)
    if "army" in army_list.source_json:
        faction = army_list.source_json["army"]["name"]
        army_list.faction = faction
        army_list.save()
        print(f"Extracted faction details for {army_list.source_id}")
        return
    print(f"Failed to extract faction details for {army_list.source_id}")