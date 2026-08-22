from django.contrib.auth.models import AbstractUser
from django.db import models


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
