from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import Citation


def resolve_get_citation_by_id(_: None, info: Info, citationGUID: str) -> Citation:
    ...
