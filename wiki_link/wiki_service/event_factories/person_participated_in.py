"""Person participated in an event factory."""

import logging
from typing import Literal, Optional

from wiki_service.event_factories.event_factory import (
    EventFactory,
    UnprocessableEventError,
    register_event_factory,
)
from wiki_service.types import (
    WikiEvent,
    PersonWikiTag,
    PlaceWikiTag,
    TimeWikiTag,
    GeoLocation,
    CoordinateLocation,
    LocationResult,
)
from wiki_service.event_factories.q_numbers import (
    PARTICIPANT_IN,
    POINT_IN_TIME,
    COORDINATE_LOCATION,
    LOCATION,
    LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
    COUNTRY,
    ORGANIZER,
    START_TIME,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)


@register_event_factory
class PersonParticipatedIn(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person participated in"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False

        if PARTICIPANT_IN in self._entity.claims:
            return True
        return False

    def _get_location_from_claim(self, claim) -> LocationResult | None:
        """
        Try to get location from various properties on the claim.
        Returns tuple of (location_name, location_id, geo_location) if found, None otherwise.

        Search progressively:
        1. Within the claim qualifiers
        2. Within the event entity (object of PARTICIPANT_IN)
        3. Within the organizer entity (object of ORGANIZER from the event entity)
        """
        location_properties = [
            COORDINATE_LOCATION,
            LOCATION,
            LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
            COUNTRY,
        ]

        # PASS 1: Try to get location from claim qualifiers
        if location_result := self._query.get_location_from_claim(
            claim, location_properties
        ):
            return location_result

        # PASS 2: Try the event entity itself
        event_id = claim["mainsnak"]["datavalue"]["value"]["id"]
        event_entity = self._query.get_entity(id=event_id)

        if location_result := self._query.get_location_from_entity(
            event_entity, location_properties
        ):
            return location_result

        # PASS 3: Try the organizer entity of the event
        if ORGANIZER in event_entity.claims:
            organizer_id = event_entity.claims[ORGANIZER][0]["mainsnak"]["datavalue"][
                "value"
            ]["id"]
            organizer_entity = self._query.get_entity(id=organizer_id)
            if location_result := self._query.get_location_from_entity(
                organizer_entity, location_properties
            ):
                return location_result

        return None

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if PARTICIPANT_IN not in self._entity.claims:
            raise UnprocessableEventError("No participation claims found")

        for participation_claim in self._entity.claims[PARTICIPANT_IN]:

            event_id = participation_claim["mainsnak"]["datavalue"]["value"]["id"]
            event_name = self._query.get_label(id=event_id, language="en")

            try:
                time_definition = build_time_definition_from_claim(participation_claim)
            except Exception as e:  # todo: narrow exception
                time_definition = self._query.get_time_definition_from_claim(
                    claim=participation_claim,
                    time_props=[POINT_IN_TIME, START_TIME],
                )
            if time_definition is None:
                continue
            time_name = wikidata_time_to_text(time_definition)

            # Get location
            location = self._get_location_from_claim(participation_claim)
            if not location:
                continue

            summary = self._summary(
                person=person_name,
                event=event_name,
                location=location.name,
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
                name=location.name,
                wiki_id=location.id,
                start_char=summary.find(location.name),
                stop_char=summary.find(location.name) + len(location.name),
                location=location.geo_location,
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
                    secondary_entity_id=event_id,
                )
            )

        if not events:
            raise UnprocessableEventError("No valid participation events found")

        return events

    def _summary(
        self,
        person: str,
        event: str,
        location: str,
        time: str,
        precision: Literal[9, 10, 11],
    ) -> str:
        """Generate the summary text for the event."""
        # Check if location name is part of event name
        location_in_event = location is not None and location.lower() in event.lower()

        if not location_in_event:
            location_text = f" in {location}"
        else:
            location_text = ""

        match precision:
            case 11:  # day
                return f"On {time}, {person} participated in {event}{location_text}."
            case 10 | 9:  # month or year
                return f"In {time}, {person} participated in {event}{location_text}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
