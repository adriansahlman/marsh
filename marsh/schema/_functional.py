from typing import (
    Callable,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import TypeAlias

import marsh
from . import core


_S = TypeVar('_S', bound=core.Schema)
_RelativePriority: TypeAlias = \
    marsh.utils.PriorityOrder.RelativePriority[Type[core.Schema]]


@overload
def register(
    schema: Type[_S],
    /,
    *,
    priority: int = 0,
    lower_priority: _RelativePriority = None,
    higher_priority: _RelativePriority = None,
    replace: bool = False,
) -> Type[_S]:
    ...


@overload
def register(
    *,
    priority: int = 0,
    lower_priority: _RelativePriority = None,
    higher_priority: _RelativePriority = None,
    replace: bool = False,
) -> Callable[[Type[_S]], Type[_S]]:
    ...


def register(
    schema: Optional[Type[_S]] = None,
    /,
    *,
    priority: int = 0,
    lower_priority: _RelativePriority = None,
    higher_priority: _RelativePriority = None,
    replace: bool = False,
) -> Union[Callable[[Type[_S]], Type[_S]], Type[_S]]:
    """Register a new schema (decorator).

    Relative priorities can be given as ``higher`` and ``lower``,
    where any schema in ``higher`` means that the schema being registered
    should have a lower priority than that, the opposite is true for ``lower``.

    The relative priority (if given) takes precedence over the base priority.

    Arguments:
        schema: The schema to register.
        priority: Base priority level.
        lower_priority: Any other schemas that should
            have lower priority compared to the new schema.
        higher_priority: Any other schemas that should
            have higher priority compared to the new schema.
        replace: Allow replacing existing registered schema
            with same name.

    Returns:
        Decorator if ``schema`` was not given, else ``schema``.
    """
    def _register(
        schema,
    ):
        schema.registry.register(
            schema,
            priority=priority,
            lower_priority=lower_priority,
            higher_priority=higher_priority,
            replace=replace,
        )
        return schema
    if schema is None:
        return _register
    return _register(schema)
