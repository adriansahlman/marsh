from typing import Any

import marsh


@marsh.schema.register
class AnyUnmarshalSchema(marsh.schema.UnmarshalSchema[marsh.element.ElementType]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return value is Any

    @staticmethod
    def doc_static_type() -> str:
        return ':data:`~typing.Any`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Any JSON-like data.\n'
            'Values should consist of one or '
            'more of the types :class:`int`, '
            ':class:`float`, :class:`str`, :class:`bool`, '
            ':class:`~collections.abc.Sequence` or '
            ':class:`~collections.abc.Mapping`. '
            'Can not contain missing values.'
        )

    def doc_type(
        self,
    ) -> str:
        return 'Any'

    def doc_field_type(
        self,
    ) -> str:
        return '<Any>'

    def doc_description(
        self,
    ) -> str:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> marsh.element.ElementType:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            raise marsh.errors.MissingValueError(
                type=self.value,
            )
        if marsh.element.has_missing(element):
            raise marsh.errors.MissingValueError(
                'element contains missing value',
                type=self.value,
            )
        return element
