# Django Keycloak Authorization Internal documentation

## 0.7.4 -> 0.7.5
### Support for celery 5
from version 0.7.4 on we should use celery 5 for the user sync. This implies running celery with `celery -A app worker ...` instead of `celery worker -A app ...`
