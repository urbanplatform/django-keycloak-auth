from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django_keycloak.api.serializers import GetTokenSerializer, RefreshTokenSerializer
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
