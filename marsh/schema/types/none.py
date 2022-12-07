from typing import Any

import marsh


@marsh.schema.register
class NoneMarshalSchema(marsh.schema.MarshalSchema):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return value in (None, type(None))
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':data:`None`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Simply marshals any :data:`None` value by returning it.'
        )

    def marshal(
        self,
    ) -> None:
        return None


@marsh.schema.register
class NoneUnmarshalSchema(marsh.schema.UnmarshalSchema[None]):

    def __str__(
        self,
    ) -> str:
        return 'None'

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return value in (None, type(None))
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':data:`None`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'A missing value is valid input '
            'as well as the :data:`None` value directly.'
        )

    def doc_type(
        self,
    ) -> str:
        return 'None'

    def doc_field_type(
        self,
    ) -> str:
        return '<None>'

    def doc_description(
        self,
    ) -> str:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> None:
        if element is None or marsh.utils.is_missing(element):
            return None
        raise marsh.errors.UnmarshalError(
            'expected `None`',
            element=element,
            type=self.value,
        )
