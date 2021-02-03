from django.contrib.auth.models import UserManager
from django.utils import timezone

from django_keycloak.keycloak import Connect


class KeycloakUserManager(UserManager):
    def __init__(self, *args, **kwargs):
        self.keycloak = Connect()
        super().__init__(*args, **kwargs)

    def create_user(self, username, password=None, **kwargs):
        """
        Creates a local user if the user exists on keycloak
        """
        token = self.keycloak.get_token_from_credentials(username, password)
        if token is None:
            raise ValueError("Wrong credentials")
        user = self.create_from_token(token, password)
        return user

    def create_superuser(self, username, password=None, **kwargs):
        """
        Creates a local super user if the user exists on keycloak and is superuser
        """
        token = self.keycloak.get_token_from_credentials(username, password)
        if token is None:
            raise ValueError("Wrong credentials")
        if not self.keycloak.has_superuser_perm(token):
            raise ValueError("You are not an administrator")

        user = self.create_from_token(token, password)
        user.save(using=self._db)
        return user

    def create_from_token(self, token, password=None, **kwargs):
        """
        Create a new user from a valid token
        """
        if not self.keycloak.is_token_active(token):
            raise ValueError("Invalid token")

        user_info = self.keycloak.introspect(token)

        # set admin permissions if user is admin
        is_staff = False
        is_superuser = False
        if self.keycloak.has_superuser_perm(token):
            is_staff = True
            is_superuser = True

        user = self.model(
            username=user_info.get("username"),
            keycloak_id=user_info.get("sub"),
            is_staff=is_staff,
            is_superuser=is_superuser,
            date_joined=timezone.now(),
            **kwargs
        )
        user.save(using=self._db)
        return user

    def get_user_info(self, user_id):
        return self.keycloak.get_user_info_by_id(user_id)
