from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from django_keycloak.urls import KEYCLOAK_ADMIN_USER_PAGE

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "keycloak_id",
        "is_staff",
        "is_superuser",
    )
    fields = [
        "username",
        "keycloak_link",
        "is_staff",
        "is_superuser",
        "is_active",
    ]
    readonly_fields = ["keycloak_link"]

    def keycloak_link(self, obj):
        config = settings.KEYCLOAK_CONFIG
        label = obj.keycloak_id
        link = KEYCLOAK_ADMIN_USER_PAGE.format(
            host=config.get("SERVER_URL"), realm=config.get("REALM"), keycloak_id=label
        )
        return format_html('<a href="{link}" target="_blank">{label}</a>', link=link, label=label)

    keycloak_link.short_description = _("keycloak link")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(User, UserAdmin)
