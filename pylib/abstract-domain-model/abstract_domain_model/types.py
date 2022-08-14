from typing import Union
from abstract_domain_model.models import (
    TimeAdded,
    TimeTagged,
    PlaceTagged,
    PlaceAdded,
    PersonTagged,
    PersonAdded,
    CitationAdded,
    MetaAdded,
    SummaryAdded,
    SummaryTagged,
)

Model = Union[
    TimeAdded,
    TimeTagged,
    PlaceTagged,
    PlaceAdded,
    PersonTagged,
    PersonAdded,
    CitationAdded,
    MetaAdded,
    SummaryAdded,
    SummaryTagged,
]
