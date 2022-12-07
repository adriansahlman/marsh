import enum
from typing import (
    Any,
    TypeVar,
)

import marsh
from . import sequence


_E = TypeVar('_E', bound=enum.Enum)


@marsh.schema.register(lower_priority=sequence.SequenceUnmarshalSchema)
class EnumUnmarshalSchema(marsh.schema.template.UnionUnmarshalSchema[_E]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.schemas = tuple(map(EnumValueUnmarshalSchema, self.value))

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return issubclass(value, enum.Enum)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~enum.Enum`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Input must match one of the '
            'enum values (the name or value).'
        )


@marsh.schema.register
class EnumValueMarshalSchema(marsh.schema.MarshalSchema):

    value: enum.Enum

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, enum.Enum)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~enum.Enum`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals an enum instance into its name.'
        )

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return self.value.name


@marsh.schema.register
class EnumValueUnmarshalSchema(marsh.schema.UnmarshalSchema[_E]):

    value: _E  # type: ignore

    def __str__(
        self,
    ) -> str:
        return self.value.name

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, enum.Enum)
        except Exception:
            return False

    def doc_type(
        self,
    ) -> str:
        return marsh.utils.get_type_name(self.value)

    def doc_field_type(
        self,
    ) -> str:
        return f'"{self.value.name}"'

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _E:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            raise marsh.errors.MissingValueError(
                type=self.value,
            )
        if not marsh.utils.is_primitive(element):
            raise marsh.errors.UnmarshalError(
                (
                    'expected a primitive value for an enum, got: '
                ),
                element=element,
                type=self.value,
            )
        try:
            marsh.utils.cast_literal(self.value.name, element)
            return self.value
        except ValueError:
            pass
        try:
            marsh.utils.cast_literal(self.value.value, element)
            return self.value
        except ValueError:
            pass
        raise marsh.errors.UnmarshalError(
            (
                f'could not convert to enum name ({self.value.name}) '
                f'or enum value ({self.value.value})'
            ),
            element=element,
            type=self.value,
        )
