"""Person nominated for award event factory."""

import logging
from typing import Literal

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
    NOMINATED_FOR,
    POINT_IN_TIME,
    COORDINATE_LOCATION,
    LOCATION,
    LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
    COUNTRY,
    HEADQUARTERS_LOCATION,
    START_TIME,
    CONFERRED_BY,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)


@register_event_factory
class PersonNominatedFor(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person nominated for award"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False

        if NOMINATED_FOR in self._entity.claims:
            return True
        return False

    def _get_location_from_claim(self, claim) -> LocationResult | None:
        """
        Try to get location from various properties on the claim.
        Returns tuple of (location_name, location_id, geo_location) if found, None otherwise.

        Search progressively:
        1. Within the claim qualifiers
        2. Within the award entity
        3. Within the conferred_by entity from claim
        4. Within the conferred_by entity from award
        5. Within the award entity's administrative/country properties
        """
        location_properties = [
            COORDINATE_LOCATION,
            LOCATION,
            LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
            COUNTRY,
        ]
        award_location_properties = [
            COORDINATE_LOCATION,
            LOCATION,
            HEADQUARTERS_LOCATION,
            COUNTRY,
        ]

        # PASS 1: Try to get location from claim qualifiers
        if location_result := self._query.get_location_from_claim(
            claim, location_properties
        ):
            return location_result

        # PASS 2: Try the award entity itself with headquarters properties
        award_id = claim["mainsnak"]["datavalue"]["value"]["id"]
        award_entity = self._query.get_entity(id=award_id)

        if location_result := self._query.get_location_from_entity(
            award_entity, award_location_properties
        ):
            return location_result

        # PASS 3: Try the conferred_by entity from claim
        if CONFERRED_BY in claim["qualifiers"]:
            conferrer_id = claim["qualifiers"][CONFERRED_BY][0]["datavalue"]["value"][
                "id"
            ]
            conferrer_entity = self._query.get_entity(id=conferrer_id)
            if location_result := self._query.get_location_from_entity(
                conferrer_entity, award_location_properties
            ):
                return location_result

        # PASS 4: Try the conferred_by entity from award
        if CONFERRED_BY in award_entity.claims:
            award_conferrer_id = award_entity.claims[CONFERRED_BY][0]["mainsnak"][
                "datavalue"
            ]["value"]["id"]
            award_conferrer_entity = self._query.get_entity(id=award_conferrer_id)
            if location_result := self._query.get_location_from_entity(
                award_conferrer_entity, award_location_properties
            ):
                return location_result

        # PASS 5: Try administrative/country properties on award entity
        admin_properties = [
            LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY,
            COUNTRY,
        ]
        if location_result := self._query.get_location_from_entity(
            award_entity, admin_properties
        ):
            return location_result

        return None

    def _get_conferrer_name(self, claim, award_entity) -> str | None:
        """Get the name of the conferring organization, if available."""
        # Try claim qualifiers first
        if CONFERRED_BY in claim.get("qualifiers", {}):
            conferrer_id = claim["qualifiers"][CONFERRED_BY][0]["datavalue"]["value"][
                "id"
            ]
            return self._query.get_label(id=conferrer_id, language="en")

        # Try award entity claims
        if CONFERRED_BY in award_entity.claims:
            conferrer_id = award_entity.claims[CONFERRED_BY][0]["mainsnak"][
                "datavalue"
            ]["value"]["id"]
            return self._query.get_label(id=conferrer_id, language="en")

        return None

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if NOMINATED_FOR not in self._entity.claims:
            raise UnprocessableEventError("No nomination claims found")

        for nomination_claim in self._entity.claims[NOMINATED_FOR]:
            award_id = nomination_claim["mainsnak"]["datavalue"]["value"]["id"]
            award_name = self._query.get_label(id=award_id, language="en")
            award_entity = self._query.get_entity(id=award_id)

            try:
                time_definition = build_time_definition_from_claim(nomination_claim)
            except Exception:  # todo: narrow exception
                time_definition = self._query.get_time_definition_from_claim(
                    claim=nomination_claim,
                    time_props=[POINT_IN_TIME, START_TIME],
                )
            if time_definition is None:
                continue

            time_name = wikidata_time_to_text(time_definition)

            # Get location
            location = self._get_location_from_claim(nomination_claim)
            if not location:
                continue

            # Get optional attributes
            conferrer_name = self._get_conferrer_name(nomination_claim, award_entity)
            include_conferrer = (
                conferrer_name
                and location.name
                and conferrer_name.lower() not in location.name.lower()
            )

            summary = self._summary(
                person=person_name,
                award=award_name,
                location=location.name,
                time=time_name,
                precision=time_definition.precision,
                conferrer=conferrer_name if include_conferrer else None,
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
                    secondary_entity_id=award_id,
                    context={
                        **self._create_base_context(),
                        "person_name": person_name,
                        "award": {"id": award_id, "name": award_name},
                        "location": {"id": location.id, "name": location.name},
                        "nomination_date": time_definition.model_dump(),
                        "nomination_claim": nomination_claim,
                        "conferrer": (
                            {"name": conferrer_name} if include_conferrer else None
                        ),
                    },
                )
            )

        if not events:
            raise UnprocessableEventError("No valid nomination events found")

        return events

    def _summary(
        self,
        person: str,
        award: str,
        location: str,
        time: str,
        precision: Literal[9, 10, 11],
        conferrer: str | None = None,
    ) -> str:
        """Generate the summary text for the event."""
        # Build the award phrase with optional conferrer
        award_phrase = f"was nominated for the {award}"

        if conferrer:
            award_phrase += f" by {conferrer}"

        # Build the location phrase
        if location.lower() not in award_phrase.lower():
            location_text = f" in {location}"
        else:
            location_text = ""

        match precision:
            case 11:  # day
                return f"On {time}, {person} {award_phrase}{location_text}."
            case 10 | 9:  # month or year
                return f"{person} {award_phrase}{location_text} in {time}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
