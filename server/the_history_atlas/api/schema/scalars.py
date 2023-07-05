from uuid import UUID

from ariadne import ScalarType


def build_uuid() -> ScalarType:

    uuid_scalar = ScalarType("UUID")

    @uuid_scalar.serializer
    def serialize_uuid(value):
        return UUID(value)

    @uuid_scalar.value_parser
    def parse_uuid_value(value):
        if value:
            return str(value)

    @uuid_scalar.literal_parser
    def parse_datetime_literal(ast):
        value = str(ast.value)
        return str(value)

    return uuid_scalar
