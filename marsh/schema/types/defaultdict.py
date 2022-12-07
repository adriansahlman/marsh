import collections
from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    TypeVar,
)

import marsh
from . import mapping


_T = TypeVar('_T')


class InitType(Generic[_T]):

    _sentinel: Any = object()

    def __init__(
        self,
        schema: marsh.schema.UnmarshalSchema[_T],
    ) -> None:
        self.schema = schema
        self.input: marsh.element.ElementType = self._sentinel

    def __call__(
        self,
    ) -> _T:
        if self.input is not self._sentinel:
            return self.schema.unmarshal(self.input)
        for self.input in (marsh.MISSING, 0, '', None):
            try:
                return self.schema.unmarshal(self.input)
            except Exception:
                pass
        self.input = self._sentinel
        raise marsh.errors.MarshError(
            'could not automatically initialize the type '
            f'{self.schema.doc_type()}',
        )


@marsh.schema.register(lower_priority=mapping.MappingUnmarshalSchema)
class DefaultDictUnmarshalSchema(
    mapping.MappingUnmarshalSchema[collections.defaultdict],
):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.initializer: Callable[[], Any]
        if marsh.utils.inspect_mapping_type(self.value).value is Any:
            self.initializer = lambda: None
        else:
            self.initializer = InitType(self.value_schema)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_defaultdict_type(value)

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~collections.defaultdict`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals an input mapping into a defaultdict. '
            'If no default value is given in the type, all  '
            'values default to :data:`None`. An attempt is made '
            'to initialize the default value with a zero-value '
            '(zero, empty sequence, empty mapping, :data:`None` e.t.c). '
            'This is not always guaranteed to work if the default type '
            'requires specific arguments to be initialized. Use with '
            'caution.'
        )

    def doc_description(
        self,
    ) -> None:
        return None

    def construct(
        self,
        value: Mapping[Any, Any],
    ) -> collections.defaultdict:
        return collections.defaultdict(self.initializer, value)
