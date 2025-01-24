import csv
import datetime

from django.db.models import Q
from django.http import HttpResponse

from data.models import (
    List,
    Pairing,
    AOS,
    BCP,
    ECKSEN,
    SNL,
    W40K,
    OLD_WORLD,
    KINGS_OF_WAR, SPEARHEAD,
)


def raw_list(request, list_id):
    list = List.objects.get(id=list_id)
    return HttpResponse(list.raw_list.replace("\n", "<br>"))


def event_lists(request, event_id):
    lists = List.objects.filter(Q(participant__event__id=event_id))
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="lists.csv"'

    writer = csv.writer(
        response,
        quoting=csv.QUOTE_NONNUMERIC,
    )
    writer.writerow(
        [
            "player_name",
            "event_name",
            "event_date",
            "event_end_date",
            "event_country",
            "event_online",
            "season",
            "player_faction",
            "player_subfaction",
            "grand_strategy",
            "player_list_url",
            "source",
        ]
    )

    for list in lists:
        if list.participant.event.source == BCP:
            player_name = f"{list.participant.source_json['firstName']} {list.participant.source_json['lastName']}"
        if (
            list.participant.event.source_json
            and "country" in list.participant.event.source_json
        ):
            event_country = list.participant.event.source_json["country"]
        else:
            event_country = ""
        if "isOnlineEvent" in list.participant.event.source_json:
            event_online = list.participant.event.source_json["isOnlineEvent"]
        else:
            event_online = False
        list_faction = list.faction if list.faction else ""
        list_subfaction = list.subfaction if list.subfaction else ""

        if len(list.raw_list) > 10000:
            list.raw_list = "List too long"

        writer.writerow(
            [
                player_name,
                list.participant.event.name,
                list.participant.event.start_date,
                list.participant.event.end_date,
                event_country,
                event_online,
                "2023",
                list_faction,
                list_subfaction,
                list.grand_strategy,
                list.raw_list,
                "bcp" if list.participant.event.source == BCP else "snl",
            ]
        )

    return response


