from rest_framework import serializers


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    refresh_token = serializers.CharField(required=True, write_only=True)
