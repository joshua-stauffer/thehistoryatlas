"""Event factory for tracking when a person moved to a location."""

from wiki_service.event_factories.event_factory import (
    EventFactory,
    UnprocessableEventError,
    register_event_factory,
)
from wiki_service.event_factories.q_numbers import (
    RESIDENCE,
    START_TIME,
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
class PersonMovedTo(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person moved to"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False

        if RESIDENCE not in self._entity.claims:
            return False

        # Check if any RESIDENCE claim has a START_TIME qualifier
        for claim in self._entity.claims[RESIDENCE]:
            if "qualifiers" in claim and START_TIME in claim["qualifiers"]:
                return True
        return False

    def _create_events(self) -> list[WikiEvent]:
        person_name = self._entity.labels["en"].value
        events = []

        for claim in self._entity.claims[RESIDENCE]:
            if "qualifiers" not in claim or START_TIME not in claim["qualifiers"]:
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
                property=START_TIME,
                time=next(
                    qualifier["datavalue"]["value"]["time"]
                    for qualifier in claim["qualifiers"][START_TIME]
                    if qualifier["property"] == START_TIME
                ),
                timezone=0,
                before=0,
                after=0,
                precision=next(
                    qualifier["datavalue"]["value"]["precision"]
                    for qualifier in claim["qualifiers"][START_TIME]
                    if qualifier["property"] == START_TIME
                ),
                calendarmodel=next(
                    qualifier["datavalue"]["value"]["calendarmodel"]
                    for qualifier in claim["qualifiers"][START_TIME]
                    if qualifier["property"] == START_TIME
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
                    entity_id=self._entity_id,
                    secondary_entity_id=residence_id,
                    context={
                        **self._create_base_context(),
                        "person_name": person_name,
                        "residence": {"id": residence_id, "name": place_name},
                        "start_date": time_definition.model_dump(),
                        "residence_claim": claim,
                    },
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
            return f"On {time}, {person} moved to {place}."
        elif precision == 10:  # Month precision
            return f"In {time}, {person} moved to {place}."
        elif precision == 9:  # Year precision
            return f"{person} moved to {place} in {time}."
        else:
            raise UnprocessableEventError(f"Unexpected time precision: {precision}")
