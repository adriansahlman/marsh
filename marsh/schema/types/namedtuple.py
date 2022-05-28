import re
import types
from typing import (
    Any,
    Optional,
    TypeVar,
    get_type_hints,
)

import marsh
from . import (
    sequence,
    tuple,
)


_T = TypeVar('_T', bound=marsh.utils.NamedTupleProtocol)


def is_generated_class_docstring(
    docstring: Optional[str],
) -> bool:
    if docstring:
        return bool(re.match(r'^[a-zA-Z0-9_]+\(([a-zA-Z0-9_]+,)*\)$', docstring))
    return False


@marsh.schema.register
class NamedTupleMarshalSchema(marsh.schema.MarshalSchema):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_namedtuple(value)

    @staticmethod
    def doc_static_type() -> str:
        return ':func:`~collections.namedtuple`, :class:`~typing.NamedTuple`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals namedtuples into a mapping '
            'where the keys correspond to the field '
            'names of the namedtuple. Supports both '
            ':func:`~collections.namedtuple` and :class:`~typing.NamedTuple`.'
        )

    def marshal(
        self,
    ) -> dict:
        return {
            name: marsh.marshal(value)
            for name, value
            in zip(self.value._fields, self.value)
        }


@marsh.schema.register(
    lower_priority=(
        sequence.SequenceUnmarshalSchema,
        tuple.TupleUnmarshalSchema,
    ),
)
class NamedTupleUnmarshalSchema(marsh.schema.template.StructuredUnmarshalSchema[_T]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        schemas = {}
        annotations = get_type_hints(self.value)
        for field in self.value._fields:
            with marsh.errors.prepend(field):
                schemas[field] = marsh.schema.UnmarshalSchema(
                    annotations.get(field, Any),
                    default=self.value._field_defaults.get(field, marsh.MISSING),
                )
        self.schemas = types.MappingProxyType(schemas)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_namedtuple_type(value)

    @staticmethod
    def doc_static_type() -> str:
        return ':func:`~collections.namedtuple`, :class:`~typing.NamedTuple`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals namedtuple types from a mapping '
            'or sequence input. Supports both '
            ':func:`~collections.namedtuple` and :class:`~typing.NamedTuple`.'
        )

    def doc_description(
        self,
    ) -> Optional[str]:
        doc = getattr(self.value, '__doc__', None)
        if not doc or is_generated_class_docstring(doc):
            return None
        return doc
