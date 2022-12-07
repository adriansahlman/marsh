from typing import (
    Optional,
    Sequence,
    TypeVar,
)

import marsh
from .. import UnmarshalSchema


_T = TypeVar('_T')


class UnionUnmarshalSchema(UnmarshalSchema[_T]):
    """A schema for a union of types.

    The order of the types is reflected in the
    order of attempted unmarshals. The value of
    the first type that is successfully unmarshaled
    is returned.

    If all types failed to unmarshal an error is raised."""

    schemas: Sequence[UnmarshalSchema]
    """The schemas for the union of types."""

    @property
    def optional_schema(
        self,
    ) -> Optional[UnmarshalSchema]:
        if (
            len(self.schemas) == 2
            and marsh.utils.is_optional(self.value)
        ):
            for schema in self.schemas:
                if schema.value not in (None, type(None)):
                    return schema
        return None

    def __str__(
        self,
    ) -> str:
        return ' | '.join(map(str, self.schemas))

    def __repr__(
        self,
    ) -> str:
        return f'{super().__repr__()[:-1]}, schemas={tuple(map(repr, self.schemas))})'

    def doc_field_type(
        self,
    ) -> str:
        return ' | '.join(schema.doc_field_type() for schema in self.schemas)

    def select(
        self,
        path: str,
    ) -> UnmarshalSchema:
        schema = self.optional_schema
        if schema is not None:
            return schema.select(path)
        if not path:
            return self
        raise marsh.errors.PathError(
            f'{marsh.utils.get_type_name(self.value)}: ambiguous '
            'traversal route (can not traverse union nodes)',
        )

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
        schema = self.optional_schema
        if schema is not None:
            try:
                return schema.unmarshal(element)
            except Exception:
                if (
                    element is None
                    or marsh.utils.is_missing(element)
                ):
                    return None  # type: ignore
                raise
        for schema in self.schemas:
            try:
                return schema.unmarshal(element)
            except Exception:
                pass
        if marsh.utils.is_missing(element):
            raise marsh.errors.MissingValueError(
                type=self.value,
            )
        raise marsh.errors.UnmarshalError(
            'failed to unmarshal element',
            element=element,
            type=self.value,
        )
