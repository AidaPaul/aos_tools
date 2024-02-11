from django.db import models

# Create your models here.

BCP = 0
TSN = 1
SNL = 2
ECKSEN = 3

event_sources = (
    (BCP, "BCP"),
    (TSN, "TSN"),
)

WIN = 2
DRAW = 1
LOSS = 0


aos_factions = [
    "Stormcast Eternals",
    "Daughters of Khaine",
    "Fyreslayers",
    "Idoneth Deepkin",
    "Kharadron Overlords",
    "Lumineth Realm-lords",
    "Sylvaneth",
    "Seraphon",
    "Cities of Sigmar",
    "Slaves to Darkness",
    "Blades of Khorne",
    "Disciples of Tzeentch",
    "Hedonites of Slaanesh",
    "Maggotkin of Nurgle",
    "Skaven",
    "Beasts of Chaos",
    "Legion of Azgorh",
    "Flesh-eater Courts",
    "Nighthaunt",
    "Ossiarch Bonereapers",
    "Soulblight Gravelords",
    "Orruk Warclans",
    "Gloomspite Gitz",
    "Sons of Behemat",
    "Ogor Mawtribes",
    "Legion of the First Prince",
]

w40k_factions = [
    "Adepta Sororitas",
    "Adeptus Custodes",
    "Adeptus Mechanicus",
    "Aeldari",
    "Astra Militarum",
    "Black Templars",
    "Blood Angels",
    "Chaos Daemons",
    "Chaos Knights",
    "Chaos Space Marines",
    "Chaos Titan Legions",
    "Dark Angels",
    "Death Guard",
    "Deathwatch",
    "Drukhari",
    "Genestealer Cults",
    "Grey Knights",
    "Imperial Agents",
    "Imperial Knights",
    "Leagues of Votann",
    "Necrons",
    "Orks",
    "Space Marines",
    "Space Wolves",
    "Thousand Sons",
    "Titan Legions",
    "Tyranids",
    "T'au Empire",
    "World Eaters",
]

w40k_marines = [
    "Adeptus Astares",
    "Adeptus Astartes",
    "Ultramarines",
    "Iron Fist",
    "Imperial Fist",
    "Imperial Fists",
    "Black Templars",
    "Iron Hands",
    "Blood Angels",
    "Dark Angels",
]

w40k_chaos_space_marines = [
    "Black Legion",
    "Death Guard",
    "Thousand Sons",
    "World Eaters",
]
w40k_dark_angel = ["Deathwing", "Ravenwing"]

GHB_2021 = 2021
GHB_2022S1 = 20221
GHB_2022S2 = 20222
GHB_2023 = 2023


GHB_2022S1_STRATEGIES = [
    "Tame the Land",
    "No Place for the Weak",
    "Demonstration of Strength",
    "Show of Dominance",
    "Take What",
]


GHB_2022S2_STRATEGIES = [
    "Tame the Land",
    "Stake a Claim",
    "Survivor's Instinct",
    "The Day is Ours!",
]

GHB_2023_STRATEGIES = [
    "Control the Nexus",
    "Spellcasting Savant",
    "Slaughter of Sorcery",
    "Barren Icescape",
    "Overshadow",
    "Magic Made Manifest",
]

AOS = 0
W40K = 1
BOLT_ACTION = 2
OLD_WORLD = 3

GAME_TYPES = [
    (AOS, "Age of Sigmar"),
    (W40K, "Warhammer 40k"),
]


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    address = models.CharField(max_length=255)


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.IntegerField(choices=event_sources)
    source_id = models.CharField(max_length=255)
    source_json = models.JSONField()
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)
    photo_url = models.URLField(null=True)
    players_count = models.IntegerField(null=True)
    points_limit = models.IntegerField(null=True)
    rounds = models.IntegerField(default=5, null=True)
    season = models.IntegerField(null=True)
    game_type = models.IntegerField(choices=GAME_TYPES, null=True, default=AOS)

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
    source_id = models.CharField(max_length=255)
    source_json = models.JSONField()


class Participant(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    source_json = models.JSONField()
    army_source_id = models.CharField(max_length=255, null=True)
    army_id = models.CharField(max_length=255, null=True)


class List(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="list"
    )
    source_id = models.CharField(max_length=255)
    source_json = models.JSONField()
    player_created_at = models.DateTimeField(null=True)
    player_updated_at = models.DateTimeField(null=True)
    raw_list = models.TextField()
    faction = models.CharField(
        max_length=255, null=True, choices=zip(aos_factions, aos_factions)
    )
    subfaction = models.CharField(max_length=255, null=True)
    grand_strategy = models.CharField(max_length=255, null=True)
    regexp_parsed = models.BooleanField(default=False)
    gpt_parsed = models.BooleanField(default=False)
    gpt_parse_error = models.JSONField(null=True)


class Pairing(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="pairings")
    player1 = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="player1", null=True
    )
    player2 = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="player2", null=True
    )
    round = models.IntegerField()
    player1_result = models.IntegerField(null=True)
    player2_result = models.IntegerField(null=True)
    player1_score = models.IntegerField(null=True)
    player2_score = models.IntegerField(null=True)
    player1_list = models.ForeignKey(
        List, on_delete=models.CASCADE, null=True, related_name="player1_list"
    )
    player2_list = models.ForeignKey(
        List, on_delete=models.CASCADE, null=True, related_name="player2_list"
    )
    source_id = models.CharField(max_length=255)
    source_json = models.JSONField()
    scenario = models.CharField(max_length=255, null=True)
