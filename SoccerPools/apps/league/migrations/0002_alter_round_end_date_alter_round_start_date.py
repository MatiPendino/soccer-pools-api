# Generated by Django 4.2.6 on 2024-09-18 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='round',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='round',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
