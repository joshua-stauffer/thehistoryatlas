from unittest.mock import Mock

import pytest

from writemodel.api.schema import get_schema


def test_query_handles_query_status():

    app = Mock()
    schema = get_schema(app)

    query = """
        query TestStatus {
            status
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["status"] == "ok"
