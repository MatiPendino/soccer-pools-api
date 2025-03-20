from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import League

class FCMToken(BaseModel):
    token_id = models.CharField(max_length=255)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='fcm_tokens')
    device_id = models.CharField(max_length=255, null=True, blank=True)
    leagues = models.ManyToManyField(League)

    def __str__(self):
        return f'{self.user.username} {self.token_id}'