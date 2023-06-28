import pytest
from ariadne import graphql_sync, graphql
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.conftest import redact_values
from the_history_atlas.apps.accounts.encryption import encrypt


def test_login(schema, context_value):
    query = """
    mutation {
        Login(username: "admin1", password: "super_secure_password") {
            token
            success
        }
    }
    """

    success, data = graphql_sync(
        data={
            "query": query,
        },
        schema=schema,
        context_value=context_value,
    )
    assert success is True
    assert data["data"]["Login"]["success"] is True
    assert isinstance(data["data"]["Login"]["token"], str)

    # this test updates the login timestamp, but isn't worth overwriting right now


def test_add_user(schema, context_value, active_admin_token, cleanup_test_add_user):
    query = """
    mutation AddUserMutation($token: String!, $user_details: NewUserDetailsInput!){
        AddUser(
            token: $token
            user_details: $user_details
        ) {
            token
            user_details {
                f_name
                l_name
                username
                email
                last_login
            }
        }
    }
    """

    user_details = {
        "f_name": "test-name-1",
        "l_name": "test-name-2",
        "username": "t123",
        "password": "xyz",
        "email": "xyz@123.com",
    }

    success, data = graphql_sync(
        data={
            "query": query,
            "variables": {"token": active_admin_token, "user_details": user_details},
        },
        schema=schema,
        context_value=context_value,
    )
    assert success is True
    stripped_data = redact_values(data=data, keys={"token", "last_login"})
    assert stripped_data == {
        "data": {
            "AddUser": {
                "token": "<REDACTED>",
                "user_details": {
                    "f_name": "test-name-1",
                    "l_name": "test-name-2",
                    "username": "t123",
                    "email": "xyz@123.com",
                    "last_login": "<REDACTED>",
                },
            }
        }
    }


@pytest.fixture
def cleanup_test_add_user(engine):
    yield
    sql = text("DELETE from users WHERE users.username = 't123';")
    with engine.connect() as conn:
        conn.execute(sql)
        conn.commit()


def test_update_user(
    schema, context_value, cleanup_test_update_user, active_admin_token
):
    username, password = cleanup_test_update_user
    query = """
    mutation UpdateUserMutation($token: String!, $user_details: UpdateUserDetailsInput!, $credentials: CredentialsInput!){
        UpdateUser(token: $token, user_details: $user_details, credentials: $credentials){
            token
            user_details {
                f_name
                l_name
                username
                email
                last_login
            }
        }
    }
    """
    update_dict = {
        "f_name": "joe",
        "l_name": "jones",
        "email": "a@b.c",
        "password": "zzz",
        "username": "joe",
    }
    credentials = {"username": username, "password": password}

    success, data = graphql_sync(
        data={
            "query": query,
            "variables": {
                "token": active_admin_token,
                "user_details": update_dict,
                "credentials": credentials,
            },
        },
        schema=schema,
        context_value=context_value,
    )
    assert success is True
    stripped_data = redact_values(data=data, keys={"token", "last_login"})
    assert stripped_data == {
        "data": {
            "UpdateUser": {
                "token": "<REDACTED>",
                "user_details": {
                    "email": "a@b.c",
                    "f_name": "joe",
                    "l_name": "jones",
                    "last_login": "<REDACTED>",
                    "username": "joe",
                },
            }
        }
    }


@pytest.fixture
def cleanup_test_update_user(engine) -> tuple[str, str]:
    id = "324b5f9e-2a5d-41e5-92c0-e333d9c95247"
    username = "t-user"
    password = "t-password"
    encrypted_password = encrypt(password).decode()
    sql = text(
        f"insert into users values ('{id}', 'a', 'b', 'c', '{username}', '{encrypted_password}', 'admin', '2023-06-27 16:56:11.277843', false, true);"
    )
    try:
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
    except IntegrityError:
        pass
    yield username, password
    sql = text(f"DELETE from users WHERE users.id = '{id}';")
    with engine.connect() as conn:
        conn.execute(sql)
        conn.commit()


def test_deactivate_account(
    schema, context_value, active_admin_token, cleanup_test_deactivate_account
):
    username, _ = cleanup_test_deactivate_account
    query = """
    mutation TestDeactivateAccount($token: String! $username: String!) {
        DeactivateAccount(token: $token, username: $username){
            token
            user_details {
                f_name
                l_name
                username
                email
                last_login
            } 
        }
    }
    """

    success, data = graphql_sync(
        data={
            "query": query,
            "variables": {"token": active_admin_token, "username": username},
        },
        schema=schema,
        context_value=context_value,
    )
    assert success is True
    stripped_data = redact_values(data=data, keys={"token", "last_login"})
    assert stripped_data == {
        "data": {
            "DeactivateAccount": {
                "token": "<REDACTED>",
                "user_details": {
                    "email": "a",
                    "f_name": "b",
                    "l_name": "c",
                    "last_login": "<REDACTED>",
                    "username": "t-user",
                },
            }
        }
    }


