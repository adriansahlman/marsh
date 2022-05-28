"""Tools that can be used for testing purposes."""
import contextlib
from typing import (
    Any,
    Iterator,
    Optional,
    Type,
    TypeVar,
)

import pytest

import marsh


_T = TypeVar('_T')


@contextlib.contextmanager
def catch_cause(
    base: Type[Exception] = marsh.errors.MarshError,
    cause: Optional[Type[Exception]] = None,
) -> Iterator[None]:
    """Assert that an error is thrown in this context.

    Similar to :func:`pytest.raises` but allows for inspecting
    and finding a specific cause for the error raised by traversing
    the __cause__ attribute chain.

    Arguments:
        base: The base exception class to catch. If not caught,
            the test fails.
        cause: If not :data:`None`, at least one of the exceptions
            in the cause chain must be an instance of this class.

    Returns:
        Context manager.
    """
    with pytest.raises(base) as exc_info:
        yield
    if cause is not None:
        exception_chain = []
        inner_exc: Optional[BaseException] = exc_info.value
        while inner_exc is not None:
            if isinstance(inner_exc, cause):
                return
            exception_chain.append(inner_exc.__class__.__name__)
            inner_exc = inner_exc.__context__
        raise AssertionError(
            f'expected an exception of type {cause} '
            f'as cause, got {tuple(exception_chain)}',
        )


def marshal_succeeds(
    value: Any,
    element: marsh.element.ElementType,
) -> marsh.element.ElementType:
    """Assert that a value can be marshaled.

    The element is also compared to the expected
    output for the marshal.

    Arguments:
        value: The value to marshal.
        element: The expected marshal value.

    Returns:
        The marshaled value if successful.
    """
    schema = marsh.schema.MarshalSchema(value)
    marshaled = schema.marshal()
    element = marsh.element.standardize(element)
    marshaled = marsh.element.standardize(marshaled)
    assert marshaled == element, f'{marshaled} != {element}, schema={schema}'
    return marshaled


def marshal_fails(
    value: Any,
    exception: Optional[Type[Exception]] = None,
) -> None:
    """Assert that a value can not be marshaled.

    Requires that marshaling of the input value
    raises :class:`marsh.errors.MarshalError`.

    Arguments:
        value: Value to marshal.
        exception: Optional cause that must
            exist in the exception chain if
            given.
    """
    with catch_cause(
        base=marsh.errors.MarshalError,
        cause=exception,
    ):
        schema = marsh.schema.MarshalSchema(value)
        schema.marshal()


def unmarshal_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: _T,
) -> _T:
    """Assert that a value is unmarshaled correctly.

    Arguments:
        type_: Unmarshal into this type.
        element: The input that should be unmarshaled.
        value: The expected result.

    Returns:
        The unmarshaled result if successful.
    """
    schema = marsh.schema.UnmarshalSchema[Any](type_)
    unmarshaled = schema.unmarshal(element)
    assert unmarshaled == value, f'{unmarshaled} != {value}'
    return unmarshaled


def unmarshal_fails(
    type_: Any,
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]] = None,
) -> None:
    """Assert that a value can not be unmarshaled.

    Requires that unmarshaling raises
    :class:`marsh.errors.UnmarshalError`.

    Arguments:
        type_: Attempt to unmarshal into this type.
        element: The input that should be unmarshaled.
        exception: Optional cause that must
            exist in the exception chain if
            given.
    """
    with catch_cause(
        base=marsh.errors.UnmarshalError,
        cause=exception,
    ):
        schema = marsh.schema.UnmarshalSchema[Any](type_)
        schema.unmarshal(element)
