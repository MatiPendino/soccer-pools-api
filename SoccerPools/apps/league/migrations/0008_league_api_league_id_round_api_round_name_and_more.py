# Generated by Django 4.2.16 on 2025-02-23 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0007_round_is_general_round'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='api_league_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='round',
            name='api_round_name',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='api_team_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
    ]
