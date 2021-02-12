from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_keycloak.keycloak import Connect

from .managers import KeycloakUserManager


class AbstractKeycloakUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(_("keycloak_id"), unique=True, primary_key=True)
    username = models.CharField(_("username"), unique=True, max_length=20)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True, blank=True)

    USERNAME_FIELD = "username"

    objects = KeycloakUserManager()

    @property
    def email(self):
        self._confirm_cache()
        return self._cached_user_info.get("email")

    @property
    def first_name(self):
        self._confirm_cache()
        return self._cached_user_info.get("firstName")

    @property
    def last_name(self):
        self._confirm_cache()
        return self._cached_user_info.get("lastName")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def _confirm_cache(self):
        if not hasattr(self, "_cached_user_info"):
            keycloak = Connect()
            self._cached_user_info = keycloak.get_user_info_by_id(self.id)

    class Meta(AbstractBaseUser.Meta):
        abstract = True

    def update_keycloak(self, email=None, first_name=None, last_name=None):
        keycloak = Connect()
        values = {}
        if email is not None:
            values["email"] = email
        if first_name is not None:
            values["firstName"] = first_name
        if last_name is not None:
            values["lastName"] = last_name
        return keycloak.update_user(self.id, **values)


class KeycloakUser(AbstractKeycloakUser):
    class Meta(AbstractKeycloakUser.Meta):
        swappable = 'AUTH_USER_MODEL'
