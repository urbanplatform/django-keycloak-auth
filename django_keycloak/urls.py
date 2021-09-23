# REST API
KEYCLOAK_INTROSPECT_TOKEN = "{}/auth/realms/{}/protocol/openid-connect/token/introspect"
KEYCLOAK_USER_INFO = "{}/auth/realms/{}/protocol/openid-connect/userinfo"
KEYCLOAK_GET_USERS = "{}/auth/admin/realms/{}/users"
KEYCLOAK_GET_TOKEN = "{}/auth/realms/{}/protocol/openid-connect/token"
KEYCLOAK_GET_USER_BY_ID = "{}/auth/admin/realms/{}/users/{}"
KEYCLOAK_UPDATE_USER = "{}/auth/admin/realms/{}/users/{}"
KEYCLOAK_CREATE_USER = "{}/auth/admin/realms/{}/users"
KEYCLOAK_SEND_ACTIONS_EMAIL = "{}/auth/admin/realms/{}/users/{}/execute-actions-email"


# ADMIN CONSOLE
KEYCLOAK_ADMIN_USER_PAGE = (
    "{host}/auth/admin/master/console/#/realms/{realm}/users/{id}"
)
