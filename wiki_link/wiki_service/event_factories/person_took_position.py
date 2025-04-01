"""Event factory for tracking when a person took a position."""

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
)
from wiki_service.event_factories.q_numbers import (
    POSITION_HELD,
    START_TIME,
    COORDINATE_LOCATION,
    WORK_LOCATION,
    ELECTORAL_DISTRICT,
    REPRESENTS,
    APPLIES_TO_JURISDICTION,
    REPLACES,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)


@register_event_factory
class PersonTookPosition(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person took position"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False

        if POSITION_HELD not in self._entity.claims:
            return False

        # Check if any POSITION_HELD claim has a START_TIME qualifier
        for claim in self._entity.claims[POSITION_HELD]:
            if "qualifiers" in claim and START_TIME in claim["qualifiers"]:
                return True
        return False

    def _get_location_from_entity(self, entity_id: str) -> Optional[GeoLocation]:
        """Try to find a location from an entity by checking various location properties."""
        try:
            # First check for direct coordinate location
            geo_location = self._query.get_geo_location(id=entity_id)
            if geo_location.coordinates or geo_location.geoshape:
                return geo_location

            # Get the entity to check other location properties
            entity = self._query.get_entity(id=entity_id)
            if not entity:
                return None

            # Check location properties in priority order
            location_properties = [
                WORK_LOCATION,
                ELECTORAL_DISTRICT,
                REPRESENTS,
                APPLIES_TO_JURISDICTION,
            ]

            for prop in location_properties:
                if prop in entity.claims:
                    for claim in entity.claims[prop]:
                        try:
                            location_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                            geo_location = self._query.get_geo_location(id=location_id)
                            if geo_location.coordinates or geo_location.geoshape:
                                return geo_location
                        except Exception as e:
                            logger.warning(f"Error getting location from {prop}: {e}")
                            continue

            return None
        except Exception as e:
            logger.warning(f"Error getting location for entity {entity_id}: {e}")
            return None

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if POSITION_HELD not in self._entity.claims:
            raise UnprocessableEventError("No position held claims found")

        for position_claim in self._entity.claims[POSITION_HELD]:
            if (
                "qualifiers" not in position_claim
                or START_TIME not in position_claim["qualifiers"]
            ):
                continue

            position_id = position_claim["mainsnak"]["datavalue"]["value"]["id"]
            position_name = self._query.get_label(id=position_id, language="en")

            # Get time information
            time_definition = build_time_definition_from_claim(
                time_claim=position_claim["qualifiers"][START_TIME][0]
            )
            time_name = wikidata_time_to_text(time_definition)

            # Try to get location information
            geo_location = None
            location_name = None
            location_id = None
            preposition = "in"  # Default preposition

            # First try to get location from the position entity
            geo_location = self._get_location_from_entity(position_id)
            if geo_location:
                location_id = position_id
                # Try to get location from work location first
                entity = self._query.get_entity(id=position_id)
                if entity and WORK_LOCATION in entity.claims:
                    try:
                        related_id = entity.claims[WORK_LOCATION][0]["mainsnak"][
                            "datavalue"
                        ]["value"]["id"]
                        location_name = self._query.get_label(
                            id=related_id, language="en"
                        )
                        preposition = "at"
                    except Exception as e:
                        logger.warning(f"Error getting work location: {e}")
                        location_name = position_name
                else:
                    location_name = position_name
            else:
                # Try to get location from related entities
                entity = self._query.get_entity(id=position_id)
                if entity:
                    location_properties = [
                        WORK_LOCATION,
                        ELECTORAL_DISTRICT,
                        REPRESENTS,
                        APPLIES_TO_JURISDICTION,
                    ]
                    for prop in location_properties:
                        if prop in entity.claims:
                            for claim in entity.claims[prop]:
                                try:
                                    related_id = claim["mainsnak"]["datavalue"][
                                        "value"
                                    ]["id"]
                                    geo_location = self._get_location_from_entity(
                                        related_id
                                    )
                                    if geo_location:
                                        location_id = related_id
                                        location_name = self._query.get_label(
                                            id=related_id, language="en"
                                        )
                                        # Use "at" if location came from WORK_LOCATION
                                        if prop == WORK_LOCATION:
                                            preposition = "at"
                                        break
                                except Exception as e:
                                    logger.warning(
                                        f"Error processing location from {prop}: {e}"
                                    )
                                    continue
                        if geo_location:
                            break

            if not geo_location or not location_name:
                logger.info(f"No valid location found for position {position_id}")
                continue

            # Get replaced person if available
            replaced_person = None
            replaced_person_id = None
            if (
                "qualifiers" in position_claim
                and REPLACES in position_claim["qualifiers"]
            ):
                try:
                    replaced_person_id = position_claim["qualifiers"][REPLACES][0][
                        "datavalue"
                    ]["value"]["id"]
                    replaced_person = self._query.get_label(
                        id=replaced_person_id, language="en"
                    )
                except Exception as e:
                    logger.warning(f"Error getting replaced person: {e}")

            # Create summary
            summary = self._summary(
                person=person_name,
                position=position_name,
                location=location_name,
                time=time_name,
                precision=time_definition.precision,
                replaced_person=replaced_person,
                preposition=preposition,
            )

            # Create tags
            people_tags = [
                PersonWikiTag(
                    name=person_name,
                    wiki_id=self._entity.id,
                    start_char=summary.find(person_name),
                    stop_char=summary.find(person_name) + len(person_name),
                )
            ]

            # Add replaced person tag if available
            if replaced_person and replaced_person_id:
                replaced_pos = summary.find(replaced_person)
                if replaced_pos != -1:
                    people_tags.append(
                        PersonWikiTag(
                            name=replaced_person,
                            wiki_id=replaced_person_id,
                            start_char=replaced_pos,
                            stop_char=replaced_pos + len(replaced_person),
                        )
                    )

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
            raise UnprocessableEventError("No valid position events found")

        return events

    def _summary(
        self,
        person: str,
        position: str,
        location: str,
        time: str,
        precision: Literal[9, 10, 11],
        replaced_person: str | None = None,
        preposition: str = "in",
    ) -> str:
        """Create a summary string for the event."""
        base = f"{person} took the position of {position} {preposition} {location}"
        if replaced_person:
            base += f", replacing {replaced_person}"

        match precision:
            case 11:  # day
                return f"On {time}, {base}."
            case 10 | 9:  # month or year
                return f"{base} in {time}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
