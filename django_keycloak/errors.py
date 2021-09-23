class KeycloakAPIError(Exception):
    """ 
    This should be raised on KeycloakAPIErrors 
    """
    def __init__(self, status, message):
        self.status = status
        self.message = message
