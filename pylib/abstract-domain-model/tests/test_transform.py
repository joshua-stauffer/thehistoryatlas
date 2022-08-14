import pytest

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
)
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
            "summary_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
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
            "summary_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
        },
    }


@pytest.fixture
def time_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "TIME_ADDED",
        "payload": {
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "time_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "time_name": "name",
            "citation_start": 10,
            "citation_end": 20,
        },
    }


@pytest.fixture
def time_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "TIME_TAGGED",
        "payload": {
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "time_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "time_name": "name",
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
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "place_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "place_name": "name",
            "citation_start": 10,
            "citation_end": 20,
            "latitude": 50.12345,
            "longitude": 45.23456,
            "geoshape": None,
        },
    }


@pytest.fixture
def place_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "PLACE_TAGGED",
        "payload": {
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "place_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "place_name": "name",
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
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "person_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "person_name": "name",
            "citation_start": 10,
            "citation_end": 20,
        },
    }


@pytest.fixture
def person_tagged_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "PERSON_TAGGED",
        "payload": {
            "summary_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "person_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "person_name": "name",
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
            "citation_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "text": "name",
            "tags": ["one", "two", "three"],
            "meta": "arbitrary value here",
        },
    }


@pytest.fixture
def meta_added_data(baseline_event_data):
    return {
        **baseline_event_data,
        "type": "META_ADDED",
        "payload": {
            "citation_id": "1c9ad5a6-834d-4af1-b8bf-69a9fbac5e81",
            "meta_id": "961b6524-693f-4f41-8153-e99e2d27a5cf",
            "title": "name",
            "author": "name",
            "publisher": "some publisher",
            "kwargs": {"accept": "arbitrary_kwargs"},
        },
    }


def test_transform_summary_added(summary_added_data):
    res = from_dict(summary_added_data)
    assert isinstance(res, SummaryAdded)
    for key, value in summary_added_data.items():
        assert getattr(res, key) == value


def test_transform_summary_tagged(summary_tagged_data):
    res = from_dict(summary_tagged_data)
    assert isinstance(res, SummaryTagged)
    for key, value in summary_tagged_data.items():
        assert getattr(res, key) == value


def test_transform_time_added(time_added_data):
    res = from_dict(time_added_data)
    assert isinstance(res, TimeAdded)
    for key, value in time_added_data.items():
        assert getattr(res, key) == value


def test_transform_time_tagged(time_tagged_data):
    res = from_dict(time_tagged_data)
    assert isinstance(res, TimeTagged)
    for key, value in time_tagged_data.items():
        assert getattr(res, key) == value


def test_transform_place_added(place_added_data):
    res = from_dict(place_added_data)
    assert isinstance(res, PlaceAdded)
    for key, value in place_added_data.items():
        assert getattr(res, key) == value


def test_transform_place_tagged(place_tagged_data):
    res = from_dict(place_tagged_data)
    assert isinstance(res, PlaceTagged)
    for key, value in place_tagged_data.items():
        assert getattr(res, key) == value


def test_transform_person_added(person_added_data):
    res = from_dict(person_added_data)
    assert isinstance(res, PersonAdded)
    for key, value in person_added_data.items():
        assert getattr(res, key) == value


def test_transform_person_tagged(person_tagged_data):
    res = from_dict(person_tagged_data)
    assert isinstance(res, PersonTagged)
    for key, value in person_tagged_data.items():
        assert getattr(res, key) == value


def test_transform_citation_added(citation_added_data):
    res = from_dict(citation_added_data)
    assert isinstance(res, CitationAdded)
    for key, value in citation_added_data.items():
        assert getattr(res, key) == value


def test_transform_meta_added(meta_added_data):
    res = from_dict(meta_added_data)
    assert isinstance(res, MetaAdded)
    for key, value in meta_added_data.items():
        assert getattr(res, key) == value
