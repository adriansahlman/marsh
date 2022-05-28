"""Mapping schema support for subclasses of :class:`collections.abc.Mapping`."""
import collections.abc
import types
from typing import (
    Any,
    Mapping,
    TypeVar,
)

import marsh


_T = TypeVar('_T', bound=Mapping)


@marsh.schema.register
class MappingUnmarshalSchema(marsh.schema.template.MappingUnmarshalSchema[_T]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        k, v = marsh.utils.inspect_mapping_type(self.value)
        self.key_schema = marsh.schema.UnmarshalSchema(k)
        self.value_schema = marsh.schema.UnmarshalSchema(v)

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~collections.abc.Mapping`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals a mapping type from a mapping input. '
            'Should work for all mapping types. If the mapping '
            'type is one of the abstract mapping classes in '
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
                marsh.utils.is_mapping_type(value)
                and issubclass(
                    marsh.utils.get_type(value),
                    collections.abc.Mapping,
                )
            )
        except Exception:
            return False

    def construct(
        self,
        value: Mapping[Any, Any],
    ) -> _T:
        value_type = marsh.utils.get_type(self.value)
        if value_type is collections.abc.MutableMapping:
            return dict(value)  # type: ignore
        if value_type is collections.abc.Mapping:
            return types.MappingProxyType(value)  # type: ignore
        return super().construct(value)
