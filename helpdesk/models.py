from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class GWSettings(models.Model):
    #id = models.PositiveSmallIntegerField(primary_key=True, unique=True)
    gwHost = models.CharField(max_length=120)
    gwPort = models.PositiveSmallIntegerField()
    gwAdmin = models.CharField(max_length=64)
    gwPass = models.CharField(max_length=64)



class Admin(models.Model):
    REQUIRED_FIELDS = ('username','role')
    ADMIN = 'AD'
    HELPDESK = "HD"
    HELPDESKLITE = "HL"
    PASSWORD = "PW"
    roleChoices = (
        (ADMIN, 'Administrator'),
        (HELPDESK, 'Helpdesk'),
        (HELPDESKLITE, 'Helpdesk Lite'),
        (PASSWORD, 'Password'),
    )
    #USERNAME_FIELD = models.CharField(max_length=64)
    username = models.CharField(max_length=128, null=True)
    first_name = models.CharField(max_length=64, null=True, blank=True)
    last_name = models.CharField(max_length=64, null=True, blank=True)
    password = models.CharField(max_length=256, null=True)
    password2 = models.CharField(max_length=256, null=True, blank=True)
    role = models.CharField(max_length=4, choices=roleChoices, default=HELPDESK)
