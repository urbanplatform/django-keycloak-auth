from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_keycloak.keycloak import Connect

from .managers import KeycloakUserManager


class KeycloakUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _("username"), unique=True, max_length=20, primary_key=True
    )
    keycloak_id = models.UUIDField(_("keycloak_id"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True, blank=True)

    USERNAME_FIELD = "username"
    # REQUIRED_FIELDS = ("keycloak_id", )

    objects = KeycloakUserManager()

    def __str__(self):
        return self.username

    class Meta(AbstractBaseUser.Meta):
        swappable = 'AUTH_USER_MODEL'


class AbstractKeycloakUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_("username"), unique=True, max_length=20)
    keycloak_id = models.UUIDField(_("keycloak_id"), unique=True, primary_key=True)
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

    class Meta:
        abstract = True
        swappable = 'AUTH_USER_MODEL'

    def _confirm_cache(self):
        if not hasattr(self, "_cached_user_info"):
            keycloak = Connect()
            self._cached_user_info = keycloak.get_user_info_by_id(self.keycloak_id)
