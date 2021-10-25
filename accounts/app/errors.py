
class MissingFieldsError(Exception):
    """Request could not be completed because of missing fields."""
    ...

class MissingUserError(Exception):
    """Request failed because user does not exist."""
    ...

class UnauthorizedUserError(Exception):
    """Request failed because the user is unauthorized to perform that action."""
    ...

class DeactivatedUserError(Exception):
    """Request failed because the user has been deactivated."""
    ...

class AuthenticationError(Exception):
    """Request failed because credentials could not be authenticated."""
    ...

class ExpiredTokenError(Exception):
    """Request failed because the token has expired. Please refresh token and try again."""
    ...

class InvalidTokenError(Exception):
    """Request failed because the token is invalid."""
    ...

class UnknownQueryError(Exception):
    """Request failed becaues the no handler was found for the requested query type."""
    ...
