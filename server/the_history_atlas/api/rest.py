from fastapi import FastAPI, Depends, Query, HTTPException, BackgroundTasks
from typing import Callable, Annotated, Literal
from faker import Faker
import random
from uuid import uuid4, UUID

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from the_history_atlas.api.handlers.history import (
    get_history_handler,
    check_time_exists_handler,
)
from the_history_atlas.api.handlers.tags import (
    create_person_handler,
    create_place_handler,
    create_time_handler,
    get_tags_handler,
    create_event_handler,
)
from the_history_atlas.api.handlers.users import login_handler
from the_history_atlas.api.types.history import (
    Source,
    CalendarDate,
    Tag,
    Map,
    HistoryEvent,
    Story,
    Point,
    TimeExistsRequest,
    TimeExistsResponse,
    StorySearchResponse,
    MapStory,
    MapStoryRequest,
)
from the_history_atlas.api.types.tags import (
    WikiDataPersonOutput,
    WikiDataPersonInput,
    WikiDataPlaceOutput,
    WikiDataPlaceInput,
    WikiDataTimeOutput,
    WikiDataTimeInput,
    WikiDataTagsOutput,
    WikiDataEventOutput,
    WikiDataEventInput,
)
from the_history_atlas.api.types.user import LoginResponse
from the_history_atlas.apps.accounts.errors import (
    DeactivatedUserError,
    MissingUserError,
)
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.models.accounts import UserDetails, GetUserPayload
from the_history_atlas.apps.domain.models.accounts.get_user import (
    GetUserResponsePayload,
)
from the_history_atlas.apps.domain import core as domain

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
    return Point(
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
            datetime=str(build_date(exact=True)),
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


def register_rest_endpoints(
    fastapi_app: FastAPI, app_manager: Callable[[], AppManager]
) -> FastAPI:

    Apps = Annotated[AppManager, Depends(app_manager)]
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def auth_required(
        token: Annotated[str, Depends(oauth2_scheme)],
        apps: Apps,
    ) -> GetUserResponsePayload:
        try:
            return apps.accounts_app.get_user(data=GetUserPayload(token=token))
        except (MissingUserError, DeactivatedUserError):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    AuthenticatedUser = Annotated[GetUserResponsePayload, Depends(auth_required)]

    def convert_map_story_to_api(story: domain.MapStory) -> MapStory:
        """Convert the internal MapStory model to the API MapStory model."""
        return MapStory(
            eventId=story.event_id,
            storyId=story.story_id,
            title=story.title,
            description=story.description,
            point=Point(
                id=story.story_id,  # Use story_id as point id since we don't have a separate point id
                latitude=story.point.latitude,
                longitude=story.point.longitude,
                name=story.title,  # Use story title as point name since we don't have a separate point name
            ),
            date=CalendarDate(
                datetime=story.date.datetime,
                calendar=story.date.calendar,
                precision=story.date.precision,
            ),
        )

    # API Endpoints
    @fastapi_app.get("/history", response_model=Story)
    def get_history(
        apps: Apps,
        eventId: Annotated[UUID, Query()] | None = None,
        storyId: Annotated[UUID, Query()] | None = None,
        direction: Annotated[Literal["next", "prev"], Query()] | None = None,
    ) -> Story:
        return get_history_handler(
            apps=apps, event_id=eventId, story_id=storyId, direction=direction
        )

    @fastapi_app.post(path="/wikidata/people", response_model=WikiDataPersonOutput)
    def create_people(
        person: WikiDataPersonInput, apps: Apps, user: AuthenticatedUser
    ) -> WikiDataPersonOutput:
        return create_person_handler(apps=apps, person=person)

    @fastapi_app.post("/wikidata/places", response_model=WikiDataPlaceOutput)
    def create_places(
        place: WikiDataPlaceInput, apps: Apps, user: AuthenticatedUser
    ) -> WikiDataPlaceOutput:
        return create_place_handler(apps=apps, place=place)

    @fastapi_app.post("/wikidata/times", response_model=WikiDataTimeOutput)
    def create_times(
        time: WikiDataTimeInput, apps: Apps, user: AuthenticatedUser
    ) -> WikiDataTimeOutput:
        return create_time_handler(apps=apps, time=time)

    @fastapi_app.get("/wikidata/tags", response_model=WikiDataTagsOutput)
    def get_tags(
        apps: Apps,
        user: AuthenticatedUser,
        wikidata_ids: Annotated[list[str] | None, Query()] = None,
    ) -> WikiDataTagsOutput:
        if not wikidata_ids:
            return WikiDataTagsOutput(wikidata_ids=[])
        return get_tags_handler(apps=apps, wikidata_ids=wikidata_ids)

    @fastapi_app.post("/wikidata/events", response_model=WikiDataEventOutput)
    def create_event(
        event: WikiDataEventInput,
        apps: Apps,
        user: AuthenticatedUser,
        background_tasks: BackgroundTasks,
    ) -> WikiDataEventOutput:
        output = create_event_handler(apps=apps, event=event)
        if apps.config_app.COMPUTE_STORY_ORDER:
            background_tasks.add_task(
                lambda: apps.history_app.calculate_story_order(
                    [tag.id for tag in event.tags]
                ),
            )
        return output

    @fastapi_app.post("/token")
    def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()], apps: Apps
    ) -> LoginResponse:
        return login_handler(form_data=form_data, apps=apps)

    @fastapi_app.post("/times/exist", response_model=TimeExistsResponse)
    def check_time_exists(
        request: TimeExistsRequest,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TimeExistsResponse:
        return check_time_exists_handler(apps=apps, request=request)

    @fastapi_app.get("/stories/search", response_model=StorySearchResponse)
    def search_stories(
        query: Annotated[str, Query()],
        apps: Apps,
    ) -> StorySearchResponse:
        """Search for stories using fuzzy text matching."""
        results = apps.history_app.fuzzy_search_stories(search_string=query)
        return StorySearchResponse(results=results)

    @fastapi_app.post("/map/stories", response_model=list[MapStory])
    def get_map_stories(
        request: MapStoryRequest,
        apps: Apps,
    ) -> list[MapStory]:
        """Get stories that have events within the given geographic bounds and time window."""
        stories = apps.history_app.get_map_stories(
            northwest_bound=domain.LatLong(
                latitude=request.northwest_bound.latitude,
                longitude=request.northwest_bound.longitude,
            ),
            southeast_bound=domain.LatLong(
                latitude=request.southeast_bound.latitude,
                longitude=request.southeast_bound.longitude,
            ),
            date=domain.CalendarDate(
                datetime=request.date.datetime,
                calendar=request.date.calendar,
                precision=request.date.precision,
            ),
        )
        return [convert_map_story_to_api(story) for story in stories]

    return fastapi_app
