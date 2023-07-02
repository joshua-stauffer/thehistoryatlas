from uuid import UUID

from the_history_atlas.apps.domain.models.readmodel.tables import TagNameAssocModel

TAG_NAME_ASSOCS: list[TagNameAssocModel] = [
    TagNameAssocModel(
        # johann sebastian bach
        tag_id=UUID("d815d481-c8bc-4be6-a687-d9aec46a7a64"),
        name_id=UUID("640fe3e0-3728-4314-9dc9-2ef22a927457"),
    ),
    TagNameAssocModel(
        # eisenach
        tag_id=UUID("1318e533-80e0-4f2b-bd08-ae7150ffee86"),
        name_id=UUID("0117b6da-f1c7-4082-9b99-e862c6361c08"),
    ),
    TagNameAssocModel(
        # the year 1685 on March 21
        tag_id=UUID("7c4fa5a6-152d-403d-b3d1-5a586578dba4"),
        name_id=UUID("b58bbd41-871d-497d-a03e-306c9438d6e9"),
    ),
]
