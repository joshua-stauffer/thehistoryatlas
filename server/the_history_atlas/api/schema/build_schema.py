import os

from ariadne import make_executable_schema, load_schema_from_path, executable_schema

from the_history_atlas.api.schema.mutation import build_mutation
from the_history_atlas.api.schema.query import build_query


def build_schema() -> executable_schema:
    types_path = os.path.abspath("server/the_history_atlas/api/types/")
    type_defs = load_schema_from_path(path=types_path)

    query = build_query()
    mutation = build_mutation()
    schema = make_executable_schema(type_defs, query, mutation)
    return schema
