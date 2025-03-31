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
)
from wiki_service.event_factories.q_numbers import (
    EMPLOYER,
    END_TIME,
    SUBJECT_HAS_ROLE,
    POSITION_HELD,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)

logger = logging.getLogger(__name__)


@register_event_factory
class PersonStoppedWorkingFor(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person stopped working for"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False
            
        if EMPLOYER not in self._entity.claims:
            return False

        # Check if any EMPLOYER claim has an END_TIME qualifier
        for claim in self._entity.claims[EMPLOYER]:
            if "qualifiers" in claim and END_TIME in claim["qualifiers"]:
                return True
        return False

    def create_wiki_event(self) -> list[WikiEvent]:
        events = []
        person_name = self._entity.labels["en"].value

        if EMPLOYER not in self._entity.claims:
            raise UnprocessableEventError("No employer claims found")

        for employer_claim in self._entity.claims[EMPLOYER]:
            if (
                "qualifiers" not in employer_claim
                or END_TIME not in employer_claim["qualifiers"]
            ):
                continue

            employer_id = employer_claim["mainsnak"]["datavalue"]["value"]["id"]
            employer_name = self._query.get_label(id=employer_id, language="en")

            # Get role or position if available
            role = None
            if "qualifiers" in employer_claim:
                if SUBJECT_HAS_ROLE in employer_claim["qualifiers"]:
                    role_id = employer_claim["qualifiers"][SUBJECT_HAS_ROLE][0][
                        "datavalue"
                    ]["value"]["id"]
                    role = self._query.get_label(id=role_id, language="en")
                elif POSITION_HELD in employer_claim["qualifiers"]:
                    position_id = employer_claim["qualifiers"][POSITION_HELD][0][
                        "datavalue"
                    ]["value"]["id"]
                    role = self._query.get_label(id=position_id, language="en")

            time_definition = build_time_definition_from_claim(
                time_claim=employer_claim["qualifiers"][END_TIME][0]
            )
            time_name = wikidata_time_to_text(time_definition)

            # Get employer location
            try:
                geo_location = self._query.get_geo_location(id=employer_id)
            except Exception as e:
                logger.warning(
                    f"Could not get location for employer {employer_id}: {e}"
                )
                continue

            if not geo_location or (
                not geo_location.coordinates and not geo_location.geoshape
            ):
                logger.warning(f"No location found for employer {employer_id}")
                continue

            summary = self._summary(
                person=person_name,
                employer=employer_name,
                role=role,
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
                name=employer_name,
                wiki_id=employer_id,
                start_char=summary.find(employer_name),
                stop_char=summary.find(employer_name) + len(employer_name),
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
            raise UnprocessableEventError("No valid employment events found")

        return events

    def _format_employer_name(self, employer: str) -> str:
        # Don't add 'the' if it already starts with it
        if employer.lower().startswith("the "):
            return employer

        # List of words that typically indicate 'the' should be added
        the_indicators = [
            "institute",
            "university",
            "college",
            "academy",
            "school",
            "museum",
            "library",
            "society",
            "organization",
            "foundation",
            "association",
            "department",
            "ministry",
            "agency",
            "orchestra",
            "theatre",
            "center",
            "laboratory",
            "hospital",
        ]

        # Check if any of the indicator words are in the employer name (case-insensitive)
        employer_words = employer.lower().split()
        if any(indicator in employer_words for indicator in the_indicators):
            return f"the {employer}"

        return employer

    def _summary(
        self,
        person: str,
        employer: str,
        role: str | None,
        time: str,
        precision: Literal[9, 10, 11],
    ) -> str:
        role_text = f" as {role}" if role else ""
        formatted_employer = self._format_employer_name(employer)

        match precision:
            case 11:  # day
                return f"On {time}, {person} stopped working for {formatted_employer}{role_text}."
            case 10 | 9:  # month or year
                return f"{person} stopped working for {formatted_employer}{role_text} in {time}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
