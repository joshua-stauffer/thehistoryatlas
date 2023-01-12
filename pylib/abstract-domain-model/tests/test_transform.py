from datetime import datetime

import pytest

from abstract_domain_model.errors import UnknownMessageError, MissingFieldsError
from abstract_domain_model.models import (
    SummaryAdded,
    SummaryTagged,
    TimeAdded,
    TimeTagged,
    PlaceAdded,
    PlaceTagged,
    PersonAdded,
    PersonTagged,
    CitationAdded,
    MetaAdded,
    TimeAddedPayload,
    SummaryAddedPayload,
    SummaryTaggedPayload,
    TimeTaggedPayload,
    PlaceAddedPayload,
    PlaceTaggedPayload,
    PersonAddedPayload,
    PersonTaggedPayload,
    CitationAddedPayload,
    MetaAddedPayload,
)
from abstract_domain_model.models.accounts import GetUser, GetUserPayload, UserDetails
from abstract_domain_model.models.accounts.get_user import (
    GetUserResponse,
    GetUserResponsePayload,
)
from abstract_domain_model.models.commands import (
    CommandFailed,
    CommandFailedPayload,
    CommandSuccess,
)
from abstract_domain_model.models.events.description import Description
from abstract_domain_model.models.events.geo import Geo
from abstract_domain_model.models.events.meta_tagged import (
    MetaTagged,
    MetaTaggedPayload,
)
from abstract_domain_model.models.events.name import Name
from abstract_domain_model.models.events.time import Time
from abstract_domain_model.transform import from_dict


@pytest.fixture
def baseline_event_data():
    return {
        "transaction_id": "2aab2a27-6b61-47d3-b5ba-a5057d0a880c",
        "app_version": "0.0.1-test",
        "timestamp": "2022-08-14 04:21:20.043861",
        "user_id": "a90de541-1455-45c5-ac51-915b93ff057f",
    }


@pytest.fixture
def summary_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "SUMMARY_ADDED",
        "payload": {
            "citation_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "text": "some text here please",
        },
    }


@pytest.fixture
def summary_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "SUMMARY_TAGGED",
        "payload": {
            "citation_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
        },
    }


@pytest.fixture
def time_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "TIME_ADDED",
        "payload": {
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "time": {
                "timestamp": str(datetime(year=1750, month=1, day=1)),
                "precision": 9,
            },
            "names": [{"name": "1750", "lang": "en", "is_default": True}],
            "desc": {
                "text": "The year 1750.",
                "lang": "en",
                "updated_at": "2023-01-12 01:43:06.822993",
            },
        },
    }


@pytest.fixture
def time_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "TIME_TAGGED",
        "payload": {
            "citation_id": "67ac5bd6-8508-487d-bd8f-0d9847e13be9",
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "name": "name",
            "citation_start": 10,
            "citation_end": 20,
        },
    }


@pytest.fixture
def place_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "PLACE_ADDED",
        "payload": {
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "names": [{"name": "Berlin", "lang": "en", "is_default": True}],
            "desc": {
                "text": "the city Berlin.",
                "lang": "en",
                "updated_at": "2023-01-12 01:43:06.822993",
            },
            "geo": {
                "latitude": 50.12345,
                "longitude": 45.23456,
            },
            "geo_names_id": 12345,
        },
    }


@pytest.fixture
def place_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "PLACE_TAGGED",
        "payload": {
            "citation_id": "67ac5bd6-8508-487d-bd8f-0d9847e13be9",
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "name": "name",
            "citation_start": 10,
            "citation_end": 20,
        },
    }


@pytest.fixture
def person_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "PERSON_ADDED",
        "payload": {
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "names": [{"name": "Bach", "lang": "en", "is_default": True}],
            "desc": {
                "text": "Baroque composer Johann Sebastian Bach.",
                "lang": "en",
                "updated_at": "2023-01-12 01:43:06.822993",
            },
        },
    }


@pytest.fixture
def person_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "PERSON_TAGGED",
        "payload": {
            "citation_id": "67ac5bd6-8508-487d-bd8f-0d9847e13be9",
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "name": "name",
            "citation_start": 10,
            "citation_end": 20,
        },
    }


@pytest.fixture
def citation_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "CITATION_ADDED",
        "payload": {
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "text": "name",
            "meta_id": "69a8bc1b-7c7c-49a3-8d05-db110c14b949",
        },
    }


@pytest.fixture
def meta_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "META_ADDED",
        "payload": {
            "citation_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "title": "name",
            "author": "name",
            "publisher": "some publisher",
            "pub_date": "1/2/23",
            "kwargs": {"accept": "arbitrary_kwargs"},
        },
    }


@pytest.fixture
def meta_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "META_TAGGED",
        "payload": {
            "citation_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
        },
    }


def test_transform_summary_added(summary_added_data):
    res = from_dict(summary_added_data)
    assert isinstance(res, SummaryAdded)
    assert isinstance(res.payload, SummaryAddedPayload)
    for key, value in summary_added_data.items():
        if isinstance(value, dict):
            value = SummaryAddedPayload(**value)
        assert getattr(res, key) == value


