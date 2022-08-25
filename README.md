# [WIP] Django Keycloak Authorization

Middleware to allow authorization using Keycloak and Django for django-rest-framework (DRF) and Graphene-based projects. 
This package should only be used in projects starting from scratch, since it overrides the users' management.

## Installation

1. Add `django_keycloak` to the Django project's `INSTALLED_APPS` set in the `settings` file
2. Add `django_keycloak.middleware.KeycloakMiddleware` to the Django `MIDDLEWARE` set in the `settings` file
3. In your Django project's `settings` file, change the Django `AUTHENTICATION_BACKENDS` to:

    ```python
    AUTHENTICATION_BACKENDS = ('django_keycloak.backends.KeycloakAuthenticationBackend',)
    ```
4. Add the following configuration to Django settings and replace the values with your own configuration attributes: 

    ```python
    KEYCLOAK_CONFIG = {
        'SERVER_URL': '<PUBLIC_SERVER_URL>',
        'INTERNAL_URL': <INTERNAL_SERVER_URL>'',
        'REALM': '<REALM_NAME>',
        'CLIENT_ID': '<CLIENT_ID>',
        'CLIENT_SECRET_KEY': '<CLIENT_SECRET_KEY>',
        'CLIENT_ADMIN_ROLE': '<CLIENT_ADMIN_ROLE>',
        'REALM_ADMIN_ROLE': '<REALM_ADMIN_ROLE>',
        'EXEMPT_URIS': [],  # URIS to be ignored by the package
        'GRAPHQL_ENDPOINT': 'graphql/'  # Default graphQL endpoint
    }
    ```
5. Override the Django user model in the `settings` file:
 
     ```python
    AUTH_USER_MODEL = "django_keycloak.KeycloakUserAutoId"
    ```

6. If you are using Graphene, add the `GRAPHQL_ENDPOINT` to settings and `KeycloakGrapheneMiddleware` to the Graphene's `MIDDLEWARE`.
    

8. Configure Django-Rest-Framework authentication classes with `django_keycloak.authentication.KeycloakAuthentication`:

    ```python
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'django_keycloak.authentication.KeycloakAuthentication'
        ],
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
        ],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
        'PAGE_SIZE': 100,  # Default to 20
        'PAGINATE_BY_PARAM': 'page_size',
        # Allow client to override, using `?page_size=xxx`.
        'MAX_PAGINATE_BY': 100,
        # Maximum limit allowed when using `?page_size=xxx`.
        'TEST_REQUEST_DEFAULT_FORMAT': 'json'
    }
    ```
    
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

Support for celery 5: from version 0.7.4 on we should use celery 5 for the user sync. This implies running celery with celery -A app worker ... instead of celery worker -A app ...

## Contact

django-keycloak-auth [at] googlegroups [dot] com
