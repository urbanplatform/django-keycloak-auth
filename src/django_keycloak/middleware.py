"""
Module containing custom middleware to authenticate, create and
sync user information between keycloak and local database.
"""
import base64
import re
from typing import Optional, Union

from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

from django_keycloak import Token
from django_keycloak.config import settings
from django_keycloak.models import KeycloakUser, KeycloakUserAutoId


class KeycloakMiddleware(MiddlewareMixin):
    """
    Middleware to validate Keycloak access based on REST validations
    """

    def get_token_from_request(self, request) -> Optional[Token]:
        """
        Get the value of "HTTTP_AUTHORIZATION" request header.
        If the authorization is "Bearer" it tries to produce a "Token"
        instance from it.
        If the authorization is "Basic" (username+password) it tries
        to authenticate the user
        """
        auth_type, value, *_ = request.META.get("HTTP_AUTHORIZATION").split()

        if auth_type == "Basic":
            decoded_username, decoded_password = (
                base64.b64decode(value).decode("utf-8").split(":")
            )
            # Try to build a Token instance from decoded credentials
            token = Token.from_credentials(decoded_username, decoded_password)
            if token:
                # Convert the request "Basic" auth to "Bearer" with access token
                request.META["HTTP_AUTHORIZATION"] = f"Bearer {token.access_token}"
            else:
                # Setup an invalid dummy bearer token
                request.META["HTTP_AUTHORIZATION"] = "Bearer not-valid-token"

        elif auth_type == "Bearer":
            token = Token.from_access_token(value)

        return token

    def append_user_info_to_request(self, request, token: Token):
        """
        Appends user info to the request
        """
        # Check if already appended in a previous request
        if hasattr(request, "remote_user"):
            return request

        user_info = token.user_info

        # add the remote user to request
        request.remote_user = {
            "client_roles": token.client_roles,
            "realm_roles": token.realm_roles,
            "client_scope": token.client_scopes,
            "name": user_info.get("name"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "username": user_info.get("preferred_username"),
            "email": user_info.get("email"),
            "email_verified": user_info.get("email_verified"),
        }

        # Get the user model
        User: Union[KeycloakUser, KeycloakUserAutoId] = get_user_model()  # type: ignore

        # Create or update user info
        try:
            user = User.objects.get_by_keycloak_id(token.user_id)

            # Only KeycloakUserAutoId stores the user details locally
            if isinstance(user, KeycloakUserAutoId):
                user.first_name = user_info.get("given_name")
                user.last_name = user_info.get("family_name")
                user.email = user_info.get("email")
                user.save()

        except User.DoesNotExist:
            user = User.objects.create_from_token(token)

        # Add the local user to request
        request.user = user

        return request

    @staticmethod
    def has_auth_header(request) -> bool:
        """Check if exists an authentication header in the HTTP request"""
        return "HTTP_AUTHORIZATION" in request.META

    def process_request(self, request):
        """
        To be executed before the view each request.
        """
        # Skip auth in the following cases:
        # 1. It is a URL in "EXEMPT_URIS"
        # 2. Request does not contain authorization header
        # Also skip auth for "EXEMPT_URIS" defined in configs
        if self.pass_auth(request) or not self.has_auth_header(request):
            return

        token: Union[Token, None] = self.get_token_from_request(request)

        # If token is None, access token was not valid
        if token:
            # Add user info to request for a valid token
            self.append_user_info_to_request(request, token)

    def pass_auth(self, request):
        """
        Check if the current URI path needs to skip authorization
        """
        path = request.path_info.lstrip("/")
        exempt_uris = settings.EXEMPT_URIS

        return any(re.match(m, path) for m in exempt_uris)
