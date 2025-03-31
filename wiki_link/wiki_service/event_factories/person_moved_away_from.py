"""Event factory for tracking when a person moved away from a location."""

from wiki_service.event_factories.event_factory import (
    EventFactory,
    UnprocessableEventError,
    register_event_factory,
)
from wiki_service.event_factories.q_numbers import (
    RESIDENCE,
    END_TIME,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
)
from wiki_service.event_factories.utils import wikidata_time_to_text
from wiki_service.types import (
    WikiEvent,
    PersonWikiTag,
    PlaceWikiTag,
    TimeWikiTag,
    TimeDefinition,
)


@register_event_factory
class PersonMovedAwayFrom(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person moved away from"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False
            
        if RESIDENCE not in self._entity.claims:
            return False

        # Check if any RESIDENCE claim has an END_TIME qualifier
        for claim in self._entity.claims[RESIDENCE]:
            if "qualifiers" in claim and END_TIME in claim["qualifiers"]:
                return True
        return False

    def create_wiki_event(self) -> list[WikiEvent]:
        person_name = self._entity.labels["en"].value
        events = []

        for claim in self._entity.claims[RESIDENCE]:
            if "qualifiers" not in claim or END_TIME not in claim["qualifiers"]:
                continue

            residence_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            place_name = self._query.get_label(id=residence_id, language="en")
            geo_location = self._query.get_geo_location(id=residence_id)

            if not geo_location.coordinates and not geo_location.geoshape:
                continue  # Skip if no location found

            time_definition = TimeDefinition(
                id="",
                type="statement",
                rank="normal",
                hash="",
                snaktype="value",
                property=END_TIME,
                time=next(
                    qualifier["datavalue"]["value"]["time"]
                    for qualifier in claim["qualifiers"][END_TIME]
                    if qualifier["property"] == END_TIME
                ),
                timezone=0,
                before=0,
                after=0,
                precision=next(
                    qualifier["datavalue"]["value"]["precision"]
                    for qualifier in claim["qualifiers"][END_TIME]
                    if qualifier["property"] == END_TIME
                ),
                calendarmodel=next(
                    qualifier["datavalue"]["value"]["calendarmodel"]
                    for qualifier in claim["qualifiers"][END_TIME]
                    if qualifier["property"] == END_TIME
                ),
            )
            time_name = wikidata_time_to_text(time_definition)

            summary = self._summary(
                person=person_name,
                place=place_name,
                time=time_name,
                precision=time_definition.precision,
            )

            people_tags = [
                PersonWikiTag(
                    name=person_name,
                    wiki_id=self._entity.id,
                    start_char=summary.find(person_name),
                    stop_char=summary.find(person_name) + len(person_name),
                )
            ]

            place_tag = PlaceWikiTag(
                name=place_name,
                wiki_id=residence_id,
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

            events.append(
                WikiEvent(
                    summary=summary,
                    people_tags=people_tags,
                    place_tag=place_tag,
                    time_tag=time_tag,
                )
            )

        return events

    def _summary(
        self,
        person: str,
        place: str,
        time: str,
        precision: int,
    ) -> str:
        """Generate a summary string for the event."""

        # Handle different time precisions
        if precision == 11:  # Day precision
            return f"On {time}, {person} moved away from {place}."
        elif precision == 10:  # Month precision
            return f"In {time}, {person} moved away from {place}."
        elif precision == 9:  # Year precision
            return f"{person} moved away from {place} in {time}."
        else:
            raise UnprocessableEventError(f"Unexpected time precision: {precision}")
