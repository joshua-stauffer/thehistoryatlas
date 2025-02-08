from wiki_service.event_factories.person_was_born import PersonWasBorn
from wiki_service.wikidata_query_service import WikiDataQueryService, Entity


class TestPersonWasBorn:
    def test_entity_has_event_success(self, bach_entity: Entity) -> None:
        factory = PersonWasBorn(entity=bach_entity)
        assert factory.entity_has_event()

    def test_entity_has_event_failure(self, eisenach_entity: Entity) -> None:
        factory = PersonWasBorn(entity=eisenach_entity)
        assert not factory.entity_has_event()

    def test_supporting_entity_ids(
        self, bach_entity: Entity, eisenach_entity: Entity
    ) -> None:
        factory = PersonWasBorn(entity=bach_entity)
        assert factory.supporting_entity_ids() == [eisenach_entity.id]

    def test_summary_precision_11(
        self, bach_entity: Entity, eisenach_entity: Entity
    ) -> None:
        factory = PersonWasBorn(entity=bach_entity)
        wiki_event = factory.create_wiki_event(
            supporting_entities={eisenach_entity.id: eisenach_entity},
        )
        assert (
            wiki_event.summary
            == "On March 21, 1685, Johann Sebastian Bach was born in Eisenach."
        )

    def test_summary_precision_10(
        self, bach_entity_precision_10: Entity, eisenach_entity: Entity
    ) -> None:
        factory = PersonWasBorn(entity=bach_entity_precision_10)
        wiki_event = factory.create_wiki_event(
            supporting_entities={eisenach_entity.id: eisenach_entity},
        )
        assert (
            wiki_event.summary
            == "Johann Sebastian Bach was born in March 1685 in Eisenach."
        )

    def test_summary_precision_9(
        self, bach_entity_precision_9: Entity, eisenach_entity: Entity
    ) -> None:
        factory = PersonWasBorn(entity=bach_entity_precision_9)
        wiki_event = factory.create_wiki_event(
            supporting_entities={eisenach_entity.id: eisenach_entity},
        )
        assert (
            wiki_event.summary == "Johann Sebastian Bach was born in 1685 in Eisenach."
        )

    def test_einstein(
        self, einstein_entity: Entity, einstein_place_of_birth: Entity
    ) -> None:
        factory = PersonWasBorn(entity=einstein_entity)
        wiki_event = factory.create_wiki_event(
            supporting_entities={
                "Q3012": einstein_place_of_birth,
            }
        )
        assert (
            wiki_event.summary == "On March 14, 1879, Albert Einstein was born in Ulm."
        )
