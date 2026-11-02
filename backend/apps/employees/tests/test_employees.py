from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.employees.models import Employee


class EmployeeApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="hr@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)

    def test_create_employee(self):
        response = self.client.post(
            reverse("employee-list"),
            {
                "name": "Test Employee",
                "email": "test.employee@example.com",
                "department": "Engineering",
                "job_title": "Developer",
                "hire_date": "2024-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Employee.objects.filter(email="test.employee@example.com").exists())

    def test_duplicate_email_rejected(self):
        Employee.objects.create(name="A", email="dup@example.com")
        response = self.client.post(
            reverse("employee-list"), {"name": "B", "email": "dup@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_requires_auth(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
