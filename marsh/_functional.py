import functools
from typing import (
    Any,
    Callable,
    Optional,
    Type,
    TypeVar,
    overload,
)

import marsh
from . import entry_point


_T = TypeVar('_T')
_R = TypeVar('_R')
_C = TypeVar('_C', bound=Callable)


def marshal(
    value: Any,
) -> marsh.element.ElementType:
    """Serialize a value to a JSON-like object.

    Arguments:
        value: The input value to serialize.

    Returns:
        The JSON representation of the object.
    """
    schema = marsh.schema.MarshalSchema(value)
    return schema.marshal()


@overload
def unmarshal(
    type_: Type[_T],
    element: marsh.element.ElementType = marsh.MISSING,
) -> _T:
    ...


@overload
def unmarshal(
    type_: Type[_T],
    element: marsh.element.MappingElementType = marsh.MISSING,
    **kwargs,
) -> _T:
    ...


def unmarshal(
    type_: Type[_T],
    element: marsh.element.ElementType = marsh.MISSING,
    **kwargs,
) -> _T:
    """Unmarshal a JSON-like object to some type.

    .. note::

        Static type checkers may give an error for
        abstract types
        (`issue <https://github.com/python/mypy/issues/5374>`_).

        Some type aliases are also not recognized as types.
        For the moment there is not better solution than
        using a simple ``# type: ignore`` comment.

    Arguments:
        type_: The type to cast to.
        element: The JSON-like object.

    Returns:
        The unmarshaled value.
    """
    schema: marsh.schema.UnmarshalSchema[_T] = \
        marsh.schema.UnmarshalSchema(type_)
    if kwargs:
        if marsh.utils.is_missing(element):
            element = marshal(kwargs)
        if not marsh.utils.is_mapping(element):
            raise TypeError(
                'additional keyword arguments may only '
                'be used when the input element is a '
                'mapping type.',
            )
        else:
            element = dict(element)
            element.update(marshal(kwargs))  # type: ignore
    return schema.unmarshal(element)


def unmarshal_args(
    callable_: Callable,
    element: marsh.element.ElementType = marsh.MISSING,
) -> marsh.schema.argument.Arguments:
    """Return the unmarshaled arguments of the given function.

    Arguments:
        callable_: The function whos arguments to unmarshal.
        element: The input to the unmarshaler.

    Returns:
        Tuple of positional arguments and keyword arguments.
    """
    schema = marsh.schema.argument.ArgumentsUnmarshalSchema(callable_)
    return schema.unmarshal(element)


def cast(
    type_: Type[_T],
    value: Any = marsh.MISSING,
) -> _T:
    """Cast a value to some type.
    The input value is serialized to
    a JSON-like object and then used
    for constructing an instance of
    the specified type.

    .. note::

        Static type checkers may give an error for
        abstract types
        (`issue <https://github.com/python/mypy/issues/5374>`_).

        Some type aliases are also not recognized as types.
        For the moment there is not better solution than
        using a simple ``# type: ignore`` comment.

    Arguments:
        type_: The type to cast to.
        value: The value to cast.

    Returns:
        The casted value.
    """
    element = marshal(value)
    return unmarshal(type_, element)


def cast_args(
    callable_: Callable,
    value: Any = marsh.MISSING,
) -> marsh.schema.argument.Arguments:
    """Return the casted arguments of the given function.

    The given input will be marshaled before being unmarshaled
    into the function arguments.

    Arguments:
        callable_: The function whos arguments to unmarshal.
        value: The input.

    Returns:
        Tuple of positional arguments and keyword arguments.
    """
    element = marshal(value)
    return unmarshal_args(
        callable_,
        element,
    )


@overload
def main(
    *,
    setup_logging: bool = False,
    prog: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    help_depth: int = 1,
) -> Callable[[_C], _C]:
    ...


@overload
def main(
    fn: _C,
    /,
    *,
    setup_logging: bool = False,
    prog: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    help_depth: int = 1,
) -> _C:
    ...


@overload
def main(
    *,
    config: Type[_T],
    setup_logging: bool = False,
    prog: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    help_depth: int = 1,
) -> Callable[[Callable[[_T], _R]], Callable[[_T], _R]]:
    ...


@overload
def main(
    fn: Callable[[_T], _R],
    /,
    *,
    config: Type[_T],
    setup_logging: bool = False,
    prog: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    help_depth: int = 1,
) -> Callable[[_T], _R]:
    ...


def main(
    fn=None,
    /,
    *,
    config: Optional[Any] = None,
    setup_logging: bool = False,
    prog: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    help_depth: int = 2,
):
    """Decorates a function, allowing it to be called as an entry
    point for a python script being run from the command line.

    If a config class is supplied, the decorated function will be passed
    an instance of that class as a single positional argument.
    If no config class is supplied, the arguments for the decorated
    function are filled out and passed to the function.

    Arguments:
        fn: The callable function to decorate. When decorating,
            this argument should not be explicitly specified.
        config: An optional config class.
        setup_loggin: Add console line arguments for logging
            level and format. Initiallizes logging through
            :func:`logging.basicConfig`.
        prog: Optional program name. Defaults to the first
            value of :attr:`sys.argv`.
        description: Optional description shown in the help message.
            Defaults to the docstring of the decorated function (or
            the config class if passed to the decorator). Can
            be set to :data:`None` to disable completely.
        epilog: Optional epilog shown in the help message.
        help_depth: How many subfields of a config to flatten
            for ``--help [PATH]``.

    Returns:
        The wrapped function.
    """

    def main_decorator(
        fn: Callable,
    ) -> Callable:
        wrapped = entry_point.EntryPoint(
            fn=fn,
            config=config,
            setup_logging=setup_logging,
            prog=prog,
            description=description,
            epilog=epilog,
            help_depth=help_depth,
        )
        return functools.wraps(fn)(wrapped)

    if fn is None:
        return main_decorator
    return main_decorator(fn)
