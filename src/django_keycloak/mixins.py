import logging
from django_keycloak.keycloak import Connect


class KeycloakTestMixin:
    """
    Cleans up the users created on the Keycloak server as test side-effects.

    Stores all Keycloak users at the start of a test and compares them to those at the
    end. Removes all new users.

    Usage: In the test class, derive from this mixin and call keycloak_init/teardown in
    the setUp and tearDown functions.

    class LoginTests(KeycloakTestMixin, TestCase):
        def setUp(self):
            keycloak_init()
            ...

        def tearDown(self):
            keycloak_teardown()
            ...
    """

    def setUp(self):  # pylint: disable=invalid-name
        logging.warning("Please call keycloak_init() manually", DeprecationWarning, 2)
        self.keycloak_init()

    def tearDown(self):  # pylint: disable=invalid-name
        logging.warning(
            "Please call keycloak_cleanup() manually", DeprecationWarning, 2
        )
        self.keycloak_cleanup()

    def keycloak_init(self):
        self.keycloak = Connect()
        self._start_users = {user.get("id") for user in self.keycloak.get_users()}

    def keycloak_cleanup(self):
        new_users = {user.get("id") for user in self.keycloak.get_users()}
        users_to_remove = new_users.difference(self._start_users)
        for user_id in users_to_remove:
            self.keycloak.delete_user(user_id)
