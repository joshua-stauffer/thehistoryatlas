from unittest.mock import create_autospec

from tests.conftest import MockQuery
from wiki_service.event_factories.event_factory import Query
from wiki_service.event_factories.person_died import PersonDied
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    Entity,
    GeoLocation,
)


class TestPersonDied:
    BACH_ENTITY_LOOKUP = {
        "Q2079": "Leipzig",  # Bach died in Leipzig
    }

    def test_entity_has_event_success(self, bach_entity: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonDied(entity=bach_entity, query=query)
        assert factory.entity_has_event()

    def test_entity_has_event_failure(self, eisenach_entity: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonDied(entity=eisenach_entity, query=query)
        assert not factory.entity_has_event()

    def test_summary_precision_11(
        self,
        bach_entity: Entity,
        leipzig_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.BACH_ENTITY_LOOKUP,
            geo_location=leipzig_geo_location,
            expected_geo_location_id="Q2079",
        )
        factory = PersonDied(entity=bach_entity, query=mock_query)

        wiki_event = factory.create_wiki_event()
        assert (
            wiki_event.summary
            == "On July 28, 1750, Johann Sebastian Bach died in Leipzig."
        )

    def test_summary_precision_10(
        self,
        bach_entity_death_precision_10: Entity,
        leipzig_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.BACH_ENTITY_LOOKUP,
            geo_location=leipzig_geo_location,
            expected_geo_location_id="Q2079",
        )
        factory = PersonDied(entity=bach_entity_death_precision_10, query=mock_query)
        wiki_event = factory.create_wiki_event()
        assert (
            wiki_event.summary
            == "Johann Sebastian Bach died in July 1750 in Leipzig."
        )

    def test_summary_precision_9(
        self,
        bach_entity_death_precision_9: Entity,
        leipzig_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.BACH_ENTITY_LOOKUP,
            geo_location=leipzig_geo_location,
            expected_geo_location_id="Q2079",
        )
        factory = PersonDied(entity=bach_entity_death_precision_9, query=mock_query)
        wiki_event = factory.create_wiki_event()
        assert (
            wiki_event.summary
            == "Johann Sebastian Bach died in 1750 in Leipzig."
        )

    def test_einstein(
        self, einstein_entity: Entity, einstein_place_of_death: Entity, config
    ) -> None:
        query = WikiDataQueryService(config=config)
        factory = PersonDied(entity=einstein_entity, query=query)
        wiki_event = factory.create_wiki_event()
        assert (
            wiki_event.summary
            == "On April 18, 1955, Albert Einstein died in Princeton."
        ) 