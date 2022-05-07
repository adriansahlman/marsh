from typing import (
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import marsh


_T = TypeVar('_T')


@marsh.schema.register
class UnionUnmarshalSchema(marsh.schema.template.UnionUnmarshalSchema[_T]):
    """Attempts to unmarshal the types in a union one at a time in the order
    of the types held by the Union type alias."""

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.schemas = tuple(
            map(
                marsh.schema.UnmarshalSchema,
                get_args(self.value),
            ),
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return bool(
            get_origin(value) is Union
            and get_args(value),
        )

    @staticmethod
    def doc_static_type() -> str:
        return ':data:`~typing.Union`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'The union type which in later versions of '
            'python may be specified using the ``|`` operator. '
            'The order of the types in the union matter as an '
            'attempt is made to unmarshal each type where the value '
            'of the first successful unmarshal is returned. :data:`~typing.Optional` '
            'will always set :data:`None` as the second type in the produced union.'
        )
