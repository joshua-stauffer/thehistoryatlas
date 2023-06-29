from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import (
    Citation,
    GetCitationByID,
)


def resolve_get_citation_by_id(_: None, info: Info, citationGUID: str) -> Citation:
    app = info.context.apps.readmodel_app

    citation = app.get_citation_by_id(query=GetCitationByID(citation_id=citationGUID))
    return citation
