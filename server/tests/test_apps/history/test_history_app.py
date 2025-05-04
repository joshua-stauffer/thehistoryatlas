from the_history_atlas.apps.domain.core import PersonInput
from the_history_atlas.apps.domain.models.history.tables.time import TimePrecision
import pytest
from uuid import UUID
import time


def test_create_person(history_app, cleanup_tag) -> None:
    person = PersonInput(
        wikidata_id="Q1339",
        wikidata_url="https://www.wikidata.org/wiki/Q1339",
        name="Johann Sebastian Bach",
    )
    created_person = history_app.create_person(person=person)
    cleanup_tag(created_person.id)
    assert created_person.id
    assert created_person.name == "Johann Sebastian Bach"
    assert created_person.wikidata_id == "Q1339"
    assert created_person.wikidata_url == "https://www.wikidata.org/wiki/Q1339"


from datetime import datetime, timezone
from the_history_atlas.apps.domain.core import TimeInput


class TestCheckTimeExists:
    def test_success(self, history_app) -> None:
        test_time = datetime(2024, 3, 14, tzinfo=timezone.utc)
        test_calendar = "gregorian"
        test_precision = 11  # DAY precision

        time_input = TimeInput(
            datetime=test_time,
            calendar_model=test_calendar,
            precision=test_precision,
            name="Test Time",
            wikidata_id=None,
            wikidata_url=None,
            date=str(test_time),
        )
        created_time = history_app.create_time(time=time_input)

        # Get the time ID directly from the check_time_exists method
        time_id = history_app.check_time_exists(
            datetime=str(test_time),
            calendar_model=test_calendar,
            precision=test_precision,
        )
        assert time_id == created_time.id

    def test_failure(self, history_app) -> None:
        test_calendar = "gregorian"
        test_precision = 11  # DAY precision
        non_existing_time = datetime(2023, 3, 14, tzinfo=timezone.utc)

        # Check that the time doesn't exist and the ID is None
        time_id = history_app.check_time_exists(
            datetime=str(non_existing_time),
            calendar_model=test_calendar,
            precision=test_precision,
        )
        assert time_id is None


class TestFuzzySearchStories:
    def test_empty_search_string(self, history_app) -> None:
        """Test that an empty search string returns an empty list."""
        results = history_app.fuzzy_search_stories("")
        assert results == []

    def test_no_matches(self, history_app) -> None:
        """Test that a search string with no matches returns an empty list."""
        results = history_app.fuzzy_search_stories("xyzabc123nonexistent")
        assert results == []

    def test_successful_search(self, history_app, cleanup_tag) -> None:
        """Test that searching for an existing story returns the correct results."""
        # Create a test person that we can search for
        person = PersonInput(
            wikidata_id="Q123456",
            wikidata_url="https://www.wikidata.org/wiki/Q123456",
            name="Test Person For Search",
        )
        created_person = history_app.create_person(person=person)
        cleanup_tag(created_person.id)

        # Search for the person
        results = history_app.fuzzy_search_stories("Test Person")

        # Verify results
        assert len(results) > 0
        assert any(
            result["name"] == "The Life of Test Person For Search" for result in results
        )
        assert all(
            isinstance(result["id"], str) and isinstance(result["name"], str)
            for result in results
        )

    def test_partial_match(self, history_app, cleanup_tag) -> None:
        """Test that searching with partial text returns matching results."""
        # Create a test person
        person = PersonInput(
            wikidata_id="Q789012",
            wikidata_url="https://www.wikidata.org/wiki/Q789012",
            name="Alexander von Humboldt",
        )
        created_person = history_app.create_person(person=person)
        cleanup_tag(created_person.id)

        # Search with partial name
        results = history_app.fuzzy_search_stories("Humbol")

        # Verify results
        assert len(results) > 0
        assert any("humboldt" in result["name"].lower() for result in results)


