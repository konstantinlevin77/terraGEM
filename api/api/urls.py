from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, SensorViewSet, UserProfileView, GreenhouseViewSet

router = DefaultRouter()
router.register(r'greenhouses', GreenhouseViewSet, basename='greenhouse')
router.register(r'sensors',SensorViewSet,basename='sensor')

urlpatterns = [
    # Router endpoints (/api/greenhouses/, /api/greenhouses/<id>/)
    path('', include(router.urls)),

    # JWT Authentication Endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/me/', UserProfileView.as_view(), name='auth_me'),
]
