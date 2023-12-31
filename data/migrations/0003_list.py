# Generated by Django 4.2.7 on 2023-11-17 11:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0002_participant_army_source_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="List",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_id", models.CharField(max_length=100)),
                ("source_json", models.JSONField()),
                ("player_created_at", models.DateTimeField()),
                ("player_updated_at", models.DateTimeField()),
                ("raw_list", models.TextField()),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data.participant",
                    ),
                ),
            ],
        ),
    ]
