from typing import Optional

from django.contrib.auth import get_user_model

from django_keycloak.config import settings
from django_keycloak.connector import lazy_keycloak_admin
from django_keycloak.models import AbstractKeycloakUser
from django_keycloak.token import Token


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

    def create_user(
        self, username: str, email: str, password: str, **kwargs
    ) -> AbstractKeycloakUser:
        self.create_user_on_keycloak(username, email, password, **kwargs)
        token = Token.from_credentials(username, password)
        return get_user_model().objects.create_from_token(token)

    def create_superuser(
        self, username: str, email: str, password: str, **kwargs
    ) -> AbstractKeycloakUser:
        return self.create_user(username, email, password, is_superuser=True, **kwargs)

    def create_user_on_keycloak(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True,
        actions: Optional[str] = None,
        is_superuser: bool = False,
        **kwargs,
    ) -> dict:
        """
        Creates user on Keycloak's server.
        No state is changed on local database.
        """
        values = {
            "username": username,
            "email": email,
            "enabled": enabled,
            "emailVerified": True,
        }
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
        if kwargs:
            values.update(kwargs)

        user_id = lazy_keycloak_admin.create_user(payload=values)
        if is_superuser:
            client_uuid = lazy_keycloak_admin.get_client_id(settings.CLIENT_ID)
            client_role = lazy_keycloak_admin.get_client_role(
                client_uuid, settings.CLIENT_ADMIN_ROLE
            )
            lazy_keycloak_admin.assign_client_role(user_id, client_uuid, client_role)

        return lazy_keycloak_admin.get_user(user_id)
