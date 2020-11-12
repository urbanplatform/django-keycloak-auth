import logging as log

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from django_keycloak.keycloak import Connect


class Command(BaseCommand):
    help = 'Synchronize users with keycloak'

    def handle(self, *args, **options):
        config = settings.KEYCLOAK_CONFIG

        server_url = config.get('SERVER_URL')
        realm = config.get('REALM')
        client_id = config.get('CLIENT_ID')
        client_secret_key = config.get('CLIENT_SECRET_KEY')

        keycloak = Connect(
            server_url=server_url,
            realm=realm,
            client_id=client_id,
            client_secret_key=client_secret_key
        )

        remote_users = set([user.get('id') for user in keycloak.get_users(
            keycloak.get_token())])

        local_users = set(User.objects.filter(is_superuser=False).values_list(
            'username', flat=True))

        users_to_remove = local_users.difference(remote_users)
        users_to_add = remote_users.difference(local_users)

        # Delete users that are no longer in keycloak
        User.objects.filter(username__in=list(users_to_remove)).delete()

        # Create new users that where added to keycloak
        for user_id in users_to_add:
            User.objects.create(
                username=user_id,
                is_superuser=False,
                is_staff=False,
                is_active=True,
            )

        log.info("Created {} new users and removed {}".format(len(
            users_to_add), len(users_to_remove)))
