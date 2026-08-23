from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


from .models import Greenhouse, Sensor, SensorMeasurement


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


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor 
        fields = ('id','greenhouse','sensor_type','sensor_brand','unit','is_active','description','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

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
    # DRF automatically looks for get_latest_measurement() function 
    latest_measurement = serializers.SerializerMethodField()

    class Meta:
        model = Sensor
        fields = ('id','sensor_type','sensor_brand','unit','is_active','description','latest_measurement')

    def get_latest_measurement(self,obj):
        latest = obj.measurements.first()
        if latest is not None:
            return LatestMeasurementSerializer(latest).data
        return None


class GreenhouseLatestSerializer(serializers.ModelSerializer):
    sensors = SensorWithLatestMeasurementSerializer(many=True, read_only=True)

    class Meta:
        model = Greenhouse
        fields = ('id','name','description','sensors','longitude','latitude')

