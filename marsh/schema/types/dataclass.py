import dataclasses
import re
import types
from typing import (
    Any,
    ForwardRef,
    Optional,
    Tuple,
    TypeVar,
    get_type_hints,
)

import marsh


_T = TypeVar('_T')


_FIELDS = getattr(dataclasses, '_FIELDS', '__dataclass_fields__')
_INITVAR_SENTINEL = dataclasses._FIELD_INITVAR  # type: ignore


def get_init_var_fields(
    dataclass: Any,
) -> Tuple[dataclasses.Field, ...]:
    return tuple(
        field
        for field
        in getattr(
            dataclass,
            _FIELDS,
        ).values()
        if field._field_type is _INITVAR_SENTINEL
    )


def is_generated_class_docstring(
    docstring: Optional[str],
) -> bool:
    if docstring:
        return bool(
            re.match(
                r'^[a-zA-Z0-9_]+\(([a-zA-Z0-9_]+: .+( = .+)?)*\)$',
                docstring,
            ),
        )
    return False


@marsh.schema.register
class DataclassMarshalSchema(marsh.schema.MarshalSchema):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return (
                dataclasses.is_dataclass(value)
                and marsh.utils.is_obj_instance(value)
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':func:`~dataclasses.dataclass`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals a dataclass instance into a mapping '
            'with the field names as keys.'
        )

    def marshal(
        self,
    ) -> dict:
        return {
            field.name: marsh.marshal(getattr(self.value, field.name))
            for field in dataclasses.fields(self.value)
            if field.init
        }


@marsh.schema.register
class DataclassUnmarshalSchema(marsh.schema.template.StructuredUnmarshalSchema[_T]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        try:
            annotations = get_type_hints(marsh.utils.get_type(self.value))
        except Exception:
            annotations = {}
        schemas = {}

        def resolve_type(
            type_: Any,
        ) -> Any:
            try:
                if isinstance(type_, (str, ForwardRef)):
                    type_ = annotations.get(field.name, type_)
            except Exception:
                pass
            type_is_str = False
            try:
                type_is_str = isinstance(type_, str)
            except Exception:
                pass
            if type_is_str:
                raise marsh.errors.MarshError(
                    f'failed to resolve type from string: "{type_}"',
                )
            type_is_initvar = False
            try:
                type_is_initvar = isinstance(type_, dataclasses.InitVar)
            except Exception:
                pass
            if type_is_initvar:
                return resolve_type(type_.type)
            return type_

        for field in (
            dataclasses.fields(self.value)
            + get_init_var_fields(self.value)
        ):
            if not field.init:
                continue
            with marsh.errors.prepend(field.name):
                type_ = resolve_type(field.type)
                schemas[field.name] = marsh.schema.UnmarshalSchema(
                    type_,
                    default=(
                        marsh.MISSING
                        if field.default == dataclasses.MISSING
                        else field.default
                    ),
                    default_factory=(
                        marsh.MISSING
                        if field.default_factory == dataclasses.MISSING
                        else field.default_factory
                    ),
                )
        self.schemas = types.MappingProxyType(schemas)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return (
                dataclasses.is_dataclass(value)
                and not marsh.utils.is_obj_instance(value)
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':func:`~dataclasses.dataclass`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Expects a mapping input with the dataclass '
            'field names as keys.'
        )

    def doc_description(
        self,
    ) -> Optional[str]:
        doc = getattr(self.value, '__doc__', None)
        if not doc or is_generated_class_docstring(doc):
            return None
        return doc
