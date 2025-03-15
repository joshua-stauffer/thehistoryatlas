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
    MOTHER,
    FATHER,
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

    def create_wiki_event(self) -> WikiEvent:
        person_name = self._entity.labels["en"].value
        time_definition = self._time_definition()
        time_name = wikidata_time_to_text(time_definition)
        place_name = self._query.get_label(id=self._place_of_birth_id(), language="en")
        geo_location = self._query.get_geo_location(id=self._place_of_birth_id())
        if not geo_location.coordinates and not geo_location.geoshape:
            raise UnprocessableEventError("Location not found")
        parent_tuples: list[tuple[str, str]] = [
            (id, self._query.get_label(id=id, language="en"))
            for id in [self._mother_id(), self._father_id()]
            if id is not None
        ]
        summary = self._summary(
            person=person_name,
            place=place_name,
            time=time_name,
            precision=time_definition.precision,
            parents=[label for id, label in parent_tuples],
        )
        people_tags: list[PersonWikiTag] = [
            PersonWikiTag(
                name=person_name,
                wiki_id=self._entity.id,
                start_char=summary.find(person_name),
                stop_char=summary.find(person_name) + len(person_name),
            )
        ]
        for parent_id, parent_name in parent_tuples:
            people_tags.append(
                PersonWikiTag(
                    name=parent_name,
                    wiki_id=parent_id,
                    start_char=summary.find(parent_name),
                    stop_char=summary.find(parent_name) + len(parent_name),
                )
            )

        place_tag = PlaceWikiTag(
            name=place_name,
            wiki_id=self._place_of_birth_id(),
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

    def _place_of_birth_id(self) -> str:
        return self._entity.claims[PLACE_OF_BIRTH][0]["mainsnak"]["datavalue"]["value"][
            "id"
        ]

    def _mother_id(self) -> str | None:
        mother_claim = self._entity.claims.get(MOTHER)
        if mother_claim:
            return mother_claim[0]["mainsnak"]["datavalue"]["value"]["id"]
        else:
            return None

    def _father_id(self) -> str | None:
        father_claim = self._entity.claims.get(FATHER)
        if father_claim:
            return father_claim[0]["mainsnak"]["datavalue"]["value"]["id"]
        else:
            return None

    def _parent_ids(self) -> list[str] | None:
        ...

    def _time_definition(self):
        return build_time_definition_from_claim(
            time_claim=next(
                claim
                for claim in self._entity.claims[DATE_OF_BIRTH]
                if claim["mainsnak"]["property"] == DATE_OF_BIRTH
            )
        )

    def _summary(
        self,
        person: str,
        place: str,
        time: str,
        precision: Literal[9, 10, 11],
        parents: list[str],
    ) -> str:
        match len(parents):
            case 0:
                parent_str = ""
            case 1:
                parent_str = f"to {parents[0]} "
            case 2:
                parent_str = f"to {parents[0]} and {parents[1]} "

        match precision:
            case 11:  # day
                return f"On {time}, {person} was born {parent_str}in {place}."
            case 10 | 9:  # month or year
                return f"{person} was born in {time} {parent_str}in {place}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
