# Generated by Django 4.2.7 on 2023-11-20 09:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0014_remove_list_faction_id_remove_list_subfaction_id_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="list",
            name="ghb",
        ),
        migrations.RemoveField(
            model_name="list",
            name="ghb_id",
        ),
        migrations.AddField(
            model_name="event",
            name="season",
            field=models.IntegerField(default=2023),
        ),
    ]
