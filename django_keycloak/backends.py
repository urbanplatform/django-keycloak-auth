from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth import get_user_model
from django_keycloak.keycloak import Connect


class KeycloakAuthenticationBackend(RemoteUserBackend):

    def authenticate(self, request, username=None, password=None):
        keycloak = Connect()
        token = keycloak.get_token_from_credentials(username, password).get("access_token")
        user = get_user_model()
        if not keycloak.is_token_active(token):
            return
        try:
            user = user.objects.get(username=username)
            # Get user info based on token
            user_info = keycloak.get_user_info(token)

            # Get user info and update
            user.first_name = user_info.get('given_name')
            user.last_name = user_info.get('family_name')
            user.email = user_info.get('email')
            user.save()

        except user.DoesNotExist:
            user = user.objects.create_user(username, password)

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
        user = get_user_model()
        try:
            return user.objects.get(username=user_identifier)
        except user.DoesNotExist:
            try:
                return user.objects.get(id=user_identifier)
            except user.DoesNotExist:
                return None
