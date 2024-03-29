from django.urls import path

from data.views import raw_list, export_pairings_as_csv, event_lists

urlpatterns = [
    path("lists/<int:list_id>/raw", raw_list, name="raw_list"),
    path(
        "woestats/<int:game_type>",
        export_pairings_as_csv,
        name="export_pairings_as_csv",
    ),
    path("event_lists/<int:event_id>", event_lists, name="event_lists"),
]
