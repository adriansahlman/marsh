"""Path tools that work with any separator character."""
from typing import (
    Iterable,
    Iterator,
    NamedTuple,
    Optional,
    Sequence,
)

from . import errors


def iterative_split(
    path: str,
    delimiter: str = '.',
) -> Iterator[str]:
    """Iterate through the fields in a path.

    Escaped or quoted (unescaped quotes) delimiters will become part of a field
    instead of splitting it into more fields. Quotes are removed
    from the final fields.

    Arguments:
        path: The path to split into fields and iterate through.
        delimiter: The delimiter between fields in the path.

    Returns:
        Field iterator.
    """
    if not path:
        return
    field = []
    quote: Optional[str] = None
    escaped: bool = False
    for char in path:
        if escaped:
            field.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif quote:
            if char == quote:
                quote = None
            else:
                field.append(char)
        elif char in ('"', "'"):
            quote = char
        elif char == delimiter:
            if field:
                yield ''.join(field)
            field = []
        else:
            field.append(char)
    if quote:
        raise errors.PathError(f'closing quote `{quote}` missing from path')
    if escaped:
        raise errors.PathError('escape character can not be last character of path')
    if field:
        yield ''.join(field)


def split(
    path: str,
    delimiter: str = '.',
) -> Sequence[str]:
    """Split the fields of a path.

    Escaped or quoted (unescaped quotes) delimiters will become part of a field
    instead of splitting it into more fields. Quotes are removed
    from the final fields.

    Arguments:
        path: The path to split into fields.
        delimiter: The delimiter between fields in the path.

    Returns:
        The fields.
    """
    return tuple(iterative_split(path=path, delimiter=delimiter))


def escape_field(
    field: str,
    delimiter: str = '.',
) -> str:
    """Escape all delimiters and quotes found in a field.

    This may be done to maintain the original field when it becomes
    part of a path that is later split back into fields.

    Arguments:
        field: The field to escape characters in.
        delimiter: The delimiter used.

    Returns:
        The escaped field.
    """
    chars = []
    for char in field:
        if char in ('"', "'", '\\', delimiter):
            chars.append('\\')
        chars.append(char)
    return ''.join(chars)


def strip_delimiter(
    field_or_path: str,
    delimiter: str = '.',
) -> str:
    """Remove any delimiters from the start and end of a field or path.

    Escaped delimiters are not removed.

    Arguments:
        field_or_path: The field or path to strip delimiters from.
        delimiter: The delimiter to strip.

    Returns:
        The field or path with stripped delimiters.
    """
    while field_or_path.startswith(delimiter):
        field_or_path = field_or_path[1:]
    while (
        field_or_path.endswith(delimiter)
        and not field_or_path.endswith(f'\\{delimiter}')
    ):
        field_or_path = field_or_path[:-1]
    return field_or_path


def prepend(
    path: str,
    field: str,
    delimiter: str = '.',
) -> str:
    """Prepend a field to a path.

    Arguments:
        field: The field to prepend to a path.
        path: The path to prepend the field to.
        delimiter: The delimiter used between fields in the path.

    Returns:
        The prepended path.
    """
    if not path:
        return field
    if not field:
        return path
    return delimiter.join(
        (
            escape_field(field, delimiter=delimiter),
            strip_delimiter(path, delimiter=delimiter),
        ),
    )


def append(
    path: str,
    field: str,
    delimiter: str = '.',
) -> str:
    """Append a field to a path.

    Arguments:
        field: The field to append to a path.
        path: The path to append the field to.
        delimiter: The delimiter used between fields in the path.

    Returns:
        The appended path.
    """
    if not path:
        return field
    if not field:
        return path
    return delimiter.join(
        (
            strip_delimiter(path, delimiter=delimiter),
            escape_field(field, delimiter=delimiter),
        ),
    )


def join_fields(
    fields: Iterable[str],
    delimiter: str = '.',
) -> str:
    """Create a path from fields.

    Arguments:
        fields: The fields to create a path from.
        delimiter: The delimiter to use in the path between fields.

    Returns:
        The path.
    """
    return delimiter.join(
        escape_field(field, delimiter)
        for field in filter(None, fields)
    )


class _head_return_value(NamedTuple):
    head: str
    path: str


def head(
    path: str,
    delimiter: str = '.',
) -> _head_return_value:
    """Split the first field in a path from the path.

    Arguments:
        path: The path to split.
        delimiter: The delimiter used between fields in the path.

    Returns:
        A tuple of the first field in the path and the remaining path.
    """
    fields = list(filter(None, split(path, delimiter=delimiter)))
    if not fields:
        fields = ['']
    return _head_return_value(
        head=fields[0],
        path=join_fields(fields[1:], delimiter=delimiter),
    )


class _tail_return_value(NamedTuple):
    tail: str
    path: str


def tail(
    path: str,
    delimiter: str = '.',
) -> _tail_return_value:
    """Split the last field in a path from the path.

    Arguments:
        path: The path to split.
        delimiter: The delimiter used between fields in the path.

    Returns:
        A tuple of the last field in the path and the remaining path.
    """
    fields = list(filter(None, split(path, delimiter=delimiter)))
    if not fields:
        fields = ['']
    return _tail_return_value(
        tail=fields[-1],
        path=join_fields(fields[:-1], delimiter=delimiter),
    )
