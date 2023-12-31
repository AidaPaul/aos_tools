# Generated by Django 4.2.7 on 2023-11-17 10:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.IntegerField(choices=[(0, "BCP"), (1, "TSN")])),
                ("source_id", models.CharField(max_length=100)),
                ("source_json", models.JSONField()),
                ("name", models.CharField(max_length=100)),
                ("start_date", models.DateTimeField(null=True)),
                ("end_date", models.DateTimeField(null=True)),
                ("photo_url", models.URLField(null=True)),
                ("players_count", models.IntegerField(null=True)),
                ("points_limit", models.IntegerField(null=True)),
            ],
            options={
                "ordering": ["start_date"],
            },
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=100)),
                ("address", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Player",
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
                ("source", models.IntegerField(choices=[(0, "BCP"), (1, "TSN")])),
                ("source_id", models.CharField(max_length=100)),
                ("source_json", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="Participant",
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
                ("source_json", models.JSONField()),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="data.event"
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="data.player"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="event",
            name="location",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="data.location",
            ),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["name", "start_date"], name="data_event_name_653672_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["start_date"], name="data_event_start_d_7e6d44_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["end_date"], name="data_event_end_dat_c46f6d_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["source", "source_id"], name="data_event_source_f2306d_idx"
            ),
        ),
    ]
