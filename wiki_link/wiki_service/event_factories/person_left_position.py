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
    POSITION_HELD,
    END_TIME,
    WORK_LOCATION,
    ELECTORAL_DISTRICT,
    LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
    APPLIES_TO_JURISDICTION,
    REPRESENTS,
    REPLACED_BY,
    COUNTRY,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)


@register_event_factory
class PersonLeftPosition(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person left position"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False

        if POSITION_HELD not in self._entity.claims:
            return False

        # Check if any POSITION_HELD claim has an END_TIME qualifier
        for claim in self._entity.claims[POSITION_HELD]:
            if "qualifiers" in claim and END_TIME in claim["qualifiers"]:
                return True
        return False

    def _get_replaced_by_person(self, position_claim) -> tuple[str | None, str | None]:
        """Get replaced by person information from the claim."""
        if (
            "qualifiers" in position_claim
            and REPLACED_BY in position_claim["qualifiers"]
        ):
            replaced_by_person_id = position_claim["qualifiers"][REPLACED_BY][0][
                "datavalue"
            ]["value"]["id"]
            replaced_by_person = self._query.get_label(
                id=replaced_by_person_id, language="en"
            )
            return replaced_by_person, replaced_by_person_id
        return None, None

    def _get_location_from_claim(self, claim) -> Optional[tuple[str, str, GeoLocation]]:
        """
        Try to get location from various properties on the claim.
        Returns tuple of (location_name, location_id, geo_location) if found, None otherwise.
        """
        location_properties = [
            WORK_LOCATION,
            ELECTORAL_DISTRICT,
            LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
            APPLIES_TO_JURISDICTION,
            REPRESENTS,
            COUNTRY,
        ]

        # First try to get location from claim qualifiers
        if "qualifiers" in claim:
            for prop in location_properties:
                if prop in claim["qualifiers"]:
                    try:
                        location_id = claim["qualifiers"][prop][0]["datavalue"][
                            "value"
                        ]["id"]
                        geo_location = self._query.get_geo_location(id=location_id)
                        location_name = self._query.get_label(
                            id=location_id, language="en"
                        )
                        return location_name, location_id, geo_location
                    except Exception as e:
                        logger.warning(f"Could not get location for {location_id}: {e}")

        # If no location found in qualifiers, try the position entity itself
        position_id = claim["mainsnak"]["datavalue"]["value"]["id"]
        position_entity = self._query.get_entity(id=position_id)

        if position_entity is not None and hasattr(position_entity, "claims"):
            for prop in location_properties:
                if prop in position_entity.claims:
                    try:
                        location_id = position_entity.claims[prop][0]["mainsnak"][
                            "datavalue"
                        ]["value"]["id"]
                        geo_location = self._query.get_geo_location(id=location_id)
                        location_name = self._query.get_label(
                            id=location_id, language="en"
                        )
                        return location_name, location_id, geo_location
                    except Exception as e:
                        logger.warning(f"Could not get location for {location_id}: {e}")

        return None

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if POSITION_HELD not in self._entity.claims:
            raise UnprocessableEventError("No position claims found")

        for position_claim in self._entity.claims[POSITION_HELD]:
            if (
                "qualifiers" not in position_claim
                or END_TIME not in position_claim["qualifiers"]
            ):
                continue

            position_id = position_claim["mainsnak"]["datavalue"]["value"]["id"]
            position_name = self._query.get_label(id=position_id, language="en")

            time_definition = build_time_definition_from_claim(
                time_claim=position_claim["qualifiers"][END_TIME][0]
            )
            time_name = wikidata_time_to_text(time_definition)

            # Get replaced by person if available
            replaced_by_person_label, replaced_by_person_id = (
                self._get_replaced_by_person(position_claim)
            )

            # Get location
            location_info = self._get_location_from_claim(position_claim)
            if not location_info:
                continue
            else:
                location_name, location_id, geo_location = location_info

            # Determine if location is from WORK_LOCATION
            is_work_location = (
                location_id is not None
                and "qualifiers" in position_claim
                and WORK_LOCATION in position_claim["qualifiers"]
                and position_claim["qualifiers"][WORK_LOCATION][0]["datavalue"][
                    "value"
                ]["id"]
                == location_id
            )

            summary = self._summary(
                person=person_name,
                position=position_name,
                location=location_name,
                time=time_name,
                replaced_by_person=replaced_by_person_label,
                replaced_by_person_id=replaced_by_person_id,
                precision=time_definition.precision,
                is_work_location=is_work_location,
            )

            people_tags = [
                PersonWikiTag(
                    name=person_name,
                    wiki_id=self._entity.id,
                    start_char=summary.find(person_name),
                    stop_char=summary.find(person_name) + len(person_name),
                )
            ]

            if (
                replaced_by_person_label
                and replaced_by_person_id
                and replaced_by_person_id != self._entity.id
            ):
                replaced_by_idx = summary.find(replaced_by_person_label)
                if replaced_by_idx != -1:
                    people_tags.append(
                        PersonWikiTag(
                            name=replaced_by_person_label,
                            wiki_id=replaced_by_person_id,
                            start_char=replaced_by_idx,
                            stop_char=replaced_by_idx + len(replaced_by_person_label),
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
        replaced_by_person: Optional[str],
        replaced_by_person_id: Optional[str],
        precision: Literal[9, 10, 11],
        is_work_location: bool,
    ) -> str:
        # Check if location name is part of position name
        location_in_position = (
            location is not None and location.lower() in position.lower()
        )
        if not location_in_position:
            preposition = "at" if is_work_location else "in"
            location_text = f" {preposition} {location}"
        else:
            location_text = ""

        # Only add replaced by text if the replaced by person is not the same as the primary entity
        replaced_by_text = ""
        if replaced_by_person and replaced_by_person_id != self._entity.id:
            replaced_by_text = f", being replaced by {replaced_by_person}"

        match precision:
            case 11:  # day
                return f"On {time}, {person} left the position of {position}{location_text}{replaced_by_text}."
            case 10 | 9:  # month or year
                return f"In {time}, {person} left the position of {position}{location_text}{replaced_by_text}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
