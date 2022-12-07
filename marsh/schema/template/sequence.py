from typing import (
    Sequence,
    TypeVar,
)

import marsh
from .. import UnmarshalSchema


_T = TypeVar('_T')


class SequenceUnmarshalSchema(UnmarshalSchema[_T]):
    """A schema for a dynamic sequence of values."""

    value_schema: UnmarshalSchema
    """The schema for the value type."""

    def __str__(
        self,
    ) -> str:
        return f'[{self.value_schema}, ...]'

    def __repr__(
        self,
    ) -> str:
        return (
            f'{super().__repr__()[:-1]}, '
            f'value_schema={repr(self.value_schema)})'
        )

    def doc_field_type(
        self,
    ) -> str:
        return f'[{self.value_schema.doc_field_type()}, ...]'

    def select(
        self,
        path: str,
    ) -> UnmarshalSchema:
        return self.value_schema.select(path)

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            return self.construct(())
        if not marsh.utils.is_sequence(element):
            raise marsh.errors.UnmarshalError(
                (
                    'expected sequence element, got: '
                    f'{marsh.utils.get_type_name(element)}'
                ),
                element=element,
                type=self.value,
            )
        prepared_input = []
        for i, item in enumerate(element):
            with marsh.errors.prepend(i):
                casted_item = self.value_schema.unmarshal(item)
            prepared_input.append(casted_item)
        try:
            return self.construct(prepared_input)
        except marsh.errors.MarshError:
            raise
        except Exception as err:
            raise marsh.errors.UnmarshalError(
                (
                    f'failed to construct sequence: {err}'
                ),
                element=element,
                type=self.value,
            ) from err

    def construct(
        self,
        value: Sequence,
    ) -> _T:
        """Build an instance of the type from unmarshaled values.

        Arguments:
            value: The unmarshaled values.

        Returns:
            An instance of the type.
        """
        return marsh.utils.get_type(self.value)(value)
