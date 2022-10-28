from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions
from rest_framework import status
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from django_keycloak.api.filters import DRYPermissionFilter
from django_keycloak.api.serializers import (
    GetTokenSerializer,
    RefreshTokenSerializer,
    KeycloakUserAutoIdSerializer,
)


class BaseTokenAPIView(generics.GenericAPIView):
    serializer_class = None
    # Allow anonymous users
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetTokenAPIView(BaseTokenAPIView):
    serializer_class = GetTokenSerializer


class RefreshTokenAPIView(BaseTokenAPIView):
    serializer_class = RefreshTokenSerializer


class UserProfileAPIView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = get_user_model().objects.all()
    serializer_class = KeycloakUserAutoIdSerializer
    filter_backends = (DRYPermissionFilter,)

    @action(
        detail=False,
        methods=["GET"],
        serializer_class=KeycloakUserAutoIdSerializer,
    )
    def me(self, request):
        """
        Get information about the current user
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
