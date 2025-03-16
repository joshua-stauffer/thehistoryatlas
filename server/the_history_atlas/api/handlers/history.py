from typing import Literal
from uuid import UUID

from fastapi import HTTPException

import the_history_atlas.api.types.history as api_types
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.core import (
    Story,
    HistoryEvent,
    CalendarDate,
    Source,
    Tag,
    Map,
    Point,
)
from the_history_atlas.apps.history.errors import MissingResourceError


def to_camel(string: str) -> str:
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def get_history_handler(
    apps: AppManager,
    event_id: UUID | None,
    story_id: UUID | None,
    direction: Literal["next", "prev"] | None,
) -> api_types.Story:
    if not event_id or not story_id:
        story_pointer = apps.history_app.get_default_story_and_event(
            story_id=story_id,
            event_id=event_id,
        )
        story_id = story_pointer.story_id
        event_id = story_pointer.event_id
    try:
        story = apps.history_app.get_story_list(
            event_id=event_id, story_id=story_id, direction=direction
        )
    except MissingResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not direction:
        index = [event.id for event in story.events].index(event_id)
    elif direction == "prev":
        index = len(story.events) - 1
    elif direction == "next":
        index = 0
    return convert_story_to_api(story, index=index)


def convert_story_to_api(story: Story, index: int) -> api_types.Story:
    """Convert the internal Story model to the API Story model."""
    return api_types.Story(
        id=story.id,
        name=story.name,
        events=[convert_event_to_api(event) for event in story.events],
        index=index,
    )


def convert_event_to_api(event: HistoryEvent) -> api_types.HistoryEvent:
    """Convert the internal HistoryEvent model to the API HistoryEvent model."""
    return api_types.HistoryEvent(
        id=event.id,
        text=event.text,
        lang=event.lang,
        date=convert_calendar_date_to_api(event.date),
        source=convert_source_to_api(event.source),
        tags=[convert_tag_to_api(tag) for tag in event.tags],
        map=convert_map_to_api(event.map),
        focus=event.focus if event.focus else None,
        storyTitle=event.story_title,
        stories=event.stories,
    )


def convert_calendar_date_to_api(date: CalendarDate) -> api_types.CalendarDate:
    """Convert the internal CalendarDate model to the API CalendarDate model."""
    return api_types.CalendarDate(
        datetime=date.datetime, calendar=date.calendar, precision=date.precision
    )


def convert_source_to_api(source: Source) -> api_types.Source:
    """Convert the internal Source model to the API Source model."""
    return api_types.Source(
        id=source.id,
        text=source.text,
        title=source.title,
        author=source.author,
        publisher=source.publisher,
        pubDate=source.pub_date,
    )


def convert_tag_to_api(tag: Tag) -> api_types.Tag:
    """Convert the internal Tag model to the API Tag model."""
    return api_types.Tag(
        id=tag.id,
        type=tag.type,
        startChar=tag.start_char,
        stopChar=tag.stop_char,
        name=tag.name,
        defaultStoryId=tag.default_story_id,
    )


def convert_map_to_api(map_data: Map) -> api_types.Map:
    """Convert the internal Map model to the API Map model."""
    return api_types.Map(
        locations=[convert_point_to_api(point) for point in map_data.locations]
    )


def convert_point_to_api(point: Point) -> api_types.Point:
    """Convert the internal Point model to the API Point model."""
    return api_types.Point(
        id=point.id, latitude=point.latitude, longitude=point.longitude, name=point.name
    )
