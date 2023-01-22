from wiki_service.database import Database
from wiki_service.wiki_service import WikiService
from wiki_service.wikidata_query_service import WikiDataQueryService


def test_get_people(config):
    wiki_service = WikiService(
        wikidata_query_service_factory=lambda: WikiDataQueryService(config=config),
        database_factory=lambda: Database(config=config),
        config_factory=lambda: config,
    )
    wiki_service.search_for_people()
