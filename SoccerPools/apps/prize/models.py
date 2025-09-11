from django.db import models
from apps.app_user.models import AppUser
from apps.base.models import BaseModel

class Prize(BaseModel):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='prizes', null=True, blank=True)
    coins_cost = models.PositiveIntegerField(default=0)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.title} - {self.coins_cost}'
    

class PrizeUser(BaseModel):
    STARTED = 0
    DELIVERED = 1
    CANCELLED = 2
    PRIZE_STATES = (
        (STARTED, 'Started'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    )

    user = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)
    prize = models.ForeignKey(Prize, on_delete=models.SET_NULL, null=True)
    prize_status = models.SmallIntegerField(choices=PRIZE_STATES, default=STARTED)

    class Meta:
        verbose_name_plural = 'Prize Users'

    def __str__(self):
        prize_status_str = PrizeUser.PRIZE_STATES[self.prize_status][1]
        return f'{self.get_user_username()} - {self.get_prize_title()} - {prize_status_str}'
    
    def get_user_username(self):
        return self.user.username if self.user else ''
    
    def get_prize_title(self):
        return self.prize.title if self.prize else ''