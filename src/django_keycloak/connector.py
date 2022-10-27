"""
Module to interact with Keycloak Admin API
"""
from typing import Dict, List

from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
from keycloak.keycloak_admin import KeycloakAdmin

from django_keycloak.config import settings
from django_keycloak.errors import (
    KeycloakMissingServiceAccountRolesError,
    KeycloakNoServiceAccountRolesError,
)

_args: List
_kwargs: Dict
_initialized: bool = False


class LazyKeycloakAdmin(KeycloakAdmin):
    def __init__(self, *args, **kwargs):
        global _args, _kwargs
        _args, _kwargs = args, kwargs

    def __getattribute__(self, item):
        global _initialized, _args, _kwargs
        if not _initialized:
            _initialized = True
            self.handle_keycloak_init(_args, _kwargs)
        # Calling the super class to avoid recursion
        return super().__getattribute__(item)

    def handle_keycloak_init(self, args, kwargs):
        try:
            super().__init__(*args, **kwargs)
            # Try to call a users method
            # if error occurs a required role is missing
            # https://github.com/marcospereirampj/python-keycloak/issues/87
            try:
                self.users_count()
            except KeycloakGetError as error:
                if "unknown_error" in str(error):
                    raise KeycloakMissingServiceAccountRolesError from error
                else:
                    raise error
        except KeycloakAuthenticationError as error:
            # Check if the error is due to service account not being enabled
            if "Client not enabled to retrieve service account" in str(error):
                raise KeycloakNoServiceAccountRolesError from error

            # Otherwise re-throw the original error
            else:
                raise error


# lazy_keycloak_admin = lazy_init(KeycloakAdmin)(
lazy_keycloak_admin = LazyKeycloakAdmin(
    server_url=settings.KEYCLOAK_URL,
    client_id=settings.CLIENT_ID,
    realm_name=settings.REALM,
    client_secret_key=settings.CLIENT_SECRET_KEY,
)
