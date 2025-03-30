from typing import Literal

from wiki_service.event_factories.event_factory import (
    register_event_factory,
    EventFactory,
    UnprocessableEventError,
)
from wiki_service.types import TimeDefinition
from wiki_service.types import (
    WikiEvent,
    PersonWikiTag,
    PlaceWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    PLACE_OF_BIRTH,
    DATE_OF_BIRTH,
    MOTHER,
    FATHER,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
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
            PLACE_OF_BIRTH in self.entity.claims and DATE_OF_BIRTH in self.entity.claims
        )

    def create_wiki_event(self) -> list[WikiEvent]:
        person_name = self.entity.labels["en"].value
        place_of_birth_id = self._place_of_birth_id()
        time_definition = self._time_definition()

        place_of_birth_label = self.query.get_label(place_of_birth_id, language="en")
        place_of_birth_geo_location = self.query.get_geo_location(place_of_birth_id)

        if not place_of_birth_geo_location:
            raise UnprocessableEventError("No geo location found for place of birth")

        time_name = wikidata_time_to_text(time_definition)

        summary = self._summary(
            person=person_name,
            place=place_of_birth_label,
            time=time_name,
            precision=time_definition.precision,
        )

        person_start_char = summary.find(person_name)
        place_start_char = summary.find(place_of_birth_label)
        time_start_char = summary.find(time_name)

        person_tag = PersonWikiTag(
            wiki_id=self.entity.id,
            name=person_name,
            label=person_name,
            start_char=person_start_char,
            stop_char=person_start_char + len(person_name),
        )

        place_tag = PlaceWikiTag(
            wiki_id=place_of_birth_id,
            name=place_of_birth_label,
            label=place_of_birth_label,
            start_char=place_start_char,
            stop_char=place_start_char + len(place_of_birth_label),
            location=place_of_birth_geo_location,
        )

        time_tag = TimeWikiTag(
            wiki_id=None,
            name=time_name,
            start_char=time_start_char,
            stop_char=time_start_char + len(time_name),
            time_definition=time_definition,
        )

        return [
            WikiEvent(
                summary=summary,
                people_tags=[person_tag],
                place_tag=place_tag,
                time_tag=time_tag,
            )
        ]

    def _place_of_birth_id(self) -> str:
        place_of_birth_claims = self.entity.claims[PLACE_OF_BIRTH]
        if not place_of_birth_claims:
            raise UnprocessableEventError("No place of birth claims found")

        return place_of_birth_claims[0]["mainsnak"]["datavalue"]["value"]["id"]

    def _time_definition(self) -> TimeDefinition:
        date_of_birth_claims = self.entity.claims[DATE_OF_BIRTH]
        if not date_of_birth_claims:
            raise UnprocessableEventError("No date of birth claims found")

        return build_time_definition_from_claim(date_of_birth_claims[0])

    def _summary(
        self,
        person: str,
        place: str,
        time: str,
        precision: Literal[9, 10, 11],
    ) -> str:
        # Get parent information
        mother_name = None
        father_name = None

        if MOTHER in self.entity.claims:
            mother_id = self.entity.claims[MOTHER][0]["mainsnak"]["datavalue"]["value"][
                "id"
            ]
            mother_name = self.query.get_label(mother_id, language="en")

        if FATHER in self.entity.claims:
            father_id = self.entity.claims[FATHER][0]["mainsnak"]["datavalue"]["value"][
                "id"
            ]
            father_name = self.query.get_label(father_id, language="en")

        # Build parent string
        parent_str = ""
        if mother_name and father_name:
            parent_str = f" to {mother_name} and {father_name}"

        match precision:
            case 11:  # day
                return f"On {time}, {person} was born{parent_str} in {place}."
            case 10 | 9:  # month or year
                return f"{person} was born in {time}{parent_str} in {place}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
