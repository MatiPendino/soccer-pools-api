# Generated by Django 4.2.16 on 2025-02-23 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('match', '0007_alter_matchresult_bet_round'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='api_match_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
    ]
