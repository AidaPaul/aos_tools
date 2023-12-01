from django.urls import path, include

from data.views import raw_list, export_pairings_as_csv

urlpatterns = [
    path("lists/<int:list_id>/raw", raw_list, name="raw_list"),
    path("woestats/", export_pairings_as_csv, name="export_pairings_as_csv"),
]
