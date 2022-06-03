from datetime import datetime, timezone
from functools import cached_property
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import jwt
import requests
from django.conf import settings
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from cachetools.func import ttl_cache

from .decorators import keycloak_api_error_handler
from .urls import (
    KEYCLOAK_CREATE_USER,
    KEYCLOAK_DELETE_USER,
    KEYCLOAK_GET_TOKEN,
    KEYCLOAK_GET_USER_BY_ID,
    KEYCLOAK_GET_USERS,
    KEYCLOAK_INTROSPECT_TOKEN,
    KEYCLOAK_USER_INFO,
    KEYCLOAK_OPENID_CONFIG,
    KEYCLOAK_UPDATE_USER,
    KEYCLOAK_CREATE_USER,
    KEYCLOAK_GET_USER_CLIENT_ROLES_BY_ID,
)


class Connect:
    """
    Keycloak connection and methods
    """

    def __init__(
        self,
        server_url=None,
        realm=None,
        client_id=None,
        client_uuid=None,
        client_secret_key=None,
        internal_url=None,
    ):
        # Load configuration from settings + args
        try:
            self.config = settings.KEYCLOAK_CONFIG
        except AttributeError:
            raise Exception("Missing KEYCLOAK_CONFIG on settings file.")
        try:
            self.server_url = server_url or self.config.get("SERVER_URL")
            self.realm = realm or self.config.get("REALM")
            self.client_uuid = client_uuid or self.config.get("CLIENT_UUID")
            self.client_id = client_id or self.config.get("CLIENT_ID")
            self.client_secret_key = client_secret_key or self.config.get(
                "CLIENT_SECRET_KEY"
            )
            self.internal_url = internal_url or self.config.get("INTERNAL_URL")
            self.client_admin_role = self.config.get("CLIENT_ADMIN_ROLE", "admin")
            self.realm_admin_role = self.config.get("REALM_ADMIN_ROLE", "admin")
            self.graphql_endpoint = self.config.get("GRAPHQL_ENDPOINT", None)
            self.exempt_uris = self.config.get("EXEMPT_URIS", [])
            # Flag if the token should be introspected or decoded
            self.enable_token_decoding = self.config.get("DECODE_TOKEN", False)
            # The percentage of a tokens valid duration until a new token is requested
            self.token_timeout_factor = self.config.get("TOKEN_TIMEOUT_FACTOR", 0.9)
            # A token belonging to a user and the respective introspection
            self.cached_token = None
            self.cached_introspect = None
            # A token belonging to the client to perform user management
            self._client_token = None
            # Audiences for the different JWT uses
            self.client_jwt_audience = self.config.get(
                "CLIENT_JWT_AUDIENCE", "realm-management"
            )
            self.user_jwt_audience = self.config.get("USER_JWT_AUDIENCE", "account")

        except KeyError as err:
            raise Exception("KEYCLOAK configuration is not defined.") from err

        if not self.server_url:
            raise Exception("SERVER_URL is not defined.")

        if not self.realm:
            raise Exception("REALM is not defined.")

        if not self.client_id:
            raise Exception("CLIENT_ID is not defined.")

        if not self.client_secret_key:
            raise Exception("CLIENT_SECRET_KEY is not defined.")

    @cached_property
    def openid_config(self):
        """Collects the identity provider's configuration"""
        return self._get_openid_config()

    @cached_property
    def jwks_client(self):
        """Collects the identity provider's public keys"""
        return PyJWKClient(self.openid_config["jwks_uri"])

    def introspect(self, token):
        """
        @param token: request token
        @return: introspected token
        """
        if self.cached_introspect and self.cached_token == token:
            return self.cached_introspect

        payload = {
            "token": token,
            "client_id": self.client_id,
            "grant_type": "client_credentials",
            "client_secret": self.client_secret_key,
        }
        server_url, headers = self._make_form_request_config()

        response = requests.request(
            "POST",
            KEYCLOAK_INTROSPECT_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
        self.cached_token = token
        self.cached_introspect = response.json()
        return self.cached_introspect

    def get_token_from_credentials(self, username, password):
        """
        Get Token for a user from credentials
        """
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
            "username": username,
            "password": password,
            "scope": "openid",
        }
        server_url, headers = self._make_form_request_config()

        response = requests.request(
            "POST",
            KEYCLOAK_GET_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
        return response.json()

    def refresh_token_from_credentials(self, refresh_token):
        """
        Refresh token
        """
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
            "refresh_token": refresh_token,
        }
        server_url, headers = self._make_form_request_config()

        response = requests.request(
            "POST",
            KEYCLOAK_GET_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
        return response.json()

    def get_token(self):
        """
        Get a client token based on client credentials
        @return:
        """

        if not self._is_client_token_timed_out():
            return self._client_token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
        }
        server_url, headers = self._make_form_request_config()

        response = requests.request(
            "POST",
            KEYCLOAK_GET_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
        self._client_token = response.json().get("access_token")
        return self._client_token

    def get_users(self, **params):
        """
        Get users for realm
        @return:
        """
        server_url, headers = self._make_secure_json_request_config()

        response = requests.request(
            "GET",
            KEYCLOAK_GET_USERS.format(server_url, self.realm),
            headers=headers,
            params=params,
        )
        return response.json()

    def get_user_info(self, token):
        """
        Get user information token
        """
        if self.enable_token_decoding:
            return self._decode_token(token, self.user_jwt_audience)

        server_url, headers = self._make_secure_request_config(token)
        response = requests.request(
            "GET", KEYCLOAK_USER_INFO.format(server_url, self.realm), headers=headers
        )
        return response.json()

    def get_user_id(self, token):
        """
        Verify if introspect token is active.
        """
        if self.enable_token_decoding:
            token_data = self._decode_token(token, self.user_jwt_audience)
        else:
            token_data = self.introspect(token)
        return token_data.get("sub", None)

    def is_token_active(self, token):
        """
        Verify if introspect token is active.
        """
        if self.enable_token_decoding:
            return bool(self._decode_token(token, audience=self.user_jwt_audience))
        introspect_token = self.introspect(token)
        return introspect_token.get("active", False)

    def client_roles(self, token):
        """
        Get client roles from token
        """
        if self.enable_token_decoding:
            token_data = self._decode_token(token, self.user_jwt_audience)
        else:
            token_data = self.introspect(token)
        client_resources = token_data.get("resource_access").get(self.client_id)
        return client_resources.get("roles", []) if client_resources else []

    def realm_roles(self, token):
        """
        Get realm roles from token
        """
        if self.enable_token_decoding:
            token_data = self._decode_token(token, self.user_jwt_audience)
        else:
            token_data = self.introspect(token)
        return token_data.get("realm_access").get("roles", None)

    def client_scope(self, token):
        """
        Get client scope from token
        """
        return self.introspect(token).get("scope").split(" ")

    def has_superuser_perm(self, token):
        """
        Check if token belongs to a user with superuser permissions
        """
        if self.client_admin_role in self.client_roles(token):
            return True
        if self.realm_admin_role in self.realm_roles(token):
            return True
        return False

    def get_user_info_by_id(self, user_id):
        """
        Get user info from the id
        """
        server_url, headers = self._make_secure_json_request_config()

        response = requests.request(
            "GET",
            KEYCLOAK_GET_USER_BY_ID.format(server_url, self.realm, user_id),
            headers=headers,
        )
        return response.json()

    def get_user_client_roles_by_id(self, user_id):
        """
        Get user client roles from the id
        """
        server_url, headers = self._make_secure_json_request_config()

        response = requests.request(
            "GET",
            KEYCLOAK_GET_USER_CLIENT_ROLES_BY_ID.format(
                server_url, self.realm, user_id, self.client_uuid
            ),
            headers=headers,
        )
        return response.json()

    @keycloak_api_error_handler
    def update_user(self, user_id, **values):
        """
        Update user with values
        """
        server_url, headers = self._make_secure_json_request_config()

        current_user = self.get_user_info_by_id(user_id)
        data = {
            **current_user,
            **values,
        }

        url = KEYCLOAK_UPDATE_USER.format(server_url, self.realm, user_id)
        res = requests.put(url, headers=headers, json=data)
        res.raise_for_status()
        return data

    @keycloak_api_error_handler
    def create_user(self, **values):
        server_url, headers = self._make_secure_json_request_config()

        url = KEYCLOAK_CREATE_USER.format(server_url, self.realm)
        res = requests.post(url, headers=headers, json=values)
        res.raise_for_status()
        return res.headers["Location"].split("/")[-1]

    @keycloak_api_error_handler
    def delete_user(self, user_id):
        server_url, headers = self._make_secure_json_request_config()

        url = KEYCLOAK_DELETE_USER.format(server_url, self.realm, user_id)
        res = requests.delete(url, headers=headers)
        res.raise_for_status()

    def _is_client_token_timed_out(self):
        """
        Checks if the cached token is timed out as given by the timeout factor

        If there is no cached token, returns true. Timeout is true if the current time is
        later than (expiration time - issue time) * timeout factor + issue time.
        """
        if not self._client_token:
            return True

        # Get the public key from the identity provider, i.e., the keycloak server
        decoded = self._decode_token(self._client_token, self.client_jwt_audience)
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)
        now = datetime.now(tz=timezone.utc)

        is_timed_out = (exp - iat) * self.token_timeout_factor + iat < now
        return is_timed_out

    def _get_openid_config(self):
        server_url, headers = self._make_json_request_config()

        response = requests.request(
            "GET",
            KEYCLOAK_OPENID_CONFIG.format(server_url, self.realm),
            headers=headers,
        )
        return response.json()

    def _make_secure_request_config(self, token):
        server_url, headers = self._make_request_config()
        if not token:
            token = self.get_token()
        headers["Authorization"] = f"Bearer {token}"
        return [server_url, headers]

    def _make_secure_json_request_config(self, token=None):
        server_url, headers = self._make_request_config()
        if not token:
            token = self.get_token()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {token}"
        return [server_url, headers]

    def _make_form_request_config(self):
        server_url, headers = self._make_request_config()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return [server_url, headers]

    def _make_json_request_config(self):
        server_url, headers = self._make_request_config()
        headers["Content-Type"] = "application/json"
        return [server_url, headers]

    def _make_request_config(self):
        server_url = self.server_url
        headers = {}
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.internal_url).netloc
        return [server_url, headers]

    @ttl_cache(maxsize=128, ttl=60)
    def _decode_token(
        self, token: str, audience: Union[str, List[str]], raise_error=False
    ) -> Optional[Dict]:
        """
        Attempts to decode the token. Returns a Dict on success or none on failure
        """
        try:
            # Get the public key from the identity provider, i.e., the keycloak server
            public_key = self.jwks_client.get_signing_key_from_jwt(token).key
            # Decode and verify the JWT with the server's public key specified in the
            # JWT's header, the required audience and the allowed crypto algorithms it
            # published
            return jwt.decode(
                token,
                public_key,
                audience=audience,
                algorithms=self.openid_config["id_token_signing_alg_values_supported"],
            )
        except InvalidTokenError as err:
            if raise_error:
                raise err
            return None
