from unittest.mock import Mock, AsyncMock

import pytest

from abstract_domain_model.models.commands import CommandSuccess, Command
from writemodel.api.api import GQLApi


@pytest.fixture
def command_handler():
    async def command_handler(message: Command):
        return CommandSuccess()

    return command_handler


@pytest.fixture
def auth_handler():
    return AsyncMock()


@pytest.fixture
def api(command_handler, auth_handler):
    return GQLApi(command_handler=command_handler, auth_handler=auth_handler)


@pytest.mark.asyncio
async def test_query_handles_query_status(api):

    query = """
        query TestStatus {
            status
        }
    """

    result = await api.get_schema().execute(
        query,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["status"] == "OK"


@pytest.mark.asyncio
async def test_mutation_add_new_citation(api, command_handler):

    schema = api.get_schema()

    query = """
    mutation PublishNewCitation($annotation: AnnotateCitationInput!) {
        PublishNewCitation(Annotation: $annotation) {
            success
            message
        }
    }
    """
    variables = {
        "annotation": {
            "citation": "test",
            "citationId": "427c7ff3-136b-4cfb-92e0-cb07602cd106",
            "meta": {
                "id": "3f015823-4c8d-47b5-b591-c34ff70a19eb",
                "author": "some",
                "pageNum": 55,
                "pubDate": "date",
                "publisher": "publisher",
                "title": "title here",
            },
            "summary": "some text",
            "summaryId": "f72c39b4-b4bc-499e-93ec-ca33b81a809e",
            "summaryTags": [
                {
                    "id": "84ca9c91-df87-4e4e-a4f6-bdeb10dbd557",
                    "name": "test person",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "PERSON",
                },
                {
                    "id": "84ca9c91-df87-4e4e-a4f6-bdeb10dbd557",
                    "geoshape": None,
                    "latitude": 5.32423,
                    "longitude": 5.4322,
                    "name": "test place",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "PLACE",
                },
                {
                    "id": "84ca9c91-df87-4e4e-a4f6-bdeb10dbd557",
                    "name": "test time",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "TIME",
                },
            ],
            "token": "test-token-value-here",
        }
    }

    result = await schema.execute(query, variable_values=variables)

    assert result.errors is None
    assert result.data["PublishNewCitation"]["success"] is True
    assert result.data["PublishNewCitation"]["message"] is None
