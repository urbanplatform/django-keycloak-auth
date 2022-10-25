"""
Module to interact with django settings
"""
import re
from dataclasses import dataclass, field
from typing import Optional, List
from django.conf import settings as django_settings

# Get settings
@dataclass
class Settings:
    """
    Django Keycloak settings container
    """

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
    # Flag if the token should be introspected or decoded
    DECODE_TOKEN: Optional[bool] = False
    # The percentage of a tokens valid duration until a new token is requested
    TOKEN_TIMEOUT_FACTOR: Optional[float] = 0.9


__desired_variables = Settings.__annotations__.keys()
__defined_variables = getattr(
    django_settings,
    "KEYCLOAK_CONFIG",
    {},
)
# Create a dict of the values of the settings defined in django
__values = {
    key: value
    for key in __desired_variables
    if key in __defined_variables
    and (value := __defined_variables.get(key)) is not None
}
try:
    # The exported settings object
    settings = Settings(**__values)
except TypeError as e:
    import django_keycloak.errors as errors

    # Get missing variables with regex
    missing_required_vars = re.findall("'([^']*)'", str(e))
    raise errors.KeycloakMissingSettingError(" / ".join(missing_required_vars)) from e
