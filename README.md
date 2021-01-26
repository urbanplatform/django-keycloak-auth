# Django Keycloak Authorization

Middleware to allow authorization using Keycloak and Django for DRF and Graphene based projects. 
This package can only be used for projects started from scratch since they override the users management.

## Installation

1. Add `django_keycloak` to the Django `INSTALLED_APPS`
3. Add `django_keycloak.middleware.KeycloakMiddleware` to the Django `MIDDLEWARE
4. Change Django `AUTHENTICATION_BACKENDS` to:

    ```json
    AUTHENTICATION_BACKENDS = (
        'django_keycloak.backends.KeycloakAuthenticationBackend',
    )
    ```
5. Add the following to Django settings:

    ```json
    KEYCLOAK_CONFIG = {
        'SERVER_URL': 'https://keycloak.staging.ubiwhere.com',
        'INTERNAL_URL': 'https://keycloak.staging.ubiwhere.com',
        'REALM': 'django',
        'CLIENT_ID': 'api',
        'CLIENT_SECRET_KEY': '0414b857-8430-4fbb-b86a-62bc398f37ea',
        'CLIENT_ADMIN_ROLE': 'admin',
        'REALM_ADMIN_ROLE': 'admin',
        'EXEMPT_URIS': [],
        'GRAPHQL_ENDPOINT': 'graphql/'
    }
    ```
6. Override the Django user model on settings:
 
     ```json
    AUTH_USER_MODEL = "django_keycloak.KeycloakUser"
    ```

7. If using graphene add the `GRAPHQL_ENDPOINT` to settings and ``KeycloakGrapheneMiddleware` to the graphene`MIDDLEWARE`
    
## Django Admin

The Django superuser that can be used for the Django Admin login, must
created with the normal management command `python manage.py
createsuperuser`. But first you must create this user on keycloak and set a
client admin role and realm admin role like the `CLIENT_ADMIN_ROLE` and
`REALM_ADMIN_ROLE` that were added on settings previously.

## Django Rest Framework

In the Django settings the the Rest Framework settings can't have any
Authorization values (used in other projects). Example:

    ```json
    # Rest framework settings
    REST_FRAMEWORK = {
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
The permissions must be set like in other projects. You must the the
permissions configuration for each model. Example:

    ```json
    @staticmethod
    @authenticated_users
    def has_read_permission(request):
        roles = request.remote_user.get('client_roles')

        return True if 'ADMIN' in roles else False
    ```

## Keycloak users synchronization

The management command `sync_keycloak_users` must be ran periodically. In
order to remove from the local users the ones that are no longer available at
keycloak. This command can be called using the task named `sync_users_with_keycloak`,
using celery. Fot that you just need to:
 
* Add the task to the `CELERY_BEAT_SCHEDULE` ìns Django settings:

  ```json
  CELERY_BEAT_SCHEDULE = {
      'sync_users_with_keycloak': {
          'task': 'django_keycloak.tasks.sync_users_with_keycloak',
          'schedule': timedelta(hours=24),
          'options': {'queue': 'sync_users'}
      },
  }
  ```

* Add the `sync_users` queue to the docker-compose celery service:

  `command: celery worker -A citibrain_base -B -E -l info -Q backup,celery,sync_users --autoscale=4,1`

**Attention:** This task is only responsible to delete users from local
storage. The creation of new users, that are on keycloak, is done when they
try to login.
