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
    START_TIME,
    WORK_LOCATION,
    ELECTORAL_DISTRICT,
    LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
    APPLIES_TO_JURISDICTION,
    REPRESENTS,
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

    def _get_replaced_person(self, position_claim) -> tuple[str | None, str | None]:
        """Get replaced person information from the claim."""
        if "qualifiers" in position_claim and REPLACES in position_claim["qualifiers"]:
            replaced_person_id = position_claim["qualifiers"][REPLACES][0]["datavalue"][
                "value"
            ]["id"]
            replaced_person = self._query.get_label(
                id=replaced_person_id, language="en"
            )
            return replaced_person, replaced_person_id
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
        ]

        # First try to get location from claim qualifiers
        if "qualifiers" in claim:
            for prop in location_properties:
                if prop in claim["qualifiers"]:
                    location_id = claim["qualifiers"][prop][0]["datavalue"]["value"][
                        "id"
                    ]
                    try:
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
                    location_id = position_entity.claims[prop][0]["mainsnak"][
                        "datavalue"
                    ]["value"]["id"]
                    try:
                        geo_location = self._query.get_geo_location(id=location_id)
                        location_name = self._query.get_label(
                            id=location_id, language="en"
                        )
                        return location_name, location_id, geo_location
                    except Exception as e:
                        logger.warning(f"Could not get location for {location_id}: {e}")

        return None

    def _create_default_coordinate_location(self) -> CoordinateLocation:
        return CoordinateLocation(
            id="",
            rank="normal",
            type="globecoordinate",
            snaktype="value",
            property="P625",
            hash="",
            latitude=0.0,
            longitude=0.0,
            altitude=None,
            precision=None,
            globe="http://www.wikidata.org/entity/Q2",
        )

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if POSITION_HELD not in self._entity.claims:
            raise UnprocessableEventError("No position claims found")

        for position_claim in self._entity.claims[POSITION_HELD]:
            if (
                "qualifiers" not in position_claim
                or START_TIME not in position_claim["qualifiers"]
            ):
                continue

            position_id = position_claim["mainsnak"]["datavalue"]["value"]["id"]
            position_name = self._query.get_label(id=position_id, language="en")

            time_definition = build_time_definition_from_claim(
                time_claim=position_claim["qualifiers"][START_TIME][0]
            )
            time_name = wikidata_time_to_text(time_definition)

            # Get replaced person if available
            replaced_person_label, replaced_person_id = self._get_replaced_person(
                position_claim
            )

            # Get location
            location_info = self._get_location_from_claim(position_claim)
            if not location_info:
                logger.warning(f"No location found for position {position_id}")
                if replaced_person_id:
                    # If we have a replaced person but no location, we should still create the event
                    location_name = None
                    location_id = None
                    geo_location = None
                else:
                    raise UnprocessableEventError("No valid position events found")
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

            # Check if location name is part of position name
            location_in_position = (
                location_name is not None
                and location_name.lower() in position_name.lower()
            )

            summary = self._summary(
                person=person_name,
                position=position_name,
                location=None if location_in_position else location_name,
                time=time_name,
                replaced_person=replaced_person_label,
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

            if replaced_person_label and replaced_person_id:
                replaced_idx = summary.find(replaced_person_label)
                if replaced_idx != -1:
                    people_tags.append(
                        PersonWikiTag(
                            name=replaced_person_label,
                            wiki_id=replaced_person_id,
                            start_char=replaced_idx,
                            stop_char=replaced_idx + len(replaced_person_label),
                        )
                    )

            # Create place tag based on available information
            if location_id is not None:
                if not location_in_position:
                    place_tag = PlaceWikiTag(
                        name=location_name,
                        wiki_id=location_id,
                        start_char=summary.find(location_name),
                        stop_char=summary.find(location_name) + len(location_name),
                        location=geo_location
                        or GeoLocation(
                            coordinates=self._create_default_coordinate_location(),
                            geoshape=None,
                        ),
                    )
                else:
                    # If location is in position name, use position name but keep location ID
                    place_tag = PlaceWikiTag(
                        name=position_name,
                        wiki_id=location_id,
                        start_char=summary.find(position_name),
                        stop_char=summary.find(position_name) + len(position_name),
                        location=geo_location
                        or GeoLocation(
                            coordinates=self._create_default_coordinate_location(),
                            geoshape=None,
                        ),
                    )
            else:
                # If no location found, use position name as place tag
                place_tag = PlaceWikiTag(
                    name=position_name,
                    wiki_id=position_id,
                    start_char=summary.find(position_name),
                    stop_char=summary.find(position_name) + len(position_name),
                    location=GeoLocation(
                        coordinates=self._create_default_coordinate_location(),
                        geoshape=None,
                    ),
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
        location: Optional[str],
        time: str,
        replaced_person: Optional[str],
        precision: Literal[9, 10, 11],
        is_work_location: bool,
    ) -> str:
        location_text = ""
        if location:
            preposition = "at" if is_work_location else "in"
            location_text = f" {preposition} {location}"

        replaced_text = f", replacing {replaced_person}" if replaced_person else ""

        match precision:
            case 11:  # day
                return f"On {time}, {person} took the position of {position}{replaced_text}{location_text}."
            case 10 | 9:  # month or year
                return f"{person} took the position of {position}{replaced_text}{location_text} in {time}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
