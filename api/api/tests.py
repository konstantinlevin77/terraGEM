from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth_register')
        self.token_obtain_url = reverse('token_obtain_pair')
        self.token_refresh_url = reverse('token_refresh')
        self.profile_url = reverse('auth_me')

        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('StrongPassword123!'))

    def test_registration_password_mismatch(self):
        invalid_data = self.user_data.copy()
        invalid_data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_jwt_token_obtain_and_refresh(self):
        # Register user first
        self.client.post(self.register_url, self.user_data, format='json')

        # Obtain token
        login_data = {
            'username': 'testuser',
            'password': 'StrongPassword123!',
        }
        token_response = self.client.post(self.token_obtain_url, login_data, format='json')
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', token_response.data)
        self.assertIn('refresh', token_response.data)

        refresh_token = token_response.data['refresh']

        # Refresh token
        refresh_response = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_protected_profile_endpoint(self):
        # Register user
        self.client.post(self.register_url, self.user_data, format='json')

        # Obtain access token
        login_data = {'username': 'testuser', 'password': 'StrongPassword123!'}
        token_res = self.client.post(self.token_obtain_url, login_data, format='json')
        access_token = token_res.data['access']

        # Access without token -> 401
        unauth_res = self.client.get(self.profile_url)
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Access with Bearer token -> 200
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        auth_res = self.client.get(self.profile_url)
        self.assertEqual(auth_res.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_res.data['username'], 'testuser')
        self.assertEqual(auth_res.data['email'], 'testuser@example.com')


class GreenhouseAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='grower1',
            email='grower1@example.com',
            password='StrongPassword123!'
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('greenhouse-list')

    def test_create_and_list_greenhouse(self):
        payload = {
            'user': self.user.id,
            'name': 'Tomato Bay',
            'description': 'Main greenhouse for tomatoes',
            'longitude': 28.9784,
            'latitude': 41.0082,
        }
        res = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Tomato Bay')

        list_res = self.client.get(self.list_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

    def test_greenhouse_latest_endpoint_success(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import (
            Greenhouse,
            SensorProfile,
            Sensor,
            SensorMeasurement,
            SensorTypeChoices,
            SensorUnitChoices,
        )

        gh = Greenhouse.objects.create(user=self.user, name='Pepper House')
        profile_temp = SensorProfile.objects.create(
            name='DS18B20',
            sensor_type=SensorTypeChoices.AIR_TEMP,
            unit=SensorUnitChoices.CELSIUS
        )
        profile_hum = SensorProfile.objects.create(
            name='DHT22',
            sensor_type=SensorTypeChoices.AIR_HUM,
            unit=SensorUnitChoices.PERCENT
        )

        sensor1 = Sensor.objects.create(
            greenhouse=gh,
            profile=profile_temp,
            is_active=True
        )
        sensor2 = Sensor.objects.create(
            greenhouse=gh,
            profile=profile_hum,
            is_active=True
        )

        # Create older measurement and newer measurement for sensor1
        now = timezone.now()
        SensorMeasurement.objects.create(
            sensor=sensor1,
            value=18.5,
            measurement_time=now - timedelta(minutes=15)
        )
        SensorMeasurement.objects.create(
            sensor=sensor1,
            value=26.4,
            measurement_time=now
        )
        # sensor2 intentionally has no measurements

        latest_url = reverse('greenhouse-latest', kwargs={'pk': gh.pk})
        res = self.client.get(latest_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], gh.id)
        self.assertEqual(res.data['name'], 'Pepper House')
        self.assertEqual(len(res.data['sensors']), 2)

        # Verify sensor1 has the latest reading (26.4, not 18.5)
        s1_data = next(s for s in res.data['sensors'] if s['id'] == sensor1.id)
        self.assertIsNotNone(s1_data['latest_measurement'])
        self.assertEqual(s1_data['latest_measurement']['value'], 26.4)
        self.assertEqual(s1_data['sensor_type'], SensorTypeChoices.AIR_TEMP)

        # Verify sensor2 has None for latest_measurement
        s2_data = next(s for s in res.data['sensors'] if s['id'] == sensor2.id)
        self.assertIsNone(s2_data['latest_measurement'])

    def test_greenhouse_latest_endpoint_isolation_and_auth(self):
        from .models import Greenhouse

        user2 = User.objects.create_user(
            username='othergrower',
            email='other@example.com',
            password='Password123!'
        )
        other_gh = Greenhouse.objects.create(user=user2, name='Secret House')
        latest_url = reverse('greenhouse-latest', kwargs={'pk': other_gh.pk})

        # User1 cannot access user2's greenhouse -> 404 Not Found
        res = self.client.get(latest_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Unauthenticated user -> 401 Unauthorized
        self.client.logout()
        unauth_res = self.client.get(latest_url)
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_greenhouse_today_endpoint_success(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import (
            Greenhouse,
            SensorProfile,
            Sensor,
            SensorMeasurement,
            SensorTypeChoices,
            SensorUnitChoices,
        )

        gh = Greenhouse.objects.create(user=self.user, name='Orchid House')
        profile_temp = SensorProfile.objects.create(
            name='DS18B20_Today',
            sensor_type=SensorTypeChoices.AIR_TEMP,
            unit=SensorUnitChoices.CELSIUS
        )
        profile_hum = SensorProfile.objects.create(
            name='DHT22_Today',
            sensor_type=SensorTypeChoices.SOIL_HUM,
            unit=SensorUnitChoices.PERCENT
        )

        # Two air_temperature sensors in different zones sharing profile_temp
        temp_sensor1 = Sensor.objects.create(
            greenhouse=gh,
            profile=profile_temp,
            is_active=True
        )
        temp_sensor2 = Sensor.objects.create(
            greenhouse=gh,
            profile=profile_temp,
            is_active=True
        )
        # One soil_humidity sensor
        hum_sensor = Sensor.objects.create(
            greenhouse=gh,
            profile=profile_hum,
            is_active=True
        )

        now = timezone.now()
        yesterday = now - timedelta(days=1)

        # Yesterday's reading (must be excluded from today's aggregations)
        SensorMeasurement.objects.create(
            sensor=temp_sensor1,
            value=10.0,
            measurement_time=yesterday
        )

        # Today's readings for air_temperature (combined across sensor1 and sensor2)
        SensorMeasurement.objects.create(sensor=temp_sensor1, value=20.0, measurement_time=now)
        SensorMeasurement.objects.create(sensor=temp_sensor1, value=28.0, measurement_time=now)
        SensorMeasurement.objects.create(sensor=temp_sensor2, value=22.0, measurement_time=now)
        SensorMeasurement.objects.create(sensor=temp_sensor2, value=30.0, measurement_time=now)

        # Today's readings for soil_humidity
        SensorMeasurement.objects.create(sensor=hum_sensor, value=50.0, measurement_time=now)
        SensorMeasurement.objects.create(sensor=hum_sensor, value=80.0, measurement_time=now)

        today_url = reverse('greenhouse-today-summary', kwargs={'pk': gh.pk})
        res = self.client.get(today_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['greenhouse_id'], gh.id)
        self.assertEqual(str(res.data['date']), str(now.date()))
        self.assertEqual(len(res.data['metrics']), 2)

        # Verify grouped air_temperature stats across both sensors
        temp_metric = next(m for m in res.data['metrics'] if m['sensor_type'] == SensorTypeChoices.AIR_TEMP)
        self.assertEqual(temp_metric['unit'], SensorUnitChoices.CELSIUS)
        self.assertEqual(temp_metric['min_value'], 20.0)
        self.assertEqual(temp_metric['max_value'], 30.0)
        self.assertEqual(temp_metric['avg_value'], 25.0)
        self.assertEqual(temp_metric['reading_count'], 4)

        # Verify grouped soil_humidity stats
        hum_metric = next(m for m in res.data['metrics'] if m['sensor_type'] == SensorTypeChoices.SOIL_HUM)
        self.assertEqual(hum_metric['unit'], SensorUnitChoices.PERCENT)
        self.assertEqual(hum_metric['min_value'], 50.0)
        self.assertEqual(hum_metric['max_value'], 80.0)
        self.assertEqual(hum_metric['avg_value'], 65.0)
        self.assertEqual(hum_metric['reading_count'], 2)

    def test_greenhouse_today_endpoint_isolation_and_auth(self):
        from .models import Greenhouse

        user2 = User.objects.create_user(
            username='grower_two',
            email='two@example.com',
            password='Password123!'
        )
        other_gh = Greenhouse.objects.create(user=user2, name='Private House')
        today_url = reverse('greenhouse-today-summary', kwargs={'pk': other_gh.pk})

        # User1 cannot access user2's greenhouse -> 404
        res = self.client.get(today_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Unauthenticated user -> 401
        self.client.logout()
        unauth_res = self.client.get(today_url)
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_greenhouse_day_overview_success(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import (
            Greenhouse,
            SensorProfile,
            Sensor,
            SensorMeasurement,
            SensorTypeChoices,
            SensorUnitChoices,
        )

        gh = Greenhouse.objects.create(user=self.user, name='Tomato Bay')
        profile_temp = SensorProfile.objects.create(
            name='DS18B20_24h',
            sensor_type=SensorTypeChoices.AIR_TEMP,
            unit=SensorUnitChoices.CELSIUS
        )
        profile_hum = SensorProfile.objects.create(
            name='DHT22_24h',
            sensor_type=SensorTypeChoices.SOIL_HUM,
            unit=SensorUnitChoices.PERCENT
        )

        temp_sensor1 = Sensor.objects.create(greenhouse=gh, profile=profile_temp, is_active=True)
        temp_sensor2 = Sensor.objects.create(greenhouse=gh, profile=profile_temp, is_active=True)
        hum_sensor = Sensor.objects.create(greenhouse=gh, profile=profile_hum, is_active=True)

        now = timezone.now()

        # 1. Measurement older than 24 hours -> MUST be excluded
        SensorMeasurement.objects.create(
            sensor=temp_sensor1,
            value=99.0,
            measurement_time=now - timedelta(hours=25)
        )

        # 2. Bucket ~30 mins ago: 2 temperature readings (20.0 and 24.0)
        time_30m_ago = now - timedelta(minutes=30)
        SensorMeasurement.objects.create(sensor=temp_sensor1, value=20.0, measurement_time=time_30m_ago)
        SensorMeasurement.objects.create(sensor=temp_sensor2, value=24.0, measurement_time=time_30m_ago)

        # 3. Bucket ~10 mins ago: 1 temperature reading (26.0) and 1 humidity reading (60.0)
        time_10m_ago = now - timedelta(minutes=10)
        SensorMeasurement.objects.create(sensor=temp_sensor1, value=26.0, measurement_time=time_10m_ago)
        SensorMeasurement.objects.create(sensor=hum_sensor, value=60.0, measurement_time=time_10m_ago)

        overview_url = reverse('greenhouse-day-overview', kwargs={'pk': gh.pk})
        res = self.client.get(overview_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['greenhouse_id'], gh.id)
        self.assertEqual(res.data['greenhouse_name'], 'Tomato Bay')
        self.assertEqual(len(res.data['series']), 2)

        # Check air_temperature series
        temp_series = next(s for s in res.data['series'] if s['sensor_type'] == SensorTypeChoices.AIR_TEMP)
        self.assertEqual(len(temp_series['timeline']), 2)

        # First bucket (30 min ago)
        b1 = temp_series['timeline'][0]
        self.assertEqual(b1['avg_value'], 22.0)
        self.assertEqual(b1['min_value'], 20.0)
        self.assertEqual(b1['max_value'], 24.0)
        self.assertEqual(b1['reading_count'], 2)

        # Second bucket (10 min ago)
        b2 = temp_series['timeline'][1]
        self.assertEqual(b2['avg_value'], 26.0)
        self.assertEqual(b2['min_value'], 26.0)
        self.assertEqual(b2['max_value'], 26.0)
        self.assertEqual(b2['reading_count'], 1)

        # Check soil_humidity series
        hum_series = next(s for s in res.data['series'] if s['sensor_type'] == SensorTypeChoices.SOIL_HUM)
        self.assertEqual(len(hum_series['timeline']), 1)
        self.assertEqual(hum_series['timeline'][0]['avg_value'], 60.0)
        self.assertEqual(hum_series['timeline'][0]['reading_count'], 1)

    def test_greenhouse_day_overview_empty_when_no_measurements(self):
        from .models import Greenhouse, SensorProfile, Sensor, SensorTypeChoices, SensorUnitChoices

        gh = Greenhouse.objects.create(user=self.user, name='Brand New Empty House')
        profile = SensorProfile.objects.create(
            name='DHT22_EmptyTest',
            sensor_type=SensorTypeChoices.AIR_TEMP,
            unit=SensorUnitChoices.CELSIUS
        )
        Sensor.objects.create(greenhouse=gh, profile=profile, is_active=True)

        overview_url = reverse('greenhouse-day-overview', kwargs={'pk': gh.pk})
        res = self.client.get(overview_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['greenhouse_id'], gh.id)
        self.assertEqual(res.data['greenhouse_name'], 'Brand New Empty House')
        self.assertEqual(res.data['series'], [])

    def test_greenhouse_day_overview_isolation_and_auth(self):
        from .models import Greenhouse

        user2 = User.objects.create_user(
            username='grower_day_two',
            email='daytwo@example.com',
            password='Password123!'
        )
        other_gh = Greenhouse.objects.create(user=user2, name='Private Overview House')
        overview_url = reverse('greenhouse-day-overview', kwargs={'pk': other_gh.pk})

        # User1 cannot access user2's greenhouse -> 404
        res = self.client.get(overview_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Unauthenticated user -> 401
        self.client.logout()
        unauth_res = self.client.get(overview_url)
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)







class SensorAndMeasurementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='StrongPassword123!'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='StrongPassword123!'
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='AdminPassword123!'
        )

        from .models import (
            Greenhouse,
            SensorProfile,
            Sensor,
            SensorMeasurement,
            SensorTypeChoices,
            SensorUnitChoices,
        )
        self.greenhouse1 = Greenhouse.objects.create(user=self.user1, name='GH 1')
        self.greenhouse2 = Greenhouse.objects.create(user=self.user2, name='GH 2')

        self.profile1 = SensorProfile.objects.create(
            name='DS18B20',
            sensor_type=SensorTypeChoices.AIR_TEMP,
            unit=SensorUnitChoices.CELSIUS
        )
        self.profile2 = SensorProfile.objects.create(
            name='DHT22',
            sensor_type=SensorTypeChoices.AIR_HUM,
            unit=SensorUnitChoices.PERCENT
        )

        self.sensor1 = Sensor.objects.create(
            greenhouse=self.greenhouse1,
            profile=self.profile1,
            is_active=True
        )
        self.sensor2 = Sensor.objects.create(
            greenhouse=self.greenhouse2,
            profile=self.profile2,
            is_active=True
        )

        self.sensors_url = reverse('sensor-list')
        self.measurements_url = reverse('measurement-list')

    def test_sensor_creation_and_isolation(self):
        from .models import SensorTypeChoices, SensorUnitChoices

        self.client.force_authenticate(user=self.user1)

        # List sensors -> user1 only sees sensor1
        res = self.client.get(self.sensors_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], self.sensor1.id)
        self.assertEqual(res.data[0]['sensor_type'], SensorTypeChoices.AIR_TEMP)
        self.assertEqual(res.data[0]['profile_name'], 'DS18B20')
        self.assertEqual(res.data[0]['unit'], SensorUnitChoices.CELSIUS)

        # Create sensor attached to greenhouse1 -> Success
        post_res = self.client.post(self.sensors_url, {
            'greenhouse': self.greenhouse1.id,
            'profile': self.profile2.id,
            'is_active': True,
        }, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post_res.data['sensor_type'], SensorTypeChoices.AIR_HUM)
        self.assertEqual(post_res.data['profile_name'], 'DHT22')
        self.assertEqual(post_res.data['unit'], SensorUnitChoices.PERCENT)

        # Cannot attach sensor to user2's greenhouse -> 400 Bad Request
        bad_post = self.client.post(self.sensors_url, {
            'greenhouse': self.greenhouse2.id,
            'profile': self.profile1.id,
        }, format='json')
        self.assertEqual(bad_post.status_code, status.HTTP_400_BAD_REQUEST)

    def test_measurement_crud_and_isolation(self):
        self.client.force_authenticate(user=self.user1)

        # 1. Listing all measurements is disabled -> 405 Method Not Allowed
        list_res = self.client.get(self.measurements_url)
        self.assertEqual(list_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # 2. Create measurement for sensor1 -> Success (201 Created)
        res = self.client.post(self.measurements_url, {
            'sensor': self.sensor1.id,
            'value': 24.5,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['value'], 24.5)
        measurement_id = res.data['id']

        detail_url = reverse('measurement-detail', kwargs={'pk': measurement_id})

        # 3. User1 can retrieve their own specific measurement -> 200 OK
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['value'], 24.5)

        # 4. User2 cannot retrieve User1's measurement -> 404 Not Found
        self.client.force_authenticate(user=self.user2)
        user2_detail = self.client.get(detail_url)
        self.assertEqual(user2_detail.status_code, status.HTTP_404_NOT_FOUND)

        # 5. User2 cannot post measurement to user1's sensor -> 400 Bad Request
        bad_res = self.client.post(self.measurements_url, {
            'sensor': self.sensor1.id,
            'value': 99.9,
        }, format='json')
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)



class CORSTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('token_obtain_pair')

    def test_cors_allowed_origin(self):
        response = self.client.post(
            self.url,
            HTTP_ORIGIN='http://localhost:3000'
        )
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), 'http://localhost:3000')

    def test_cors_disallowed_origin(self):
        response = self.client.post(
            self.url,
            HTTP_ORIGIN='http://unauthorized-origin.com'
        )
        self.assertIsNone(response.headers.get('Access-Control-Allow-Origin'))


class ThresholdAndAlertAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='grower_alert_1',
            email='grower_alert_1@example.com',
            password='StrongPassword123!'
        )
        self.user2 = User.objects.create_user(
            username='grower_alert_2',
            email='grower_alert_2@example.com',
            password='StrongPassword123!'
        )

        from .models import (
            Greenhouse,
            SensorProfile,
            Sensor,
            SensorTypeChoices,
            SensorUnitChoices,
        )

        self.gh1 = Greenhouse.objects.create(user=self.user1, name='North Tunnel')
        self.gh2 = Greenhouse.objects.create(user=self.user2, name='South Tunnel')

        self.profile1 = SensorProfile.objects.create(
            name='RidgeProbeDS18B20',
            sensor_type=SensorTypeChoices.AIR_TEMP,
            unit=SensorUnitChoices.CELSIUS
        )
        self.profile2 = SensorProfile.objects.create(
            name='CanopyDHT22',
            sensor_type=SensorTypeChoices.AIR_HUM,
            unit=SensorUnitChoices.PERCENT
        )

        self.sensor1 = Sensor.objects.create(
            greenhouse=self.gh1,
            profile=self.profile1,
            description='Ridge probe, middle aisle',
            is_active=True
        )
        self.sensor2 = Sensor.objects.create(
            greenhouse=self.gh2,
            profile=self.profile2,
            description='Canopy sensor',
            is_active=True
        )

        self.thresholds_url = reverse('threshold-list')
        self.alerts_url = reverse('alert-list')
        self.active_alerts_url = reverse('alert-active')


    def test_threshold_crud_and_validation(self):
        self.client.force_authenticate(user=self.user1)

        # 1. Create valid threshold for sensor1
        res = self.client.post(self.thresholds_url, {
            'sensor': self.sensor1.id,
            'warning_min': 18.0,
            'warning_max': 30.0,
            'critical_min': 10.0,
            'critical_max': 38.0,
            'is_active': True,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['warning_min'], 18.0)
        self.assertEqual(res.data['critical_max'], 38.0)
        threshold_id = res.data['id']

        # 2. Cannot create threshold for user2's sensor
        bad_res = self.client.post(self.thresholds_url, {
            'sensor': self.sensor2.id,
            'warning_min': 20.0,
            'warning_max': 80.0,
        }, format='json')
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Invalid threshold bounds (warning_min > warning_max) -> 400
        invalid_res = self.client.post(self.thresholds_url, {
            'sensor': self.sensor1.id,
            'warning_min': 40.0,
            'warning_max': 20.0,
        }, format='json')
        self.assertEqual(invalid_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. List thresholds -> only sees user1's threshold
        list_res = self.client.get(self.thresholds_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

    def test_active_alerts_endpoint_and_isolation(self):
        from .models import Alert, AlertStatus, SeverityLevel

        # Create active alert for user1's sensor
        alert1 = Alert.objects.create(
            sensor=self.sensor1,
            triggered_value=57.2,
            severity=SeverityLevel.CRITICAL,
            status=AlertStatus.ACTIVE,
            message='Temperature critical'
        )

        # Create resolved alert for user1 (should NOT appear in /active/)
        Alert.objects.create(
            sensor=self.sensor1,
            triggered_value=24.0,
            severity=SeverityLevel.WARNING,
            status=AlertStatus.RESOLVED,
            message='Old resolved alert'
        )

        # User1 requests /api/alerts/active/
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(self.active_alerts_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_active'], 1)
        alert_data = res.data['alerts'][0]
        self.assertEqual(alert_data['sensor_description'], 'Ridge probe, middle aisle')
        self.assertEqual(alert_data['greenhouse_name'], 'North Tunnel')
        self.assertEqual(alert_data['triggered_value'], 57.2)
        self.assertEqual(alert_data['unit'], 'celsius')
        self.assertEqual(alert_data['severity'], 'critical')
        self.assertEqual(alert_data['severity_display'], 'Kritik')
        self.assertEqual(alert_data['status'], AlertStatus.ACTIVE)

        # User2 requests /api/alerts/active/ -> gets 0 active alerts
        self.client.force_authenticate(user=self.user2)
        u2_res = self.client.get(self.active_alerts_url)
        self.assertEqual(u2_res.status_code, status.HTTP_200_OK)
        self.assertEqual(u2_res.data['total_active'], 0)

    def test_alert_acknowledge_endpoint(self):
        from .models import Alert, AlertStatus, SeverityLevel

        alert = Alert.objects.create(
            sensor=self.sensor1,
            triggered_value=57.2,
            severity=SeverityLevel.CRITICAL,
            status=AlertStatus.ACTIVE
        )

        ack_url = reverse('alert-acknowledge', kwargs={'pk': alert.pk})

        # User2 cannot acknowledge User1's alert -> 404
        self.client.force_authenticate(user=self.user2)
        bad_ack = self.client.post(ack_url)
        self.assertEqual(bad_ack.status_code, status.HTTP_404_NOT_FOUND)

        # User1 acknowledges -> 200 OK and status becomes ACKNOWLEDGED
        self.client.force_authenticate(user=self.user1)
        ack_res = self.client.post(ack_url)
        self.assertEqual(ack_res.status_code, status.HTTP_200_OK)
        self.assertEqual(ack_res.data['status'], AlertStatus.ACKNOWLEDGED)

        # Acknowledged alert still included in /active/ (unresolved)
        u1_active = self.client.get(self.active_alerts_url)
        self.assertEqual(u1_active.data['total_active'], 1)
        self.assertEqual(u1_active.data['alerts'][0]['status'], AlertStatus.ACKNOWLEDGED)