@pytest.fixture
def cleanup_test_deactivate_account(engine) -> tuple[str, str]:
    id = "5acbdae6-f362-4299-8198-376dad8abcc3"
    username = "t-user"
    password = "t-password"
    encrypted_password = encrypt(password).decode()
    sql = text(
        f"insert into users values ('{id}', 'a', 'b', 'c', '{username}', '{encrypted_password}', 'admin', '2023-06-27 16:56:11.277843', false, true);"
    )
    try:
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
    except IntegrityError:
        pass  # this test finished without cleaning up - let it run
    yield username, password
    sql = text(f"DELETE from users WHERE users.id = '{id}';")
    with engine.connect() as conn:
        conn.execute(sql)
        conn.commit()


def test_confirm_account(
    schema,
    context_value,
    cleanup_test_confirm_account,
    unconfirmed_user_token,
    engine,
    unconfirmed_user_id,
):
    query = """
    mutation TestConfirmAccount($token: String!){
        ConfirmAccount(token: $token) {
            token
            user_details {
                f_name
                l_name
                username
                email
                last_login
            } 
        }
    }
    """

    success, data = graphql_sync(
        data={"query": query, "variables": {"token": unconfirmed_user_token}},
        schema=schema,
        context_value=context_value,
    )
    assert success is True
    stripped_data = redact_values(data=data, keys={"token", "last_login"})
    assert stripped_data == {
        "data": {
            "ConfirmAccount": {
                "token": "<REDACTED>",
                "user_details": {
                    "email": "another_test_email@thehistoryatlas.org",
                    "f_name": "freethrow",
                    "l_name": "shooter",
                    "last_login": "<REDACTED>",
                    "username": "swoop",
                },
            }
        }
    }
    with engine.connect() as conn:
        sql = text(
            f"select users.confirmed from users where users.id = '{unconfirmed_user_id}'"
        )
        is_confirmed = conn.execute(sql).scalar()
        assert is_confirmed is True


@pytest.fixture
def cleanup_test_confirm_account(engine, unconfirmed_user_id) -> None:

    sql = text(
        f"update users set confirmed=false where users.id = '{unconfirmed_user_id}'"
    )
    try:
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()

    except IntegrityError:
        pass  # this test finished without cleaning up - let it run
    yield

    with engine.connect() as conn:
        conn.execute(sql)  # same sql statement
        conn.commit()


@pytest.mark.asyncio
async def test_publish_citation(
    schema, context_value, cleanup_test_publish_citation, active_admin_token
):
    query = """
    mutation TestPublishCitation($annotation: AnnotateCitationInput!) {
        PublishNewCitation(Annotation: $annotation) {
            success
            message
            token
        }
    }
    """

    variables = {
        "annotation": {
            "citation": "test",
            "citationId": "427c7ff3-136b-4cfb-92e0-cb07602cd106",
            "meta": {
                "author": "some",
                "pageNum": 55,
                "pubDate": "date",
                "publisher": "publisher",
                "title": "title here",
            },
            "summary": "some text",
            "summaryTags": [
                {
                    "name": "test person",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "PERSON",
                },
                {
                    "geoshape": None,
                    "latitude": 5.32423,
                    "longitude": 5.4322,
                    "name": "test place",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "PLACE",
                },
                {
                    "name": "test time",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "TIME",
                },
            ],
            "token": active_admin_token,
        }
    }

    success, data = await graphql(
        data={"query": query, "variables": variables},
        schema=schema,
        context_value=context_value,
    )
    assert success is True
    stripped_data = redact_values(data=data, keys={"token", "last_login"})
    assert stripped_data == {
        "data": {
            "PublishNewCitation": {
                "message": None,
                "success": True,
                "token": "<REDACTED>",
            }
        }
    }


@pytest.fixture
def cleanup_test_publish_citation(engine) -> tuple[str, str]:
    # setup, if needed

    yield

    with engine.connect() as conn:
        sql = text(
            "delete from guids where guids.value = '427c7ff3-136b-4cfb-92e0-cb07602cd106';"
        )
        conn.execute(sql)
        sql = text(
            """delete from citation_hashes where citation_hashes."GUID" = '427c7ff3-136b-4cfb-92e0-cb07602cd106';"""
        )
        conn.execute(sql)
        sql = text("""delete from events;""")
        conn.execute(sql)
        conn.commit()
