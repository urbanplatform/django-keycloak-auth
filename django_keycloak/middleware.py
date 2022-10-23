"""
Module containing custom middleware to authenticate, create and
sync user information between keycloak and local database.
"""
import logging
import re
from typing import Union
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django_keycloak.models import KeycloakUserAutoId, KeycloakUser
from django_keycloak import Token
from django_keycloak.config import settings

# Create a reusable no permission JSON response with 401 status code
NO_PERMISSION = lambda: JsonResponse(
    {"detail": "Invalid credentials provided to perform this action."},
    status=401,
)


class KeycloakMiddlewareMixin:
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
    def is_auth_header_missing(request):
        """Check if exists an authentication header in the HTTP request"""
        return "HTTP_AUTHORIZATION" not in request.META

    @staticmethod
    def get_token(request):
        """Get the token from the HTTP request"""
        auth_header = request.META.get("HTTP_AUTHORIZATION").split()
        if len(auth_header) > 1:
            return auth_header[1]
        return auth_header[0]


class KeycloakGrapheneMiddleware(KeycloakMiddlewareMixin):
    """
    Middleware to validate Keycloak access based on Graphql validations
    """

    def __init__(self):
        logging.warning(
            "All functionality is provided by KeycloakMiddleware", DeprecationWarning, 2
        )

    def resolve(self, next, root, info, **kwargs):
        """
        Graphene Middleware to validate keycloak access
        """
        request = info.context

        if self.is_auth_header_missing(request):
            # Append anonymous user and continue
            return next(root, info, **kwargs)

        # Build token from request
        token = Token.from_access_token(self.get_token(request))

        # Check if Token was created
        if not token:
            return NO_PERMISSION()

        info.context = self.append_user_info_to_request(request, token.access_token)

        return next(root, info, **kwargs)


class KeycloakMiddleware(KeycloakMiddlewareMixin, MiddlewareMixin):
    """
    Middleware to validate Keycloak access based on REST validations
    """

    def process_request(self, request):
        """
        To be executed before the view each request.
        """
        # Skip auth in the following cases:
        # 1. It is a graphql endpoint (handled by KeycloakGrapheneMiddleware)
        # 2. It is a URL in "EXEMPT_URIS"
        # 3. Request does not contain authorization header
        # Also skip auth for "EXEMPT_URIS" defined in configs
        if (
            self.is_graphql_endpoint(request)
            or self.pass_auth(request)
            or self.is_auth_header_missing(request)
        ):
            return

        # Otherwise validate the token
        token = Token.from_access_token(KeycloakMiddleware.get_token(request))

        # If token is None, access token was not valid
        if not token:
            return NO_PERMISSION()

        # Add user info to request for a valid token
        self.append_user_info_to_request(request, token)

    def pass_auth(self, request):
        """
        Check if the current URI path needs to skip authorization
        """
        path = request.path_info.lstrip("/")
        exempt_uris = settings.EXEMPT_URIS

        return any(re.match(m, path) for m in exempt_uris)

    def is_graphql_endpoint(self, request):
        """
        Check if the request path belongs to a graphql endpoint
        """
        graphql_endpoint = settings.GRAPHQL_ENDPOINT
        if graphql_endpoint is None:
            return False

        path = request.path_info.lstrip("/")
        is_graphql_endpoint = re.match(graphql_endpoint, path)
        if is_graphql_endpoint and request.method != "GET":
            return True

        return False
