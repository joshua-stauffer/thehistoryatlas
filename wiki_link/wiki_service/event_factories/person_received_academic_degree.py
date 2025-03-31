from typing import Literal
from dataclasses import dataclass

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
    ACADEMIC_DEGREE,
    EDUCATED_AT,
    ACADEMIC_MAJOR,
    ACADEMIC_MINOR,
    DOCTORAL_ADVISOR,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
    POINT_IN_TIME,
)
from wiki_service.event_factories.utils import (
    wikidata_time_to_text,
)


@dataclass
class AdvisorInfo:
    """Intermediate storage for advisor information before creating PersonWikiTag."""

    name: str
    wiki_id: str


@register_event_factory
class PersonReceivedAcademicDegree(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person received academic degree"

    def entity_has_event(self) -> bool:
        if self._entity_type != "PERSON":
            return False

        if ACADEMIC_DEGREE not in self._entity.claims:
            return False

        # Check if any ACADEMIC_DEGREE claim has a POINT_IN_TIME qualifier
        for claim in self._entity.claims[ACADEMIC_DEGREE]:
            if "qualifiers" in claim and POINT_IN_TIME in claim["qualifiers"]:
                return True
        return False

    def create_wiki_event(self) -> list[WikiEvent]:
        person_name = self._entity.labels["en"].value
        events = []

        for claim in self._entity.claims[ACADEMIC_DEGREE]:
            degree_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            degree_name = self._query.get_label(id=degree_id, language="en")

            # Get institution information if available
            institution_id = None
            place_name = None
            geo_location = None
            if "qualifiers" in claim and EDUCATED_AT in claim["qualifiers"]:
                institution_id = claim["qualifiers"][EDUCATED_AT][0]["datavalue"][
                    "value"
                ]["id"]
                place_name = self._query.get_label(id=institution_id, language="en")
                geo_location = self._query.get_geo_location(id=institution_id)

            # Skip if we have an institution but no location data
            if institution_id and not (
                geo_location.coordinates or geo_location.geoshape
            ):
                continue

            # Get time information
            time_definition = None
            if "qualifiers" in claim and POINT_IN_TIME in claim["qualifiers"]:
                time_qualifier = claim["qualifiers"][POINT_IN_TIME][0]
                time_definition = TimeDefinition(
                    id="",
                    type="statement",
                    rank="normal",
                    hash="",
                    snaktype="value",
                    property=POINT_IN_TIME,
                    time=time_qualifier["datavalue"]["value"]["time"],
                    timezone=0,
                    before=0,
                    after=0,
                    precision=time_qualifier["datavalue"]["value"]["precision"],
                    calendarmodel=time_qualifier["datavalue"]["value"]["calendarmodel"],
                )

            # Get academic majors if available
            academic_majors = []
            if "qualifiers" in claim and ACADEMIC_MAJOR in claim["qualifiers"]:
                for major_qualifier in claim["qualifiers"][ACADEMIC_MAJOR]:
                    major_id = major_qualifier["datavalue"]["value"]["id"]
                    major_name = self._query.get_label(id=major_id, language="en")
                    academic_majors.append(major_name)

            # Get academic minors if available
            academic_minors = []
            if "qualifiers" in claim and ACADEMIC_MINOR in claim["qualifiers"]:
                for minor_qualifier in claim["qualifiers"][ACADEMIC_MINOR]:
                    minor_id = minor_qualifier["datavalue"]["value"]["id"]
                    minor_name = self._query.get_label(id=minor_id, language="en")
                    academic_minors.append(minor_name)

            academic_major_name = None
            if academic_majors:
                if len(academic_majors) == 1:
                    academic_major_name = academic_majors[0]
                else:
                    academic_major_name = (
                        ", ".join(academic_majors[:-1]) + " and " + academic_majors[-1]
                    )

            academic_minor_name = None
            if academic_minors:
                if len(academic_minors) == 1:
                    academic_minor_name = academic_minors[0]
                else:
                    academic_minor_name = (
                        ", ".join(academic_minors[:-1]) + " and " + academic_minors[-1]
                    )

            # Get doctoral advisors if available
            advisor_infos = []
            if "qualifiers" in claim and DOCTORAL_ADVISOR in claim["qualifiers"]:
                for advisor_qualifier in claim["qualifiers"][DOCTORAL_ADVISOR]:
                    advisor_id = advisor_qualifier["datavalue"]["value"]["id"]
                    advisor_name = self._query.get_label(id=advisor_id, language="en")
                    advisor_infos.append(
                        AdvisorInfo(name=advisor_name, wiki_id=advisor_id)
                    )

            advisor_names = None
            if advisor_infos:
                if len(advisor_infos) == 1:
                    advisor_names = advisor_infos[0].name
                else:
                    advisor_names = (
                        ", ".join(adv.name for adv in advisor_infos[:-1])
                        + " and "
                        + advisor_infos[-1].name
                    )

            # Create summary
            time_name = (
                wikidata_time_to_text(time_definition) if time_definition else None
            )
            precision = time_definition.precision if time_definition else None

            summary = self._summary(
                person=person_name,
                degree=degree_name,
                place=place_name,
                time=time_name,
                precision=precision,
                academic_major=academic_major_name,
                academic_minor=academic_minor_name,
                advisor_names=advisor_names,
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

            # Add advisor tags if present
            if advisor_infos:
                for advisor_info in advisor_infos:
                    advisor_pos = summary.find(advisor_info.name)
                    if advisor_pos != -1:
                        people_tags.append(
                            PersonWikiTag(
                                name=advisor_info.name,
                                wiki_id=advisor_info.wiki_id,
                                start_char=advisor_pos,
                                stop_char=advisor_pos + len(advisor_info.name),
                            )
                        )

            # Create place tag if we have location information
            place_tag = None
            if place_name and geo_location:
                place_tag = PlaceWikiTag(
                    name=place_name,
                    wiki_id=institution_id,
                    start_char=summary.find(place_name),
                    stop_char=summary.find(place_name) + len(place_name),
                    location=geo_location,
                )

            # Create time tag if we have time information
            time_tag = None
            if time_name and time_definition:
                time_tag = TimeWikiTag(
                    name=time_name,
                    wiki_id=None,
                    start_char=summary.find(time_name),
                    stop_char=summary.find(time_name) + len(time_name),
                    time_definition=time_definition,
                )

            # Only create event if we have both place and time information
            if place_tag and time_tag:
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
        degree: str,
        place: str | None,
        time: str | None,
        precision: int | None,
        academic_major: str | None = None,
        academic_minor: str | None = None,
        advisor_names: str | None = None,
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

        # Build base summary
        if academic_major and academic_minor:
            base = f"{person} received {pronoun} {degree} in {academic_major} with a minor in {academic_minor}"
        elif academic_major:
            base = f"{person} received {pronoun} {degree} in {academic_major}"
        elif academic_minor:
            base = (
                f"{person} received {pronoun} {degree} with a minor in {academic_minor}"
            )
        else:
            base = f"{person} received {pronoun} {degree}"

        # Add institution if available
        if place:
            base += f" from {place}"

        # Add advisor information if available
        if advisor_names:
            base += f", under the supervision of {advisor_names}"

        # Add time information based on precision
        if time and precision:
            match precision:
                case 11:  # day
                    return f"On {time}, {base}."
                case 10 | 9:  # month or year
                    return f"{base} in {time}."
                case _:
                    raise UnprocessableEventError(
                        f"Unexpected time precision: {precision}"
                    )
        else:
            return f"{base}."
