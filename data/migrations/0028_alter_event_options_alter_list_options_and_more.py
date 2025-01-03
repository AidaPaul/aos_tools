# Generated by Django 4.2.16 on 2024-10-19 13:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0027_remove_pairing_player1_remove_pairing_player1_list_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['start_date'], 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AlterModelOptions(
            name='list',
            options={'ordering': ['participant'], 'verbose_name': 'List', 'verbose_name_plural': 'Lists'},
        ),
        migrations.AlterModelOptions(
            name='pairing',
            options={'ordering': ['event', 'round'], 'verbose_name': 'Pairing', 'verbose_name_plural': 'Pairings'},
        ),
        migrations.AlterModelOptions(
            name='participant',
            options={'ordering': ['event', 'player'], 'verbose_name': 'Participant', 'verbose_name_plural': 'Participants'},
        ),
        migrations.AlterModelOptions(
            name='player',
            options={'verbose_name': 'Player', 'verbose_name_plural': 'Players'},
        ),
        migrations.AlterField(
            model_name='event',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='End Date'),
        ),
        migrations.AlterField(
            model_name='event',
            name='game_type',
            field=models.IntegerField(choices=[(0, 'Age of Sigmar'), (1, 'Warhammer 40k'), (2, 'Bolt Action'), (3, 'Old World'), (4, 'Kings of War')], default=0, null=True, verbose_name='Game Type'),
        ),
        migrations.AlterField(
            model_name='event',
            name='location',
            field=models.ForeignKey(help_text='Location where the event takes place.', null=True, on_delete=django.db.models.deletion.CASCADE, to='data.location', verbose_name='Location'),
        ),
        migrations.AlterField(
            model_name='event',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Event Name'),
        ),
        migrations.AlterField(
            model_name='event',
            name='photo_url',
            field=models.URLField(blank=True, null=True, verbose_name='Photo URL'),
        ),
        migrations.AlterField(
            model_name='event',
            name='players_count',
            field=models.PositiveIntegerField(null=True, verbose_name='Players Count'),
        ),
        migrations.AlterField(
            model_name='event',
            name='points_limit',
            field=models.PositiveIntegerField(null=True, verbose_name='Points Limit'),
        ),
        migrations.AlterField(
            model_name='event',
            name='rounds',
            field=models.PositiveIntegerField(default=5, help_text='Number of rounds in the event.', null=True, verbose_name='Rounds'),
        ),
        migrations.AlterField(
            model_name='event',
            name='season',
            field=models.IntegerField(blank=True, null=True, verbose_name='Season'),
        ),
        migrations.AlterField(
            model_name='event',
            name='source',
            field=models.IntegerField(choices=[(0, 'BCP'), (1, 'TSN'), (2, 'SNL'), (3, 'ECKSEN')], help_text='Source from which the event was imported.', verbose_name='Event Source'),
        ),
        migrations.AlterField(
            model_name='event',
            name='source_id',
            field=models.CharField(help_text='Unique identifier from the event source.', max_length=255, verbose_name='Source ID'),
        ),
        migrations.AlterField(
            model_name='event',
            name='source_json',
            field=models.JSONField(blank=True, help_text='Raw data from the source.', null=True, verbose_name='Source JSON'),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Start Date'),
        ),
        migrations.AlterField(
            model_name='event',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='list',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='list',
            name='drops',
            field=models.PositiveIntegerField(db_index=True, help_text='Number of drops in the list.', null=True, verbose_name='Drops'),
        ),
        migrations.AlterField(
            model_name='list',
            name='faction',
            field=models.CharField(blank=True, choices=[('Stormcast Eternals', 'Stormcast Eternals'), ('Daughters of Khaine', 'Daughters of Khaine'), ('Fyreslayers', 'Fyreslayers'), ('Idoneth Deepkin', 'Idoneth Deepkin'), ('Kharadron Overlords', 'Kharadron Overlords'), ('Lumineth Realm-lords', 'Lumineth Realm-lords'), ('Sylvaneth', 'Sylvaneth'), ('Seraphon', 'Seraphon'), ('Cities of Sigmar', 'Cities of Sigmar'), ('Slaves to Darkness', 'Slaves to Darkness'), ('Blades of Khorne', 'Blades of Khorne'), ('Disciples of Tzeentch', 'Disciples of Tzeentch'), ('Hedonites of Slaanesh', 'Hedonites of Slaanesh'), ('Maggotkin of Nurgle', 'Maggotkin of Nurgle'), ('Skaven', 'Skaven'), ('Beasts of Chaos', 'Beasts of Chaos'), ('Legion of Azgorh', 'Legion of Azgorh'), ('Flesh-eater Courts', 'Flesh-eater Courts'), ('Nighthaunt', 'Nighthaunt'), ('Ossiarch Bonereapers', 'Ossiarch Bonereapers'), ('Soulblight Gravelords', 'Soulblight Gravelords'), ('Orruk Warclans', 'Orruk Warclans'), ('Gloomspite Gitz', 'Gloomspite Gitz'), ('Sons of Behemat', 'Sons of Behemat'), ('Ogor Mawtribes', 'Ogor Mawtribes'), ('Legion of the First Prince', 'Legion of the First Prince')], db_index=True, max_length=255, null=True, verbose_name='Faction'),
        ),
        migrations.AlterField(
            model_name='list',
            name='gpt_parse_error',
            field=models.JSONField(blank=True, db_index=True, help_text='Error information from GPT parsing.', null=True, verbose_name='GPT Parse Error'),
        ),
        migrations.AlterField(
            model_name='list',
            name='gpt_parsed',
            field=models.BooleanField(db_index=True, help_text='Indicates if GPT parsing was successful.', null=True, verbose_name='GPT Parsed'),
        ),
        migrations.AlterField(
            model_name='list',
            name='grand_strategy',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='Grand Strategy'),
        ),
        migrations.AlterField(
            model_name='list',
            name='manifestation_lore',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='Manifestation Lore'),
        ),
        migrations.AlterField(
            model_name='list',
            name='participant',
            field=models.ForeignKey(help_text='Participant to whom this list belongs.', on_delete=django.db.models.deletion.CASCADE, related_name='lists', to='data.participant', verbose_name='Participant'),
        ),
        migrations.AlterField(
            model_name='list',
            name='player_created_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Player Created At'),
        ),
        migrations.AlterField(
            model_name='list',
            name='player_updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Player Updated At'),
        ),
        migrations.AlterField(
            model_name='list',
            name='points',
            field=models.PositiveIntegerField(db_index=True, help_text='Total points of the list.', null=True, verbose_name='Points'),
        ),
        migrations.AlterField(
            model_name='list',
            name='prayer_lore',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='Prayer Lore'),
        ),
        migrations.AlterField(
            model_name='list',
            name='raw_list',
            field=models.TextField(help_text='Original list text.', verbose_name='Raw List'),
        ),
        migrations.AlterField(
            model_name='list',
            name='regexp_parsed',
            field=models.BooleanField(db_index=True, help_text='Indicates if regexp parsing was successful.', null=True, verbose_name='Regexp Parsed'),
        ),
        migrations.AlterField(
            model_name='list',
            name='source_id',
            field=models.CharField(help_text='Unique identifier from the list source.', max_length=255, verbose_name='Source ID'),
        ),
        migrations.AlterField(
            model_name='list',
            name='source_json',
            field=models.JSONField(blank=True, help_text='Raw data from the source.', null=True, verbose_name='Source JSON'),
        ),
        migrations.AlterField(
            model_name='list',
            name='spell_lore',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='Spell Lore'),
        ),
        migrations.AlterField(
            model_name='list',
            name='subfaction',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='Subfaction'),
        ),
        migrations.AlterField(
            model_name='list',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='location',
            name='address',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Address'),
        ),
        migrations.AlterField(
            model_name='location',
            name='country',
            field=models.CharField(max_length=255, verbose_name='Country'),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Location Name'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='event',
            field=models.ForeignKey(help_text='Event in which the pairing occurs.', on_delete=django.db.models.deletion.CASCADE, related_name='pairings', to='data.event', verbose_name='Event'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='is_draw',
            field=models.BooleanField(default=False, help_text='Indicates if the game was a draw.', verbose_name='Is Draw'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='loser',
            field=models.ForeignKey(blank=True, help_text='Participant who lost the game.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='losses', to='data.participant', verbose_name='Loser'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='loser_list',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='loser_list', to='data.list', verbose_name="Loser's List"),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='loser_score',
            field=models.PositiveIntegerField(blank=True, help_text='Score of the loser.', null=True, verbose_name='Loser Score'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='round',
            field=models.PositiveIntegerField(help_text='Round number of the pairing.', verbose_name='Round'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='scenario',
            field=models.CharField(blank=True, help_text='Scenario played in the pairing.', max_length=255, null=True, verbose_name='Scenario'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='source_id',
            field=models.CharField(help_text='Unique identifier from the pairing source.', max_length=255, verbose_name='Source ID'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='source_json',
            field=models.JSONField(blank=True, help_text='Raw data from the source.', null=True, verbose_name='Source JSON'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='winner',
            field=models.ForeignKey(blank=True, help_text='Participant who won the game.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wins', to='data.participant', verbose_name='Winner'),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='winner_list',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='winner_list', to='data.list', verbose_name="Winner's List"),
        ),
        migrations.AlterField(
            model_name='pairing',
            name='winner_score',
            field=models.PositiveIntegerField(blank=True, help_text='Score of the winner.', null=True, verbose_name='Winner Score'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='army_id',
            field=models.CharField(blank=True, help_text='Unique identifier for the army.', max_length=255, null=True, verbose_name='Army ID'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='army_source_id',
            field=models.CharField(blank=True, help_text='Unique identifier for the army from the source.', max_length=255, null=True, verbose_name='Army Source ID'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='event',
            field=models.ForeignKey(help_text='Event in which the player is participating.', on_delete=django.db.models.deletion.CASCADE, to='data.event', verbose_name='Event'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='player',
            field=models.ForeignKey(help_text='The player participating in the event.', on_delete=django.db.models.deletion.PROTECT, to='data.player', verbose_name='Player'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='source_json',
            field=models.JSONField(blank=True, help_text='Raw data from the source.', null=True, verbose_name='Source JSON'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='player',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='player',
            name='source',
            field=models.IntegerField(choices=[(0, 'BCP'), (1, 'TSN'), (2, 'SNL'), (3, 'ECKSEN')], help_text='Source from which the player was imported.', verbose_name='Player Source'),
        ),
        migrations.AlterField(
            model_name='player',
            name='source_id',
            field=models.CharField(help_text='Unique identifier from the player source.', max_length=255, verbose_name='Source ID'),
        ),
        migrations.AlterField(
            model_name='player',
            name='source_json',
            field=models.JSONField(blank=True, help_text='Raw data from the source.', null=True, verbose_name='Source JSON'),
        ),
        migrations.AlterField(
            model_name='player',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterUniqueTogether(
            name='event',
            unique_together={('source', 'source_id')},
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together={('event', 'player')},
        ),
        migrations.AlterUniqueTogether(
            name='player',
            unique_together={('source', 'source_id')},
        ),
        migrations.AddIndex(
            model_name='list',
            index=models.Index(fields=['participant'], name='data_list_partici_19f57a_idx'),
        ),
        migrations.AddIndex(
            model_name='list',
            index=models.Index(fields=['faction'], name='data_list_faction_425a1b_idx'),
        ),
        migrations.AddIndex(
            model_name='participant',
            index=models.Index(fields=['event'], name='data_partic_event_i_12571c_idx'),
        ),
        migrations.AddIndex(
            model_name='participant',
            index=models.Index(fields=['player'], name='data_partic_player__6fdbd6_idx'),
        ),
    ]
