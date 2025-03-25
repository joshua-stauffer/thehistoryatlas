from the_history_atlas.apps.domain.core import PersonInput
from the_history_atlas.apps.domain.models.history.tables.time import TimePrecision


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
