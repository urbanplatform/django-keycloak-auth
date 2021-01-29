import re

from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from django_keycloak.keycloak import Connect


class KeycloakMiddlewareMixin:

    def append_user_info_to_request(self, request, token):
        """Appends user info to the request"""

        if hasattr(request, "remote_user"):
            return request

        user_info = self.keycloak.get_user_info(token)
        request.remote_user = {
            'client_roles': self.keycloak.client_roles(token),
            'realm_roles': self.keycloak.client_roles(token),
            'client_scope': self.keycloak.client_scope(token),
            'name': user_info.get('name'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name'),
            'username': user_info.get('preferred_username'),
            'email': user_info.get('email'),
            'email_verified': user_info.get('email_verified'),
        }

        # get user or create from token
        User = get_user_model()
        try:
            request.user = User.objects.get(keycloak_id=self.keycloak.get_user_id(token))
        except User.DoesNotExist:
            request.user = User.objects.create_from_token(token)

        return request

    def has_auth_header(self, request):
        """Check if exists an authentication header in the HTTP request"""
        return 'HTTP_AUTHORIZATION' not in request.META

    def get_token(self, request):
        """Get the token from the HTTP request"""
        auth_header = request.META.get('HTTP_AUTHORIZATION').split()
        if len(auth_header) == 2:
            return auth_header[1]
        return None


class KeycloakGrapheneMiddleware(KeycloakMiddlewareMixin):
    """
    Middleware to validate Keycloak access based on Graphql validations
    """

    def __init__(self):
        self.keycloak = Connect()

    def resolve(self, next, root, info, **kwargs):
        """
        Graphene Middleware to validate keycloak access
        """
        request = info.context

        if self.has_auth_header(request):
            raise Exception("Authorization header missing")

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
        self.keycloak = Connect()

        # Django response
        self.get_response = get_response

    def __call__(self, request):
        """
        To be executed before the view each request
        """
        # Checks URIs that doesn't need authentication
        if self.pass_auth(request) or self.is_graphql_endpoint(request):
            return self.get_response(request)

        if self.has_auth_header(request):
            return JsonResponse(
                {"detail": "Authentication credentials were not provided."},
                status=401,
            )

        token = self.get_token(request)
        if token is None:
            return JsonResponse(
                {"detail": "Invalid token structure. Must be 'Bearer <token>'"},
                status=401,
            )

        if not self.keycloak.is_token_active(token):
            return JsonResponse(
                {"detail": "Invalid or expired token."},
                status=401,
            )

        request = self.append_user_info_to_request(request, token)
        return self.get_response(request)

    def pass_auth(self, request):
        """
        Check if the current URI path needs to skip authorization
        """
        path = request.path_info.lstrip('/')
        return any(re.match(m, path) for m in self.keycloak.exempt_uris)

    def is_graphql_endpoint(self, request):
        """
        Check if the request path belongs to a graphql endpoint
        """
        if self.keycloak.graphql_endpoint is None:
            return False

        path = request.path_info.lstrip('/')
        if re.match(path, self.keycloak.graphql_endpoint):
            return True

        return False