class TestCalculateStoryOrderRange:
    def test_empty_range(self, history_app, mocker) -> None:
        """Test that an empty range returns immediately without processing."""
        # Mock the repository to return an empty list
        mock_get_tag_ids = mocker.patch.object(
            history_app._repository, "get_tag_ids_with_null_orders", return_value=[]
        )

        # Call the method with default arguments
        history_app.calculate_story_order_range()

        # Assert repository was called with correct arguments - now including session
        assert mock_get_tag_ids.call_count == 1
        call_args = mock_get_tag_ids.call_args
        assert call_args[1]["start_tag_id"] is None
        assert call_args[1]["stop_tag_id"] is None
        assert "session" in call_args[1]

    def test_single_worker(self, history_app, mocker) -> None:
        """Test that single worker mode processes tags correctly."""
        # Create test UUIDs using valid UUIDs
        test_uuids = [
            UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        ]

        # Mock the repository methods
        mock_get_tag_ids = mocker.patch.object(
            history_app._repository,
            "get_tag_ids_with_null_orders",
            return_value=test_uuids,
        )
        mock_update_null_story_order = mocker.patch.object(
            history_app._repository, "update_null_story_order"
        )

        # Call the method with single worker
        history_app.calculate_story_order_range(num_workers=1)

        # Assert get_tag_ids_with_null_orders was called
        mock_get_tag_ids.assert_called_once()

        # Assert update_null_story_order was called for each tag ID
        assert mock_update_null_story_order.call_count == len(test_uuids)

    def test_multiple_workers(self, history_app, mocker) -> None:
        """Test that multiple worker mode processes tags in parallel."""
        # Create test UUIDs using valid UUIDs
        test_uuids = [
            UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b813-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b814-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b815-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b816-9dad-11d1-80b4-00c04fd430c8"),
            UUID("6ba7b817-9dad-11d1-80b4-00c04fd430c8"),
        ]

        # Mock the repository methods
        mock_get_tag_ids = mocker.patch.object(
            history_app._repository,
            "get_tag_ids_with_null_orders",
            return_value=test_uuids,
        )

        # Mock the calculate_story_order method to track calls and simulate work
        original_method = history_app.calculate_story_order
        call_count = {"value": 0}
        processed_ids = []

        def mock_calculate_story_order(tag_ids, session=None):
            call_count["value"] += 1
            processed_ids.extend(tag_ids)
            time.sleep(0.1)  # Simulate some work
            return original_method(tag_ids, session)

        mocker.patch.object(
            history_app, "calculate_story_order", side_effect=mock_calculate_story_order
        )

        # Call the method with multiple workers
        num_workers = 3
        history_app.calculate_story_order_range(num_workers=num_workers)

        # Assert get_tag_ids_with_null_orders was called
        mock_get_tag_ids.assert_called_once()

        # Assert calculate_story_order was called the expected number of times (once per chunk)
        assert call_count["value"] == min(num_workers, len(test_uuids))

        # Assert all IDs were processed
        assert set(processed_ids) == set(test_uuids)

    def test_with_range_bounds(self, history_app, mocker) -> None:
        """Test that range bounds are correctly passed to the repository."""
        # Create test UUIDs for range bounds using valid UUIDs
        start_id = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
        stop_id = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

        # Mock the repository methods
        mock_get_tag_ids = mocker.patch.object(
            history_app._repository, "get_tag_ids_with_null_orders", return_value=[]
        )

        # Call the method with range bounds
        history_app.calculate_story_order_range(
            start_tag_id=start_id, stop_tag_id=stop_id, num_workers=2
        )

        # Assert get_tag_ids_with_null_orders was called with correct arguments - now including session
        assert mock_get_tag_ids.call_count == 1
        call_args = mock_get_tag_ids.call_args
        assert call_args[1]["start_tag_id"] == start_id
        assert call_args[1]["stop_tag_id"] == stop_id
        assert "session" in call_args[1]

    def test_rebalance_error_handling(self, history_app, mocker) -> None:
        """Test that RebalanceError is properly handled in threads."""
        from the_history_atlas.apps.history.repository import RebalanceError

        # Create test UUIDs using valid UUIDs
        test_uuids = [
            UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        ]

        # Mock the repository methods
        mock_get_tag_ids = mocker.patch.object(
            history_app._repository,
            "get_tag_ids_with_null_orders",
            return_value=test_uuids,
        )

        # Create mock functions with proper behavior - now expecting session parameter
        update_calls = 0
        rebalance_calls = 0

        def mock_update(tag_id, session):
            nonlocal update_calls
            update_calls += 1
            # First tag call will throw an error, but second call (after rebalance) will succeed
            if tag_id == test_uuids[0] and update_calls == 1:
                raise RebalanceError()
            return None

        def mock_rebalance(tag_id, session):
            nonlocal rebalance_calls
            rebalance_calls += 1
            return {}

        # Install the mocks
        mock_update_null_story_order = mocker.patch.object(
            history_app._repository, "update_null_story_order", side_effect=mock_update
        )

        mock_rebalance_story_order = mocker.patch.object(
            history_app._repository, "rebalance_story_order", side_effect=mock_rebalance
        )

        # Call the method
        history_app.calculate_story_order_range(num_workers=1)

        # Verify expected behavior - we now only have 3 calls total because we don't retry after rebalance
        assert update_calls == len(test_uuids)
        assert rebalance_calls == 1

    def test_integration(self, history_app, cleanup_tag) -> None:
        """Integration test that creates actual records and processes them."""
        from datetime import datetime, timezone
        from the_history_atlas.apps.domain.core import (
            TimeInput,
            PlaceInput,
            PersonInput,
            TagInstance,
            CitationInput,
        )
        import uuid
        from typing import List

        cleanup_ids = []

        try:
            # Create test data
            # First create a person
            person = PersonInput(
                wikidata_id=f"Q{uuid.uuid4().hex[:8]}",  # Generate unique wikidata ID
                wikidata_url=f"https://www.wikidata.org/wiki/Q{uuid.uuid4().hex[:8]}",
                name="Test Person",
                description="Test person for integration test",
            )
            created_person = history_app.create_person(person=person)
            cleanup_ids.append(created_person.id)

            # Create two times with different dates
            time1 = TimeInput(
                datetime=datetime(2020, 1, 1, tzinfo=timezone.utc),
                calendar_model="gregorian",
                precision=11,  # DAY precision
                name="January 1, 2020",
                wikidata_id=None,
                wikidata_url=None,
                date=str(datetime(2020, 1, 1, tzinfo=timezone.utc)),
                description="Test time 1",
            )
            created_time1 = history_app.create_time(time=time1)
            cleanup_ids.append(created_time1.id)

            time2 = TimeInput(
                datetime=datetime(2020, 1, 2, tzinfo=timezone.utc),
                calendar_model="gregorian",
                precision=11,  # DAY precision
                name="January 2, 2020",
                wikidata_id=None,
                wikidata_url=None,
                date=str(datetime(2020, 1, 2, tzinfo=timezone.utc)),
                description="Test time 2",
            )
            created_time2 = history_app.create_time(time=time2)
            cleanup_ids.append(created_time2.id)

            # Create a place
            place = PlaceInput(
                wikidata_id=f"Q{uuid.uuid4().hex[:8]}",
                wikidata_url=f"https://www.wikidata.org/wiki/Q{uuid.uuid4().hex[:8]}",
                name="Test Place",
                latitude=0.0,
                longitude=0.0,
                description="Test place for integration test",
            )
            created_place = history_app.create_place(place=place)
            cleanup_ids.append(created_place.id)

            # Create events that reference these entities but with NULL story_order values
            # We'll create events by using the create_wikidata_event method

            # Setup common citation data
            citation = CitationInput(
                wikidata_item_id="Q12345",
                wikidata_item_title="Test Item",
                wikidata_item_url="https://www.wikidata.org/wiki/Q12345",
                access_date="2023-01-01",
            )

            # Create two events with the person and different times
            tags1: List[TagInstance] = [
                TagInstance(
                    id=created_person.id, start_char=0, stop_char=10, name="Test Person"
                ),
                TagInstance(
                    id=created_time1.id,
                    start_char=15,
                    stop_char=25,
                    name="January 1, 2020",
                ),
                TagInstance(
                    id=created_place.id, start_char=30, stop_char=40, name="Test Place"
                ),
            ]

            event1_id = history_app.create_wikidata_event(
                text="Test Person went to Test Place on January 1, 2020",
                tags=tags1,
                citation=citation,
                after=[],
            )

            tags2: List[TagInstance] = [
                TagInstance(
                    id=created_person.id, start_char=0, stop_char=10, name="Test Person"
                ),
                TagInstance(
                    id=created_time2.id,
                    start_char=15,
                    stop_char=25,
                    name="January 2, 2020",
                ),
                TagInstance(
                    id=created_place.id, start_char=30, stop_char=40, name="Test Place"
                ),
            ]

            event2_id = history_app.create_wikidata_event(
                text="Test Person left Test Place on January 2, 2020",
                tags=tags2,
                citation=citation,
                after=[],
            )

            # Now the person's story should have NULL story_order values
            # Process the story order
            history_app.calculate_story_order_range(num_workers=2)

            # Check if the story orders were set correctly by retrieving the story
            story = history_app.get_story_list(
                event_id=event1_id, story_id=created_person.id, direction=None
            )

            # Verify there are events in the story
            assert len(story.events) > 0

            # Check that events are in chronological order
            if len(story.events) >= 2:
                event_dates = [event.date.datetime for event in story.events]
                assert event_dates == sorted(event_dates)

        finally:
            # Clean up all created tags
            for tag_id in cleanup_ids:
                cleanup_tag(tag_id)
