from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="admin2@example.com", password="StrongPass123!")

    def test_login_returns_tokens(self):
        response = self.client.post(
            reverse("auth-login"), {"email": "admin2@example.com", "password": "StrongPass123!"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password_rejected(self):
        response = self.client.post(
            reverse("auth-login"), {"email": "admin2@example.com", "password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_auth(self):
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        login = self.client.post(
            reverse("auth-login"), {"email": "admin2@example.com", "password": "StrongPass123!"}
        )
        access = login.data["access"]
        response = self.client.get(reverse("auth-me"), HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "admin2@example.com")
