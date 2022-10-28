"""
Module to interact with the Keycloak token API
"""
from __future__ import annotations

import logging
from typing import Optional

from cachetools.func import ttl_cache
from jose.exceptions import JOSEError
from keycloak.exceptions import (
    KeycloakAuthenticationError,
    KeycloakError,
    KeycloakPostError,
)
from keycloak.keycloak_openid import KeycloakOpenID

from django_keycloak.config import settings

# Define keycloak openid instance
KEYCLOAK = KeycloakOpenID(
    server_url=settings.KEYCLOAK_URL,
    client_id=settings.CLIENT_ID,
    realm_name=settings.REALM,
    client_secret_key=settings.CLIENT_SECRET_KEY,
)

logger = logging.getLogger(__name__)


class Token:
    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token

    @property
    @ttl_cache(maxsize=1, ttl=60)
    def public_key(self):
        """
        Obtains the Keycloak's Public key, used for token
        decodings.

        Raises:
            KeycloakError: On Keycloak API errors
        """

        return f"-----BEGIN PUBLIC KEY-----\n{KEYCLOAK.public_key()}\n-----END PUBLIC KEY-----"

    @ttl_cache(maxsize=1, ttl=60)
    def get_access_token_info(self) -> dict:
        """
        Gets the information from a token either using token decode
        or introspect, depending on `DECODE_TOKEN` setting.

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        if not self.access_token:
            return {}
        # If user enabled `DECODE_TOKEN` using local decoding
        if settings.DECODE_TOKEN:
            return KEYCLOAK.decode_token(
                self.access_token,
                key=self.public_key,
                options={"verify_aud": settings.VERIFY_AUDIENCE},
            )
        # Otherwise hit the Keycloak API for info
        return KEYCLOAK.introspect(self.access_token)

    @ttl_cache(maxsize=1, ttl=60)
    def get_refresh_token_info(self) -> dict:
        """
        Gets the information from a token either using token decode
        or introspect, depending on `DECODE_TOKEN` setting.

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        if not self.refresh_token:
            return {}
        # If user enabled `DECODE_TOKEN` using local decoding
        if settings.DECODE_TOKEN:
            return KEYCLOAK.decode_token(
                self.refresh_token,
                key=self.public_key,
                options={"verify_aud": settings.VERIFY_AUDIENCE},
            )
        # Otherwise hit the Keycloak API for info
        return KEYCLOAK.introspect(self.refresh_token)

    @staticmethod
    def _parse_keycloak_response(keycloak_response: dict) -> dict:
        """
        Builds a dictionary mapping internal values to keycloak API
        values
        """
        return {
            "access_token": keycloak_response.get("access_token"),
            "refresh_token": keycloak_response.get("refresh_token"),
        }

    # Properties
    @property
    def is_active(self) -> bool:
        """
        Returns a boolean indicating if the current access token is active or not.
        """
        try:
            info = self.get_access_token_info()
        except (JOSEError, KeycloakError) as err:
            logger.debug(
                "%s: %s",
                type(err).__name__,
                err.args,
                exc_info=settings.TRACE_DEBUG_LOGS,
            )
            return False
        # Keycloak introspections return {"active": bool}
        return info["active"] if "active" in info else True

    @property
    def user_info(self) -> dict:
        """
        Returns the user information contained on the provided access token.

        When DECODE_TOKEN and USER_INFO_IN_TOKEN are enabled the entire token is returned

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        if settings.DECODE_TOKEN and settings.USER_INFO_IN_TOKEN:
            return self.get_access_token_info()
        return KEYCLOAK.userinfo(self.access_token)

    @property
    def user_id(self) -> str:
        """
        Returns the Keycloak user id

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        return self.user_info.get("sub")  # type: ignore

    @property
    def is_superuser(self) -> bool:
        """
        Check if token belongs to a user with superuser permissions

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        if (settings.CLIENT_ADMIN_ROLE in self.client_roles) or (  # type: ignore
            settings.REALM_ADMIN_ROLE in self.realm_roles
        ):  # type: ignore
            return True

        return False

    @property
    def client_roles(self) -> list:
        """
        Returns the client roles based on the provided access token.

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        return (
            self.get_access_token_info()
            .get("resource_access", {})
            .get(settings.CLIENT_ID, {})
            .get("roles", [])
        )

    @property
    def realm_roles(self) -> list:
        """
        Returns the realm roles based on the access token.

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        return self.get_access_token_info().get("realm_access", {}).get("roles", [])

    @property
    def client_scopes(self) -> list:
        """
        Returns the client scope based on the  access token.

        Raises:
            JOSEError: On expired or invalid tokens
            KeycloakError: On expired / invalid tokens or Keycloak API errors
        """
        return self.get_access_token_info().get("scope", "").split(" ")

    @classmethod
    def from_credentials(cls, username: str, password: str) -> Optional[Token]:  # type: ignore
        """
        Creates a `Token` object from a set of user credentials.
        Returns `None` if authentication fails.
        """
        try:
            keycloak_response = KEYCLOAK.token(username, password)
            return cls(**cls._parse_keycloak_response(keycloak_response))
        # Catch authentication error (invalid credentials),
        # and post error (account not completed.)
        except (KeycloakAuthenticationError, KeycloakPostError) as err:
            logger.debug(
                f"{type(err).__name__}: {err.args}", exc_info=settings.TRACE_DEBUG_LOGS
            )
            return None

    @classmethod
    def from_access_token(cls, access_token: str) -> Optional[Token]:
        """
        Creates a `Token` object from an existing access token.
        Returns `None` if token is not active.
        """
        instance = cls(access_token=access_token)
        return instance if instance.is_active else None

    @classmethod
    def from_refresh_token(cls, refresh_token: str) -> Optional[Token]:
        """
        Creates a `Token` from the provided refresh token.
        """
        instance = cls(refresh_token=refresh_token)
        instance.refresh()
        return instance if instance.is_active else None

    def refresh(self) -> None:
        """
        Refreshes the `access_token` with `refresh_token`.

        Raises:
            KeycloakError: On Keycloak API errors
        """
        if self.refresh_token:
            mapping = self._parse_keycloak_response(
                KEYCLOAK.refresh_token(self.refresh_token)
            )
            for key, value in mapping.items():
                setattr(self, key, value)
