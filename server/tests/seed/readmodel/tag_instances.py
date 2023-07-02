from uuid import UUID

from the_history_atlas.apps.domain.models.readmodel.tables import TagInstanceModel

TAG_INSTANCES: list[TagInstanceModel] = [
    TagInstanceModel(
        id=1,
        start_char=30,
        stop_char=34,
        summary_id=1,
        tag_id=UUID("d815d481-c8bc-4be6-a687-d9aec46a7a64"),
    ),
    TagInstanceModel(
        id=2,
        start_char=230,
        stop_char=238,
        summary_id=1,
        tag_id=UUID("1318e533-80e0-4f2b-bd08-ae7150ffee86"),
    ),
    TagInstanceModel(
        id=3,
        start_char=251,
        stop_char=267,
        summary_id=1,
        tag_id=UUID("7c4fa5a6-152d-403d-b3d1-5a586578dba4"),
    ),
]
