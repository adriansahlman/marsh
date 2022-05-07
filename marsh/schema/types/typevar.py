from typing import (
    Any,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)


import marsh


@marsh.schema.register
class TypeVarUnmarshalSchema(marsh.schema.UnmarshalSchema[Any]):

    value: TypeVar  # type: ignore
    schema: marsh.schema.UnmarshalSchema

    def __init__(
        self,
        value: Any,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(value, *args, **kwargs)
        self.schema = marsh.schema.UnmarshalSchema(
            self.resolve_type(),
            *args,
            **kwargs,
        )

    def __str__(
        self,
    ) -> str:
        return str(self.schema)

    def __repr__(
        self,
    ) -> str:
        return repr(self.schema)

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return bool(
                isinstance(value, TypeVar)
                and (
                    value.__bound__ is not None
                    or value.__constraints__
                ),
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~typing.TypeVar`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unwraps the :class:`~typing.TypeVar`, using its bound '
            'or constraints when unmarshaling. If '
            'no bound or constraints are present '
            'the type can not be unmarshaled.'
        )

    def resolve_type(
        self,
    ) -> Any:
        if self.value.__constraints__:
            if len(self.value.__constraints__) == 1:
                return self.value.__constraints__[0]
            return Union[self.value.__constraints__]  # pyright: ignore
        return self.value.__bound__

    def select(
        self,
        path: str,
    ) -> marsh.schema.UnmarshalSchema:
        return self.schema.select(path)

    def doc(
        self,
        depth: int = 0,
    ) -> marsh.schema.UnmarshalSchema.Doc:
        return self.schema.doc(depth)

    def doc_type(
        self,
    ) -> str:
        return self.schema.doc_type()

    def doc_field_type(
        self,
    ) -> str:
        return self.schema.doc_field_type()

    def doc_default(
        self,
    ) -> Optional[str]:
        return self.schema.doc_default()

    def doc_description(
        self,
    ) -> Optional[str]:
        return self.schema.doc_description()

    def doc_fields(
        self,
        depth: int,
    ) -> Optional[Mapping[str, marsh.schema.UnmarshalSchema.Doc.Field]]:
        return self.schema.doc_fields(depth)

    def doc_special_fields(
        self,
    ) -> Optional[Sequence[marsh.schema.UnmarshalSchema.Doc.SpecialField]]:
        return self.schema.doc_special_fields()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> Any:
        return self.schema.unmarshal(element)
