from uuid import UUID

from the_history_atlas.apps.domain.models.readmodel.tables import TagInstanceModel

TAG_INSTANCES: list[TagInstanceModel] = [
    TagInstanceModel(
        id=UUID("8152e78b-ddcd-4ad9-8317-01bf7dd37516"),
        start_char=30,
        stop_char=34,
        summary_id=UUID("f423a520-006c-40d3-837f-a802fe299742"),
        tag_id=UUID("d815d481-c8bc-4be6-a687-d9aec46a7a64"),
        story_order=0,
    ),
    TagInstanceModel(
        id=UUID("d3b2de72-8ddc-4cde-a56e-6ad15350d077"),
        start_char=230,
        stop_char=238,
        summary_id=UUID("f423a520-006c-40d3-837f-a802fe299742"),
        tag_id=UUID("1318e533-80e0-4f2b-bd08-ae7150ffee86"),
        story_order=0,
    ),
    TagInstanceModel(
        id=UUID("035fb2b4-2c6d-41f2-83b3-6f7e92d2b879"),
        start_char=251,
        stop_char=267,
        summary_id=UUID("f423a520-006c-40d3-837f-a802fe299742"),
        tag_id=UUID("7c4fa5a6-152d-403d-b3d1-5a586578dba4"),
        story_order=0,
    ),
]
