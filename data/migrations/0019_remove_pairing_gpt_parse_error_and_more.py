# Generated by Django 4.2.7 on 2023-11-20 09:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0018_pairing_gpt_parse_error_pairing_gpt_parsed_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pairing",
            name="gpt_parse_error",
        ),
        migrations.RemoveField(
            model_name="pairing",
            name="gpt_parsed",
        ),
        migrations.RemoveField(
            model_name="pairing",
            name="regexp_parsed",
        ),
        migrations.AddField(
            model_name="list",
            name="gpt_parse_error",
            field=models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name="list",
            name="gpt_parsed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="list",
            name="regexp_parsed",
            field=models.BooleanField(default=False),
        ),
    ]