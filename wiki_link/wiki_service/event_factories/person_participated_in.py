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

    def _get_location_from_claim(self, claim) -> Optional[tuple[str, str, GeoLocation]]:
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
        if "qualifiers" in claim:
            for prop in location_properties:
                if prop in claim["qualifiers"]:
                    try:
                        # Special handling for coordinate location which has a different structure
                        if prop == COORDINATE_LOCATION:
                            coords = claim["qualifiers"][prop][0]["datavalue"]["value"]
                            latitude = coords["latitude"]
                            longitude = coords["longitude"]

                            # Get the event entity to use as location name
                            event_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                            location_name = self._query.get_label(
                                id=event_id, language="en"
                            )

                            geo_location = GeoLocation(
                                coordinates=CoordinateLocation(
                                    latitude=latitude,
                                    longitude=longitude,
                                ),
                                geoshape=None,
                            )
                            return location_name, event_id, geo_location
                        else:
                            location_id = claim["qualifiers"][prop][0]["datavalue"][
                                "value"
                            ]["id"]
                            geo_location = self._query.get_geo_location(id=location_id)
                            location_name = self._query.get_label(
                                id=location_id, language="en"
                            )
                            return location_name, location_id, geo_location
                    except Exception as e:
                        logger.warning(
                            f"Could not get location for qualifier {prop}: {e}"
                        )

        # PASS 2: Try the event entity itself
        event_id = claim["mainsnak"]["datavalue"]["value"]["id"]
        event_entity = self._query.get_entity(id=event_id)
        event_name = self._query.get_label(id=event_id, language="en")

        if event_entity is not None and hasattr(event_entity, "claims"):
            for prop in location_properties:
                if prop in event_entity.claims:
                    try:
                        if prop == COORDINATE_LOCATION:
                            coords = event_entity.claims[prop][0]["mainsnak"][
                                "datavalue"
                            ]["value"]
                            geo_location = GeoLocation(
                                coordinates=CoordinateLocation(**coords),
                                geoshape=None,
                            )
                            return event_name, event_id, geo_location
                        else:
                            location_id = event_entity.claims[prop][0]["mainsnak"][
                                "datavalue"
                            ]["value"]["id"]
                            geo_location = self._query.get_geo_location(id=location_id)
                            location_name = self._query.get_label(
                                id=location_id, language="en"
                            )
                            return location_name, location_id, geo_location
                    except Exception as e:
                        logger.warning(
                            f"Could not get location for event property {prop}: {e}"
                        )

            # PASS 3: Try the organizer entity of the event
            if ORGANIZER in event_entity.claims:
                try:
                    organizer_id = event_entity.claims[ORGANIZER][0]["mainsnak"][
                        "datavalue"
                    ]["value"]["id"]
                    organizer_entity = self._query.get_entity(id=organizer_id)
                    organizer_name = self._query.get_label(
                        id=organizer_id, language="en"
                    )

                    if organizer_entity is not None and hasattr(
                        organizer_entity, "claims"
                    ):
                        for prop in location_properties:
                            if prop in organizer_entity.claims:
                                try:
                                    if prop == COORDINATE_LOCATION:
                                        coords = organizer_entity.claims[prop][0][
                                            "mainsnak"
                                        ]["datavalue"]["value"]
                                        latitude = coords["latitude"]
                                        longitude = coords["longitude"]
                                        geo_location = GeoLocation(
                                            coordinates=CoordinateLocation(
                                                latitude=latitude,
                                                longitude=longitude,
                                            ),
                                            geoshape=None,
                                        )
                                        return (
                                            organizer_name,
                                            organizer_id,
                                            geo_location,
                                        )
                                    else:
                                        location_id = organizer_entity.claims[prop][0][
                                            "mainsnak"
                                        ]["datavalue"]["value"]["id"]
                                        geo_location = self._query.get_geo_location(
                                            id=location_id
                                        )
                                        location_name = self._query.get_label(
                                            id=location_id, language="en"
                                        )
                                        return (
                                            location_name,
                                            location_id,
                                            geo_location,
                                        )
                                except Exception as e:
                                    logger.warning(
                                        f"Could not get location for organizer property {prop}: {e}"
                                    )
                except Exception as e:
                    logger.warning(f"Could not get organizer entity: {e}")

        return None

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if PARTICIPANT_IN not in self._entity.claims:
            raise UnprocessableEventError("No participation claims found")

        for participation_claim in self._entity.claims[PARTICIPANT_IN]:

            event_id = participation_claim["mainsnak"]["datavalue"]["value"]["id"]
            event_name = self._query.get_label(id=event_id, language="en")

            time_definition = self._query.get_hierarchical_time(
                entity=self._entity,
                claim=PARTICIPANT_IN,
                time_props=[POINT_IN_TIME, START_TIME],
            )
            if time_definition is None:
                continue
            time_name = wikidata_time_to_text(time_definition)

            # Get location
            location_info = self._get_location_from_claim(participation_claim)
            if not location_info:
                continue
            else:
                location_name, location_id, geo_location = location_info

            summary = self._summary(
                person=person_name,
                event=event_name,
                location=location_name,
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
                name=location_name,
                wiki_id=location_id,
                start_char=summary.find(location_name),
                stop_char=summary.find(location_name) + len(location_name),
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
