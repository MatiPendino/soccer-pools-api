# Generated by Django 4.2.16 on 2025-02-17 01:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('league', '0007_round_is_general_round'),
        ('bet', '0005_rename_bet_betround'),
    ]

    operations = [
        migrations.AlterField(
            model_name='betround',
            name='round',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bets', to='league.round'),
        ),
        migrations.AlterField(
            model_name='betround',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bets', to=settings.AUTH_USER_MODEL),
        ),
    ]
