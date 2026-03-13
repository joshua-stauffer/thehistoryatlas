from fastapi import FastAPI, Depends, Query, HTTPException, BackgroundTasks, Header
from typing import Callable, Annotated, Literal, Optional
from faker import Faker
import random
from uuid import uuid4, UUID

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from the_history_atlas.api.handlers.api_keys import (
    create_api_key_handler,
    deactivate_api_key_handler,
)
from the_history_atlas.api.handlers.history import (
    get_history_handler,
    get_nearby_events_handler,
    check_time_exists_handler,
)
from the_history_atlas.api.handlers.tags import (
    create_person_handler,
    create_place_handler,
    create_time_handler,
    get_tags_handler,
    create_event_handler,
)
from the_history_atlas.api.handlers.text_reader import (
    create_source_handler,
    search_people_handler,
    create_person_without_wikidata_handler,
    search_places_handler,
    create_place_without_wikidata_handler,
    create_time_without_wikidata_handler,
    create_text_reader_event_handler,
    find_matching_summary_handler,
    create_text_reader_story_handler,
    get_story_by_source_handler,
)
from the_history_atlas.api.handlers.users import login_handler
from the_history_atlas.api.types.api_keys import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    DeactivateApiKeyResponse,
)
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
    NearbyEventsResponse,
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
    PlaceSearchResult,
    SummaryMatchResult,
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
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

    def auth_required(
        token: Annotated[Optional[str], Depends(oauth2_scheme)],
        apps: Apps,
        x_api_key: Annotated[Optional[str], Header()] = None,
    ) -> GetUserResponsePayload:
        # Try API key auth first
        if x_api_key:
            user_id = apps.accounts_app.validate_api_key(raw_key=x_api_key)
            if user_id:
                try:
                    return apps.accounts_app.get_user_by_id(user_id=user_id)
                except (MissingUserError, DeactivatedUserError):
                    pass
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
            )

        # Fall back to JWT Bearer token
        if token:
            try:
                return apps.accounts_app.get_user(data=GetUserPayload(token=token))
            except (MissingUserError, DeactivatedUserError):
                pass

        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def jwt_auth_required(
        token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="token"))],
        apps: Apps,
    ) -> GetUserResponsePayload:
        """JWT-only auth for sensitive operations like API key management."""
        try:
            return apps.accounts_app.get_user(data=GetUserPayload(token=token))
        except (MissingUserError, DeactivatedUserError):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    AuthenticatedUser = Annotated[GetUserResponsePayload, Depends(auth_required)]
    JWTAuthenticatedUser = Annotated[GetUserResponsePayload, Depends(jwt_auth_required)]

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

    @fastapi_app.get("/history/nearby", response_model=NearbyEventsResponse)
    def get_nearby_events(
        apps: Apps,
        eventId: Annotated[UUID, Query()],
        calendarModel: Annotated[str, Query()],
        precision: Annotated[int, Query()],
        datetime: Annotated[str, Query()],
        minLat: Annotated[float, Query()],
        maxLat: Annotated[float, Query()],
        minLng: Annotated[float, Query()],
        maxLng: Annotated[float, Query()],
    ) -> NearbyEventsResponse:
        return get_nearby_events_handler(
            apps=apps,
            event_id=eventId,
            calendar_model=calendarModel,
            precision=precision,
            datetime=datetime,
            min_lat=minLat,
            max_lat=maxLat,
            min_lng=minLng,
            max_lng=maxLng,
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

    # --- API Key Management (JWT-only) ---

    @fastapi_app.post("/api-keys", response_model=CreateApiKeyResponse)
    def create_api_key(
        request: CreateApiKeyRequest,
        apps: Apps,
        user: JWTAuthenticatedUser,
    ) -> CreateApiKeyResponse:
        user_id = apps.accounts_app.get_user_id_from_token(user.token)
        return create_api_key_handler(apps=apps, request=request, user_id=user_id)

    @fastapi_app.delete("/api-keys/{key_id}", response_model=DeactivateApiKeyResponse)
    def deactivate_api_key(
        key_id: UUID,
        apps: Apps,
        user: JWTAuthenticatedUser,
    ) -> DeactivateApiKeyResponse:
        user_id = apps.accounts_app.get_user_id_from_token(user.token)
        return deactivate_api_key_handler(apps=apps, key_id=key_id, user_id=user_id)

    # --- Text Reader Endpoints ---

    @fastapi_app.post("/text-reader/sources", response_model=TextReaderSourceOutput)
    def create_text_reader_source(
        source: TextReaderSourceInput,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TextReaderSourceOutput:
        return create_source_handler(apps=apps, source=source)

    @fastapi_app.get(
        "/text-reader/people/search",
        response_model=PeopleSearchResult,
    )
    def search_text_reader_people(
        apps: Apps,
        user: AuthenticatedUser,
        name: Annotated[str, Query()],
    ) -> PeopleSearchResult:
        return search_people_handler(apps=apps, name=name)

    @fastapi_app.post("/text-reader/people", response_model=TextReaderPersonOutput)
    def create_text_reader_person(
        person: TextReaderPersonInput,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TextReaderPersonOutput:
        return create_person_without_wikidata_handler(apps=apps, person=person)

    @fastapi_app.get(
        "/text-reader/places/search",
        response_model=PlaceSearchResult,
    )
    def search_text_reader_places(
        apps: Apps,
        user: AuthenticatedUser,
        name: Annotated[str, Query()] = "",
        latitude: Annotated[float | None, Query()] = None,
        longitude: Annotated[float | None, Query()] = None,
        radius: Annotated[float, Query()] = 1.0,
    ) -> PlaceSearchResult:
        return search_places_handler(
            apps=apps,
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
        )

    @fastapi_app.post("/text-reader/places", response_model=TextReaderPlaceOutput)
    def create_text_reader_place(
        place: TextReaderPlaceInput,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TextReaderPlaceOutput:
        return create_place_without_wikidata_handler(apps=apps, place=place)

    @fastapi_app.post("/text-reader/times", response_model=TextReaderTimeOutput)
    def create_text_reader_time(
        time_input: TextReaderTimeInput,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TextReaderTimeOutput:
        return create_time_without_wikidata_handler(apps=apps, time_input=time_input)

    @fastapi_app.post("/text-reader/events", response_model=TextReaderEventOutput)
    def create_text_reader_event(
        event: TextReaderEventInput,
        apps: Apps,
        user: AuthenticatedUser,
        background_tasks: BackgroundTasks,
    ) -> TextReaderEventOutput:
        return create_text_reader_event_handler(
            apps=apps, event=event, background_tasks=background_tasks
        )

    @fastapi_app.get(
        "/text-reader/summaries/match",
        response_model=SummaryMatchResult,
    )
    def find_matching_summary(
        apps: Apps,
        user: AuthenticatedUser,
        personIds: Annotated[list[UUID], Query()],
        placeId: Annotated[UUID, Query()],
        datetime: Annotated[str, Query()],
        calendarModel: Annotated[str, Query()],
        precision: Annotated[int, Query()],
    ) -> SummaryMatchResult:
        return find_matching_summary_handler(
            apps=apps,
            person_ids=personIds,
            place_id=placeId,
            datetime=datetime,
            calendar_model=calendarModel,
            precision=precision,
        )

    @fastapi_app.post("/text-reader/stories", response_model=TextReaderStoryOutput)
    def create_text_reader_story(
        story: TextReaderStoryInput,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TextReaderStoryOutput:
        return create_text_reader_story_handler(apps=apps, story=story)

    @fastapi_app.get(
        "/text-reader/stories/by-source/{source_id}",
        response_model=TextReaderStoryOutput | None,
    )
    def get_story_by_source(
        source_id: UUID,
        apps: Apps,
        user: AuthenticatedUser,
    ) -> TextReaderStoryOutput | None:
        return get_story_by_source_handler(apps=apps, source_id=source_id)

    return fastapi_app
