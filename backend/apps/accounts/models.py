from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager


class User(AbstractUser):
    """Single-role user: whoever logs in is the HR/IT admin who manages all
    employees and assets. There is no per-employee login and no
    multi-tenant scoping - this is one admin's view of their org."""

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
