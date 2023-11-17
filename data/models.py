from django.db import models

# Create your models here.

BCP = 0
TSN = 1

event_sources = (
    (BCP, "BCP"),
    (TSN, "TSN"),
)


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address = models.CharField(max_length=255)


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.IntegerField(choices=event_sources)
    source_id = models.CharField(max_length=100)
    source_json = models.JSONField()
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)
    photo_url = models.URLField(null=True)
    players_count = models.IntegerField(null=True)
    points_limit = models.IntegerField(null=True)
    rounds = models.IntegerField(default=5)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    class Meta:
        ordering = ["start_date"]
        indexes = [
            models.Index(fields=["name", "start_date"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["source", "source_id"]),
        ]


class Player(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.IntegerField(choices=event_sources)
    source_id = models.CharField(max_length=100)
    source_json = models.JSONField()


class Participant(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    source_json = models.JSONField()
    army_source_id = models.CharField(max_length=100, null=True)


class List(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    source_id = models.CharField(max_length=100)
    source_json = models.JSONField()
    player_created_at = models.DateTimeField()
    player_updated_at = models.DateTimeField()
    raw_list = models.TextField()
