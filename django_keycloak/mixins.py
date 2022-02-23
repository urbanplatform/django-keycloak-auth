from django_keycloak.keycloak import Connect


class KeycloakTestMixin:
    """
    Cleans up the users created on the Keycloak server as test side-effects.

    Stores all Keycloak users at the start of a test and compares them to those at the
    end. Removes all new users.

    Usage: Add the mixin before the TestCase class and call super().setUp()/tearDown() if
    adding your own setUp and tearDown functions.

    class LoginTests(KeycloakTestMixin, TestCase):
        def setUp(self):
            super().setUp()
            ...
    """

    def setUp(self):  # pylint: disable=invalid-name
        self.keycloak = Connect()
        self._start_users = {user.get("id") for user in self.keycloak.get_users()}

    def tearDown(self):  # pylint: disable=invalid-name
        new_users = {user.get("id") for user in self.keycloak.get_users()}
        users_to_remove = new_users.difference(self._start_users)
        for user_id in users_to_remove:
            self.keycloak.delete_user(user_id)
