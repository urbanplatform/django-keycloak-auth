from requests import HTTPError

from .errors import KeycloakAPIError

def keycloak_api_error_handler(f):
    """
    Decorator to wrapp all keycloak api calls
    NOTE: remember to call res.raise_for_status() after the request
    """
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except HTTPError as err:
            raise KeycloakAPIError(status=err.response.status_code, message=err.response.json())
    return wrapper
