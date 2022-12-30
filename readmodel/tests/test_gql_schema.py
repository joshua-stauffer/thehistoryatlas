import pytest

from readmodel.api import GQLApi


@pytest.mark.asyncio
async def test_query_handles_query_status():

    api = GQLApi()

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
