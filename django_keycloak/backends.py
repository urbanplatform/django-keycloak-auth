from django.contrib.auth.backends import RemoteUserBackend

from django_keycloak.models import CustomUser
from django_keycloak.keycloak import Connect


class KeycloakAuthenticationBackend(RemoteUserBackend):

    create_unknown_user = False

    def authenticate(self, request, username=None, password=None):
        keycloak = Connect()
        token = keycloak.get_token_from_credentials(username, password)
        if not keycloak.is_token_active(token):
            return
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(username, password)
        return user

    def get_user(self, username):
        try:
            return CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return
