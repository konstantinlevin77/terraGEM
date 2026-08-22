from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Maintains standard username, email, and password authentication
    while allowing future custom fields.
    """
    email = models.EmailField(unique=True)
    company = models.TextField(blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.username


class Greenhouse(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="greenhouses"
    )
    name = models.CharField(max_length=50,blank=True,default='')
    description = models.CharField(max_length=300,blank=True,default='')
    longitude = models.FloatField(null=True,blank=True)
    latitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
