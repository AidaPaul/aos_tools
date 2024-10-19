from django.db import models


# Event Sources
BCP = 0
TSN = 1
SNL = 2
ECKSEN = 3

event_sources = (
    (BCP, "BCP"),
    (TSN, "TSN"),
    (SNL, "SNL"),
    (ECKSEN, "ECKSEN"),
)

# Game Types
AOS = 0
W40K = 1
BOLT_ACTION = 2
OLD_WORLD = 3
KINGS_OF_WAR = 4

GAME_TYPES = [
    (AOS, "Age of Sigmar"),
    (W40K, "Warhammer 40k"),
    (BOLT_ACTION, "Bolt Action"),
    (OLD_WORLD, "Old World"),
    (KINGS_OF_WAR, "Kings of War"),
]

# Factions Lists
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


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Location Name")
    country = models.CharField(max_length=255, verbose_name="Country")
    address = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Address"
    )

    def __str__(self):
        return f"{self.name}, {self.country}"

class Event(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Updated At"
    )
    source = models.IntegerField(
        choices=event_sources,
        verbose_name="Event Source",
        help_text="Source from which the event was imported.",
    )
    source_id = models.CharField(
        max_length=255,
        verbose_name="Source ID",
        help_text="Unique identifier from the event source.",
    )
    source_json = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Source JSON",
        help_text="Raw data from the source.",
    )
    name = models.CharField(max_length=255, verbose_name="Event Name")
    start_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Start Date"
    )
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Location",
        help_text="Location where the event takes place.",
    )
    photo_url = models.URLField(null=True, blank=True, verbose_name="Photo URL")
    players_count = models.PositiveIntegerField(
        null=True, verbose_name="Players Count"
    )
    points_limit = models.PositiveIntegerField(
        null=True, verbose_name="Points Limit"
    )
    rounds = models.PositiveIntegerField(
        default=5,
        null=True,
        verbose_name="Rounds",
        help_text="Number of rounds in the event.",
    )
    season = models.IntegerField(
        null=True, blank=True, verbose_name="Season"
    )
    game_type = models.IntegerField(
        choices=GAME_TYPES,
        null=True,
        default=AOS,
        verbose_name="Game Type",
    )

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('source', 'source_id')
        ordering = ["start_date"]
        indexes = [
            models.Index(fields=["name", "start_date"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["source", "source_id"]),
        ]
        verbose_name = "Event"
        verbose_name_plural = "Events"

class Player(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Updated At"
    )
    source = models.IntegerField(
        choices=event_sources,
        verbose_name="Player Source",
        help_text="Source from which the player was imported.",
    )
    source_id = models.CharField(
        max_length=255,
        verbose_name="Source ID",
        help_text="Unique identifier from the player source.",
    )
    source_json = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Source JSON",
        help_text="Raw data from the source.",
    )

    def __str__(self):
        return f"Player {self.source_id} from {dict(event_sources).get(self.source, 'Unknown')}"

    class Meta:
        unique_together = ('source', 'source_id')
        verbose_name = "Player"
        verbose_name_plural = "Players"

class Participant(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Updated At"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        verbose_name="Event",
        help_text="Event in which the player is participating.",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        verbose_name="Player",
        help_text="The player participating in the event.",
    )
    source_json = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Source JSON",
        help_text="Raw data from the source.",
    )
    army_source_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Army Source ID",
        help_text="Unique identifier for the army from the source.",
    )
    army_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Army ID",
        help_text="Unique identifier for the army.",
    )

    def __str__(self):
        return f"Participant {self.player} in {self.event}"

    class Meta:
        unique_together = ('event', 'player')
        ordering = ['event', 'player']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['player']),
        ]
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

