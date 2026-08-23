from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import (
    SensorSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    GreenhouseSerializer,
    SensorMeasurementSerializer,
    GreenhouseLatestSerializer,
    SensorThresholdSerializer,
    AlertSerializer,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Min, Max, Avg, Count, F

from rest_framework import viewsets
from .models import (
    Greenhouse,
    Sensor,
    SensorMeasurement,
    SensorThreshold,
    Alert,
    AlertStatus,
)

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
    def today_summary(self,request,pk=None):
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


class SensorThresholdViewSet(viewsets.ModelViewSet):
    queryset = SensorThreshold.objects.all()
    serializer_class = SensorThresholdSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Admins/Staff can see and manage all thresholds
        if self.request.user.is_staff:
            queryset = SensorThreshold.objects.all()
        else:
            # Regular users only see thresholds for their own sensors
            queryset = SensorThreshold.objects.filter(sensor__greenhouse__user=self.request.user)

        sensor_id = self.request.query_params.get('sensor')
        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)
        return queryset


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Admins/Staff can see all alerts
        if self.request.user.is_staff:
            queryset = Alert.objects.all()
        else:
            # Regular users only see alerts for their own sensors
            queryset = Alert.objects.filter(sensor__greenhouse__user=self.request.user)

        sensor_id = self.request.query_params.get('sensor')
        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)

        greenhouse_id = self.request.query_params.get('greenhouse')
        if greenhouse_id:
            queryset = queryset.filter(sensor__greenhouse_id=greenhouse_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        GET /api/alerts/active/
        Returns all unresolved alerts (active or acknowledged) for the user's dashboard.
        """
        active_alerts = self.get_queryset().filter(status__in=[AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED])
        serializer = self.get_serializer(active_alerts, many=True)
        return Response({
            "total_active": active_alerts.count(),
            "alerts": serializer.data
        })

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        POST /api/alerts/{id}/acknowledge/
        Marks an alert as acknowledged by the user.
        """
        alert = self.get_object()
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.save(update_fields=['status', 'updated_at'])
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


