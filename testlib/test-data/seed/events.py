from datetime import datetime

from abstract_domain_model.models import (
    PersonAdded,
    PersonAddedPayload,
    PlaceAdded,
    PlaceAddedPayload,
    TimeAdded,
    TimeAddedPayload,
)
from abstract_domain_model.models.core import Name, Description, Geo, Time
from .synthetic_events import SYNTHETIC_EVENTS
from .util import get_version

USER_ID = "9ee62665-5037-441b-86bc-09514c17ab6b"

EVENTS = [event for events in SYNTHETIC_EVENTS for event in events]

PEOPLE_ADDED = [
    PersonAdded(
        transaction_id="89be0615-0804-44f8-9e29-3ee4082f1290",
        app_version=get_version(),
        timestamp="2023-01-14 05:00:57.383971",
        user_id=USER_ID,
        payload=PersonAddedPayload(
            id="d4720213-9d88-4c0e-a02c-ea3cfb229944",
            names=[
                Name(
                    id="7f0c5242-3e28-4ae2-9f1d-96ec515aafc5",
                    name="Bach",
                    lang="en",
                    is_default=False,
                ),
                Name(
                    id="7ad8f316-98a1-4182-8656-67e85526c0ba",
                    name="Johann Sebastian Bach",
                    lang="en",
                    is_default=False,
                ),
                Name(
                    id="86d4af61-bd42-41c1-b17b-458f771127d3",
                    name="J.S. Bach",
                    lang="en",
                    is_default=False,
                ),
            ],
            desc=[
                Description(
                    id="ac4019d5-c028-4d83-849c-38ece8e2c48a",
                    text="German composer (1685–1750)",
                    lang="en",
                    source_updated_at="2023-01-14 05:00:57.383971",
                )
            ],
            wiki_link="https://www.wikidata.org/wiki/Q1339",
            wiki_data_id="Q1339",
        ),
        type="PERSON_ADDED",
        index=1,
    )
]

PLACES_ADDED = [
    PlaceAdded(
        transaction_id="ff5291fd-2011-4c1e-ae45-c4412a29101c",
        app_version=get_version(),
        timestamp="2023-01-14 06:54:43.405897",
        user_id=USER_ID,
        type="PLACE_ADDED",
        index=2,
        payload=PlaceAddedPayload(
            id="fd6da39c-6b76-445a-96c3-f29daf0a49ea",
            names=[
                Name(
                    id="bd66106b-ac13-4dc6-9caa-acee4b1c06b5",
                    name="Einsenach",
                    lang="en",
                    is_default=True,
                )
            ],
            desc=[
                Description(
                    id="f51db0a4-c499-44cd-ac12-68d545680ac6",
                    text="municipality in Thuringia, Germany",
                    lang="en",
                    source_updated_at="2023-01-14 02:05:58",
                    wiki_link="https://www.wikidata.org/wiki/Q7070",
                    wiki_data_id="Q7070",
                )
            ],
            wiki_link="https://www.wikidata.org/wiki/Q7070",
            wiki_data_id="Q7070",
            geo_names_id="6547386",
            geo=Geo(
                latitude=50.97443,
                longitude=10.33407,
                geoshape=None,
                population=42250,
                feature_code="historical third-order administrative division",
                feature_class="country, state, region,... (A)",
            ),
        ),
    )
]

TIMES_ADDED = [
    TimeAdded(
        transaction_id="84e8907c-bbc2-408a-bb41-204792ac77af",
        app_version=get_version(),
        timestamp="2023-01-14 10:54:16",
        user_id=USER_ID,
        type="TIME_ADDED",
        index=3,
        payload=TimeAddedPayload(
            id="de246ee5-99aa-452d-9df4-1959b5cccc50",
            names=[
                Name(
                    id="9081e3b6-9113-464c-836f-ab2fc99f63b7",
                    name="21 March 1685",
                    lang="en",
                    is_default=True,
                )
            ],
            desc=[
                Description(
                    id="0e6f18ee-caad-4017-bdb7-4f2f6836280b",
                    text="Date in gregorian calendar.",
                    lang="en",
                    source_updated_at="2023-01-14 16:53:02",
                    wiki_link="https://www.wikidata.org/wiki/Q69125225",
                    wiki_data_id="Q69125225",
                )
            ],
            wiki_link="https://www.wikidata.org/wiki/Q69125225",
            wiki_data_id="Q69125225",
            time=Time(
                timestamp=str(datetime(year=1685, month=3, day=21)),
                precision=11,
                calendar_type="gregorian",
                circa=False,
                latest=False,
                earliest=False,
            ),
        ),
    )
]
