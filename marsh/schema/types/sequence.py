"""Sequence schema support.

For generic sequence-matching schemas we set the priority lower
than schemas of normal types as a ducktyped match should be
the last resort.
"""
import collections.abc
from typing import (
    Any,
    Sequence,
    TypeVar,
)

import marsh


_T = TypeVar('_T', bound=Sequence)


@marsh.schema.register
class SequenceUnmarshalSchema(marsh.schema.template.SequenceUnmarshalSchema[_T]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.value_schema = marsh.schema.UnmarshalSchema(
            marsh.utils.inspect_sequence_type(self.value),
        )

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~collections.abc.Sequence`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals a sequence type from a sequence input. '
            'Should work for all sequence types. If the sequence '
            'type is one of the abstract sequence classes in '
            '`collections.abc` then a suitable replacement type '
            'is implicitly used instead.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return (
                marsh.utils.is_sequence_type(value)
                and issubclass(
                    marsh.utils.get_type(value),
                    collections.abc.Sequence,
                )
            )
        except Exception:
            return False

    def construct(
        self,
        value: Sequence,
    ) -> _T:
        value_type = marsh.utils.get_type(self.value)
        if value_type is collections.abc.Sequence:
            return tuple(value)  # type: ignore
        if value_type is collections.abc.MutableSequence:
            return list(value)  # type: ignore
        return super().construct(value)
