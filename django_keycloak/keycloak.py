from urllib.parse import urlparse

import requests
from django.conf import settings

from django_keycloak.urls import (KEYCLOAK_GET_TOKEN, KEYCLOAK_GET_USER_BY_ID,
                                  KEYCLOAK_GET_USERS,
                                  KEYCLOAK_INTROSPECT_TOKEN,
                                  KEYCLOAK_USER_INFO)


class Connect:
    """
    Keycloak connection and methods
    """

    def __init__(
        self,
        server_url=None,
        realm=None,
        client_id=None,
        client_secret_key=None,
        internal_url=None,
    ):
        # Load configuration from settings + args
        self.config = settings.KEYCLOAK_CONFIG
        try:
            self.server_url = server_url or self.config.get("SERVER_URL")
            self.realm = realm or self.config.get("REALM")
            self.client_id = client_id or self.config.get("CLIENT_ID")
            self.client_secret_key = client_secret_key or self.config.get(
                "CLIENT_SECRET_KEY"
            )
            self.internal_url = internal_url or self.config.get("INTERNAL_URL")
            self.client_admin_role = self.config.get("CLIENT_ADMIN_ROLE", "admin")
            self.realm_admin_role = self.config.get("REALM_ADMIN_ROLE", "admin")
            self.graphql_endpoint = self.config.get("GRAPHQL_ENDPOINT", None)
            self.exempt_uris = self.config.get("EXEMPT_URIS", [])

        except KeyError:
            raise Exception("KEYCLOAK configuration is not defined.")

        if not self.server_url:
            raise Exception("SERVER_URL is not defined.")

        if not self.realm:
            raise Exception("REALM is not defined.")

        if not self.client_id:
            raise Exception("CLIENT_ID is not defined.")

        if not self.client_secret_key:
            raise Exception("CLIENT_SECRET_KEY is not defined.")

    def introspect(self, token):
        """
        @param token: request token
        @return: introspected token
        """
        if hasattr(self, "cached_introspect"):
            return self.cached_introspect

        payload = {
            "token": token,
            "client_id": self.client_id,
            "grant_type": "client_credentials",
            "client_secret": self.client_secret_key,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        server_url = self.server_url
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.server_url).netloc

        response = requests.request(
            "POST",
            KEYCLOAK_INTROSPECT_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
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
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        server_url = self.server_url
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.server_url).netloc

        response = requests.request(
            "POST",
            KEYCLOAK_GET_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
        return response.json().get("access_token")

    def get_token(self):
        """
        Get Token based on client credentials
        @return:
        """

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        server_url = self.server_url
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.server_url).netloc

        response = requests.request(
            "POST",
            KEYCLOAK_GET_TOKEN.format(server_url, self.realm),
            data=payload,
            headers=headers,
        )
        return response.json().get("access_token")

    def get_users(self, token):
        """
        Get users for realm
        @return:
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }
        server_url = self.server_url
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.server_url).netloc

        response = requests.request(
            "GET", KEYCLOAK_GET_USERS.format(server_url, self.realm), headers=headers
        )
        return response.json()

    def get_user_info(self, token):
        """
        Get user information token
        """
        headers = {"authorization": "Bearer " + token}
        server_url = self.server_url
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.server_url).netloc

        response = requests.request(
            "GET", KEYCLOAK_USER_INFO.format(server_url, self.realm), headers=headers
        )
        return response.json()

    def get_user_id(self, token):
        """
        Verify if introspect token is active.
        """
        introspect_token = self.introspect(token)
        return introspect_token.get("sub", None)

    def is_token_active(self, token):
        """
        Verify if introspect token is active.
        """
        introspect_token = self.introspect(token)
        return introspect_token.get("active", False)

    def client_roles(self, token):
        """
        Get client roles from token
        """
        client_id = self.introspect(token).get("resource_access").get(self.client_id)
        return client_id.get("roles", []) if client_id else []

    def realm_roles(self, token):
        """
        Get realm roles from token
        """
        return self.introspect(token).get("realm_access").get("roles", None)

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

        token = self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }

        server_url = self.server_url
        if self.internal_url:
            server_url = self.internal_url
            headers["HOST"] = urlparse(self.server_url).netloc

        response = requests.request(
            "GET",
            KEYCLOAK_GET_USER_BY_ID.format(server_url, self.realm, user_id),
            headers=headers,
        )

        return response.json()
