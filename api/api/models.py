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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every .save()

    def __str__(self):
        return self.name


class Sensor(models.Model):
    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.CASCADE,
        related_name="sensors"
    )
    sensor_type = models.CharField(max_length=50,default='')
    is_active= models.BooleanField(default=False)
    description = models.CharField(max_length=200,blank=True,default='')
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every .save()

    def __str__(self):
        return_str = self.sensor_type + ": " + self.description
        return return_str

    
