"""
Expected exceptions for the Accounts Service. Should return a meaningful string 
representation, which will be returned to the requesting service. All exceptions
should be included in the **known_exceptions** list.
"""


class MissingFieldsError(Exception):
    def __str__(self):
        return """Request could not be completed because of missing fields."""


class MissingUserError(Exception):
    def __str__(self):
        return """Request failed because user does not exist."""


class UnauthorizedUserError(Exception):
    def __str__(self):
        return """Request failed because the user is unauthorized to perform that action."""


class DeactivatedUserError(Exception):
    def __str__(self):
        return """Request failed because the user has been deactivated."""


class AuthenticationError(Exception):
    def __str__(self):
        return """Request failed because credentials could not be authenticated."""


class ExpiredTokenError(Exception):
    def __str__(self) -> str:
        return """Request failed because the token has expired. Please refresh token and try again."""


class InvalidTokenError(Exception):
    def __str__(self) -> str:
        return """Request failed because the token is invalid."""


class UnknownQueryError(Exception):
    def __str__(self) -> str:
        return """Request failed because the query type was unknown."""


class UnconfirmedUserError(Exception):
    def __str__(self) -> str:
        return """Request failed because this user hasn't confirmed their email yet."""


class DuplicateUsernameError(Exception):
    def __str__(self) -> str:
        return """Request failed because this username is already registered"""


known_exceptions = (
    MissingFieldsError,
    MissingUserError,
    UnauthorizedUserError,
    DeactivatedUserError,
    AuthenticationError,
    ExpiredTokenError,
    InvalidTokenError,
    UnknownQueryError,
    UnconfirmedUserError,
    DuplicateUsernameError,
)
