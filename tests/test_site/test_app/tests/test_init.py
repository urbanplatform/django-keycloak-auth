from django.test import TestCase
from django_keycloak import Token
from django_keycloak.connector import KeycloakAdminConnector
from django_keycloak.mixins import KeycloakTestMixin


class TestInit(KeycloakTestMixin, TestCase):
    def setUp(self):
        self.keycloak_init()

    def tearDown(self):
        self.keycloak_cleanup()

    def test_model(self):
        user_a = self.create_user_on_keycloak(
            username="ownerA",
            email="user@example.com",
            password="PWowNerA0!",
            first_name="Owner",
            last_name="AAAA",
        )
        KeycloakAdminConnector.update_user(user_a["id"], {"emailVerified": True})
        valid_token = Token.from_credentials(username="ownerA", password="PWowNerA0!")
        self.assertTrue(valid_token)
