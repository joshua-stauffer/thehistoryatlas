from typing import List
from uuid import UUID

from the_history_atlas.apps.domain.models.readmodel.tables import SourceModel

SOURCES: List[SourceModel] = [
    SourceModel(
        id=UUID("be42aa15-324b-4ed1-930f-456a64e9c55b"),
        title="Johann Sebastian Bach, The Learned Musician",
        author="Wolff, Christoph",
        publisher="W.W. Norton and Company",
        pub_date="2000",
        kwargs="{}",
    )
]
