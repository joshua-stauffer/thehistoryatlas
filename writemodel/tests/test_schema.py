from unittest.mock import Mock

from abstract_domain_model.models.commands import CommandSuccess
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


def test_mutation_add_new_citation():

    app = Mock()
    app.handle_command = Mock()
    app.handle_command.return_value = CommandSuccess()

    schema = get_schema(app)

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
            "citationGuid": "427c7ff3-136b-4cfb-92e0-cb07602cd106",
            "meta": {
                "GUID": "3f015823-4c8d-47b5-b591-c34ff70a19eb",
                "author": "some",
                "pageNum": 55,
                "pubDate": "date",
                "publisher": "publisher",
                "title": "title here",
            },
            "summary": "some text",
            "summaryGuid": "f72c39b4-b4bc-499e-93ec-ca33b81a809e",
            "summaryTags": [
                {
                    "GUID": "84ca9c91-df87-4e4e-a4f6-bdeb10dbd557",
                    "name": "test person",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "PERSON",
                },
                {
                    "GUID": "84ca9c91-df87-4e4e-a4f6-bdeb10dbd557",
                    "geoshape": None,
                    "latitude": 5.32423,
                    "longitude": 5.4322,
                    "name": "test place",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "PLACE",
                },
                {
                    "GUID": "84ca9c91-df87-4e4e-a4f6-bdeb10dbd557",
                    "name": "test time",
                    "startChar": 5,
                    "stopChar": 7,
                    "type": "TIME",
                },
            ],
        }
    }

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors is None
    assert result.data["PublishNewCitation"]["success"] is True
    assert result.data["PublishNewCitation"]["message"] is None
