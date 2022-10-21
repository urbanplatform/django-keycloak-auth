import logging
import re

from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from django_keycloak.keycloak import Connect
from django_keycloak.models import KeycloakUserAutoId


class KeycloakMiddlewareMixin:
    def append_user_info_to_request(self, request, token):
        """Appends user info to the request"""

        if hasattr(request, "remote_user"):
            return request

        user_info = self.keycloak.get_user_info(token)
        request.remote_user = {
            "client_roles": self.keycloak.client_roles(token),
            "realm_roles": self.keycloak.realm_roles(token),
            "client_scope": self.keycloak.client_scope(token),
            "name": user_info.get("name"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "username": user_info.get("preferred_username"),
            "email": user_info.get("email"),
            "email_verified": user_info.get("email_verified"),
        }

        # Create or update user info
        try:
            user = get_user_model().objects.get_by_keycloak_id(
                self.keycloak.get_user_id(token)
            )

            # Only KeycloakUserAutoId stores the user details locally
            if isinstance(user, KeycloakUserAutoId):
                user.first_name = user_info.get("given_name")
                user.last_name = user_info.get("family_name")
                user.email = user_info.get("email")
                user.save()

        except get_user_model().DoesNotExist:
            user = get_user_model().objects.create_from_token(token)
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
        if len(auth_header) == 2:
            return auth_header[1]
        return None


class KeycloakGrapheneMiddleware(KeycloakMiddlewareMixin):
    """
    Middleware to validate Keycloak access based on Graphql validations
    """

    def __init__(self):
        logging.warning(
            "All functionality is provided by KeycloakMiddleware", DeprecationWarning, 2
        )
        self.keycloak = Connect()

    def resolve(self, next, root, info, **kwargs):
        """
        Graphene Middleware to validate keycloak access
        """
        request = info.context

        if self.is_auth_header_missing(request):
            """Append anonymous user and continue"""
            return next(root, info, **kwargs)

        token = self.get_token(request)
        if token is None:
            raise Exception("Invalid token structure. Must be 'Bearer <token>'")

        if not self.keycloak.is_token_active(token):
            raise Exception("Invalid or expired token.")

        info.context = self.append_user_info_to_request(request, token)

        return next(root, info, **kwargs)


class KeycloakMiddleware(KeycloakMiddlewareMixin, MiddlewareMixin):
    """
    Middleware to validate Keycloak access based on REST validations
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.keycloak = Connect()

    def process_request(self, request):
        """
        To be executed before the view each request
        """
        # Skip auth for gql endpoint (it is done in KeycloakGrapheneMiddleware)
        if self.is_graphql_endpoint(request):
            return
        # Extract token from "Bearer <token>" string
        if auth_value := request.META.get("HTTP_AUTHORIZATION"):
            split_auth_value = auth_value.split("Bearer ")
            if len(split_auth_value) != 2:
                return
            token = split_auth_value[1]
            if not self.keycloak.is_token_active(token):
                return JsonResponse({"detail": "Invalid or expired token."}, status=401)
            self.append_user_info_to_request(request, token)

    def pass_auth(self, request):
        """
        Check if the current URI path needs to skip authorization
        """
        logging.warning("Not used by middleware", DeprecationWarning, 2)
        path = request.path_info.lstrip("/")
        return any(re.match(m, path) for m in self.keycloak.exempt_uris)

    def is_graphql_endpoint(self, request):
        """
        Check if the request path belongs to a graphql endpoint
        """
        if self.keycloak.graphql_endpoint is None:
            return False

        path = request.path_info.lstrip("/")
        is_graphql_endpoint = re.match(self.keycloak.graphql_endpoint, path)
        if is_graphql_endpoint and request.method != "GET":
            return True

        return False
