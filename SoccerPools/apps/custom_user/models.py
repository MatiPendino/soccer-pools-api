from django.db import models
from django.contrib.auth.models import User


class CustomUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='custom_user', null=True, blank=True)
    balance = models.DecimalField(default=0, max_digits=8, decimal_places=2)

    def __str__(self):
        return self.user.username