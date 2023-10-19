from django.db import models

class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    state = models.BooleanField(default=True)
    creation_date = models.DateField(auto_now_add=True, auto_now=False, blank=True, null=True)
    updating_date = models.DateField(auto_now_add=False, auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True