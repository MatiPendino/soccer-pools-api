# Generated by Django 4.2.16 on 2024-11-10 02:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bet', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bet',
            name='match_results',
        ),
    ]
