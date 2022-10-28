from typing import Optional

from django_keycloak.connector import lazy_keycloak_admin


class KeycloakTestMixin:
    """
    Cleans up the users created on the Keycloak server as test side-effects.

    Stores all Keycloak users at the start of a test and compares them to those at the
    end. Removes all new users.

    Usage: In the test class, derive from this mixin and call keycloak_init/teardown in
    the setUp and tearDown functions.
    """

    def keycloak_init(self):
        self._start_users = {user.get("id") for user in lazy_keycloak_admin.get_users()}

    def keycloak_cleanup(self):
        new_users = {user.get("id") for user in lazy_keycloak_admin.get_users()}
        users_to_remove = new_users.difference(self._start_users)
        for user_id in users_to_remove:
            lazy_keycloak_admin.delete_user(user_id)

    def create_user_on_keycloak(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True,
        actions: Optional[str] = None,
    ) -> dict:
        """
        Creates user on Keycloak's server.
        No state is changed on local database.
        """
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

        user_id = lazy_keycloak_admin.create_user(payload=values)
        return lazy_keycloak_admin.get_user(user_id)
