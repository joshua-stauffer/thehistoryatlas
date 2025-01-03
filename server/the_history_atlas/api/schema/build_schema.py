from ariadne import make_executable_schema, load_schema_from_path, executable_schema

from the_history_atlas.api.schema.mutation import build_mutation
from the_history_atlas.api.schema.query import build_query
from the_history_atlas import ROOT_DIR
from the_history_atlas.api.schema.scalars import build_uuid


def build_schema() -> executable_schema:
    types_path = f"{ROOT_DIR}/api/types"
    type_defs = load_schema_from_path(path=types_path)

    query = build_query()
    mutation = build_mutation()
    uuid_scalar = build_uuid()
    try:
        schema = make_executable_schema(type_defs, query, mutation, uuid_scalar)
    except Exception as exc:
        print(exc)  # don't swallow schema errors
        raise Exception from exc
    return schema
