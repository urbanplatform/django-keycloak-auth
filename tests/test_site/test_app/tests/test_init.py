from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django_keycloak.mixins import KeycloakTestMixin
from django_keycloak.models import KeycloakUser


class TestInit(KeycloakTestMixin, TestCase):
    def setUp(self):
        # import ipdb; ipdb.set_trace()
        self.keycloak_init()

    def tearDown(self):
        self.keycloak_cleanup()

    def test_pass(self):
        self.assertTrue(True)

    def test_model(self):
        user_a = get_user_model().objects.create_keycloak_user(
            username="ownerA",
            email="user@example.com",
            password="PWowNerA0!",
            first_name="Owner",
            last_name="AAAA",
        )
        self.keycloak.update_user(user_a.id, emailVerified=True)
        valid_token = self.keycloak.get_token_from_credentials(
            username="ownerA", password="PWowNerA0!"
        )