def test_transform_summary_tagged(summary_tagged_data):
    res = from_dict(summary_tagged_data)
    assert isinstance(res, SummaryTagged)
    assert isinstance(res.payload, SummaryTaggedPayload)
    for key, value in summary_tagged_data.items():
        if isinstance(value, dict):
            value = SummaryTaggedPayload(**value)
        assert getattr(res, key) == value


def test_transform_time_added(time_added_data):
    res = from_dict(time_added_data)
    assert isinstance(res, TimeAdded)
    assert isinstance(res.payload, TimeAddedPayload)
    assert isinstance(res.payload.time, Time)
    assert isinstance(res.payload.names, list)
    for name in res.payload.names:
        assert isinstance(name, Name)
    assert isinstance(res.payload.desc, Description)


def test_transform_time_tagged(time_tagged_data):
    res = from_dict(time_tagged_data)
    assert isinstance(res, TimeTagged)
    assert isinstance(res.payload, TimeTaggedPayload)
    for key, value in time_tagged_data.items():
        if isinstance(value, dict):
            value = TimeTaggedPayload(**value)
        assert getattr(res, key) == value


def test_transform_place_added(place_added_data):
    res = from_dict(place_added_data)
    assert isinstance(res, PlaceAdded)
    assert isinstance(res.payload, PlaceAddedPayload)
    assert isinstance(res.payload.names, list)
    for name in res.payload.names:
        assert isinstance(name, Name)
    assert isinstance(res.payload.desc, Description)
    assert isinstance(res.payload.geo, Geo)


def test_transform_place_tagged(place_tagged_data):
    res = from_dict(place_tagged_data)
    assert isinstance(res, PlaceTagged)
    assert isinstance(res.payload, PlaceTaggedPayload)
    for key, value in place_tagged_data.items():
        if isinstance(value, dict):
            value = PlaceTaggedPayload(**value)
        assert getattr(res, key) == value


def test_transform_person_added(person_added_data):
    res = from_dict(person_added_data)
    assert isinstance(res, PersonAdded)
    assert isinstance(res.payload, PersonAddedPayload)
    assert isinstance(res.payload.names, list)
    for name in res.payload.names:
        assert isinstance(name, Name)
    assert isinstance(res.payload.desc, Description)


def test_transform_person_tagged(person_tagged_data):
    res = from_dict(person_tagged_data)
    assert isinstance(res, PersonTagged)
    assert isinstance(res.payload, PersonTaggedPayload)
    for key, value in person_tagged_data.items():
        if isinstance(value, dict):
            value = PersonTaggedPayload(**value)
        assert getattr(res, key) == value


def test_transform_citation_added(citation_added_data):
    res = from_dict(citation_added_data)
    assert isinstance(res, CitationAdded)
    assert isinstance(res.payload, CitationAddedPayload)
    for key, value in citation_added_data.items():
        if isinstance(value, dict):
            value = CitationAddedPayload(**value)
        assert getattr(res, key) == value


def test_transform_meta_added(meta_added_data):
    res = from_dict(meta_added_data)
    assert isinstance(res, MetaAdded)
    assert isinstance(res.payload, MetaAddedPayload)
    for key, value in meta_added_data.items():
        if isinstance(value, dict):
            value = MetaAddedPayload(**value)
        assert getattr(res, key) == value


def test_transform_meta_tagged(meta_tagged_data):
    res = from_dict(meta_tagged_data)
    assert isinstance(res, MetaTagged)
    assert isinstance(res.payload, MetaTaggedPayload)
    for key, value in meta_tagged_data.items():
        if isinstance(value, dict):
            value = MetaTaggedPayload(**value)
        assert getattr(res, key) == value


def test_transform_without_type_raises_exception():
    with pytest.raises(UnknownMessageError):
        _ = from_dict({})


def test_transform_with_missing_fields_raises_exception():
    data = {"type": "PERSON_TAGGED"}
    with pytest.raises(MissingFieldsError):
        _ = from_dict(data)


def test_transform_command_failed():
    data = {"type": "COMMAND_FAILED", "payload": {"reason": "some reason"}}
    res = from_dict(data)
    assert isinstance(res, CommandFailed)
    assert isinstance(res.payload, CommandFailedPayload)


def test_transform_command_success():
    data = {
        "type": "COMMAND_SUCCESS",
    }
    res = from_dict(data)
    assert isinstance(res, CommandSuccess)


def test_transform_get_user():
    get_user = from_dict(
        {
            "type": "GET_USER",
            "payload": {
                "token": "token-value-here",
            },
        }
    )
    assert isinstance(get_user, GetUser)
    assert isinstance(get_user.payload, GetUserPayload)


def test_transform_get_user_response():
    get_user_response = from_dict(
        {
            "type": "GET_USER_RESPONSE",
            "payload": {
                "token": "token-value-here",
                "user_details": {
                    "f_name": "Bilbo",
                    "l_name": "Baggins",
                    "username": "dragonslayer",
                    "email": "bagends@theshire.middleearth",
                    "last_login": "2022-12-23 16:30:53.368102",
                },
            },
        }
    )
    assert isinstance(get_user_response, GetUserResponse)
    assert isinstance(get_user_response.payload, GetUserResponsePayload)
    assert isinstance(get_user_response.payload.user_details, UserDetails)
