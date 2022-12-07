from typing import (
    Any,
    Type,
    TypeVar,
    Union,
)

import marsh


_P = TypeVar('_P', int, float, bool, str)
Primitive = Union[int, float, bool, str]
PrimitiveType = Union[Type[int], Type[float], Type[bool], Type[str]]


@marsh.schema.register
class PrimitiveMarshalSchema(marsh.schema.MarshalSchema):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_primitive(value)

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`int`, :class:`float`, :class:`bool`, :class:`str`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals any instance of a primitive class or subclass '
            'into its baseclass value.'
        )

    def marshal(
        self,
    ) -> Primitive:
        if isinstance(self.value, bool):
            return bool(self.value)
        elif isinstance(self.value, int):
            return int(self.value)
        elif isinstance(self.value, float):
            return float(self.value)
        else:
            return str(self.value)


@marsh.schema.register
class PrimitiveUnmarshalSchema(marsh.schema.UnmarshalSchema[_P]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return (
            marsh.utils.is_primitive_type(value)
            or marsh.utils.is_literal_string(value)
        )

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`int`, :class:`float`, :class:`bool`, :class:`str`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals any primitive class or its subclass. '
            'Special rules for :class:`bool` is documented in '
            ':func:`~marsh.utils.primitive_to_bool`.'
        )

    def get_type(
        self,
    ) -> Type[_P]:
        if marsh.utils.is_literal_string(self.value):
            return str  # type: ignore
        return self.value

    def doc_field_type(
        self,
    ) -> str:
        return f'<{marsh.utils.get_type_name(self.value)}>'

    def doc_description(
        self,
    ) -> None:
        return None

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _P:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            raise marsh.errors.MissingValueError
        if not marsh.utils.is_primitive(element):
            raise marsh.errors.UnmarshalError(
                (
                    f'expected a primitive value, got: '
                    f'{marsh.utils.get_type_name(element)}'
                ),
                element=element,
                type=self.value,
            )
        try:
            return marsh.utils.cast_primitive(
                self.get_type(),
                element,
            )
        except Exception:
            raise marsh.errors.UnmarshalError(
                f'could not convert to {marsh.utils.get_type_name(self.value)}',
                element=element,
                type=self.value,
            )
