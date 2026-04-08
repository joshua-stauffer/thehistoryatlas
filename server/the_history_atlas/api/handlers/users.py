from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

import the_history_atlas.api.types.user as api_types
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.models.accounts import Credentials


def login_handler(
    form_data: OAuth2PasswordRequestForm, apps: AppManager
) -> api_types.LoginResponse:
    login_result = apps.accounts_app.login(
        data=Credentials(username=form_data.username, password=form_data.password)
    )
    if not login_result.success:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_types.LoginResponse(access_token=login_result.token, token_type="bearer")
