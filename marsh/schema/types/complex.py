import numbers
from typing import (
    Any,
    Literal,
    Mapping,
    Tuple,
    Union,
)

import marsh


Arg = Union[
    float,
    Tuple[()],
    Tuple[float],
    Tuple[float, float],
    Mapping[Literal['real', 'imag'], float],
]


@marsh.schema.register
class ComplexMarshalSchema(marsh.schema.MarshalSchema):

    value: numbers.Complex

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, numbers.Complex)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`complex`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals a complex value into a dictionary with keys '
            '``"real"`` and ``"imag"`` containing float values.'
        )

    def marshal(
        self,
    ) -> Union[float, dict]:
        c = complex(self.value)
        if c.imag == 0:
            return c.real
        return dict(
            real=c.real,
            imag=c.imag,
        )


@marsh.schema.register
class ComplexUnmarshalSchema(marsh.schema.UnmarshalSchema[complex]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            # let the generic unmarshal schema for
            # callables handle any subclasses of
            # numbers.Complex as they may contain
            # more arguments than just `real` and `imag`.
            return (
                issubclass(value, complex)
                or value == numbers.Complex
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`complex`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Expects a mapping with optional keys "real" '
            'and/or "imag" with float values or a sequence containing '
            'up to two float values, the first being the real value '
            'and the second being the imaginary value. If passed '
            'a float value instead of a mapping or sequence, it is '
            'treated as the real value.'
        )

    def doc_field_type(
        self,
    ) -> str:
        return '<complex>'

    def doc_description(
        self,
    ) -> str:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> complex:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            raise marsh.errors.MissingValueError(
                type=self.value,
            )
        try:
            arg: Arg = marsh.unmarshal(Arg, element)  # type: ignore
        except Exception:
            raise marsh.errors.UnmarshalError(
                (
                    'failed to unmarshal input element '
                    'into a float, tuple of floats or mapping '
                    'with optional keys `name` and `level`'
                ),
                element=element,
                type=self.value,
            )
        if isinstance(arg, float):
            return complex(arg)
        if marsh.utils.is_sequence(arg):
            return complex(*arg)
        return complex(**arg)  # type: ignore
