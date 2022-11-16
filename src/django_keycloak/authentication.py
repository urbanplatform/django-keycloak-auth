"""
Custom authentication class for Django Rest Framework.
"""
from typing import Union
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django_keycloak import Token
from django_keycloak.config import settings


class KeycloakAuthentication(TokenAuthentication):
    """
    A custom token authentication class for Keycloak.
    """

    # `keyword` refers to expected prefix in HTTP
    # Authentication header. Use the user-defined prefix
    keyword = settings.TOKEN_PREFIX

    def authenticate_credentials(self, access_token: str):
        """
        Overrides `authenticate_credentials` to provide custom
        Keycloak authentication for a given token in a request.
        """
        # Try to build a Token instance from the provided access token in request
        token: Union[Token, None] = Token.from_access_token(access_token)

        # Check for valid Token instance
        if not token:
            raise AuthenticationFailed

        # Get the associated user by keycloak id
        user = get_user_model().objects.get_by_keycloak_id(token.user_id)

        # Return the user and the associated access token
        return (user, token.access_token)
