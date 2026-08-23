from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import (
    SensorSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    GreenhouseSerializer,
    SensorMeasurementSerializer,
    GreenhouseLatestSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Min,Max,Avg,Count,F

from rest_framework import viewsets
from .models import Greenhouse, Sensor, SensorMeasurement
from datetime import datetime, time

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Endpoint for registering new users.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for retrieving and updating the authenticated user's profile.
    Requires Bearer JWT token in Authorization header.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class GreenhouseViewSet(viewsets.ModelViewSet):
    queryset = Greenhouse.objects.all()
    serializer_class = GreenhouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Admins/Staff can see and manage all greenhouses
        if self.request.user.is_staff:
            return Greenhouse.objects.all()
        # Regular users only see their own
        return Greenhouse.objects.filter(user=self.request.user)

    
    def perform_create(self, serializer):
        # If admin specified a user in request body, keep it;
        # otherwise, force the owner to be the logged-in user
        if self.request.user.is_staff and 'user' in serializer.validated_data:
            serializer.save()
        else:
            serializer.save(user=self.request.user)

    @action(detail=True,methods=['get'])
    def latest(self,request,pk=None):
        gh = self.get_object()
        serializer = GreenhouseLatestSerializer(gh)
        return Response(serializer.data)

    @action(detail=True,methods=['get'])
    def today(self,request,pk=None):
        gh = self.get_object()
        date = timezone.now().date()
        start_of_today = timezone.now().replace(hour=0,minute=0,second=0,microsecond=0)
        metrics = SensorMeasurement.objects.filter(
            sensor__greenhouse=gh,
            measurement_time__gte=start_of_today
        ).values(sensor_type = F('sensor__sensor_type'), unit = F('sensor__unit') ).annotate(
            min_value = Min('value'),
            max_value = Max('value'),
            avg_value = Avg('value'),
            reading_count = Count('id')
        )
        return Response({
                "greenhouse_id":gh.id,
                "date":date,
                "metrics": metrics
        })



class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Admins/Staff can see and manage all sensors
        if self.request.user.is_staff:
            queryset = Sensor.objects.all()
        else:
            # Regular users only see their own
            queryset = Sensor.objects.filter(greenhouse__user=self.request.user)

        greenhouse_id = self.request.query_params.get('greenhouse')
        if greenhouse_id:
            queryset = queryset.filter(greenhouse_id=greenhouse_id)
        return queryset


class SensorMeasurementViewSet(viewsets.ModelViewSet):
    queryset = SensorMeasurement.objects.all()
    serializer_class = SensorMeasurementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Admins/Staff can see and manage all measurements
        if self.request.user.is_staff:
            queryset = SensorMeasurement.objects.all()
        else:
            # Regular users only see measurements from their own greenhouses
            queryset = SensorMeasurement.objects.filter(sensor__greenhouse__user=self.request.user)

        sensor_id = self.request.query_params.get('sensor')
        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)
        return queryset

