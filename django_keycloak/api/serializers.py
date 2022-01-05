from django.contrib.auth import get_user_model
from rest_framework import serializers


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, write_only=True)


class KeycloakUserAutoIdSerializer(serializers.ModelSerializer):
    """
    Serializer for the user endpoint
    """

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email',)
