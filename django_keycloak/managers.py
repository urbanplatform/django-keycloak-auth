"""
Module containing custom object managers
"""
from django.contrib.auth.models import UserManager
from django_keycloak import Token


class KeycloakUserManager(UserManager):
    def create_from_token(self, token: Token, **kwargs):
        """
        Create a new local database user from a valid token.
        """

        # Get user info from token
        user_info = token.user_info

        # set admin permissions if user is admin
        if token.is_superuser:
            is_staff = is_superuser = True
        else:
            is_staff = is_superuser = False

        # Create the django user from the token information
        user = self.model(
            id=user_info.get("sub"),
            username=user_info.get("preferred_username"),
            is_staff=is_staff,
            is_superuser=is_superuser,
            **kwargs
        )
        user.save(using=self._db)
        return user

    def get_by_keycloak_id(self, keycloak_id):
        return self.get(id=keycloak_id)


class KeycloakUserManagerAutoId(KeycloakUserManager):
    def create_from_token(self, token: Token, **kwargs):
        """
        Create a local new user from a valid token
        """

        user_info = token.user_info

        # set admin permissions if user is admin
        if token.is_superuser:
            is_staff = is_superuser = True
        else:
            is_staff = is_superuser = False

        # Create the django user from the token information
        user = self.model(
            keycloak_id=user_info.get("sub"),
            username=user_info.get("preferred_username"),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name"),
            email=user_info.get("email"),
            is_staff=is_staff,
            is_superuser=is_superuser,
            **kwargs
        )
        user.save(using=self._db)
        return user

    def get_by_keycloak_id(self, keycloak_id):
        """
        Returns a local user by keycloak id
        """
        return self.get(keycloak_id=keycloak_id)
