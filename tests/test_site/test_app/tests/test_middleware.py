from unittest import skip

from django.test import TestCase
from django.urls import reverse
from django_keycloak.mixins import KeycloakTestMixin


class TestMiddleware(KeycloakTestMixin, TestCase):
    def setUp(self):
        self.keycloak_init()
        self.keycloak_user = self.create_user_on_keycloak(
            username="ownerA",
            email="user@example.com",
            password="PWowNerA0!",
            first_name="Owner",
            last_name="AAAA",
        )

    def tearDown(self):
        self.keycloak_cleanup()

    def test_simple_api_call(self):
        response = self.client.get(reverse("test_app:simple"))
        self.assertEqual(response.json()["status"], "ok")

    @skip
    def test_user_auth(self):
        self.assertTrue(False)


class TestErrorHandling(TestCase):
    def test_invalid_auth_token(self):
        header = {"HTTP_AUTHORIZATION": "Bearer DummyJWT"}
        response = self.client.get(reverse("test_app:who_am_i"), **header)
        self.assertTrue(response.json()["is_anonymous"])
