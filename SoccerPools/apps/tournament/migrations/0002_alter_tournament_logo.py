# Generated by Django 4.2.16 on 2025-02-16 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='logo',
            field=models.ImageField(blank=True, default='default-tournament-logo.png', null=True, upload_to='tournament'),
        ),
    ]
