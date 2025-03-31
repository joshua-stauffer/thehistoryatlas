from unittest.mock import create_autospec


from tests.conftest import MockQuery
from wiki_service.event_factories.event_factory import Query
from wiki_service.event_factories.person_was_born import PersonWasBorn
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    Entity,
    GeoLocation,
)


class TestPersonWasBorn:
    BACH_ENTITY_LOOKUP = {
        "Q7070": "Eisenach",
        "Q66671": "Maria Elisabeth Lämmerhirt",
        "Q309470": "Johann Ambrosius Bach",
    }

    def test_entity_has_event_success(self, bach_entity: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonWasBorn(entity=bach_entity, query=query, entity_type="PERSON")
        assert factory.entity_has_event()

    def test_entity_has_event_failure(self, eisenach_entity: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonWasBorn(
            entity=eisenach_entity, query=query, entity_type="PERSON"
        )
        assert not factory.entity_has_event()

    def test_summary_precision_11(
        self,
        bach_entity: Entity,
        eisenach_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.BACH_ENTITY_LOOKUP,
            geo_location=eisenach_geo_location,
            expected_geo_location_id="Q7070",
        )
        factory = PersonWasBorn(
            entity=bach_entity, query=mock_query, entity_type="PERSON"
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On March 21, 1685, Johann Sebastian Bach was born to Maria Elisabeth Lämmerhirt and Johann Ambrosius Bach in Eisenach."
        )

    def test_summary_precision_10(
        self,
        bach_entity_precision_10: Entity,
        eisenach_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.BACH_ENTITY_LOOKUP,
            geo_location=eisenach_geo_location,
            expected_geo_location_id="Q7070",
        )
        factory = PersonWasBorn(
            entity=bach_entity_precision_10, query=mock_query, entity_type="PERSON"
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "Johann Sebastian Bach was born in March 1685 to Maria Elisabeth Lämmerhirt and Johann Ambrosius Bach in Eisenach."
        )

    def test_summary_precision_9(
        self,
        bach_entity_precision_9: Entity,
        eisenach_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.BACH_ENTITY_LOOKUP,
            geo_location=eisenach_geo_location,
            expected_geo_location_id="Q7070",
        )
        factory = PersonWasBorn(
            entity=bach_entity_precision_9, query=mock_query, entity_type="PERSON"
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "Johann Sebastian Bach was born in 1685 to Maria Elisabeth Lämmerhirt and Johann Ambrosius Bach in Eisenach."
        )

    def test_einstein(
        self, einstein_entity: Entity, einstein_place_of_birth: Entity, config
    ) -> None:
        query = WikiDataQueryService(config=config)
        factory = PersonWasBorn(
            entity=einstein_entity, query=query, entity_type="PERSON"
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On March 14, 1879, Albert Einstein was born to Pauline Koch and Hermann Einstein in Ulm.",
        )
