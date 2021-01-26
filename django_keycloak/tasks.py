from celery import task
from django.core.management import call_command


@task(queue='sync_users')
def sync_users_with_keycloak():
    """
    Users synchronization task
    """
    call_command('sync_keycloak_users')
