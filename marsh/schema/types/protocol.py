import collections.abc
import numbers
from typing import (
    Any,
    Iterable,
    Iterator,
)

import marsh


BASE_TYPES = (
    float,
    int,
    bool,
    bytes,
    collections.abc.MutableMapping,
    collections.abc.Mapping,
    collections.abc.MutableSequence,
    collections.abc.Sequence,
    str,
    numbers.Complex,
)


def _match_iter(
    protocol: Any,
) -> Iterator:
    try:
        for type_ in BASE_TYPES:
            if issubclass(type_, protocol):
                yield type_
    except TypeError:
        pass


@marsh.schema.caches.new_callable_cache(
    name='marsh.schema.types.protocol.match',
)
def match(
    protocol: Any,
) -> Iterable:
    return marsh.utils.IterableFromIterator(_match_iter(protocol))


@marsh.schema.register
class ProtocolUnmarshalSchema(marsh.schema.UnmarshalSchema[Any]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.matched = tuple(match(self.value))

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return (
                marsh.utils.is_protocol(value)
                and bool(match(value))
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~typing.Protocol`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Attempts to unmarshal :func:`~typing.runtime_checkable` '
            'Protocols into a matching class. The available classes. '
            'that can be matched against are :class:`float`, '
            ':class:`int`, :class:`bool`, :class:`bytes`, :class:`dict`, '
            ':class:`list`, :class:`str` and :class:`complex`.'
        )

    def doc_field_type(
        self,
    ) -> str:
        return self.value.__name__

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> Any:
        for type_ in self.matched:
            try:
                return marsh.unmarshal(type_, element)
            except Exception:
                pass
        raise marsh.errors.UnmarshalError(
            f'failed to unmarshal into one of the classes {self.matched}',
            element=element,
            type=self.value,
        )
