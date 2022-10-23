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

    def __init__(self, keycloak_client: str):
        super().__init__(
            (
                "'Service account roles' setting not enabled. "
                f"Please enable this authentication workflow for client '{keycloak_client}'."
            )
        )


class KeycloakMissingServiceAccountRolesError(Exception):
    """
    Raised when the Keycloak server has service account roles enabled,
    but a necessary role is missing.
    """

    def __init__(self, keycloak_client: str):
        super().__init__(
            (
                "'Service account roles' setting is enabled, "
                "but role 'manage-users' is missing. "
                f"To enable it go to '{keycloak_client}' client --> Service accounts roles "
                " --> Assign role --> Filter by clients --> and add 'manage-users'."
            )
        )


class KeycloakMissingSettingError(Exception):
    """
    When a setting is missing
    """

    def __init__(self, setting_name):
        self.setting_name = setting_name
        super().__init__(
            f"Could not find setting '{self.setting_name}' in 'KEYCLOAK_CONFIG' settings."
        )
