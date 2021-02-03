from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth import get_user_model
from django_keycloak.keycloak import Connect


class KeycloakAuthenticationBackend(RemoteUserBackend):

    def authenticate(self, request, username=None, password=None):
        keycloak = Connect()
        token = keycloak.get_token_from_credentials(username, password)
        User = get_user_model()
        if not keycloak.is_token_active(token):
            return
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, password)

        if keycloak.has_superuser_perm(token):
            user.is_staff = True
            user.is_superuser = True
            user.save()
        else:
            user.is_staff = False
            user.is_superuser = False
            user.save()

        return user

    def get_user(self, user_identifier):
        User = get_user_model()
        try:
            return User.objects.get(username=user_identifier)
        except User.DoesNotExist:
            return User.objects.get(keycloak_id=user_identifier)
