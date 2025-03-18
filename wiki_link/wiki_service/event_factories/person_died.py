import logging
from typing import Literal

from wiki_service.event_factories.event_factory import (
    register_event_factory,
    EventFactory,
    UnprocessableEventError,
    WikiEvent,
    PlaceWikiTag,
    PersonWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    PLACE_OF_DEATH,
    DATE_OF_DEATH,
)
from wiki_service.wikidata_query_service import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)

@register_event_factory
class PersonDied(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person died"

    def entity_has_event(self) -> bool:
        has_event = (
            PLACE_OF_DEATH in self._entity.claims
            and DATE_OF_DEATH in self._entity.claims
        )
        logger.info(f"PersonDied has_event: {has_event}")
        return has_event

    def create_wiki_event(self) -> WikiEvent:
        person_name = self._entity.labels["en"].value
        time_definition = self._time_definition()
        time_name = wikidata_time_to_text(time_definition)
        place_name = self._query.get_label(id=self._place_of_death_id(), language="en")
        geo_location = self._query.get_geo_location(id=self._place_of_death_id())
        if not geo_location.coordinates and not geo_location.geoshape:
            raise UnprocessableEventError("Location not found")

        summary = self._summary(
            person=person_name,
            place=place_name,
            time=time_name,
            precision=time_definition.precision,
        )

        people_tags: list[PersonWikiTag] = [
            PersonWikiTag(
                name=person_name,
                wiki_id=self._entity.id,
                start_char=summary.find(person_name),
                stop_char=summary.find(person_name) + len(person_name),
            )
        ]

        place_tag = PlaceWikiTag(
            name=place_name,
            wiki_id=self._place_of_death_id(),
            start_char=summary.find(place_name),
            stop_char=summary.find(place_name) + len(place_name),
            location=geo_location,
        )
        time_tag = TimeWikiTag(
            name=time_name,
            wiki_id=None,
            start_char=summary.find(time_name),
            stop_char=summary.find(time_name) + len(time_name),
            time_definition=time_definition,
        )
        return WikiEvent(
            summary=summary,
            people_tags=people_tags,
            place_tag=place_tag,
            time_tag=time_tag,
        )

    def _place_of_death_id(self) -> str:
        return self._entity.claims[PLACE_OF_DEATH][0]["mainsnak"]["datavalue"]["value"][
            "id"
        ]

    def _time_definition(self):
        return build_time_definition_from_claim(
            time_claim=next(
                claim
                for claim in self._entity.claims[DATE_OF_DEATH]
                if claim["mainsnak"]["property"] == DATE_OF_DEATH
            )
        )

    def _summary(
        self,
        person: str,
        place: str,
        time: str,
        precision: Literal[9, 10, 11],
    ) -> str:
        match precision:
            case 11:  # day
                return f"On {time}, {person} died in {place}."
            case 10 | 9:  # month or year
                return f"{person} died in {time} in {place}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}") 