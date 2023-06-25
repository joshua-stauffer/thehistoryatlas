from ariadne import ObjectType

from the_history_atlas.api.resolvers import (
    resolve_login,
    resolve_deactivate_account,
    resolve_update_user,
    resolve_add_user,
    resolve_confirm_account,
)


def build_mutation() -> ObjectType:
    object = ObjectType("Mutation")

    object.set_field(name="ConfirmAccount", resolver=resolve_confirm_account)
    object.set_field(name="DeactivateAccount", resolver=resolve_deactivate_account)
    object.set_field(name="UpdateUser", resolver=resolve_update_user)
    object.set_field(name="AddUser", resolver=resolve_add_user)
    object.set_field(name="Login", resolver=resolve_login)
    return object
