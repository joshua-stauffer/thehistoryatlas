from the_history_atlas.apps.domain.models.accounts import LoginResponse


def resolve_login(_, info, username, password) -> LoginResponse:
    ...
