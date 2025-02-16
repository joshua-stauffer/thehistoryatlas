from typing import Literal

from wiki_service.event_factories.event_factory import (
    register_event_factory,
    EventFactory,
    WikiTag,
    UnprocessableEventError,
    WikiEvent,
    PlaceWikiTag,
    PersonWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    PLACE_OF_BIRTH,
    DATE_OF_BIRTH,
    COORDINATE_LOCATION,
)
from wiki_service.wikidata_query_service import (
    build_time_definition_from_claim,
    TimeDefinition,
    Entity,
    build_coordinate_location,
    wikidata_time_to_text,
)


@register_event_factory
class PersonWasBorn(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person was born"

    def entity_has_event(self) -> bool:
        return (
            PLACE_OF_BIRTH in self._entity.claims
            and DATE_OF_BIRTH in self._entity.claims
        )

    def supporting_entity_ids(self) -> list[str]:
        # todo: handle case of more than one
        return [
            self._entity.claims[PLACE_OF_BIRTH][0]["mainsnak"]["datavalue"]["value"][
                "id"
            ]
        ]

    def create_wiki_event(self, supporting_entities: dict[str, Entity]) -> WikiEvent:
        person_name = self._entity.labels["en"].value
        time_definition = self._time_definition()
        time_name = wikidata_time_to_text(time_definition)
        place_entity = supporting_entities[self._place_of_birth_id()]
        place_name = place_entity.labels["en"].value
        coordinate_location = build_coordinate_location(
            supporting_entities[self._place_of_birth_id()].claims[COORDINATE_LOCATION][
                0
            ]
        )
        summary = self._summary(
            person=person_name,
            place=place_name,
            time=time_name,
            precision=time_definition.precision,
        )
        person_tag = PersonWikiTag(
            name=person_name,
            wiki_id=self._entity.id,
            start_char=summary.find(person_name),
            stop_char=summary.find(person_name) + len(person_name),
            entity=self._entity,
        )
        place_tag = PlaceWikiTag(
            name=place_name,
            wiki_id=place_entity.id,
            start_char=summary.find(place_name),
            stop_char=summary.find(place_name) + len(place_name),
            location=coordinate_location,
            entity=place_entity,
        )
        time_tag = TimeWikiTag(
            name=time_name,
            wiki_id=None,
            start_char=summary.find(time_name),
            stop_char=summary.find(time_name) + len(time_name),
            entity=None,
            time_definition=time_definition,
        )
        return WikiEvent(
            summary=summary,
            people_tags=[person_tag],
            place_tag=place_tag,
            time_tag=time_tag,
        )

    def _place_of_birth_id(self) -> str:
        return self._entity.claims[PLACE_OF_BIRTH][0]["mainsnak"]["datavalue"]["value"][
            "id"
        ]

    def _time_definition(self):
        return build_time_definition_from_claim(
            time_claim=next(
                claim
                for claim in self._entity.claims[DATE_OF_BIRTH]
                if claim["mainsnak"]["property"] == DATE_OF_BIRTH
            )
        )

    def _summary(
        self, person: str, place: str, time: str, precision: Literal[9, 10, 11]
    ) -> str:
        match precision:
            case 11:  # day
                return f"On {time}, {person} was born in {place}."
            case 10 | 9:  # month or year
                return f"{person} was born in {time} in {place}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
