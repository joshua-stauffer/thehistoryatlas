from typing import Literal

from wiki_service.event_factories.event_factory import (
    EventFactory,
    UnprocessableEventError,
    register_event_factory,
)
from wiki_service.types import TimeDefinition
from wiki_service.types import (
    WikiEvent,
    PersonWikiTag,
    PlaceWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    EDUCATED_AT,
    START_TIME,
    ACADEMIC_MAJOR,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
)
from wiki_service.event_factories.utils import (
    wikidata_time_to_text,
)


@register_event_factory
class PersonEducationBegan(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person education began"

    def entity_has_event(self) -> bool:
        if EDUCATED_AT not in self._entity.claims:
            return False

        # Check if any EDUCATED_AT claim has a START_TIME qualifier
        for claim in self._entity.claims[EDUCATED_AT]:
            if "qualifiers" in claim and START_TIME in claim["qualifiers"]:
                return True
        return False

    def create_wiki_event(self) -> list[WikiEvent]:
        person_name = self._entity.labels["en"].value
        events = []

        for claim in self._entity.claims[EDUCATED_AT]:
            if "qualifiers" not in claim or START_TIME not in claim["qualifiers"]:
                continue

            institution_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            place_name = self._query.get_label(id=institution_id, language="en")
            geo_location = self._query.get_geo_location(id=institution_id)

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

            # Check for academic majors
            academic_majors = []
            if "qualifiers" in claim and ACADEMIC_MAJOR in claim["qualifiers"]:
                for major_qualifier in claim["qualifiers"][ACADEMIC_MAJOR]:
                    major_id = major_qualifier["datavalue"]["value"]["id"]
                    major_name = self._query.get_label(id=major_id, language="en")
                    academic_majors.append(major_name)

            academic_major_name = None
            if academic_majors:
                if len(academic_majors) == 1:
                    academic_major_name = academic_majors[0]
                else:
                    # Join all but the last major with commas, then add "and" before the last one
                    academic_major_name = (
                        ", ".join(academic_majors[:-1]) + " and " + academic_majors[-1]
                    )

            summary = self._summary(
                person=person_name,
                place=place_name,
                time=time_name,
                precision=time_definition.precision,
                academic_major=academic_major_name,
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
        academic_major: str | None = None,
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

        if academic_major:
            match precision:
                case 11:  # day
                    return f"On {time}, {person} began {pronoun} studies in {academic_major} at {place}."
                case 10 | 9:  # month or year
                    return f"{person} began {pronoun} studies in {academic_major} at {place} in {time}."
                case _:
                    raise UnprocessableEventError(
                        f"Unexpected time precision: {precision}"
                    )
        else:
            match precision:
                case 11:  # day
                    return f"On {time}, {person} began {pronoun} studies at {place}."
                case 10 | 9:  # month or year
                    return f"{person} began {pronoun} studies at {place} in {time}."
                case _:
                    raise UnprocessableEventError(
                        f"Unexpected time precision: {precision}"
                    )
