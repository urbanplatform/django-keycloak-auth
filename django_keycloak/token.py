"""
Module to interact with the Keycloak token API
"""
from __future__ import annotations
from typing import Any, Callable, TypeVar, cast, Optional
from dataclasses import dataclass
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError
from keycloak.keycloak_openid import KeycloakOpenID
from django_keycloak.config import settings

F = TypeVar("F", bound=Callable[..., Any])


def with_active_token_property(f: F) -> F:
    @property
    def wrapper(self, *args, **kwargs):
        # Only allow the method if token is active
        if not self.active:
            return None
        return f(self, *args, **kwargs)

    return cast(F, wrapper)


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

# Define keycloak openid instance
KEYCLOAK = KeycloakOpenID(
    server_url=URL,
    client_id=CLIENT_ID,
    realm_name=REAL_NAME,
    client_secret_key=CLIENT_SECRET_KEY,
)


@dataclass
class Token:
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_expires_in: Optional[int] = None

    # Helpers methods

    @staticmethod
    def get_token_info(access_token: str) -> dict:
        """
        Gets the information from a token either using token decode
        or introspect, depending on `DECODE_TOKEN` setting.
        """
        # If user enabled `DECODE_TOKEN` using local decoding
        if settings.DECODE_TOKEN:
            return KEYCLOAK.decode_token(
                access_token,
                key=(
                    "-----BEGIN PUBLIC KEY-----\n"
                    + KEYCLOAK.public_key()
                    + "\n-----END PUBLIC KEY-----"
                ),
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_exp": True,
                },
            )
        # Otherwise hit the Keycloak API for info
        return KEYCLOAK.introspect(access_token)

    @staticmethod
    def _parse_keycloak_response(keycloak_response: dict) -> dict:
        """
        Builds a dictionary mapping internal values to keycloak API
        values
        """
        return {
            "access_token": keycloak_response["access_token"],
            "refresh_token": keycloak_response["refresh_token"],
            "expires_in": keycloak_response["expires_in"],
            "refresh_expires_in": keycloak_response["refresh_expires_in"],
        }

    # Properties

    @property
    def active(self):
        """
        Returns a boolean indicating if the current access token is active or not.
        """
        return KEYCLOAK.introspect(self.access_token).get("active", False)

    @with_active_token_property
    def user_info(self) -> dict:
        """
        Returns the user information contained on the provided access token.
        """
        return KEYCLOAK.userinfo(self.access_token)

    @with_active_token_property
    def user_id(self) -> str:
        """
        Returns the Keycloak user id
        """
        return self.user_info.get("sub")  # type: ignore

    @with_active_token_property
    def superuser(self) -> bool:
        """
        Returns a boolean indicating if the user has admin
        permissions
        """
        if (settings.CLIENT_ADMIN_ROLE in self.client_roles) or (  # type: ignore
            settings.REALM_ADMIN_ROLE in self.realm_roles
        ):  # type: ignore
            return True

        return False

    @with_active_token_property
    def client_roles(self) -> list:
        """
        Returns the client roles based on the provided access token.
        """
        return (
            Token.get_token_info(self.access_token)
            .get("resource_access", {})
            .get(settings.CLIENT_ID, {})
            .get("roles", [])
        )

    @with_active_token_property
    def realm_roles(self) -> list:
        """
        Returns the realm roles based on the access token.
        """
        return (
            Token.get_token_info(self.access_token)
            .get("realm_access", {})
            .get("roles", [])
        )

    @with_active_token_property
    def client_scopes(self) -> list:
        """
        Returns the client scope based on the  access token.
        """
        return Token.get_token_info(self.access_token).get("scope", "").split(" ")

    # Methods

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
        except (KeycloakAuthenticationError, KeycloakPostError):
            return None

    @classmethod
    def from_access_token(cls, access_token: str) -> Optional[Token]:
        """
        Creates a `Token` object from an existing access token.
        Returns `None` if token is not active.
        """
        instance = cls(access_token=access_token)
        return instance if instance.active else None

    @classmethod
    def from_refresh_token(cls, refresh_token: str) -> Optional[Token]:
        """
        Creates a `Token` from the provided refresh token.
        """
        instance = cls(refresh_token=refresh_token)
        instance.refresh()
        return instance

    def refresh(self) -> None:
        """
        Refreshes the `access_token` with `refresh_token`.
        """
        if self.refresh_token:
            mapping = self._parse_keycloak_response(
                KEYCLOAK.refresh_token(self.refresh_token)
            )
            for key, value in mapping.items():
                setattr(self, key, value)
