from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Greenhouse,
    SensorProfile,
    Sensor,
    SensorMeasurement,
    SensorThreshold,
    Alert,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('company', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'company', 'phone_number')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Greenhouse)
class GreenhouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'latitude', 'longitude', 'created_at')
    search_fields = ('name', 'description', 'user__username', 'user__email')
    list_filter = ('user',)


@admin.register(SensorProfile)
class SensorProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sensor_type', 'unit', 'period', 'created_at')
    search_fields = ('name', 'sensor_type', 'description')
    list_filter = ('sensor_type', 'unit')


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'greenhouse', 'is_active', 'created_at')
    search_fields = ('profile__name', 'profile__sensor_type', 'description', 'greenhouse__name', 'greenhouse__user__username')
    list_filter = ('is_active', 'profile__sensor_type', 'greenhouse')


@admin.register(SensorMeasurement)
class SensorMeasurementAdmin(admin.ModelAdmin):
    list_display = ('id', 'sensor', 'value', 'measurement_time', 'created_at')
    search_fields = ('sensor__profile__sensor_type', 'sensor__greenhouse__name')
    list_filter = ('sensor', 'measurement_time')


@admin.register(SensorThreshold)
class SensorThresholdAdmin(admin.ModelAdmin):
    list_display = ('id', 'sensor', 'warning_min', 'warning_max', 'critical_min', 'critical_max', 'is_active')
    list_filter = ('is_active',)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'sensor', 'triggered_value', 'severity', 'status', 'created_at')
    list_filter = ('severity', 'status', 'created_at')

