from unittest.mock import MagicMock

import pytest

from the_history_atlas.apps.writemodel.state_manager.database import Database


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def existing_summary_id():
    return "b73eb1f4-756a-445c-addb-c56ac2bb1fe5"


@pytest.fixture
def existing_meta_id():
    return "f7bb4de9-1b5b-4b89-a955-afd32ed70cfd"


@pytest.fixture
def existing_time_id():
    return "728ac243-48d4-453c-a120-56d9e0176c7c"


@pytest.fixture
def existing_person_id():
    return "cb08564a-8021-4491-ac7b-b8684d9b9297"


@pytest.fixture
def existing_place_id():
    return "a54d1a83-0685-4f1b-bf4e-abaae4e159a5"
