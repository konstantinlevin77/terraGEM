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


class SensorUnitChoices(models.TextChoices):
    CELSIUS = "celsius"
    PERCENT = "percent"
    PPM = "ppm"
    PH = "ph"
    NOT_SPEC = "not_specified"


class SensorProfile(models.Model):
    name = models.CharField(max_length=100)
    sensor_type = models.CharField(max_length=100,choices=SensorTypeChoices,default=SensorTypeChoices.NOT_SPEC)
    unit = models.CharField(max_length=100,choices=SensorUnitChoices,default=SensorUnitChoices.NOT_SPEC)
    period = models.FloatField(null=True,blank=True,default=5.0)
    description = models.CharField(max_length=200,null=True,blank=True)


    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every .save()

    def __str__(self):
        return f"{self.name} ({self.get_sensor_type_display() if hasattr(self, 'get_sensor_type_display') else self.sensor_type})"



class Sensor(models.Model):
    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.CASCADE,
        related_name="sensors"
    )
    profile = models.ForeignKey(
        SensorProfile,
        on_delete=models.PROTECT,
        related_name="sensors",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=False)
    description = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every .save()

    def __str__(self):
        profile_name = self.profile.name if self.profile else 'Sensor'
        return f"{profile_name} ({self.greenhouse.name or self.greenhouse.pk})"




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
        profile_name = self.sensor.profile.name if (self.sensor and self.sensor.profile) else 'Sensor'
        return f"{profile_name}: {self.value} @ {self.measurement_time}"


class SeverityLevel(models.TextChoices):
    WARNING = 'warning', 'Uyarı'
    CRITICAL = 'critical', 'Kritik'




class SensorThreshold(models.Model):
    sensor = models.OneToOneField(
        Sensor,
        on_delete=models.CASCADE,
        related_name="threshold"
    )

    # Inner band: Warning limits (mild breach)
    warning_min = models.FloatField(null=True, blank=True, help_text="Below this triggers a Warning")
    warning_max = models.FloatField(null=True, blank=True, help_text="Above this triggers a Warning")

    # Outer band: Critical limits (severe danger)
    critical_min = models.FloatField(null=True, blank=True, help_text="Below this triggers Critical")
    critical_max = models.FloatField(null=True, blank=True, help_text="Above this triggers Critical")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Threshold for {self.sensor}"

    def evaluate_status(self, value):
        """
        Evaluates a measurement value against the threshold bands.
        Returns: 'critical', 'warning', or 'normal'
        """
        if value is None or not self.is_active:
            return "normal"

        # 1. Check Critical (Outer Band) first
        if (self.critical_min is not None and value < self.critical_min) or \
           (self.critical_max is not None and value > self.critical_max):
            return "critical"

        # 2. Check Warning (Inner Band) second
        if (self.warning_min is not None and value < self.warning_min) or \
           (self.warning_max is not None and value > self.warning_max):
            return "warning"

        # 3. Inside safe zone
        return "normal"


class AlertStatus(models.TextChoices):
    ACTIVE = "active", "Açık"
    RESOLVED = "resolved", "Çözüldü"
    ACKNOWLEDGED = "acknowledged", "Onaylandı"


class Alert(models.Model):
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name="alerts"
    )
    threshold = models.ForeignKey(
        SensorThreshold,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    triggered_value = models.FloatField()
    severity = models.CharField(
        max_length=20,
        choices=SeverityLevel.choices,
        default=SeverityLevel.CRITICAL
    )
    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.ACTIVE
    )
    message = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.severity.upper()} Alert for {self.sensor} ({self.status}): {self.triggered_value}"