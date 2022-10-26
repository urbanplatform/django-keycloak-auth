from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django_keycloak.mixins import KeycloakTestMixin


class TestMiddleware(KeycloakTestMixin, TestCase):
    def setUp(self):
        self.keycloak_init()
        self.user_a = self.create_user_on_keycloak(
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

    def test_user_auth(self):
        pass
