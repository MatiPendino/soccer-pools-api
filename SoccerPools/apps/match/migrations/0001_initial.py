# Generated by Django 4.2.6 on 2023-12-24 08:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('league', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.BooleanField(default=True)),
                ('creation_date', models.DateField(auto_now_add=True, null=True)),
                ('updating_date', models.DateField(auto_now=True, null=True)),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='Start date of the match')),
                ('round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='league.round')),
                ('team_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_1', to='league.team')),
                ('team_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_2', to='league.team')),
            ],
            options={
                'verbose_name': 'Match',
                'verbose_name_plural': 'Matches',
            },
        ),
        migrations.CreateModel(
            name='MatchResult',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.BooleanField(default=True)),
                ('creation_date', models.DateField(auto_now_add=True, null=True)),
                ('updating_date', models.DateField(auto_now=True, null=True)),
                ('goals_team_1', models.PositiveSmallIntegerField(default=0, verbose_name='Number of goals team 1')),
                ('goals_team_2', models.PositiveSmallIntegerField(default=0, verbose_name='Number of goals team 2')),
                ('original_result', models.BooleanField(default=False, verbose_name='Original result of the match')),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='match.match')),
            ],
            options={
                'verbose_name': 'Match Result',
                'verbose_name_plural': 'Matches results',
            },
        ),
    ]
