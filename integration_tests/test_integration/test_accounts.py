import json

import requests


def test_login(gql_api_url, username, password):
    login_mutation = """
    mutation Login($username: String!, $password: String!) {
      Login(username: $username, password: $password) {
        success
        token
      }
    }
    """

    login_request = {
        "query": login_mutation,
        "variables": {"username": username, "password": password},
    }

    res = requests.post(
        url=gql_api_url,
        data=json.dumps(login_request),
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 200
    json_res = res.json()
    assert json_res["data"]["Login"]["success"] is True
    assert isinstance(json_res["data"]["Login"]["token"], str)
