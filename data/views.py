import csv

from django.db.models import Q
from django.http import HttpResponse

from data.models import (
    List,
    Pairing,
    AOS,
    BCP,
)


def raw_list(request, list_id):
    list = List.objects.get(id=list_id)
    return HttpResponse(list.raw_list.replace("\n", "<br>"))


def event_lists(request, event_id):
    lists = List.objects.filter(
        Q(participant__event__id=event_id)
    )
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
        if list.participant.event.source_json and "country" in list.participant.event.source_json:
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
    pairings = Pairing.objects.filter(
        Q(event__start_date__range=["2023-09-01", "2024-01-09"])
        & Q(event__rounds__in=[3, 5, 8])
        & Q(event__game_type=game_type)
    ).order_by("event__name", "-event__start_date", "round", "id")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="pairings.csv"'

    writer = csv.writer(
        response,
        quoting=csv.QUOTE_NONNUMERIC,
    )
    writer.writerow(
        [
            "pairing_id",
            "round",
            "player1_name",
            "player2_name",
            "player1_result",
            "player2_result",
            "player1_score",
            "player2_score",
            "event_name",
            "event_date",
            "event_end_date",
            "event_country",
            "event_online",
            "season",
            "player1_faction",
            "player1_subfaction",
            "player2_faction",
            "player2_subfaction",
            "player1_list_url",
            "player2_list_url",
            "source",
        ]
    )

    for pairing in pairings:
        if pairing.event.source == BCP:
            player1_name = (
                f"{pairing.player1.player.source_json['firstName']} {pairing.player1.player.source_json['lastName']}"
                if pairing.player1
                else ""
            )
            player2_name = (
                f"{pairing.player2.player.source_json['firstName']} {pairing.player2.player.source_json['lastName']}"
                if pairing.player2
                else ""
            )
        else:
            player1_name = (
                pairing.player1.player.source_json["playerName"]
                if pairing.player1
                else ""
            )
            player2_name = (
                pairing.player2.player.source_json["playerName"]
                if pairing.player2
                else ""
            )
        if pairing.event.source_json and "country" in pairing.event.source_json:
            event_country = pairing.event.source_json["country"]
        else:
            event_country = ""
        if "isOnlineEvent" in pairing.event.source_json:
            event_online = pairing.event.source_json["isOnlineEvent"]
        else:
            event_online = False
        player1_list_faction = (
            pairing.player1_list.faction if pairing.player1_list else ""
        )
        player1_list_subfaction = (
            pairing.player1_list.subfaction if pairing.player1_list else ""
        )
        player2_list_faction = (
            pairing.player2_list.faction if pairing.player2_list else ""
        )
        player2_list_subfaction = (
            pairing.player2_list.subfaction if pairing.player2_list else ""
        )

        if pairing.player1_list and len(pairing.player1_list.raw_list) > 10000:
            pairing.player1_list.raw_list = "List too long"
        if pairing.player2_list and len(pairing.player2_list.raw_list) > 10000:
            pairing.player2_list.raw_list = "List too long"

        writer.writerow(
            [
                pairing.id,
                pairing.round,
                player1_name,
                player2_name,
                pairing.player1_result,
                pairing.player2_result,
                pairing.player1_score,
                pairing.player2_score,
                pairing.event.name,
                pairing.event.start_date,
                pairing.event.end_date,
                event_country,
                event_online,
                "2023",
                player1_list_faction,
                player1_list_subfaction,
                player2_list_faction,
                player2_list_subfaction,
                pairing.player1_list.raw_list if pairing.player1_list else "",
                pairing.player2_list.raw_list if pairing.player2_list else "",
                "bcp" if pairing.event.source == BCP else "snl",
            ]
        )

    return response
