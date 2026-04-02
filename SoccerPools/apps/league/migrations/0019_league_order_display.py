from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0018_alter_league_minimum_coins_first_prize_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='order_display',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
