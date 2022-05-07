from typing import (
    Any,
    get_args,
)

import marsh
from . import sequence


@marsh.schema.register(lower_priority=sequence.SequenceUnmarshalSchema)
class TupleUnmarshalSchema(marsh.schema.template.StructuredUnmarshalSchema[tuple]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.schemas = {
            str(i): marsh.schema.UnmarshalSchema(type_)
            for i, type_ in enumerate(
                arg for arg in get_args(self.value)
                if arg != ()  # empty tuple type
            )
        }

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_fixed_size_tuple_type(value)

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`tuple`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals a sequence input into a fixed size '
            'tuple. The input sequence must contain the same '
            'number of elements as the tuple type specifies.'
        )

    def doc_field_type(
        self,
    ) -> str:
        content = ', '.join(
            schema.doc_field_type()
            for schema
            in self.schemas.values()
        )
        return f'[{content}]'

    def construct(
        self,
        *args,
        **kwargs,
    ) -> tuple:
        return tuple(args, **kwargs)
