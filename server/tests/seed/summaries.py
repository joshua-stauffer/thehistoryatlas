from uuid import UUID

from the_history_atlas.apps.domain.models.history.tables import SummaryModel

SUMMARIES: list[SummaryModel] = [
    SummaryModel(
        id=UUID("f423a520-006c-40d3-837f-a802fe299742"),
        text="J.S. Bach was born in Eisenach on March 21st, 1685.",
        time_tag="1685|3|21",
        datetime="+1685-03-21T00:00:00Z",
        calendar_model="http://www.wikidata.org/entity/Q1985727",
        precision=9,
        latitude=10.3147,
        longitude=50.9796,
    )
]
