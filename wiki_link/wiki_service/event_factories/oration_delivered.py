"""Oration delivered event factory."""

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
    LocationResult,
)
from wiki_service.event_factories.q_numbers import (
    POINT_IN_TIME,
    COORDINATE_LOCATION,
    LOCATION,
    COUNTRY,
    PRESENTED_IN,
    AUTHOR,
    SPEAKER,
    PUBLICATION_DATE,
    LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)


@register_event_factory
class OrationDelivered(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Oration delivered"

    def entity_has_event(self) -> bool:
        if self._entity_type != "ORATION":
            logger.debug("Wrong entity type: %s", self._entity_type)
            return False

        # Helper function to check if a claim has a valid value
        def has_valid_claim(claim_id: str) -> bool:
            if claim_id not in self._entity.claims:
                logger.debug("Missing claim: %s", claim_id)
                return False
            if not self._entity.claims[claim_id]:
                logger.debug("Empty claim list: %s", claim_id)
                return False
            if len(self._entity.claims[claim_id]) == 0:
                logger.debug("Zero-length claim list: %s", claim_id)
                return False
            if "mainsnak" not in self._entity.claims[claim_id][0]:
                logger.debug("Missing mainsnak in claim: %s", claim_id)
                return False
            if "datavalue" not in self._entity.claims[claim_id][0]["mainsnak"]:
                logger.debug("Missing datavalue in claim: %s", claim_id)
                return False
            if "value" not in self._entity.claims[claim_id][0]["mainsnak"]["datavalue"]:
                logger.debug("Missing value in claim: %s", claim_id)
                return False
            return True

        # Check for required properties
        has_time = has_valid_claim(POINT_IN_TIME)
        has_author = has_valid_claim(AUTHOR)
        has_speaker = has_valid_claim(SPEAKER)

        logger.debug(
            "Time: %s, Author: %s, Speaker: %s", has_time, has_author, has_speaker
        )
        return has_time and (has_author or has_speaker)

    def _get_location(self, oration_name: str) -> LocationResult | None:
        """
        Try to get location from various properties.
        First checks the oration entity itself, then checks the PRESENTED_IN entity if available.
        """
        location_properties = [
            COORDINATE_LOCATION,
            LOCATION,
            PRESENTED_IN,
            LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
            COUNTRY,
        ]

        location = self._query.get_location_from_entity(
            entity=self._entity, claim_props=location_properties
        )
        if location and location.name == oration_name:
            # the entity has a COORDINATE_LOCATION claim, so we've mistakenly picked up the
            # entity label. Look for another location label to use.
            for prop in location_properties:
                prop_claim = self._entity.claims.get(prop, [])
                if prop_claim:
                    location_id = prop_claim[0]["mainsnak"]["datavalue"]["value"].get(
                        "id"
                    )
                    if not location_id:
                        continue
                    try:
                        label = self._query.get_label(location_id, language="en")
                        location.name = label
                        break
                    except Exception as exc:
                        logger.info(f"Failed to get location from {location_id}: {exc}")
                        pass
            if location.name == oration_name:
                # unable to find label
                logger.info(
                    f"Unable to find label for {oration_name}: {self._entity.id}"
                )
                location = None
        return location

    def _get_person_info(self) -> tuple[str, str]:
        """Get the person (author/speaker) name and ID."""
        if SPEAKER in self._entity.claims:
            person_id = self._entity.claims[SPEAKER][0]["mainsnak"]["datavalue"][
                "value"
            ]["id"]
        else:
            person_id = self._entity.claims[AUTHOR][0]["mainsnak"]["datavalue"][
                "value"
            ]["id"]

        person_name = self._query.get_label(id=person_id, language="en")
        return person_name, person_id

    def _create_events(self) -> list[WikiEvent]:
        events = []
        oration_name = self._entity.labels["en"].value

        # Get time definition
        if not self.entity_has_event():
            raise UnprocessableEventError("No valid time definition found")

        time_claim = self._entity.claims[POINT_IN_TIME][0]
        time_definition = self._query.get_time_definition_from_claim(
            claim=time_claim,
            time_props=[POINT_IN_TIME, PUBLICATION_DATE],
        )
        if time_definition is None:
            raise UnprocessableEventError("No valid time definition found")

        time_name = wikidata_time_to_text(time_definition)

        # Get location
        location = self._get_location(oration_name=oration_name)
        if not location:
            raise UnprocessableEventError("No valid location found")

        # Get person info
        person_name, person_id = self._get_person_info()

        summary = self._summary(
            person=person_name,
            oration=oration_name,
            location=location.name,
            time=time_name,
            precision=time_definition.precision,
        )

        people_tags = [
            PersonWikiTag(
                name=person_name,
                wiki_id=person_id,
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
                entity_id=person_id,
                secondary_entity_id=self._entity_id,
                context={
                    **self._create_base_context(),
                    "person_name": person_name,
                    "oration": {"id": self._entity_id, "name": oration_name},
                    "location": {"id": location.id, "name": location.name},
                    "delivery_date": time_definition.model_dump(),
                    "is_speaker": SPEAKER in self._entity.claims,
                    "is_author": AUTHOR in self._entity.claims,
                },
            )
        )

        return events

    def _summary(
        self,
        person: str,
        oration: str,
        location: str,
        time: str,
        precision: Literal[9, 10, 11],
    ) -> str:
        """Generate the summary text for the event."""
        match precision:
            case 11:  # day
                return (
                    f"On {time}, {person} delivered the speech {oration} at {location}."
                )
            case 10 | 9:  # month or year
                return (
                    f"{person} delivered the speech {oration} at {location} in {time}."
                )
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
