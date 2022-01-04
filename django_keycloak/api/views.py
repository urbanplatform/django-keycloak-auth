from django.contrib.auth import get_user_model
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django_keycloak.api.filters import DRYPermissionFilter
from django_keycloak.api.serializers import GetTokenSerializer, RefreshTokenSerializer, KeycloakUserAutoIdSerializer
from django_keycloak.keycloak import Connect


class GetTokenAPIView(GenericAPIView):
    serializer_class = GetTokenSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        keycloak = Connect()
        data = keycloak.get_token_from_credentials(
            request.data.get('username'),
            request.data.get('password')
        )

        return Response(data)


class RefreshTokenAPIView(GenericAPIView):
    serializer_class = RefreshTokenSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        keycloak = Connect()
        data = keycloak.refresh_token_from_credentials(
            request.data.get('refresh_token')
        )

        return Response(data)


class UserProfileAPIView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = get_user_model().objects.all()
    serializer_class = KeycloakUserAutoIdSerializer
    filter_backends = (DRYPermissionFilter,)

    @action(detail=False, methods=['GET'], serializer_class=KeycloakUserAutoIdSerializer)
    def me(self, request):
        """
        Get information about the current user
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