class List(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Updated At"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="lists",
        verbose_name="Participant",
        help_text="Participant to whom this list belongs.",
    )
    source_id = models.CharField(
        max_length=255,
        verbose_name="Source ID",
        help_text="Unique identifier from the list source.",
    )
    source_json = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Source JSON",
        help_text="Raw data from the source.",
    )
    player_created_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Player Created At"
    )
    player_updated_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Player Updated At"
    )
    raw_list = models.TextField(
        verbose_name="Raw List", help_text="Original list text."
    )
    faction = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=zip(aos_factions, aos_factions),
        db_index=True,
        verbose_name="Faction",
    )
    subfaction = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Subfaction",
    )
    grand_strategy = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Grand Strategy",
    )
    regexp_parsed = models.BooleanField(
        null=True,
        db_index=True,
        verbose_name="Regexp Parsed",
        help_text="Indicates if regexp parsing was successful.",
    )
    gpt_parsed = models.BooleanField(
        null=True,
        db_index=True,
        verbose_name="GPT Parsed",
        help_text="Indicates if GPT parsing was successful.",
    )
    gpt_parse_error = models.JSONField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="GPT Parse Error",
        help_text="Error information from GPT parsing.",
    )
    drops = models.PositiveIntegerField(
        null=True,
        db_index=True,
        verbose_name="Drops",
        help_text="Number of drops in the list.",
    )
    points = models.PositiveIntegerField(
        null=True,
        db_index=True,
        verbose_name="Points",
        help_text="Total points of the list.",
    )
    manifestation_lore = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Manifestation Lore",
    )
    spell_lore = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Spell Lore",
    )
    prayer_lore = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Prayer Lore",
    )

    def __str__(self):
        return f"List for {self.participant}"

    class Meta:
        ordering = ['participant']
        indexes = [
            models.Index(fields=['participant']),
            models.Index(fields=['faction']),
            # Add other indexes as needed...
        ]
        verbose_name = "List"
        verbose_name_plural = "Lists"

class Pairing(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Updated At"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="pairings",
        verbose_name="Event",
        help_text="Event in which the pairing occurs.",
    )
    winner = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        related_name="wins",
        null=True,
        blank=True,
        verbose_name="Winner",
        help_text="Participant who won the game.",
    )
    loser = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        related_name="losses",
        null=True,
        blank=True,
        verbose_name="Loser",
        help_text="Participant who lost the game.",
    )
    is_draw = models.BooleanField(
        default=False,
        verbose_name="Is Draw",
        help_text="Indicates if the game was a draw.",
    )
    round = models.PositiveIntegerField(
        verbose_name="Round", help_text="Round number of the pairing."
    )
    winner_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Winner Score",
        help_text="Score of the winner.",
    )
    loser_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Loser Score",
        help_text="Score of the loser.",
    )
    winner_list = models.ForeignKey(
        List,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="winner_list",
        verbose_name="Winner's List",
    )
    loser_list = models.ForeignKey(
        List,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loser_list",
        verbose_name="Loser's List",
    )
    source_id = models.CharField(
        max_length=255,
        verbose_name="Source ID",
        help_text="Unique identifier from the pairing source.",
    )
    source_json = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Source JSON",
        help_text="Raw data from the source.",
    )
    scenario = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Scenario",
        help_text="Scenario played in the pairing.",
    )

    def __str__(self):
        return f"{self.event.name} Round {self.round}"

    class Meta:
        ordering = ['event', 'round']
        indexes = [
            models.Index(fields=["event", "round"]),
            models.Index(fields=["winner"]),
            models.Index(fields=["loser"]),
            models.Index(fields=["is_draw"]),
            models.Index(fields=["scenario"]),
        ]
        verbose_name = "Pairing"
        verbose_name_plural = "Pairings"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.winner == self.loser and self.winner is not None:
            raise ValidationError("Winner and loser cannot be the same participant.")
        if self.is_draw and (self.winner or self.loser):
            raise ValidationError("A draw cannot have a winner or loser.")
        if not self.is_draw and (not self.winner or not self.loser):
            raise ValidationError("A non-draw must have both a winner and a loser.")
