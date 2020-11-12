from django.contrib.auth.backends import RemoteUserBackend

from django_keycloak.models import KeycloakUser
from django_keycloak.keycloak import Connect


class KeycloakAuthenticationBackend(RemoteUserBackend):

    create_unknown_user = False

    def authenticate(self, request, username=None, password=None):
        keycloak = Connect()
        token = keycloak.get_token_from_credentials(username, password)
        if not keycloak.is_token_active(token):
            return
        try:
            user = KeycloakUser.objects.get(username=username)
        except KeycloakUser.DoesNotExist:
            user = KeycloakUser.objects.create_user(username, password)
        return user

    def get_user(self, username):
        try:
            return KeycloakUser.objects.get(username=username)
        except KeycloakUser.DoesNotExist:
            return
