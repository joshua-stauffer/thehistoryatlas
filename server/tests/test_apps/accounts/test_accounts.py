import pytest
from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.domain.models.accounts import (
    Credentials,
    UserDetails,
    GetUserPayload,
)
from the_history_atlas.apps.domain.models.accounts.add_user import AddUserPayload
from the_history_atlas.apps.domain.models.accounts.confirm_account import (
    ConfirmAccountPayload,
)
from the_history_atlas.apps.domain.models.accounts.deactivate_account import (
    DeactivateAccountPayload,
)
from the_history_atlas.apps.domain.models.accounts.is_username_unique import (
    IsUsernameUniquePayload,
)
from the_history_atlas.apps.domain.models.accounts.update_user import UpdateUserPayload


@pytest.fixture
def accounts(accounts_loaded_db, config):
    accounts = Accounts(config=config, database_client=accounts_loaded_db._engine)
    return accounts


def test_login(accounts, user_details):
    input = Credentials(
        username=user_details["username"], password=user_details["password"]
    )
    output = accounts.login(data=input)
    assert output.success is True
    assert isinstance(output.token, str)


def test_add_user(accounts, active_admin_token, other_user_details):
    input = AddUserPayload(
        token=active_admin_token,
        user_details=other_user_details,
    )
    output = accounts.add_user(data=input)

    assert output.token == active_admin_token
    assert isinstance(output.user_details, UserDetails)


def test_get_user(accounts, active_token):
    input = GetUserPayload(token=active_token)
    output = accounts.get_user(data=input)

    assert output.token == active_token
    assert isinstance(output.user_details, UserDetails)


def test_update_user(accounts, active_token):
    f_name = "sebastian"
    input = UpdateUserPayload(
        token=active_token, user_details={"f_name": f_name}, credentials=None
    )

    output = accounts.update_user(data=input)

    assert output.token == active_token
    assert isinstance(output.user_details, UserDetails)
    assert output.user_details.f_name == f_name


def test_is_username_unique(accounts):
    username = "ludovico"
    input = IsUsernameUniquePayload(username=username)
    output = accounts.is_username_unique(data=input)
    assert output.username == username
    assert output.is_unique is True


def test_deactivate_account(accounts, active_admin_token, user_id, user_details):
    input = DeactivateAccountPayload(
        token=active_admin_token, username=user_details["username"]
    )
    output = accounts.deactivate_account(data=input)
    assert output.token == active_admin_token
    assert isinstance(output.user_details, UserDetails)


def test_confirm_account(accounts, unconfirmed_user_token):
    output = accounts.confirm_account(token=unconfirmed_user_token)
    # emailed tokens should be changed immediately
    assert output.token != unconfirmed_user_token
    assert isinstance(output.user_details, UserDetails)
