# [WIP] Django Keycloak Authorization

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
        'SERVER_URL': '<PUBLIC_SERVER_URL>',
        'INTERNAL_URL': '<INTERNAL_SERVER_URL>', # Optional: Default is SERVER_URL
        'BASE_PATH': '', # Optional: Default matches Keycloak's default '/auth'
        'REALM': '<REALM_NAME>',
        'CLIENT_ID': '<CLIENT_ID>',
        'CLIENT_SECRET_KEY': '<CLIENT_SECRET_KEY>',
        'CLIENT_ADMIN_ROLE': '<CLIENT_ADMIN_ROLE>',
        'REALM_ADMIN_ROLE': '<REALM_ADMIN_ROLE>',
        'EXEMPT_URIS': [],  # URIS to be ignored by the package
        'GRAPHQL_ENDPOINT': 'graphql/'  # Default graphQL endpoint
        'DECODE_TOKEN': True  # Required since version 1.1.1
    }
    ```

6. Override the Django user model in the `settings` file:

     ```python
    AUTH_USER_MODEL = "django_keycloak.KeycloakUserAutoId"
    ```

7. If you are using Graphene, add the `GRAPHQL_ENDPOINT` to `KEYCLOAK_CONFIG` in settings and `KeycloakGrapheneMiddleware` to Graphene's `MIDDLEWARE`:

   ```python
    GRAPHENE = {
        "SCHEMA": "api.schema.schema",
        "MIDDLEWARE": [
            "django_keycloak.middleware.KeycloakGrapheneMiddleware",
        ],
    }
    ```

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
    
## Keycloak Integration

As soon as all services are up and running, log in to Keycloak's admin page using the administrator credentials. When inside Keycloak, go to the clients' section and create a new client. You must set the `Client ID` (in this example, we call it `backend`) and the Root URL. The Root URL can be a local instance or an already deployed one:

![image](https://user-images.githubusercontent.com/115562920/196928807-2f229d68-32ea-440e-9015-7afb9b5ba0f3.png)

In the next stage, already inside the created client, change the access type to `confidential` and save those changes:

![image](https://user-images.githubusercontent.com/115562920/196928214-52fcff74-d8da-4f4b-a5ab-e06b4e05fbd4.png)

Inside the client, Open the `Mappers` tab and add the following:

![image](https://user-images.githubusercontent.com/115562920/196929534-37e50d85-73db-4932-bc27-476712dd7fb3.png)

Only the client roles are needed for the Django Admin authorization, but the other ones can be convenient, feel free to add them.

The last step inside the client settings' configuration is to get the `SECRET_KEY` used in the Django Project configuration alongside the client ID. This secret is already created and can be updated inside the `Credentials` section. Bear in mind that every time this attribute is updated, the Django Project configuration must also be updated:

![image](https://user-images.githubusercontent.com/115562920/196930157-fd0737c6-1d55-4c59-b132-93b7b38e12ee.png)

The next step is the creation of user(s). Here, we can create not only the users that will have access to the _Django Admin_ panel but also the ones using the Django APIs. Access the `Users` section and add a new user. **Don't forget to check the email as verified**:

![image](https://user-images.githubusercontent.com/115562920/196930712-84113349-2df1-4848-ba07-b35640d9e249.png)

To set up the user credentials, you must enter the `Credentials` section and set the password. **Don't forget to remove the `Temporary` option**:

![image](https://user-images.githubusercontent.com/115562920/196930838-367ed6af-66bf-43a3-b0b8-c073c1192339.png)

Finally, if this user needs to access your Django application's admin interface, we need to add them to the client role that was previously created (`admin`) for your Django application, i.e. the client (`backend`):

![image](https://user-images.githubusercontent.com/115562920/196931388-7044f09f-a7c0-4f96-aa15-5d97ee0e2bf2.png)


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

Support for celery 5: from version 0.7.4 on we should use celery 5 for the user sync. This implies running celery with celery -A app worker ... instead of celery worker -A app ...

## Contact

django-keycloak-auth [at] googlegroups [dot] com
