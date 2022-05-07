from typing import (
    Any,
    get_args,
    get_origin,
)

import marsh
from . import sequence


@marsh.schema.register
class SetUnmarshalSchema(sequence.SequenceUnmarshalSchema):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        type_ = Any
        if (_args := get_args(self.value)):
            type_ = _args[0]
        self.value_schema = marsh.schema.UnmarshalSchema(type_)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return (
                get_origin(value) is set
                or issubclass(value, set)
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`set`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals a sequence input into '
            'a set. Any duplicate values will be '
            'discarded.'
        )
