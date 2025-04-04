# Generated by Django 4.2.16 on 2024-12-31 00:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('league', '0006_team_acronym'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.BooleanField(default=True)),
                ('creation_date', models.DateField(auto_now_add=True, null=True)),
                ('updating_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('logo', models.ImageField(default='default-tournament-logo.png', upload_to='tournament')),
                ('admin_tournament', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='league.league')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TournamentUser',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.BooleanField(default=True)),
                ('creation_date', models.DateField(auto_now_add=True, null=True)),
                ('updating_date', models.DateField(auto_now=True, null=True)),
                ('tournament_user_state', models.IntegerField(choices=[(0, 'NOT SENT'), (1, 'PENDING'), (2, 'ACCEPTED'), (3, 'REJECTED')], default=0)),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.tournament')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
