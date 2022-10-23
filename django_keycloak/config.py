"""
Module to interact with django settings
"""
from django.conf import settings as django_settings

# Get settings

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Settings:
    SERVER_URL: str
    REALM: str
    CLIENT_ID: str
    CLIENT_SECRET_KEY: str
    CLIENT_ADMIN_ROLE: str
    REALM_ADMIN_ROLE: str
    EXEMPT_URIS: Optional[List] = field(default_factory=[])
    INTERNAL_URL: Optional[str] = None
    BASE_PATH: Optional[str] = ""
    GRAPHQL_ENDPOINT: Optional[str] = "graphql/"

    def __init__(self, **vars) -> None:

        for key, value in vars.items():
            setattr(self, key, value)


__desired_variables = Settings.__annotations__.keys()
__defined_variables = getattr(django_settings, "KEYCLOAK_CONFIG", {})
# Create a dict of the values of the settings defined in django
__values = {key: __defined_variables.get(key) for key in __desired_variables}

# The exported settings object
settings = Settings(**__values)
