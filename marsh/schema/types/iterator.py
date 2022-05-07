from typing import (
    Any,
    Iterable,
)

import marsh


@marsh.schema.register(priority=-10)
class IterableMarshalSchema(marsh.schema.MarshalSchema):

    value: Iterable

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        if not marsh.utils.is_obj_instance(value):
            return False
        try:
            iter(value)
            return True
        except TypeError:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return '``Iterable``'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Fetches and marshals all items in an iterable.'
        )

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return tuple(marsh.marshal(item) for item in self.value)
