import requests

from django_keycloak.urls import (
    KEYCLOAK_INTROSPECT_TOKEN, KEYCLOAK_USER_INFO
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
            "client_secret": self.client_secret_key
        }
        headers = {
            'authorization': "Bearer " + token
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
        return self.introspect(token).get('resource_access').get(
            self.client_id).get('roles', None)

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
