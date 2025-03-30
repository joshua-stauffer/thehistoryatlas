import logging
from typing import Literal

from wiki_service.event_factories.event_factory import (
    register_event_factory,
    EventFactory,
    UnprocessableEventError,
    WikiEvent,
    PlaceWikiTag,
    PersonWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    EDUCATED_AT,
    END_TIME,
    ACADEMIC_DEGREE,
    DOCTORAL_ADVISOR,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
)
from wiki_service.wikidata_query_service import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)
from wiki_service.wikidata_query_service import TimeDefinition

logger = logging.getLogger(__name__)


@register_event_factory
class PersonEducationEnded(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person education ended"

    def entity_has_event(self) -> bool:
        if EDUCATED_AT not in self._entity.claims:
            return False

        # Check if any EDUCATED_AT claim has an END_TIME qualifier
        for claim in self._entity.claims[EDUCATED_AT]:
            if "qualifiers" in claim and END_TIME in claim["qualifiers"]:
                return True
        return False

    def create_wiki_event(self) -> list[WikiEvent]:
        person_name = self._entity.labels["en"].value
        events = []

        for claim in self._entity.claims[EDUCATED_AT]:
            if "qualifiers" not in claim or END_TIME not in claim["qualifiers"]:
                continue

            institution_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            place_name = self._query.get_label(id=institution_id, language="en")
            geo_location = self._query.get_geo_location(id=institution_id)

            if not geo_location.coordinates and not geo_location.geoshape:
                logger.info(
                    f"No geo location found for Education Ended at institute {institution_id}"
                )
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

            # Check for academic degrees
            academic_degrees = []
            if "qualifiers" in claim and ACADEMIC_DEGREE in claim["qualifiers"]:
                for degree_qualifier in claim["qualifiers"][ACADEMIC_DEGREE]:
                    degree_id = degree_qualifier["datavalue"]["value"]["id"]
                    degree_name = self._query.get_label(id=degree_id, language="en")
                    academic_degrees.append(degree_name)

            # Check for doctoral advisor
            advisor_tags = []
            if "qualifiers" in claim and DOCTORAL_ADVISOR in claim["qualifiers"]:
                for advisor_qualifier in claim["qualifiers"][DOCTORAL_ADVISOR]:
                    advisor_id = advisor_qualifier["datavalue"]["value"]["id"]
                    advisor_name = self._query.get_label(id=advisor_id, language="en")
                    advisor_tags.append(
                        PersonWikiTag(
                            name=advisor_name,
                            wiki_id=advisor_id,
                            start_char=None,  # Will be set after summary is created
                            stop_char=None,  # Will be set after summary is created
                        )
                    )

            academic_degree_name = None
            if academic_degrees:
                if len(academic_degrees) == 1:
                    academic_degree_name = academic_degrees[0]
                else:
                    # Join all but the last degree with commas, then add "and" before the last one
                    academic_degree_name = (
                        ", ".join(academic_degrees[:-1])
                        + " and "
                        + academic_degrees[-1]
                    )

            summary = self._summary(
                person=person_name,
                place=place_name,
                time=time_name,
                precision=time_definition.precision,
                academic_degree=academic_degree_name,
                advisor_name=advisor_tags[0].name if advisor_tags else None,
            )

            people_tags = [
                PersonWikiTag(
                    name=person_name,
                    wiki_id=self._entity.id,
                    start_char=summary.find(person_name),
                    stop_char=summary.find(person_name) + len(person_name),
                )
            ]

            # Update advisor tag positions if present
            if advisor_tags:
                advisor_name = advisor_tags[0].name
                advisor_pos = summary.find(advisor_name)
                advisor_tags[0].start_char = advisor_pos
                advisor_tags[0].stop_char = advisor_pos + len(advisor_name)
                people_tags.extend(advisor_tags)

            place_tag = PlaceWikiTag(
                name=place_name,
                wiki_id=institution_id,
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
        precision: Literal[9, 10, 11],
        academic_degree: str | None = None,
        advisor_name: str | None = None,
    ) -> str:
        # Determine pronoun based on gender
        pronoun = "their"
        if SEX_OR_GENDER in self._entity.claims:
            gender_id = self._entity.claims[SEX_OR_GENDER][0]["mainsnak"]["datavalue"][
                "value"
            ]["id"]
            if gender_id == MALE:
                pronoun = "his"
            elif gender_id == FEMALE:
                pronoun = "her"

        # Build the summary based on available information
        if academic_degree:
            base = f"{person} graduated from {place} with a degree of {academic_degree}"
        else:
            base = f"{person} ended {pronoun} studies at {place}"

        # Add advisor information if present
        if advisor_name:
            base += f", under the supervision of {advisor_name}"

        # Add time information based on precision
        match precision:
            case 11:  # day
                return f"On {time}, {base}."
            case 10 | 9:  # month or year
                return f"{base} in {time}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
