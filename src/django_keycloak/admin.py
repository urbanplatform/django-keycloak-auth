"""
Module to register models into Django admin dashboard.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from django_keycloak.config import settings

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "is_staff",
        "is_superuser",
    )
    fields = [
        "username",
        "keycloak_link",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
    ]
    readonly_fields = ["keycloak_link", "email", "first_name", "last_name"]

    search_fields = ["username", "email"]

    def keycloak_link(self, obj):
        """
        Adds an hyperlink to django-admin, which open the Keycloak's user profiles on Keycloak's Admin Console.
        """
        base_path = settings.BASE_PATH
        server = settings.SERVER_URL
        realm = settings.REALM

        link = f"{server}{base_path}/admin/master/console/#/{realm}/users/{obj.keycloak_identifier}/settings"

        return format_html(
            '<a href="{link}" target="_blank">{label}</a>',
            link=link,
            label=obj.keycloak_identifier,
        )

    keycloak_link.short_description = _("keycloak link")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(User, UserAdmin)
