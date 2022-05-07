"""Mapping schema support.

For generic map-matching schemas we set the priority lower
than schemas of normal types as a ducktyped match should be
the last resort.
"""
import collections.abc
import types
from typing import (
    Any,
    Mapping,
    TypeVar,
)

import marsh


_T = TypeVar('_T', bound=Mapping)


@marsh.schema.register(priority=-5)
class MappingMarshalSchema(marsh.schema.MarshalSchema):

    value: Mapping

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_mapping(value)

    def marshal(
        self,
    ) -> dict:
        return {
            str(key): marsh.marshal(self.value[key])
            for key in self.value
        }


@marsh.schema.register
class AbcMappingMarshalSchema(MappingMarshalSchema):

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~collections.abc.Mapping`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals any mapping into a new mapping with '
            'string keys. All values of the mapping are '
            'also marshaled.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, collections.abc.Mapping)
        except Exception:
            return False


@marsh.schema.register(priority=-5)
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

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_mapping_type(value)

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


@marsh.schema.register
class AbcMappingUnmarshalSchema(MappingUnmarshalSchema):

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
            return issubclass(value, collections.abc.Mapping)
        except Exception:
            return False
