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


@marsh.schema.register(priority=-5)
class SequenceMarshalSchema(marsh.schema.MarshalSchema):

    value: Sequence

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_sequence(value)

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return tuple(
            marsh.marshal(self.value[i])
            for i in range(len(self.value))
        )


@marsh.schema.register
class AbcSequenceMarshalSchema(SequenceMarshalSchema):

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~collections.abc.Sequence`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals any sequence into a tuple containing '
            'the marshaled value of each item in the sequence.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return (
                isinstance(value, collections.abc.Sequence)
                and marsh.utils.is_sequence(value)  # make sure not AnyStr
            )
        except Exception:
            return False


@marsh.schema.register(priority=-5)
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

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_sequence_type(value)

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


@marsh.schema.register
class AbcSequenceUnmarshalSchema(SequenceUnmarshalSchema):

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
                issubclass(value, collections.abc.Sequence)
                and marsh.utils.is_sequence_type(value)  # make sure not AnyStr
            )
        except Exception:
            return False
