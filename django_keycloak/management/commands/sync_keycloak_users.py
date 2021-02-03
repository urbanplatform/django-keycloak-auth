import logging as log

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from django_keycloak.keycloak import Connect


class Command(BaseCommand):
    help = 'Synchronize users with keycloak'

    def handle(self, *args, **options):
        keycloak = Connect()
        User = get_user_model()

        remote_users = set([user.get('id') for user in keycloak.get_users(
            keycloak.get_token())])
        local_users = set(str(_u.keycloak_id) for _u in User.objects.all())

        users_to_remove = local_users.difference(remote_users)
        users_to_add = remote_users.difference(local_users)

        # Delete users that are no longer in keycloak
        User.objects.filter(keycloak_id__in=list(users_to_remove)).delete()

        log.info("Removed {} users".format(len(users_to_remove)),
                 "and there are {} new users in keycloak that are not"
                 " locally".format(len(users_to_add)))
