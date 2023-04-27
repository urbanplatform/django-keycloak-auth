# Django Keycloak Authorization

Middleware to allow authorization using Keycloak and Django for django-rest-framework (DRF) and Graphene-based projects.
This package should only be used in projects starting from scratch, since it overrides the users' management.

## Installation

1. Add the module to your environment
    * With PIP:

        ```shell
        pip install django-uw-keycloak
        ```

    * By compiling from source:

        ```shell
        git clone https://github.com/urbanplatform/django-keycloak-auth && \
        cd django-keycloak-auth && \
        python3 setup.py install
        ```

2. Add `django_keycloak` to the Django project's `INSTALLED_APPS` set in the `settings` file
3. Add `django_keycloak.middleware.KeycloakMiddleware` to the Django `MIDDLEWARE` set in the `settings` file
4. In your Django project's `settings` file, change the Django `AUTHENTICATION_BACKENDS` to:

    ```python
    AUTHENTICATION_BACKENDS = ('django_keycloak.backends.KeycloakAuthenticationBackend',)
    ```

5. Add the following configuration to Django settings and replace the values with your own configuration attributes:

    ```python
    KEYCLOAK_CONFIG = {
        # Keycloak's Public Server URL (e.g. http://localhost:8080)
        'SERVER_URL': '<PUBLIC_SERVER_URL>',
        # Keycloak's Internal URL
        # (e.g. http://keycloak:8080 for a docker service named keycloak)
        # Optional: Default is SERVER_URL
        'INTERNAL_URL': '<INTERNAL_SERVER_URL>',
        # Override for default Keycloak's base path
        # Default is '/auth/'
        'BASE_PATH': '/auth/',
        # The name of the Keycloak's realm
        'REALM': '<REALM_NAME>',
        # The ID of this client in the above Keycloak realm
        'CLIENT_ID': '<CLIENT_ID>',
        # The secret for this confidential client
        'CLIENT_SECRET_KEY': '<CLIENT_SECRET_KEY>',
        # The name of the admin role for the client
        'CLIENT_ADMIN_ROLE': '<CLIENT_ADMIN_ROLE>',
        # The name of the admin role for the realm
        'REALM_ADMIN_ROLE': '<REALM_ADMIN_ROLE>',
        # Regex formatted URLs to skip authentication
        'EXEMPT_URIS': [],
        # Flag if the token should be introspected or decoded (default is False)
        'DECODE_TOKEN': False,
        # Flag if the audience in the token should be verified (default is True)
        'VERIFY_AUDIENCE': True,
        # Flag if the user info has been included in the token (default is True)
        'USER_INFO_IN_TOKEN': True,
        # Flag to show the traceback of debug logs (default is False)
        'TRACE_DEBUG_LOGS': False,
        # The token prefix that is expected in Authorization header (default is 'Bearer')
        'TOKEN_PREFIX': 'Bearer'
    }
    ```

6. Override the Django user model in the `settings` file:

     ```python
    AUTH_USER_MODEL = "django_keycloak.KeycloakUserAutoId"
    ```

7. Configure Django-Rest-Framework authentication classes with `django_keycloak.authentication.KeycloakAuthentication`:

    ```python
    REST_FRAMEWORK = {
        # ... other rest framework settings.
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'django_keycloak.authentication.KeycloakAuthentication'
        ],
    }
    ```

## Customization

### Server URLs

To customise Keycloak's URL path, set `BASE_PATH` (for example `/my_path` or `/`) as follows:

* `SERVER_URL/auth/admin/...` to `SERVER_URL/my_path/admin/...`
* `SERVER_URL/auth/realms/...` to `SERVER_URL/realms/...`

If your OAuth clients (web or mobile app) use a different URL than your Django service, specify the public URL (`https://oauth.example.com`) in `SERVER_URL` and the internal URL (`http://keycloak.local`) in `INTERNAL_URL`.

## DRY Permissions

The permissions must be set like in other projects. You must set the
permissions configuration for each model. Example:

```python
@staticmethod
@authenticated_users
def has_read_permission(request):
    roles = request.remote_user.get('client_roles')

    return True if 'ADMIN' in roles else False
```

## Keycloak users synchronization

The management command `sync_keycloak_users` must be ran periodically, in
order to remove from the users no longer available at
Keycloak from the local users. This command can be called using the task named
`sync_users_with_keycloak`, using Celery. Fot that, you just need to:

* Add the task to the `CELERY_BEAT_SCHEDULE` ìn the Django project's settings:

  ```python
  CELERY_BEAT_SCHEDULE = {
      'sync_users_with_keycloak': {
          'task': 'django_keycloak.tasks.sync_users_with_keycloak',
          'schedule': timedelta(hours=24),
          'options': {'queue': 'sync_users'}
      },
  }
  ```

* Add the `sync_users` queue to the `docker-compose`'s `celery` service:

  `command: celery worker -A citibrain_base -B -E -l info -Q backup,celery,sync_users --autoscale=4,1`

**Attention:** This task is only responsible to delete users from local
storage. The creation of new users, on Keycloak, is done when they
try to login.

## Notes

Support for celery 5: from version 0.7.4 on we should use celery 5 for the user sync. This implies running celery with `celery -A app worker ...` instead of `celery worker -A app ...`

## Development

### Making Migrations

Save the changes in the respective model and run the command below.

```py
python makemigrations.py
```

### Creating a Coverage Report

Run all tests and create a coverage report at ./tests/htmlcov/index.html

```sh
./tests/start.sh coverage
```


## Contact

django-keycloak-auth [at] googlegroups [dot] com
