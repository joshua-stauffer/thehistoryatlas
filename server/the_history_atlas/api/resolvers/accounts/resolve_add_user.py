from the_history_atlas.apps.domain.models.accounts.add_user import AddUserPayload


def resolve_add_user(_, info, token, user_details) -> AddUserPayload:
    ...
