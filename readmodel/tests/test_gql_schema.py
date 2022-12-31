from unittest.mock import Mock

import pytest

from abstract_domain_model.models.readmodel import DefaultEntity
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


@pytest.mark.asyncio
async def test_query_default_entity():

    default_entity = DefaultEntity(
        id="c0484f0e-3ddf-44bd-9ed6-7ed4acf242f2",
        type="PERSON",
        name="Johann Sebastian Bach",
    )

    api = GQLApi(default_entity_handler=Mock(return_value=default_entity))

    query = """
        query TestStatus {
            defaultEntity {
                id
                type
                name
            }
        }
    """

    result = await api.get_schema().execute(
        query,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["defaultEntity"] == {
        "id": default_entity.id,
        "type": default_entity.type,
        "name": default_entity.name,
    }
