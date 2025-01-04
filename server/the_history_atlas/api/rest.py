from fastapi import FastAPI
from typing import Literal
from faker import Faker
import random
from uuid import uuid4

from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.models.core import (
    Location,
    Source,
    CalendarDate,
    Tag,
    Map,
    HistoryEvent,
    Story,
)

fake = Faker()
Faker.seed(872)

# Models

# Helper Functions
def build_story_title():
    time_name = fake.date_this_century().strftime("%Y-%m-%d")
    story_templates = [
        lambda: f"The life of {fake.name()}.",
        lambda: f"The history of {time_name}.",
        lambda: f"The history of {fake.city()}.",
    ]
    return random.choice(story_templates)()


def build_date(exact: bool, base_date=None):
    if exact:
        return base_date or fake.date_this_century()
    return fake.date_between(start_date="-60y", end_date="today")


def build_source():
    return Source(
        id=str(uuid4()),
        text=fake.paragraph(),
        title=fake.sentence(),
        author=fake.name(),
        publisher=fake.company(),
        pubDate=str(fake.date_this_decade()),
    )


def build_tags(text, map_options):
    person_name = fake.name()
    point = build_point(map_options)
    time_name = fake.date_this_century().strftime("%Y-%m-%d")

    tagged_text = f"{person_name} visited {point.name} on {time_name}. {text}"

    return [
        Tag(
            id=str(uuid4()),
            type="PERSON",
            startChar=0,
            stopChar=len(person_name),
            name=person_name,
            defaultStoryId=str(uuid4()),
        ),
        Tag(
            id=str(uuid4()),
            type="PLACE",
            startChar=len(person_name) + 9,
            stopChar=len(person_name) + 9 + len(point.name),
            name=point.name,
            defaultStoryId=str(uuid4()),
        ),
        Tag(
            id=str(uuid4()),
            type="TIME",
            startChar=len(person_name) + 19 + len(point.name),
            stopChar=len(person_name) + 19 + len(point.name) + len(time_name),
            name=time_name,
            defaultStoryId=str(uuid4()),
        ),
    ], tagged_text


def build_point(map_options):
    latitude, longitude = fake.local_latlng(country_code="US", coords_only=True)
    return Location(
        id=str(uuid4()),
        latitude=float(latitude),
        longitude=float(longitude),
        name=fake.city(),
    )


def build_event(map_options, story_title):
    text = fake.sentence()
    tags, tagged_text = build_tags(text, map_options)
    return HistoryEvent(
        id=str(uuid4()),
        text=tagged_text,
        lang="en",
        date=CalendarDate(
            time=str(build_date(exact=True)),
            calendar="gregorian",
            precision=11,
        ),
        source=build_source(),
        tags=tags,
        map=Map(locations=[build_point(map_options)]),
        focus=None,
        storyTitle=story_title,
        stories=[],
    )


def build_story():
    story_title = build_story_title()
    events = [build_event({}, story_title) for _ in range(10)]
    return Story(id=str(uuid4()), name=story_title, events=events, index=5)


def register_rest_endpoints(app: FastAPI, app_manager: AppManager) -> FastAPI:
    # API Endpoints
    @app.get("/history", response_model=Story)
    def get_history(
        storyId: int | None = None,
        eventId: int | None = None,
        direction: Literal["next", "prev"] | None = None,
    ):
        return app_manager

    return app
