from django_keycloak.connector import KeycloakAdminConnector


class KeycloakTestMixin:
    """
    Cleans up the users created on the Keycloak server as test side-effects.

    Stores all Keycloak users at the start of a test and compares them to those at the
    end. Removes all new users.

    Usage: In the test class, derive from this mixin and call keycloak_init/teardown in
    the setUp and tearDown functions.
    """

    def keycloak_init(self):
        self._start_users = {
            user.get("id") for user in KeycloakAdminConnector.get_users()
        }

    def keycloak_cleanup(self):
        new_users = {user.get("id") for user in KeycloakAdminConnector.get_users()}
        users_to_remove = new_users.difference(self._start_users)
        for user_id in users_to_remove:
            KeycloakAdminConnector.delete_user(user_id)

    def create_user_on_keycloak(
        self,
        username,
        email,
        password=None,
        first_name=None,
        last_name=None,
        enabled=True,
        actions=None,
    ) -> dict:
        """Creates user on keycloak server, No state is changed on local db"""

        values = {"username": username, "email": email, "enabled": enabled}
        if password is not None:
            values["credentials"] = [
                {"type": "password", "value": password, "temporary": False}
            ]
        if first_name is not None:
            values["firstName"] = first_name
        if last_name is not None:
            values["lastName"] = last_name
        if actions is not None:
            values["requiredActions"] = actions

        return KeycloakAdminConnector.create_user(payload=values)
