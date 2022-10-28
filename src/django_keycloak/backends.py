"""
Module containing custom Django authentication backends.
"""
from typing import Optional, Union
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth import get_user_model
from django_keycloak.models import KeycloakUserAutoId, KeycloakUser
from django_keycloak import Token


class KeycloakAuthenticationBackend(RemoteUserBackend):
    """
    Custom remote backend for Keycloak
    """

    def authenticate(
        self,
        request,
        remote_user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Authenticates a user by credentials, and
        updates their information (first name, last name, email).
        If user does not exist it is created with appropriate permissions.

        Parameters
        ----------
        remote_user: str
            The Keycloak's username.
        password: str
            The Keycloak's password.
        """

        # Create token from the provided credentials and check if
        # credentials were valid
        token = Token.from_credentials(remote_user, password)  # type: ignore

        # Check for non-existing or inactive token
        if not token:
            # credentials were not valid
            return

        # Get the user model
        User: Union[KeycloakUser, KeycloakUserAutoId] = get_user_model()  # type: ignore

        # try to get user from database
        try:
            user = User.objects.get(username=remote_user)
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

        user.is_staff = user.is_superuser = bool(token.is_superuser)

        user.save()
        return user

    def get_user(self, user_id: str):
        User: Union[KeycloakUser, KeycloakUserAutoId] = get_user_model()
        try:
            return User.objects.get(username=user_id)
        except User.DoesNotExist:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None
