import pytest
from uuid import uuid4

from the_history_atlas.apps.accounts.api_keys import ApiKeyRepository


@pytest.fixture
def api_key_repo(engine):
    return ApiKeyRepository(engine=engine)


@pytest.fixture
def user_in_db(engine, user_details):
    """Insert a user into the database for API key tests."""
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    from the_history_atlas.apps.accounts.encryption import encrypt

    with Session(engine, future=True) as session:
        session.execute(
            text(
                "INSERT INTO users (id, email, f_name, l_name, username, password, type, confirmed, deactivated) "
                "VALUES (:id, :email, :f_name, :l_name, :username, :password, :type, true, false)"
            ),
            {
                "id": user_details["id"],
                "email": user_details["email"],
                "f_name": user_details["f_name"],
                "l_name": user_details["l_name"],
                "username": user_details["username"],
                "password": encrypt(user_details["password"]).decode(),
                "type": "contrib",
            },
        )
        session.commit()
    return user_details["id"]


class TestCreateApiKey:
    def test_returns_raw_key(self, api_key_repo, user_in_db):
        raw_key, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        assert isinstance(raw_key, str)
        assert len(raw_key) > 0

    def test_returns_record_with_id(self, api_key_repo, user_in_db):
        _, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        assert record["id"] is not None

    def test_returns_record_with_name(self, api_key_repo, user_in_db):
        _, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="my-key"
        )

        assert record["name"] == "my-key"

    def test_returns_record_with_user_id(self, api_key_repo, user_in_db):
        _, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        assert record["user_id"] == user_in_db

    def test_returns_record_with_created_at(self, api_key_repo, user_in_db):
        _, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        assert record["created_at"] is not None


class TestValidateApiKey:
    def test_valid_key_returns_user_id(self, api_key_repo, user_in_db):
        raw_key, _ = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        result = api_key_repo.validate_api_key(raw_key)

        assert result == user_in_db

    def test_invalid_key_returns_none(self, api_key_repo):
        result = api_key_repo.validate_api_key("not-a-real-key")

        assert result is None

    def test_deactivated_key_returns_none(self, api_key_repo, user_in_db):
        raw_key, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )
        api_key_repo.deactivate_api_key(
            key_id=record["id"], user_id=user_in_db
        )

        result = api_key_repo.validate_api_key(raw_key)

        assert result is None

    def test_updates_last_used_at(self, api_key_repo, user_in_db, engine):
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        raw_key, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )
        api_key_repo.validate_api_key(raw_key)

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT last_used_at FROM api_keys WHERE id = :id"),
                {"id": record["id"]},
            ).one()

        assert row.last_used_at is not None


class TestDeactivateApiKey:
    def test_returns_true_when_found(self, api_key_repo, user_in_db):
        _, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        result = api_key_repo.deactivate_api_key(
            key_id=record["id"], user_id=user_in_db
        )

        assert result is True

    def test_returns_false_for_nonexistent_key(self, api_key_repo, user_in_db):
        result = api_key_repo.deactivate_api_key(
            key_id=uuid4(), user_id=user_in_db
        )

        assert result is False

    def test_returns_false_for_wrong_user(self, api_key_repo, user_in_db):
        _, record = api_key_repo.create_api_key(
            user_id=user_in_db, name="test-key"
        )

        result = api_key_repo.deactivate_api_key(
            key_id=record["id"], user_id="wrong-user-id"
        )

        assert result is False
