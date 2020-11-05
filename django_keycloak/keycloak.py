import requests

from django_keycloak.urls import (
    KEYCLOAK_INTROSPECT_TOKEN, KEYCLOAK_USER_INFO, KEYCLOAK_GET_USERS,
    KEYCLOAK_GET_TOKEN
)


class Connect:
    """
    Keycloak connection and methods
    """

    def __init__(self, server_url, realm, client_id,
                 client_secret_key=None):
        """
        :param server_url:
        :param realm:
        :param client_id:
        :param client_secret_key:
        """
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret_key = client_secret_key

    def introspect(self, token):
        """
        @param token: request token
        @return: introspected token
        """
        payload = {
            "token": token,
            "client_id": self.client_id,
            "grant_type": "client_credentials",
            "client_secret": self.client_secret_key
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        response = requests.request(
            "POST",
            KEYCLOAK_INTROSPECT_TOKEN.format(
                self.server_url, self.realm
            ),
            data=payload,
            headers=headers
        )
        return response.json()

    def get_token(self):
        """
        Get Token based on client credentials
        @return:
        """

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret_key
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        response = requests.request(
            "POST",
            KEYCLOAK_GET_TOKEN.format(
                self.server_url, self.realm
            ),
            data=payload,
            headers=headers
        )
        return response.json().get('access_token')

    def get_users(self, token):
        """
        Get users for realm
        @return:
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(token),
        }
        response = requests.request(
            "GET",
            KEYCLOAK_GET_USERS.format(
                self.server_url, self.realm
            ),
            headers=headers
        )
        return response.json()

    def get_user_info(self, token):
        """
        Get user information token
        """
        headers = {
            'authorization': "Bearer " + token
        }
        response = requests.request(
            "GET", KEYCLOAK_USER_INFO.format(
                self.server_url, self.realm
            ),
            headers=headers)
        return response.json()

    def get_user_id(self, token):
        """
        Verify if introspect token is active.
        """
        introspect_token = self.introspect(token)
        return introspect_token.get('sub', None)

    def is_token_active(self, token):
        """
        Verify if introspect token is active.
        """
        introspect_token = self.introspect(token)
        return True if introspect_token.get('active', None) else False

    def client_roles(self, token):
        """
        Get client roles from token
        """
        client_id = self.introspect(token).get('resource_access').get(
            self.client_id)
        return client_id.get('roles', []) if client_id else []

    def realm_roles(self, token):
        """
        Get realm roles from token
        """
        return self.introspect(token).get('realm_access').get(
            self.realm).get('roles', None)

    def client_scope(self, token):
        """
        Get client scope from token
        """
        return self.introspect(token).get('scope').split(' ')
