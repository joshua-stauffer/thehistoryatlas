from typing import List
from uuid import UUID

from the_history_atlas.apps.domain.models.readmodel.tables import CitationModel

CITATIONS: List[CitationModel] = [
    CitationModel(
        id="078d478a-3ed4-4a65-b636-9aa0a3fb3ca1",
        text="In fact, for private purposes Bach had actually put down a bare outline of his professional career for a family Genealogy he was compiling around 1735: No. 24. Joh. Sebastian Bach, youngest son of Joh. Ambrosius Bach, was born in Eisenach in the year 1685 on March 21.",
        summary_id=UUID("f423a520-006c-40d3-837f-a802fe299742"),
        source_id=UUID("be42aa15-324b-4ed1-930f-456a64e9c55b"),
        page_num=3,
        access_date="2022-03-01",
    )
]
