"""
Module to interact with Keycloak Admin API
"""
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError


from keycloak.keycloak_admin import KeycloakAdmin
from django_keycloak.errors import (
    KeycloakNoServiceAccountRolesError,
    KeycloakMissingServiceAccountRolesError,
)

from django_keycloak.config import settings

# Variables for parent constructor
SERVER_URL = settings.SERVER_URL
INTERNAL_URL = settings.INTERNAL_URL
BASE_PATH = settings.BASE_PATH
REAL_NAME = settings.REALM
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET_KEY = settings.CLIENT_SECRET_KEY

# Decide URL (internal url overrides serverl url)
URL = INTERNAL_URL if INTERNAL_URL else SERVER_URL
# Add base path
URL += BASE_PATH

try:
    KeycloakAdminConnector = KeycloakAdmin(
        server_url=URL,
        client_id=CLIENT_ID,
        realm_name=REAL_NAME,
        client_secret_key=CLIENT_SECRET_KEY,
    )

    # # Check for 403 unknown error (missing required roles)
    # except if "unknown_error" in str(error):
    #     raise KeycloakMissingServiceAccountRolesError(CLIENT_ID)
except KeycloakAuthenticationError as error:
    # Check if the error is due to service account not being enabled
    if "Client not enabled to retrieve service account" in str(error):
        raise KeycloakNoServiceAccountRolesError(CLIENT_ID)

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
        raise KeycloakMissingServiceAccountRolesError(CLIENT_ID)
    else:
        raise error
