from typing import (
    Mapping,
    TypeVar,
)

import marsh
from .. import UnmarshalSchema


_T = TypeVar('_T')


class MappingUnmarshalSchema(UnmarshalSchema[_T]):
    """A schema for a type with dynamic keys and values."""

    key_schema: UnmarshalSchema
    """The schema for the key type."""

    value_schema: UnmarshalSchema
    """The schema for the value type."""

    def __str__(
        self,
    ) -> str:
        return '{%s: %s, ...}' % (self.key_schema, self.value_schema)

    def __repr__(
        self,
    ) -> str:
        return (
            f'{super().__repr__()[:-1]}, '
            f'key_schema={repr(self.key_schema)}, '
            f'value_schema={repr(self.value_schema)})'
        )

    def select(
        self,
        path: str,
    ) -> UnmarshalSchema:
        return self.value_schema.select(path)

    def doc_field_type(
        self,
    ) -> str:
        return '{%s: %s, ...}' % (
            self.key_schema.doc_field_type(),
            self.value_schema.doc_field_type(),
        )

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            return self.construct({})
        if not marsh.utils.is_mapping(element):
            raise marsh.errors.UnmarshalError(
                (
                    'expected mapping element, got: '
                    f'{marsh.utils.get_type_name(element)}'
                ),
                element=element,
                type=self.value,
            )
        prepared_input = {}
        for key in element.keys():
            with marsh.errors.prepend(key):
                casted_key = self.key_schema.unmarshal(key)
                casted_value = self.value_schema.unmarshal(element[key])
            prepared_input[casted_key] = casted_value
        try:
            return self.construct(prepared_input)
        except marsh.errors.MarshError:
            raise
        except Exception as err:
            raise marsh.errors.UnmarshalError(
                (
                    f'failed to construct mapping: {err}'
                ),
                element=element,
                type=self.value,
            ) from err

    def construct(
        self,
        value: Mapping,
    ) -> _T:
        """Build an instance of the type from unmarshaled keys
        and values.

        Arguments:
            value: The unmarshaled keys and values.

        Returns:
            An instance of the type.
        """
        return marsh.utils.get_type(self.value)(value)
