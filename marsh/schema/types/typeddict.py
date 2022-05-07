import functools
import types
from typing import (
    Any,
    Sequence,
    TypeVar,
    get_type_hints,
)

import marsh
from . import mapping


_T = TypeVar('_T')


class _Sentinel:

    def __str__(
        self,
    ) -> str:
        return ''


@marsh.schema.register(lower_priority=mapping.MappingUnmarshalSchema)
class TypedDictUnmarshalSchema(marsh.schema.template.StructuredUnmarshalSchema[_T]):

    @functools.cached_property
    def required_keys(
        self,
    ) -> Sequence[str]:
        if hasattr(self.value, '__required_keys__'):
            keys = self.value.__required_keys__  # type: ignore
        elif self.value.__total__:  # type: ignore
            keys = frozenset(get_type_hints(self.value))
        else:
            keys = frozenset()
        ordered_keys = tuple(get_type_hints(self.value))
        return sorted(keys, key=lambda x: ordered_keys.index(x))

    @functools.cached_property
    def optional_keys(
        self,
    ) -> Sequence[str]:
        if hasattr(self.value, '__optional_keys__'):
            keys = self.value.__optional_keys__  # type: ignore
        elif not self.value.__total__:  # type: ignore
            keys = frozenset(get_type_hints(self.value))
        else:
            keys = frozenset()
        ordered_keys = tuple(get_type_hints(self.value))
        return sorted(keys, key=lambda x: ordered_keys.index(x))

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._sentinel = _Sentinel()
        annotations = get_type_hints(self.value)
        self.schemas = types.MappingProxyType(
            {
                **{
                    name: marsh.schema.UnmarshalSchema(
                        annotations[name],
                    )
                    for name in self.required_keys
                },
                **{
                    name: marsh.schema.UnmarshalSchema(
                        annotations[name],
                        default=self._sentinel,
                    )
                    for name in self.optional_keys
                },
            },
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_typeddict_type(value)

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~typing.TypedDict`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals any subclass of :class:`~typing.TypedDict` '
            'from a mapping input. If ``total=False`` then '
            'all keys are optional.'
        )

    def construct(
        self,
        *args,
        **kwargs,
    ) -> _T:
        if args and not kwargs:
            kwargs = {
                key: value
                for key, value
                in zip(get_type_hints(self.value), args)
            }
            args = ()
        mapping = dict(*args, **kwargs)
        for key, value in tuple(mapping.items()):
            if value is self._sentinel:
                if key in self.optional_keys:
                    del mapping[key]
                else:
                    raise marsh.errors.MissingValueError(
                        f'required key: {key}',
                    )
        return mapping  # type: ignore
