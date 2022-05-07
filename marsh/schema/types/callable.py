from typing import (
    Any,
    TypeVar,
)


import marsh


_T = TypeVar('_T')


def is_callable(
    value: Any,
) -> bool:
    if not callable(value):
        return False
    if marsh.utils.is_protocol(value):
        return False
    if marsh.utils.is_typing_alias(value):
        return False
    return True


@marsh.schema.register(priority=-10)
class CallableUnmarshalSchema(marsh.schema.template.CallableUnmarshalSchema[_T]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return is_callable(value)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return '``Callable``'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Covers anything that is callable, be it a class, '
            'function or callable class instance. '
            'Callable arguments are inspected and the input '
            'should be a sequence or mapping(similar to '
            '`*args` or `**kwargs`).'
        )
