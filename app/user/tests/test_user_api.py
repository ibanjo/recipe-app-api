from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')

PAYLOAD = {
    'email': 'test@ibanjo.it',
    'password': 'password123',
    'name': 'Test Name'
}

PAYLOAD_SHORT_PASSWORD = {
    **PAYLOAD,
    'password': 'pass'
}


def create_user(**kwargs):
    return get_user_model().objects.create_user(**kwargs)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        res = self.client.post(CREATE_USER_URL, PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(PAYLOAD['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails"""
        create_user(**PAYLOAD)

        res = self.client.post(CREATE_USER_URL, PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters long"""
        res = self.client.post(CREATE_USER_URL, PAYLOAD_SHORT_PASSWORD)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=PAYLOAD_SHORT_PASSWORD['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        create_user(**PAYLOAD)
        res = self.client.post(TOKEN_URL, PAYLOAD)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that a token is not created if invalid credentials are given"""
        create_user(**PAYLOAD)
        wrong_payload = {
            **PAYLOAD,
            'password': 'wrong_pass'
        }
        res = self.client.post(TOKEN_URL, wrong_payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that a token is not created if user does not exist"""
        res = self.client.post(TOKEN_URL, PAYLOAD)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        res = self.client.post(TOKEN_URL, {**PAYLOAD, 'password': ''})

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
