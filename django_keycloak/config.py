"""
Module to interact with django settings
"""
from dataclasses import dataclass, field
from typing import List, Optional

from django.conf import settings as django_settings


# Get settings
@dataclass
class Settings:
    # Base URL to the Keycloak server from the client application https://auth.example.com
    SERVER_URL: str
    # The Keycloak realm in which this client is registered
    REALM: str
    # The ID of this client in the above Keycloak realm
    CLIENT_ID: str
    # The secret for this confidential client
    CLIENT_SECRET_KEY: str
    # The name of the admin role for the client
    CLIENT_ADMIN_ROLE: str
    # The name of the admin role for the realm
    REALM_ADMIN_ROLE: str
    # Regex formatted URLs to skip authentication for (uses re.match())
    EXEMPT_URIS: Optional[List] = field(default_factory=[])
    # Overrides SERVER_URL for Keycloak admin calls
    INTERNAL_URL: Optional[str] = None
    # Override default Keycloak base path (/auth/)
    BASE_PATH: Optional[str] = "/auth/"
    # Regex formatted URL to excempt the GraphQL URL"""
    GRAPHQL_ENDPOINT: Optional[str] = "graphql/"
    # Flag if the token should be introspected or decoded
    DECODE_TOKEN: Optional[bool] = False
    # Flag if the audience in the token should be verified
    VERIFY_AUDIENCE: Optional[bool] = True
    # Flag if the user info has been included in the token
    USER_INFO_IN_TOKEN: Optional[bool] = True
    # Derived setting of the SERVER/INTERNAL_URL and BASE_PATH
    KEYCLOAK_URL: str = field(init=False)

    def __post_init__(self) -> None:
        # Decide URL (internal url overrides serverl url)
        URL = self.INTERNAL_URL if self.INTERNAL_URL else self.SERVER_URL
        self.KEYCLOAK_URL = f"{URL}{self.BASE_PATH}"


# The exported settings object
settings = Settings(**django_settings.KEYCLOAK_CONFIG)
