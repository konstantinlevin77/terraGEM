from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


from .models import (
    Greenhouse,
    SensorProfile,
    Sensor,
    SensorMeasurement,
    SensorThreshold,
    Alert,
)


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name',)
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'company', 'phone_number', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class GreenhouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Greenhouse
        fields = ('id', 'user', 'name', 'description', 'longitude', 'latitude','created_at','updated_at')
        read_only_fields = ('id','user','created_at','updated_at')


class SensorProfileSerializer(serializers.ModelSerializer):
    sensor_type_display = serializers.CharField(source='get_sensor_type_display', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)

    class Meta:
        model = SensorProfile
        fields = (
            'id',
            'name',
            'sensor_type',
            'sensor_type_display',
            'unit',
            'unit_display',
            'period',
            'description',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SensorSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    sensor_type = serializers.CharField(source='profile.sensor_type', read_only=True)
    unit = serializers.CharField(source='profile.unit', read_only=True)

    class Meta:
        model = Sensor 
        fields = (
            'id',
            'greenhouse',
            'profile',
            'profile_name',
            'sensor_type',
            'unit',
            'is_active',
            'description',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow selecting greenhouses owned by the logged-in user (unless admin)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['greenhouse'].queryset = Greenhouse.objects.filter(user=request.user)


class SensorMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorMeasurement
        fields = ('id', 'sensor', 'value', 'measurement_time', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow selecting sensors owned by the logged-in user (unless admin)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['sensor'].queryset = Sensor.objects.filter(greenhouse__user=request.user)



#######################################################
# SERIALIZERS FOR /api/greenhouses/<id>/latest
#######################################################



class LatestMeasurementSerializer(serializers.ModelSerializer):
    """
    This serializer is for a custom /greenhouses/<id>/latest endpoint
    """
    class Meta:
        model = SensorMeasurement
        fields = ('id', 'value', 'measurement_time')


class SensorWithLatestMeasurementSerializer(serializers.ModelSerializer):
    """
    This serializer is for one sensor and its latest measurement combined.
    """
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    sensor_type = serializers.CharField(source='profile.sensor_type', read_only=True)
    unit = serializers.CharField(source='profile.unit', read_only=True)
    latest_measurement = serializers.SerializerMethodField()

    class Meta:
        model = Sensor
        fields = (
            'id',
            'profile',
            'profile_name',
            'sensor_type',
            'unit',
            'is_active',
            'description',
            'latest_measurement',
        )

    def get_latest_measurement(self, obj):
        latest = obj.measurements.first()
        if latest is not None:
            return LatestMeasurementSerializer(latest).data
        return None


class GreenhouseLatestSerializer(serializers.ModelSerializer):
    sensors = SensorWithLatestMeasurementSerializer(many=True, read_only=True)

    class Meta:
        model = Greenhouse
        fields = ('id','name','description','sensors','longitude','latitude')


class SensorThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorThreshold
        fields = (
            'id',
            'sensor',
            'warning_min',
            'warning_max',
            'critical_min',
            'critical_max',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow selecting sensors owned by the logged-in user (unless admin)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['sensor'].queryset = Sensor.objects.filter(greenhouse__user=request.user)

    def validate(self, attrs):
        w_min = attrs.get('warning_min', getattr(self.instance, 'warning_min', None))
        w_max = attrs.get('warning_max', getattr(self.instance, 'warning_max', None))
        c_min = attrs.get('critical_min', getattr(self.instance, 'critical_min', None))
        c_max = attrs.get('critical_max', getattr(self.instance, 'critical_max', None))

        if w_min is not None and w_max is not None and w_min >= w_max:
            raise serializers.ValidationError({"warning_min": "warning_min must be less than warning_max."})

        if c_min is not None and c_max is not None and c_min >= c_max:
            raise serializers.ValidationError({"critical_min": "critical_min must be less than critical_max."})

        if c_min is not None and w_min is not None and c_min > w_min:
            raise serializers.ValidationError({"critical_min": "critical_min cannot be greater than warning_min."})

        if c_max is not None and w_max is not None and c_max < w_max:
            raise serializers.ValidationError({"critical_max": "critical_max cannot be less than warning_max."})

        return attrs


class AlertSerializer(serializers.ModelSerializer):
    sensor_type = serializers.CharField(source='sensor.profile.sensor_type', read_only=True)
    sensor_type_display = serializers.CharField(source='sensor.profile.get_sensor_type_display', read_only=True)
    sensor_description = serializers.CharField(source='sensor.description', read_only=True)
    greenhouse_id = serializers.IntegerField(source='sensor.greenhouse.id', read_only=True)
    greenhouse_name = serializers.CharField(source='sensor.greenhouse.name', read_only=True)
    unit = serializers.CharField(source='sensor.profile.unit', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Alert
        fields = (
            'id',
            'sensor',
            'sensor_type',
            'sensor_type_display',
            'sensor_description',
            'greenhouse_id',
            'greenhouse_name',
            'triggered_value',
            'unit',
            'severity',
            'severity_display',
            'status',
            'status_display',
            'message',
            'created_at',
            'updated_at',
            'resolved_at',
        )
        read_only_fields = fields



