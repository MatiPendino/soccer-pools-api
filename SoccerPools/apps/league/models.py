from django.db import models
from apps.base.models import BaseModel


class League(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text='Must be written with no spaces')
    logo = models.ImageField('Logo of the league', upload_to='league', blank=True, null=True)

    def __str__(self):
        return self.name
    

class Round(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text='Must be written with no spaces')
    



class Team(BaseModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, help_text='Must be written with no spaces')
    badge = models.ImageField('Badge of the team', upload_to='league', null=True, blank=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} - {self.league}'
    

