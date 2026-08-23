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

        from .models import Greenhouse, Sensor, SensorMeasurement
        self.greenhouse1 = Greenhouse.objects.create(user=self.user1, name='GH 1')
        self.greenhouse2 = Greenhouse.objects.create(user=self.user2, name='GH 2')

        self.sensor1 = Sensor.objects.create(greenhouse=self.greenhouse1, sensor_type='temperature')
        self.sensor2 = Sensor.objects.create(greenhouse=self.greenhouse2, sensor_type='humidity')

        self.sensors_url = reverse('sensor-list')
        self.measurements_url = reverse('measurement-list')

    def test_sensor_creation_and_isolation(self):
        self.client.force_authenticate(user=self.user1)

        # List sensors -> user1 only sees sensor1
        res = self.client.get(self.sensors_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], self.sensor1.id)

        # Create sensor attached to greenhouse1 -> Success
        post_res = self.client.post(self.sensors_url, {
            'greenhouse': self.greenhouse1.id,
            'sensor_type': 'soil_moisture',
            'is_active': True,
        }, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)

        # Cannot attach sensor to user2's greenhouse -> 400 Bad Request
        bad_post = self.client.post(self.sensors_url, {
            'greenhouse': self.greenhouse2.id,
            'sensor_type': 'co2',
        }, format='json')
        self.assertEqual(bad_post.status_code, status.HTTP_400_BAD_REQUEST)

    def test_measurement_crud_and_isolation(self):
        self.client.force_authenticate(user=self.user1)

        # Create measurement for sensor1 -> Success
        res = self.client.post(self.measurements_url, {
            'sensor': self.sensor1.id,
            'value': 24.5,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['value'], 24.5)
        measurement_id = res.data['id']

        # List measurements -> user1 sees 1 measurement
        list_res = self.client.get(self.measurements_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

        # User2 logs in -> Sees 0 measurements from user1
        self.client.force_authenticate(user=self.user2)
        user2_res = self.client.get(self.measurements_url)
        self.assertEqual(user2_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(user2_res.data), 0)

        # User2 cannot post measurement to user1's sensor
        bad_res = self.client.post(self.measurements_url, {
            'sensor': self.sensor1.id,
            'value': 99.9,
        }, format='json')
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Admin logs in -> Sees all measurements
        self.client.force_authenticate(user=self.admin_user)
        admin_res = self.client.get(self.measurements_url)
        self.assertEqual(admin_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(admin_res.data), 1)
