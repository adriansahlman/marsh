"""Collection of common errors used throughout the framework."""
import contextlib
import os
from typing import (
    Any,
    Callable,
    ClassVar,
    Final,
    Iterator,
    Type,
    TypeVar,
    overload,
)

import marsh


_E = TypeVar('_E', bound=BaseException)


_MARSH_FULL_ERROR_ENV: Final = 'MARSH_FULL_ERROR'


class MarshError(Exception):
    """Base class for marsh errors.

    Allows tracking of the path that produced the
    error.

    Arguments:
        *args: General exception arguments.
        path: The path that produced the error.
    """

    delimiter: ClassVar[str] = '.'

    def __init__(
        self,
        *args,
        path: str = '',
    ) -> None:
        super().__init__(*args)
        self.path = path

    def pretty(
        self,
        cause: bool = False,
    ) -> str:
        pretty = ', '.join(map(str, self.args))
        if self.path:
            pretty = f'{pretty}\n\tpath: {self.path}'
        if cause:
            error: BaseException = self
            while error.__cause__ is not None:
                if not isinstance(error.__cause__, MarshError):
                    pretty = f'{pretty}\n\tcause: {error}'
                    break
                error = error.__cause__
        return pretty

    def __str__(
        self,
    ) -> str:
        return self.pretty(cause=True)

    def __repr__(
        self,
    ) -> str:
        pretty = self.pretty(cause=True)
        if pretty:
            return f'{self.__class__.__name__}: {pretty}'
        return self.__class__.__name__

    def append(
        self,
        field: str,
    ) -> None:
        """Append a field to the path of this error."""
        self.path = marsh.path.append(
            path=self.path,
            field=field,
            delimiter=self.delimiter,
        )

    def prepend(
        self,
        field: str,
    ) -> None:
        """Prepend a field to the path of this error."""
        self.path = marsh.path.prepend(
            path=self.path,
            field=field,
            delimiter=self.delimiter,
        )


class PathError(MarshError, KeyError, IndexError):
    """Accessing non-existing fields or indices.

    Also used for path formatting errors.
    """
    pass


class UnmarshalError(MarshError):
    """Failure to unmarshal an element to a specific type."""

    def __init__(
        self,
        msg: str = '',
        path: str = '',
        element: 'marsh.element.ElementType' = '???',
        type: Any = '???',
    ) -> None:
        super().__init__(msg)
        self.path = path
        self.element = element
        self.type = type

    def pretty(
        self,
        cause: bool = False,
        element: bool = False,
    ) -> str:
        pretty = super().pretty(cause)
        if not marsh.utils.is_missing(self.type):
            pretty += f'\n\ttype: {marsh.utils.get_type_name(self.type)}'
        if element and not marsh.utils.is_missing(self.element):
            pretty += f'\n\telement: {self.element}'
        return pretty


class MissingValueError(UnmarshalError):
    """Required value is missing."""
    pass


class MarshalError(MarshError):
    """Failure to serialize a value."""
    pass


class ConfigFileError(MarshError):
    """Base error for config files."""

    delimiter: ClassVar[str] = '/'


# TODO: Python 3.9: add [None] to return type.
@overload
def maybe_handle_error(
    callback: Callable[[MarshError], Any],
) -> contextlib.AbstractContextManager:
    ...


# TODO: Python 3.9: add [None] to return type.
@overload
def maybe_handle_error(
    callback: Callable[[_E], Any],
    error: Type[_E],
) -> contextlib.AbstractContextManager:
    ...


@contextlib.contextmanager
def maybe_handle_error(
    callback: Callable[[Any], Any],
    error: Type[BaseException] = MarshError,
) -> Iterator[None]:
    """Context manager that invokes a callback when catching an error.

    The error is propagated and the callback ignored if the environmental variable
    ``MARSH_FULL_ERROR`` is set and not empty.

    The error is passed to the callback.

    Arguments:
        callback: Callback function which may be called with the caught error.

    Returns:
        Context manager.
    """
    try:
        yield
    except error as err:
        if os.environ.get(_MARSH_FULL_ERROR_ENV, None):
            raise
        callback(err)


@contextlib.contextmanager
def prepend(
    field: Any,
) -> Iterator[None]:
    """Catches any marsh error, prepends a field to it and then re-raises the error.

    Arguments:
        field: The field to prepend to the marsh error path attribute.

    Returns:
        Context manager.
    """
    try:
        yield
    except MarshError as err:
        field = str(field)
        if field:
            err.prepend(field)
        raise
