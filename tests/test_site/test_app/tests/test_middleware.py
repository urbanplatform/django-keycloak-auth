from django.test import TestCase
from django.urls import reverse
from django_keycloak.config import settings
from django_keycloak.mixins import KeycloakTestMixin
from keycloak import KeycloakOpenID


class TestMiddleware(KeycloakTestMixin, TestCase):
    def setUp(self):
        self.keycloak_init()
        self.user_password = "PWowNerA0!"
        self.keycloak_user = self.create_user_on_keycloak(
            username="ownerA",
            email="user@example.com",
            password=self.user_password,
            first_name="Owner",
            last_name="AAAA",
        )
        self.keycloak_client = KeycloakOpenID(
            server_url=settings.SERVER_URL,
            client_id=settings.CLIENT_ID,
            realm_name=settings.REALM,
            client_secret_key=settings.CLIENT_SECRET_KEY,
        )

    def tearDown(self):
        self.keycloak_cleanup()

    def test_simple_api_call(self):
        response = self.client.get(reverse("test_app:simple"))
        self.assertEqual(response.json()["status"], "ok")

    def test_user_auth(self):
        tokens = self.keycloak_client.token(
            username=self.keycloak_user["username"],
            password=self.user_password,
        )
        header = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}"}
        response = self.client.get(reverse("test_app:who_am_i"), **header)
        data = response.json()
        self.assertFalse(data.pop("isAnonymous"))
        self.assertDictContainsSubset(data, self.keycloak_user)


class TestErrorHandling(TestCase):
    def test_invalid_auth_token(self):
        header = {"HTTP_AUTHORIZATION": "Bearer DummyJWT"}
        response = self.client.get(reverse("test_app:who_am_i"), **header)
        self.assertTrue(response.json()["isAnonymous"])
