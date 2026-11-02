from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds the user's email to the JWT claims as a frontend convenience.
    Every request is still re-validated server-side (IsAuthenticated +
    request.user), so a stale/tampered claim can't grant extra access."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token
