from celery import Celery
from django.core.management import call_command


app = Celery()
@app.task(queue='sync_users')
def sync_users_with_keycloak():
    """
    Users synchronization task
    """
    call_command('sync_keycloak_users')
