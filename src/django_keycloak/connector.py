"""
Module to interact with Keycloak Admin API
"""
from django.contrib.auth import get_user_model
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
from keycloak.keycloak_admin import KeycloakAdmin

from django_keycloak.config import settings
from django_keycloak.errors import (
    KeycloakMissingServiceAccountRolesError,
    KeycloakNoServiceAccountRolesError,
)

# Avoid circular import
import django_keycloak.models as models

# Only try to start connector if auth model user is one of this package
# user might be using conditional auth systems, and we dont want to connect
# to server if it does not exist
if not issubclass(get_user_model(), models.AbstractKeycloakUser):
    KeycloakAdminConnector = None
else:
    try:
        KeycloakAdminConnector = KeycloakAdmin(
            server_url=settings.KEYCLOAK_URL,
            client_id=settings.CLIENT_ID,
            realm_name=settings.REALM,
            client_secret_key=settings.CLIENT_SECRET_KEY,
        )
    except KeycloakAuthenticationError as error:
        # Check if the error is due to service account not being enabled
        if "Client not enabled to retrieve service account" in str(error):
            raise KeycloakNoServiceAccountRolesError from error

        # Otherwise re-throw the original error
        else:
            raise error

    # Try to call a users method
    # if error occurs a required role is missing
    # https://github.com/marcospereirampj/python-keycloak/issues/87
    try:
        KeycloakAdminConnector.users_count()
    except KeycloakGetError as error:
        if "unknown_error" in str(error):
            raise KeycloakMissingServiceAccountRolesError from error
        else:
            raise error
