from graphql import GraphQLSchema

from the_history_atlas.api.schema import build_schema


def test_build_schema():

    schema = build_schema()
    assert isinstance(schema, GraphQLSchema)
