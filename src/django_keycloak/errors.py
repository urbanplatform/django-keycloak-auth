"""
Module containing custom errors.
"""
import django_keycloak.config as config


class KeycloakAPIError(Exception):
    """
    This should be raised on KeycloakAPIErrors
    """

    def __init__(self, status, message):
        self.status = status
        self.message = message


class KeycloakMissingSettingError(Exception):
    """
    Raised when a given Django Keycloak setting(s) is missing.
    """

    def __init__(self, setting: str):
        super().__init__(
            (
                f"The following settings are missing: '{setting}' "
                "Please add them in 'KEYCLOAK_CONFIG' inside Django settings"
            )
        )


class KeycloakNoServiceAccountRolesError(Exception):
    """
    Raised when the Keycloak server is not configured for
    "Service account roles" for a particular client.
    """

    def __init__(self):
        super().__init__(
            (
                "'Service account roles' setting not enabled. "
                f"Please enable this authentication workflow for client '{config.settings.CLIENT_ID}'."
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
                f"To enable it go to realm '{config.settings.REALM}' --> '{config.settings.CLIENT_ID}' client --> Service accounts roles "
                " --> Assign role --> Filter by clients --> and add 'manage-users'."
            )
        )