def export_pairings_as_csv(request, game_type: int = AOS):
    daterange_start = datetime.date.today() - datetime.timedelta(days=30)
    daterange_end = datetime.date.today()
    pairings = Pairing.objects.filter(
        Q(event__start_date__range=[daterange_start, daterange_end])
        & Q(event__rounds__in=[3, 5, 6, 8])
        & Q(event__game_type=game_type)
    ).order_by("event__name", "-event__start_date", "round", "id")

    response = HttpResponse(content_type="text/csv")
    if game_type == AOS:
        output_game = "aos"
    elif game_type == W40K:
        output_game = "40k"
    elif game_type == OLD_WORLD:
        output_game = "old_world"
    elif game_type == KINGS_OF_WAR:
        output_game = "kow"
    elif game_type == SPEARHEAD:
        output_game = "spearhead"
    output_name = f"pairings_{output_game}_{daterange_start}_{daterange_end}.csv"
    response["Content-Disposition"] = f'attachment; filename="{output_name}"'

    writer = csv.writer(
        response,
        quoting=csv.QUOTE_NONNUMERIC,
    )
    writer.writerow(
        [
            "pairing_id",
            "round",
            "winner_name",
            "loser_name",
            "is_draw",
            "winner_score",
            "loser_score",
            "event_name",
            "event_date",
            "event_end_date",
            "event_country",
            "event_online",
            "season",
            "winner_faction",
            "winner_subfaction",
            "loser_faction",
            "loser_subfaction",
            "winner_list_url",
            "loser_list_url",
            "winner_drops",
            "loser_drops",
            "winner_points",
            "loser_points",
            "winner_manifestation_lore",
            "loser_manifestation_lore",
            "winner_spell_lore",
            "loser_spell_lore",
            "winner_prayer_lore",
            "loser_prayer_lore",
            "source",
            "is_draw",
        ]
    )

    for pairing in pairings:
        # Determine player names based on event source
        if pairing.event.source == BCP:
            winner_name = (
                f"{pairing.winner.player.source_json['firstName']} {pairing.winner.player.source_json['lastName']}"
                if pairing.winner
                else ""
            )
            loser_name = (
                f"{pairing.loser.player.source_json['firstName']} {pairing.loser.player.source_json['lastName']}"
                if pairing.loser
                else ""
            )
        elif pairing.event.source == ECKSEN:
            winner_name = pairing.winner.player.source_json["name"] if pairing.winner else ""
            loser_name = pairing.loser.player.source_json["name"] if pairing.loser else ""
        else:
            winner_name = pairing.winner.player.source_json["playerName"] if pairing.winner else ""
            loser_name = pairing.loser.player.source_json["playerName"] if pairing.loser else ""

        # Determine event country and if it's an online event
        event_country = pairing.event.source_json.get("country", "")
        event_online = pairing.event.source_json.get("isOnlineEvent", False)

        # Faction and subfaction based on winner/loser lists
        if pairing.event.game_type == OLD_WORLD:
            winner_list_faction = pairing.winner_list.source_json.get("armyName", "") if pairing.winner_list else ""
            loser_list_faction = pairing.loser_list.source_json.get("armyName", "") if pairing.loser_list else ""
            winner_list_subfaction = loser_list_subfaction = ""
        else:
            winner_list_faction = pairing.winner_list.faction if pairing.winner_list else ""
            loser_list_faction = pairing.loser_list.faction if pairing.loser_list else ""
            winner_list_subfaction = pairing.winner_list.subfaction if pairing.winner_list else ""
            loser_list_subfaction = pairing.loser_list.subfaction if pairing.loser_list else ""

        # Handle long lists
        if pairing.winner_list and len(pairing.winner_list.raw_list) > 10000:
            pairing.winner_list.raw_list = "List too long"
        if pairing.loser_list and len(pairing.loser_list.raw_list) > 10000:
            pairing.loser_list.raw_list = "List too long"

        # Determine drops, points, lore for winner and loser
        winner_drops = pairing.winner_list.drops if pairing.winner_list else None
        loser_drops = pairing.loser_list.drops if pairing.loser_list else None
        winner_points = pairing.winner_list.points if pairing.winner_list else None
        loser_points = pairing.loser_list.points if pairing.loser_list else None
        winner_manifestation_lore = pairing.winner_list.manifestation_lore if pairing.winner_list else ""
        loser_manifestation_lore = pairing.loser_list.manifestation_lore if pairing.loser_list else ""
        winner_spell_lore = pairing.winner_list.spell_lore if pairing.winner_list else ""
        loser_spell_lore = pairing.loser_list.spell_lore if pairing.loser_list else ""
        winner_prayer_lore = pairing.winner_list.prayer_lore if pairing.winner_list else ""
        loser_prayer_lore = pairing.loser_list.prayer_lore if pairing.loser_list else ""

        # Determine source
        if pairing.event.source == BCP:
            source = "bcp"
        elif pairing.event.source == ECKSEN:
            source = "ecksen"
        elif pairing.event.source == SNL:
            source = "snl"
        else:
            source = "unknown"

        # Write the row to the CSV
        writer.writerow(
            [
                pairing.id,
                pairing.round,
                winner_name,
                loser_name,
                pairing.is_draw,
                pairing.winner_score,
                pairing.loser_score,
                pairing.event.name,
                pairing.event.start_date,
                pairing.event.end_date,
                event_country,
                event_online,
                "2024",  # Assuming season for now, can be dynamically set if needed
                winner_list_faction,
                winner_list_subfaction,
                loser_list_faction,
                loser_list_subfaction,
                pairing.winner_list.raw_list if pairing.winner_list else "",
                pairing.loser_list.raw_list if pairing.loser_list else "",
                winner_drops,
                loser_drops,
                winner_points,
                loser_points,
                winner_manifestation_lore,
                loser_manifestation_lore,
                winner_spell_lore,
                loser_spell_lore,
                winner_prayer_lore,
                loser_prayer_lore,
                source,
                pairing.is_draw,
            ]
        )

    return response
