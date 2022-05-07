from typing import (
    Any,
    Mapping,
    NamedTuple,
    Sequence,
)

from . import template


class Arguments(NamedTuple):
    args: Sequence[Any]
    kwargs: Mapping[str, Any]


class ArgumentsUnmarshalSchema(
    template.CallableUnmarshalSchema[Arguments],
):

    def construct(
        self,
        *args,
        **kwargs,
    ) -> Arguments:
        return Arguments(
            args=args,
            kwargs=kwargs,
        )
