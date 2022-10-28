from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django_keycloak import Token


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)

    def to_representation(self, instance):
        """
        Return an "access" and "refresh" token if the given credentials are correct.
        Otherwise return an authentication error
        """
        token = Token.from_credentials(instance["username"], instance["password"])
        if not token:
            raise AuthenticationFailed

        return {
            "access": token.access_token,
            "refresh": token.refresh_token,
        }


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, write_only=True)

    def to_representation(self, instance):
        """
        Return an "access" token from the "refresh" token.
        If the refresh token is not valid return a validation error.
        """
        token = Token.from_refresh_token(instance["refresh_token"])
        if not token:
            raise ValidationError
        return {
            "access": token.access_token,
        }


class KeycloakUserAutoIdSerializer(serializers.ModelSerializer):
    """
    Serializer for the user endpoint
    """

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
        )
