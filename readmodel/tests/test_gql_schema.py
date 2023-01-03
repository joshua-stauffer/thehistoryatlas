from dataclasses import asdict
from unittest.mock import Mock

import pytest

from abstract_domain_model.models.readmodel import DefaultEntity, Source
from readmodel.api import GQLApi


@pytest.mark.asyncio
async def test_query_handles_query_status():

    api = GQLApi(default_entity_handler=Mock(), search_sources_handler=Mock())

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

    api = GQLApi(
        default_entity_handler=Mock(return_value=default_entity),
        search_sources_handler=Mock(),
    )

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


@pytest.mark.asyncio
async def test_search_sources():
    search_term = "test-term"
    sources = [
        Source(
            id="a603b235-22bf-4ea7-a718-b0f3a4e45a09",
            title="source 1",
            author="author 1",
            publisher="publisher 1",
            pub_date="1/2/23",
        ),
        Source(
            id="286b73c6-d058-4960-b5d0-6a853b1ce42d",
            title="source 2",
            author="author 2",
            publisher="publisher 2",
            pub_date="1/2/23",
        ),
    ]
    search_sources_handler = Mock(return_value=sources)
    api = GQLApi(
        default_entity_handler=Mock(), search_sources_handler=search_sources_handler
    )

    query = """
        query SearchSources($searchTerm: String!) {
            searchSources(searchTerm: $searchTerm) {
                id
                title
                author
                publisher
                pubDate
            }
        }
    """

    result = await api.get_schema().execute(
        query,
        variable_values={"searchTerm": search_term},
    )

    assert result.errors is None
    search_sources_handler.assert_called_with(search_term)
