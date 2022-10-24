"""
Module containing custom errors.
"""
from django_keycloak.config import settings


class KeycloakAPIError(Exception):
    """
    This should be raised on KeycloakAPIErrors
    """

    def __init__(self, status, message):
        self.status = status
        self.message = message


class KeycloakNoServiceAccountRolesError(Exception):
    """
    Raised when the Keycloak server is not configured for
    "Service account roles" for a particular client.
    """

    def __init__(self):
        super().__init__(
            (
                "'Service account roles' setting not enabled. "
                f"Please enable this authentication workflow for client '{settings.CLIENT_ID}'."
            )
        )


class KeycloakMissingServiceAccountRolesError(Exception):
    """
    Raised when the Keycloak server has service account roles enabled,
    but a necessary role is missing.
    """

    def __init__(self):
        super().__init__(
            (
                "'Service account roles' setting is enabled, "
                "but role 'manage-users' is missing. "
                f"To enable it go to realm '{settings.REALM}' --> '{settings.CLIENT_ID}' client --> Service accounts roles "
                " --> Assign role --> Filter by clients --> and add 'manage-users'."
            )
        )
