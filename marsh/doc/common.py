from typing import (
    Any,
    Iterable,
    Sequence,
    Type,
    Union,
    cast,
)

import marsh


UnmarshalDocType = Union[
    Type[Any],
    marsh.schema.UnmarshalSchema,
    marsh.schema.UnmarshalSchema.Doc,
]


RegisteredSchemasType = Union[
    Type[marsh.schema.core.Schema],
    marsh.schema.core.SchemaRegistry,
    Iterable[Type[marsh.schema.core.Schema]],
]


def get_unmarshal_doc(
    source: UnmarshalDocType,
    depth: int,
) -> marsh.schema.UnmarshalSchema.Doc:
    try:
        if isinstance(source, marsh.schema.UnmarshalSchema.Doc):
            return source
    except TypeError:
        pass
    try:
        if isinstance(source, marsh.schema.UnmarshalSchema):
            return source.doc(depth)
    except TypeError:
        pass
    return marsh.schema.UnmarshalSchema(source).doc(depth)


def get_registered_schemas(
    source: RegisteredSchemasType,
) -> Sequence[Type[marsh.schema.core.Schema]]:
    try:
        if issubclass(source, marsh.schema.core.Schema):  # type: ignore
            return tuple(
                cast(
                    Type[marsh.schema.core.Schema],
                    source,
                ).registry,
            )
    except TypeError:
        pass
    try:
        if isinstance(source, marsh.schema.core.SchemaRegistry):
            return tuple(source)
    except TypeError:
        pass
    return tuple(
        cast(
            Iterable[Type[marsh.schema.core.Schema]],
            source,
        ),
    )
