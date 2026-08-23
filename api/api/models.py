from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


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
    name = models.CharField(max_length=50, blank=True, default='')
    description = models.CharField(max_length=300, blank=True, default='')
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every .save()

    def __str__(self):
        return self.name or f"Greenhouse #{self.pk}"


class SensorTypeChoices(models.TextChoices):
    SOIL_TEMP = "soil_temperature"
    SOIL_HUM = "soil_humidity"
    AIR_TEMP = "air_temperature"
    AIR_HUM = "air_humidity"
    CO2 = "co2"                       
    PH = "ph"                         
    LIGHT = "light_intensity"        
    NOT_SPEC = "not_specified"


class SensorBrandChoices(models.TextChoices):
    DS18B20 = "DS18B20"
    RESISTIVE_SOIL_HUM = "resistive_soil_hum"
    NOT_SPEC = "not_specified"

class UnitChoices(models.TextChoices):
    CELSIUS = "celsius"
    PERCENT = "percent"
    PPM = "ppm"
    PH = "ph"
    NOT_SPEC = "not_specified"


class Sensor(models.Model):
    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.CASCADE,
        related_name="sensors"
    )
    sensor_type = models.CharField(max_length=50,choices=SensorTypeChoices, default=SensorTypeChoices.NOT_SPEC)
    sensor_brand = models.CharField(max_length=50,choices=SensorBrandChoices,default=SensorBrandChoices.NOT_SPEC)
    unit = models.CharField(max_length=20,choices=UnitChoices,default=UnitChoices.NOT_SPEC)

    is_active = models.BooleanField(default=False)
    description = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every .save()

    def __str__(self):
        return f"{self.sensor_type or 'Sensor'} ({self.greenhouse.name or self.greenhouse.pk})"


class SensorMeasurement(models.Model):
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name="measurements"
    )
    value = models.FloatField()
    measurement_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-measurement_time']

    def __str__(self):
        return f"{self.sensor.sensor_type}: {self.value} @ {self.measurement_time}"
