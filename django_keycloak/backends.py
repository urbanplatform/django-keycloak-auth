"""
Module containing custom Django authentication backends.
"""
from typing import Optional, Union
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth import get_user_model
from django_keycloak.models import KeycloakUserAutoId
from django_keycloak import Token
from django_keycloak.models import KeycloakUser, KeycloakUserAutoId


class KeycloakAuthenticationBackend(RemoteUserBackend):
    """
    Custom remote backend for Keycloak
    """

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Authenticates an user by credentials, and
        updates it's information (first name, last name, email).
        If user does not exist it is created with appropriate permissions.
        """

        # Create token from the provided credentials and check if
        # credentials were valid
        token = Token.from_credentials(username, password)  # type: ignore

        # Check for non-existing or unactive token
        if not token:
            # credentials were not valid
            return

        # Get the user model
        User: Union[KeycloakUser, KeycloakUserAutoId] = get_user_model()  # type: ignore

        # try to get user from database
        try:
            user = User.objects.get(username=username)
            if isinstance(user, KeycloakUserAutoId):
                # Get user information from token
                user_info = token.user_info

                # Update local user information based on Keycloak
                # information from token
                user.first_name = user_info.get("given_name")
                user.last_name = user_info.get("family_name")
                user.email = user_info.get("email")

        except User.DoesNotExist:
            # If user does not exist create in database
            # `create_from_token` takes cares of password hashing
            user = User.objects.create_from_token(token)

        if token.is_superuser:
            user.is_staff = user.is_superuser = True
        else:
            user.is_staff = user.is_superuser = False

        user.save()
        return user

    def get_user(self, user_identifier: str):
        User: Union[KeycloakUser, KeycloakUserAutoId] = get_user_model()
        try:
            return User.objects.get(username=user_identifier)
        except User.DoesNotExist:
            try:
                return User.objects.get(id=user_identifier)
            except User.DoesNotExist:
                return None
