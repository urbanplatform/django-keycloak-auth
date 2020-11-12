from django.contrib import admin

from django_keycloak.models import CustomUser


class UserAdmin(admin.ModelAdmin):
    list_display = ('username',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(CustomUser, UserAdmin)
