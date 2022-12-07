from typing import (
    Any,
    Literal,
    Sequence,
    TypeVar,
    get_args,
)

import marsh


_T = TypeVar('_T')


@marsh.schema.register
class LiteralUnmarshalSchema(marsh.schema.template.UnionUnmarshalSchema[_T]):

    schemas: Sequence['LiteralValueUnmarshalSchema']

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.schemas = tuple(
            LiteralValueUnmarshalSchema(Literal[arg])  # pyright: ignore
            for arg in get_args(self.value)
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return (
            marsh.utils.is_literal(value)
            and len(get_args(value)) > 1
        )

    @staticmethod
    def doc_static_type() -> str:
        return ':data:`~typing.Literal`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Matches the input against the literal value(s), '
            'then returns the matched value.'
        )

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        try:
            return super().unmarshal(element)
        except Exception:
            closest = marsh.utils.get_closest(
                value=str(element),
                candidates=(schema.literal_value for schema in self.schemas),
            )
            err_msg = (
                'failed to unmarshal input into one '
                f'of the literals {get_args(self.value)}'
            )
            if closest:
                err_msg += f', did you mean "{closest}"?'
            raise marsh.errors.UnmarshalError(
                err_msg,
                element=element,
                type=self.value,
            )


@marsh.schema.register
class LiteralValueMarshalSchema(marsh.schema.MarshalSchema):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return (
            marsh.utils.is_literal(value)
            and len(get_args(value)) == 1
        )

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return get_args(self.value)[0]


@marsh.schema.register
class LiteralValueUnmarshalSchema(marsh.schema.UnmarshalSchema[_T]):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.literal_value = get_args(self.value)[0]
        self.schema: marsh.schema.UnmarshalSchema = \
            marsh.schema.UnmarshalSchema(type(self.literal_value))

    def __str__(
        self,
    ) -> str:
        if isinstance(self.literal_value, str):
            return f'"{self.literal_value}"'
        return str(self.literal_value)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return (
            marsh.utils.is_literal(value)
            and len(get_args(value)) == 1
        )

    def doc_field_type(
        self,
    ) -> str:
        if isinstance(self.literal_value, str):
            return f'"{self.literal_value}"'
        return str(self.literal_value)

    def doc_description(
        self,
    ) -> str:
        return (
            f'A literal {self.doc_field_type()} of '
            f'of type {self.schema.doc_type()}'
        )

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
        literal_value = self.schema.unmarshal(element)
        if literal_value != self.literal_value:
            raise marsh.errors.UnmarshalError(
                (
                    'input did not match the literal '
                    f'value {self.literal_value}'
                ),
                element=element,
                type=self.value,
            )
        return literal_value
