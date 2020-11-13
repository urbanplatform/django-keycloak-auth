import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from django_keycloak.keycloak import Connect


def pass_auth(request):
    """
    Check if the current UTR path needs to skip authorization
    @param request:
    @return:
    """
    # Checks URIs that doesn't need authentication
    if hasattr(settings, 'KEYCLOAK_EXEMPT_URIS'):
        path = request.path_info.lstrip('/')
        if any(re.match(m, path) for m in settings.KEYCLOAK_EXEMPT_URIS):
            return True


class KeycloakGrapheneMiddleware(MiddlewareMixin):
    """
    Middleware to validate Keycloak access based on Graphene validations
    """

    def __init__(self, get_response):
        self.keycloak = Connect()

        # Django response
        self.get_response = get_response

    def __call__(self, request):
        """
        To be executed before the view each request
        """

        # TODO: Validate headers and token

        return self.get_response(request)


class KeycloakDRFMiddleware(MiddlewareMixin):
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
        if pass_auth(request):
            return self.get_response(request)

            # Checks if exists an authentication in the http request header
        if 'HTTP_AUTHORIZATION' not in request.META:
            return JsonResponse(
                {"detail": NotAuthenticated.default_detail},
                status=NotAuthenticated.status_code
            )

        # Get token from the http request header
        auth_header = request.META.get('HTTP_AUTHORIZATION').split()
        if len(auth_header) == 2:
            token = auth_header[1]
        else:
            return JsonResponse(
                {"detail": "Invalid token structure. Must be 'Bearer <token>'"},
                status=AuthenticationFailed.status_code
            )

        # Checks if token is active
        if not self.keycloak.is_token_active(token):
            return JsonResponse(
                {"detail": "Invalid or expired token."},
                status=AuthenticationFailed.status_code
            )

        # Added to the request to be used by the next middleware
        request.session.keycloak_connection = self.keycloak
        request.session.token = token

        return self.get_response(request)


class KeycloakMiddleware(MiddlewareMixin):
    """
    Middleware to include information from keycloak about the user
    """

    def __init__(self, get_response):
        # Django response
        self.get_response = get_response

    def __call__(self, request):
        """
        To be executed before the view each request
        """
        # Checks URIs that doesn't need authentication
        if pass_auth(request):
            return self.get_response(request)

            # Get keycloak connection and token from previous middleware (
        # injected in the request session)
        keycloak = request.session.keycloak_connection
        token = request.session.token

        # Get client/realm roles, scope and user info from access token and
        # added them to the request
        user_info = keycloak.get_user_info(token)

        request.remote_user = {
            'client_roles': keycloak.client_roles(token),
            'realm_roles': keycloak.client_roles(token),
            'client_scope': keycloak.client_scope(token),
            'name': user_info.get('name'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name'),
            'username': user_info.get('preferred_username'),
            'email': user_info.get('email'),
            'email_verified': user_info.get('email_verified'),
        }

        # Delete injected (previous middleware) information in the request
        # session
        del request.session.keycloak_connection
        del request.session.token

        # TODO: Create a specific model for User with a specific field for
        #  keycloak user ID that will be the primary_key
        # Get user id from keycloak and create a local reference
        User = get_user_model()
        c_user, created = User.objects.update_or_create(
            username=keycloak.get_user_id(token),
            defaults={
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'last_login': timezone.now()
            }
        )
        request.user = c_user

        return self.get_response(request)
