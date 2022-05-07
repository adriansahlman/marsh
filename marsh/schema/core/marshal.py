from typing import (
    Any,
    ClassVar,
)

import marsh
from . import base


class MarshalSchemaMeta(base.SchemaMeta['MarshalSchema']):

    def __call__(
        cls,  # noqa: B902
        value,
        *args,
        **kwargs,
    ):
        if cls is not MarshalSchema:
            return type(object).__call__(cls, value, *args, **kwargs)
        return cls.registry.match(value).build(value, *args, **kwargs)


class MarshalSchema(base.Schema, metaclass=MarshalSchemaMeta):
    """Marshals its value input into a JSON-like object.

    Arguments:
        value: The value to match/marshal.
    """

    registry: ClassVar[base.SchemaRegistry['MarshalSchema']] = \
        base.SchemaRegistry(error=marsh.errors.MarshalError)

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        """Marshal the value held by this instance
        into a JSON-like object.

        Returns:
            The JSON-like marshaled value.
        """
        raise NotImplementedError


class WrapperMarshalSchema(
    base.WrapperSchema[MarshalSchema],
    MarshalSchema,
):

    def __init__(
        self,
        value: Any,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(value, *args, **kwargs)

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return self.schema.marshal()
