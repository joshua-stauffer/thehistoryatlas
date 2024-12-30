from uuid import UUID

from the_history_atlas.apps.domain.models.readmodel.tables import SummaryModel

SUMMARIES: list[SummaryModel] = [
    SummaryModel(
        id=UUID("f423a520-006c-40d3-837f-a802fe299742"),
        text="J.S. Bach was born in Eisenach on March 21st, 1685.",
        time_tag="1685|3|21",
    )
]
