from django.contrib.auth.models import UserManager
from django.utils import timezone

from django_keycloak.keycloak import Connect


class KeycloakUserManager(UserManager):
    def __init__(self, *args, **kwargs):
        self.keycloak = Connect()
        super().__init__(*args, **kwargs)

    def _create_user_on_keycloak(
            self, username, email, first_name=None, last_name=None, enabled=True, actions=None
    ):
        """Creates user on keycloak server, No state is changed on local db"""
        keycloak = Connect()
        values = {"username": username, "email": email, "enabled": enabled}
        if first_name is not None:
            values["firstName"] = first_name
        if last_name is not None:
            values["lastName"] = last_name
        if actions is not None:
            values["requiredActions"] = actions
        keycloak.create_user(**values)
        return keycloak.get_users(username=username)[0]

    def create_user(self, username, password=None, **kwargs):
        """
        Creates a local user if the user exists on keycloak
        """
        token = self.keycloak.get_token_from_credentials(username, password).get("access_token")
        if token is None:
            raise ValueError("Wrong credentials")
        user = self.create_from_token(token, password)
        return user

    def create_superuser(self, username, password=None, **kwargs):
        """
        Creates a local super user if the user exists on keycloak and is superuser
        """
        token = self.keycloak.get_token_from_credentials(username, password).get("access_token")
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
            id=user_info.get("sub"),
            username=user_info.get("username"),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_ame"),
            email=user_info.get("email"),
            is_staff=is_staff,
            is_superuser=is_superuser,
            date_joined=timezone.now(),
            **kwargs
        )
        user.save(using=self._db)
        return user

    def get_by_keycloak_id(self, keycloak_id):
        return self.get(id=keycloak_id)


    def create_keycloak_user(self,  *args, **kwargs):
        keycloak_user = self._create_user_on_keycloak(*args, **kwargs)
        self.create(
            id=keycloak_user.get('id'),
            username=keycloak_user.get('username'),
        )


class KeycloakUserManagerAutoId(KeycloakUserManager):
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
            keycloak_id=user_info.get("sub"),
            username=user_info.get("username"),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name"),
            email=user_info.get("email"),
            is_staff=is_staff,
            is_superuser=is_superuser,
            date_joined=timezone.now(),
            **kwargs
        )
        user.save(using=self._db)
        return user

    def get_by_keycloak_id(self, keycloak_id):
        return self.get(keycloak_id=keycloak_id)

    def create_keycloak_user(self, *args, **kwargs):
        keycloak_user = self._create_user_on_keycloak(*args, **kwargs)
        self.create(
            username=keycloak_user.get('username'),
            keycloak_id=keycloak_user.get('id'),
        )
