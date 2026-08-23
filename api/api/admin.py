from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Greenhouse, Sensor, SensorMeasurement


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


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('id', 'sensor_type', 'greenhouse', 'is_active', 'created_at')
    search_fields = ('sensor_type', 'description', 'greenhouse__name', 'greenhouse__user__username')
    list_filter = ('is_active', 'sensor_type', 'greenhouse')


@admin.register(SensorMeasurement)
class SensorMeasurementAdmin(admin.ModelAdmin):
    list_display = ('id', 'sensor', 'value', 'measurement_time', 'created_at')
    search_fields = ('sensor__sensor_type', 'sensor__greenhouse__name')
    list_filter = ('sensor', 'measurement_time')
