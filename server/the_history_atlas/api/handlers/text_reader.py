from uuid import UUID

from fastapi import HTTPException, BackgroundTasks

from the_history_atlas.api.types.text_reader import (
    TextReaderSourceInput,
    TextReaderSourceOutput,
    TextReaderPersonInput,
    TextReaderPersonOutput,
    TextReaderPlaceInput,
    TextReaderPlaceOutput,
    TextReaderTimeInput,
    TextReaderTimeOutput,
    TextReaderEventInput,
    TextReaderEventOutput,
    TextReaderStoryInput,
    TextReaderStoryOutput,
    PeopleSearchResult,
    PersonSearchCandidate,
    PlaceSearchResult,
    PlaceSearchCandidate,
    SummaryMatchResult,
)
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.core import TagInstance
from the_history_atlas.apps.history.errors import (
    DuplicateEventError,
    MissingTagTypesError,
)


def create_source_handler(
    apps: AppManager, source: TextReaderSourceInput
) -> TextReaderSourceOutput:
    result = apps.history_app.create_text_reader_source(
        title=source.title,
        author=source.author,
        publisher=source.publisher,
        pub_date=source.pub_date,
        pdf_page_offset=source.pdf_page_offset,
    )
    return TextReaderSourceOutput(**result)


def search_people_handler(apps: AppManager, name: str) -> PeopleSearchResult:
    candidates = apps.history_app.search_people_by_name(name=name)
    return PeopleSearchResult(
        candidates=[
            PersonSearchCandidate(
                id=c["id"],
                name=c["name"],
                type=c["type"],
                description=c.get("description"),
                earliest_date=c.get("earliest_date"),
                latest_date=c.get("latest_date"),
            )
            for c in candidates
        ]
    )


def create_person_without_wikidata_handler(
    apps: AppManager, person: TextReaderPersonInput
) -> TextReaderPersonOutput:
    result = apps.history_app.create_person_without_wikidata(
        name=person.name, description=person.description
    )
    return TextReaderPersonOutput(**result)


def search_places_handler(
    apps: AppManager,
    name: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    radius: float = 1.0,
) -> PlaceSearchResult:
    candidates = apps.history_app.search_places(
        name=name, latitude=latitude, longitude=longitude, radius=radius
    )
    return PlaceSearchResult(
        candidates=[
            PlaceSearchCandidate(
                id=c["id"],
                name=c["name"],
                latitude=c.get("latitude"),
                longitude=c.get("longitude"),
            )
            for c in candidates
        ]
    )


def create_place_without_wikidata_handler(
    apps: AppManager, place: TextReaderPlaceInput
) -> TextReaderPlaceOutput:
    result = apps.history_app.create_place_without_wikidata(
        name=place.name,
        latitude=place.latitude,
        longitude=place.longitude,
        geonames_id=place.geonames_id,
        description=place.description,
    )
    return TextReaderPlaceOutput(**result)


def create_time_without_wikidata_handler(
    apps: AppManager, time_input: TextReaderTimeInput
) -> TextReaderTimeOutput:
    result = apps.history_app.create_time_without_wikidata(
        name=time_input.name,
        date=time_input.date,
        calendar_model=time_input.calendar_model,
        precision=time_input.precision,
        description=time_input.description,
    )
    return TextReaderTimeOutput(**result)


def create_text_reader_event_handler(
    apps: AppManager,
    event: TextReaderEventInput,
    background_tasks: BackgroundTasks,
) -> TextReaderEventOutput:
    # Validate that every tag name appears in the summary at the declared position
    for tag in event.tags:
        actual = event.summary[tag.start_char : tag.stop_char]
        if actual != tag.name:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Tag '{tag.name}' not found at position "
                    f"{tag.start_char}:{tag.stop_char} in summary "
                    f"(found '{actual}')"
                ),
            )

    tags = [
        TagInstance(
            id=tag.id,
            name=tag.name,
            start_char=tag.start_char,
            stop_char=tag.stop_char,
        )
        for tag in event.tags
    ]
    try:
        summary_id = apps.history_app.create_text_reader_event(
            text=event.summary,
            tags=tags,
            citation_text=event.citation.text,
            citation_page_num=event.citation.page_num,
            citation_access_date=event.citation.access_date,
            source_id=event.source_id,
            story_id=event.story_id,
            canonical_summary_id=event.canonical_summary_id,
            theme_slugs=event.theme_slugs,
        )
    except MissingTagTypesError as e:
        raise HTTPException(status_code=422, detail=e.msg)
    except DuplicateEventError:
        raise HTTPException(
            status_code=409,
            detail="An event with this text already exists",
        )

    if apps.config_app.COMPUTE_STORY_ORDER:
        background_tasks.add_task(
            lambda: apps.history_app.calculate_story_order(
                [tag.id for tag in event.tags]
            ),
        )

    return TextReaderEventOutput(id=summary_id)


def find_matching_summary_handler(
    apps: AppManager,
    person_ids: list[UUID],
    place_id: UUID,
    datetime: str,
    calendar_model: str,
    precision: int,
) -> SummaryMatchResult:
    result = apps.history_app.find_matching_summary(
        person_ids=person_ids,
        place_id=place_id,
        datetime_val=datetime,
        calendar_model=calendar_model,
        precision=precision,
    )
    if result:
        return SummaryMatchResult(
            found=True,
            summary_id=result["summary_id"],
            summary_text=result["summary_text"],
            has_wikidata_citation=result["has_wikidata_citation"],
        )
    return SummaryMatchResult(found=False)


def create_text_reader_story_handler(
    apps: AppManager, story: TextReaderStoryInput
) -> TextReaderStoryOutput:
    result = apps.history_app.create_text_reader_story(
        name=story.name,
        description=story.description,
        source_id=story.source_id,
    )
    return TextReaderStoryOutput(**result)


def get_story_by_source_handler(
    apps: AppManager, source_id: UUID
) -> TextReaderStoryOutput | None:
    result = apps.history_app.get_story_by_source_id(source_id=source_id)
    if result:
        return TextReaderStoryOutput(**result)
    return None
