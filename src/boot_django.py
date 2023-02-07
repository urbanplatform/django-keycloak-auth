# This file sets up and configures Django. It's used by scripts that need to
# execute as if running in a Django server.

import os

import django
from django.conf import settings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "django_keycloak"))


def boot_django():
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
            }
        },
        INSTALLED_APPS=(
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django_keycloak",
        ),
        TIME_ZONE="UTC",
        USE_TZ=True,
        KEYCLOAK_CONFIG={
            "SERVER_URL": "http://localhost:8080",
            "REALM": "<REALM_NAME>",
            "CLIENT_ID": "<CLIENT_ID>",
            "CLIENT_SECRET_KEY": "<CLIENT_SECRET_KEY>",
            "CLIENT_ADMIN_ROLE": "<CLIENT_ADMIN_ROLE>",
            "REALM_ADMIN_ROLE": "<REALM_ADMIN_ROLE>",
        },
    )
    django.setup()
