"""Tools for parsing strings into elements and/or commands."""
import contextlib
import dataclasses
from typing import (
    Any,
    Dict,
    Final,
    Iterator,
    List,
    Mapping,
    MutableSequence,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

import marsh


SET_VALUE_CHARACTERS: Final = '+='
SET_CONFIG_CHARACTERS: Final = '+@'
DELETE_VALUE_CHARACTERS: Final = '~'
OPENING_SEQUENCE_CHARACTERS: Final = '(['
OPENING_MAPPING_CHARACTERS: Final = '{'
QUOTE_CHARACTERS: Final = '\'"'
ESCAPE: Final = '\\'


_MaybeMutableSource = Union[str, MutableSequence[str]]


class _ParseFunction(Protocol):

    def __call__(
        self,
        source: Union[str, MutableSequence[str]],
        terminal_chars: str = '',
    ) -> 'marsh.element.ElementType':
        ...


class ParseError(Exception):

    def __init__(
        self,
        *args,
        remaining: _MaybeMutableSource,
        source: Optional[_MaybeMutableSource] = None,
    ) -> None:
        super().__init__(*args)
        if not isinstance(remaining, str):
            remaining = ''.join(remaining)
        self.remaining = remaining
        if source and not isinstance(source, str):
            source = ''.join(source)
        self.source = source

    def __str__(
        self,
    ) -> str:
        rep = super().__str__()
        if not self.remaining:
            return rep
        if not self.source:
            return f'{rep}\n... {self.remaining[:70]}\n{" " * 3}^'
        index = min(len(self.source) - 1, max(0, len(self.source) - len(self.remaining)))
        source = self.source
        if index > 35:
            source = f'... {source[index - 35:]}'
            index = index - 35 + 4
        if len(source) > 70:
            source = f'{source[:70]} ...'
        return f'{rep}\n{source}\n{" " * index}^'


@contextlib.contextmanager
def parsing(
    source: _MaybeMutableSource,
    terminal_chars: str = '',
) -> Iterator[MutableSequence[str]]:
    if isinstance(source, str):
        original_source = source
        source = list(source)
    else:
        original_source = ''.join(source)
    try:
        yield source
    except ParseError as err:
        err.source = original_source
        raise err
    remaining = list(source)
    consume_whitespace(remaining)
    if remaining and peek(remaining) not in terminal_chars:
        terminals: Union[str, Tuple[str, ...]]
        terminals = terminal_chars
        if len(terminals) > 1:
            terminals = tuple(terminals)
        raise ParseError(
            (
                'parsing did not terminate correctly at ' + (
                    f'terminal character: {terminals}'
                    if terminals else
                    'end of input string'
                )
            ),
            remaining=remaining,
            source=original_source,
        )


def is_whitespace(
    source: Sequence[str],
) -> bool:
    if not isinstance(source, str):
        source = ''.join(source)
    return source.isspace()


def consume_whitespace(
    source: MutableSequence[str],
) -> None:
    while source and source[0].isspace():
        pop(source)


def peek(
    source: Sequence[str],
) -> str:
    if source:
        return source[0]
    return ''


def pop(
    source: MutableSequence[str],
) -> str:
    if not source:
        raise ValueError('can not pop from empty source')
    return source.pop(0)


@dataclasses.dataclass
class Override:

    path: str

    def apply(
        self,
        element: marsh.element.ElementType,
        **kwargs,
    ) -> marsh.element.ElementType:
        raise NotImplementedError


@dataclasses.dataclass
class SetValue(Override):

    value: marsh.element.ElementType

    combine: bool

    def apply(
        self,
        element: marsh.element.ElementType,
        **kwargs,
    ) -> marsh.element.ElementType:
        return marsh.element.override(
            element=element,
            path=self.path,
            value=self.value,
            combine=self.combine,
        )


@dataclasses.dataclass
class SetConfig(Override):

    names: Sequence[str]

    combine: bool

    def apply(
        self,
        element: marsh.element.ElementType,
        root: Optional[str] = None,
        keep_meta: bool = False,
        **kwargs,
    ) -> marsh.element.ElementType:
        return marsh.element.override(
            element=element,
            path=self.path,
            value=marsh.config.load(
                *self.names,
                root=root,
                keep_meta=keep_meta,
                concatenate=True,
            ),
            combine=self.combine,
        )


@dataclasses.dataclass
class DeleteValue(Override):

    def apply(
        self,
        element: marsh.element.ElementType,
        **kwargs,
    ) -> marsh.element.ElementType:
        if not (
            marsh.utils.is_mapping(element)
            or marsh.utils.is_sequence(element)
        ):
            raise marsh.errors.PathError(
                'can not remove value for '
                f'non-existing path: {self.path}',
            )
        return marsh.element.remove(
            element=element,
            path=self.path,
        )


def override(
    source: Union[str, MutableSequence[str]],
) -> Override:
    """Parse an override.
    Accepts the format
    ``path.to.field@name1,name2``/``path.to.field+@name1,name2``
    for config assignments and
    ``path.to.field=value``/``path.to.field+=value``/
    ``~path.to.field`` for value assignments/deletion.

    Arguments:
        source: The string source to parse

    Returns:
        The override
    """
    with parsing(source) as source:
        consume_whitespace(source)
        delete = False
        if peek(source) == '~':
            delete = True
            pop(source)
        path = string(
            source,
            terminal_chars=SET_VALUE_CHARACTERS + SET_CONFIG_CHARACTERS,
        )
        if delete:
            consume_whitespace(source)
            if source:
                raise ParseError(
                    f'unexpected reserved character: "{peek(source)}". '
                    'The delete override should be in the form of `~path.to.field`',
                    remaining=source,
                )
            return DeleteValue(path=path)
        if peek(source) not in (SET_VALUE_CHARACTERS + SET_CONFIG_CHARACTERS):
            raise ParseError(
                'expected `@`, `+@`, `=`, `+=` or `~` in override',
                remaining=source,
            )
        missing_err = 'expected `@`, `+@`, `=`, `+=` or `~` in override'
        combine = False
        if peek(source) == '+':
            pop(source)
            combine = True
            if peek(source) not in '=@':
                missing_err = 'expected `+@`, or `+=`'
        if peek(source) == '@':
            pop(source)
            return SetConfig(
                path=path,
                names=config_names(source),
                combine=combine,
            )
        if peek(source) == '=':
            pop(source)
            return SetValue(
                path=path,
                value=element(source),
                combine=combine,
            )
        raise ParseError(
            missing_err,
            remaining=source,
        )


def config_names(
    source: Union[str, MutableSequence[str]],
) -> Sequence[str]:
    """Parse the names of a config assignment as a
    comma-separated list of strings. List bracket/parenthesis
    `()`/`[]` may be omitted.

    Parsing terminates at end of input source.
    String is split at `,` unless escaped or within a pair of quotation
    marks.
    Quotation marks and escape characters are not kept (unless escaped).

    Arguments:
        source: The string source to parse.

    Returns:
        The names.
    """
    with parsing(source) as source:
        consume_whitespace(source)
        if peek(source) in '[(':
            return tuple(map(str, sequence(source, element_parser=string)))
        names: List[str] = []
        while source:
            if names:
                if peek(source) != ',':
                    raise ParseError(
                        'expected `,` or the termination of the input string',
                        remaining=source,
                    )
                pop(source)
            names.append(string(source, terminal_chars=','))
            consume_whitespace(source)
        return names


def string(
    source: Union[str, MutableSequence[str]],
    terminal_chars: str = '',
) -> str:
    """Parse a single string.

    Reserved characters are allowed by being
    escaped (`\\`) or for the string (or part of the
    string) to be enclosed in quotes (``"`` or ``'``).

    Quotes are discarded before returning the result.

    Arguments:
        source: The string source to parse
        terminal_chars: Any characters that should terminate the parsing process (
            unless escaped or within a set of quotes). If none are given the
            entire input is consumed.

    Returns:
        The parsed string.
    """
    with parsing(source, terminal_chars) as source:
        consume_whitespace(source)
        if not source:
            return ''
        quote: Optional[str] = None
        chars: List[str] = []
        if peek(source) in QUOTE_CHARACTERS:
            quote = pop(source)
        while (char := peek(source)) not in terminal_chars or quote:
            if char == ESCAPE:
                if len(source) < 2:
                    raise ParseError(
                        'a character must succeed the escape character `\\`',
                        remaining=source,
                    )
                pop(source)
                chars.append(pop(source))
                continue
            if char == quote:
                pop(source)
                quote = None
                break
            chars.append(pop(source))
        if quote:
            raise ParseError(
                f'expected closing quote `{quote}`',
                remaining=source,
            )
        return ''.join(chars)


def terminal(
    source: Union[str, MutableSequence[str]],
    terminal_chars: str = '',
) -> Union[None, int, float, bool, str]:
    """Parse a terminal value.

    None | int | float | string | bool

    Arguments:
        source: The string source to parse
        terminal_chars: Any characters that should terminate the parsing process (
            unless escaped or within a set of quotes). If none are given the
            entire input is consumed.

    Returns:
        The parsed value.
    """
    if isinstance(source, str):
        original_source = source
        source = list(source)
    else:
        original_source = ''.join(source)
    consume_whitespace(source)
    if not source:
        return ''
    quoted = peek(source) in QUOTE_CHARACTERS
    try:
        value = string(
            source,
            terminal_chars=terminal_chars,
        )
    except ParseError as err:
        err.source = original_source
        raise err
    if quoted or not value:
        return value
    try:
        fl_value = float(value)
        if fl_value.is_integer():
            return int(fl_value)
        return fl_value
    except ValueError:
        pass
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null':
        return None
    return value


def element(
    source: Union[str, MutableSequence[str]],
    terminal_chars: str = '',
) -> 'marsh.element.ElementType':
    """Parse a single element.

    Returns a mapping, sequence or terminal element.

    See :func:`mapping`, :func:`sequence` and :func:`terminal`
    for more information parsing rules.

    Arguments:
        source: The string source to parse
        terminal_chars: Expected characters that can succeed the part
            of the input string that contains the element. If not given,
            an exception is raised if there is anything other than
            whitespace after the element.

    Returns:
        The parsed element.
    """
    with parsing(source, terminal_chars) as source:
        consume_whitespace(source)
        if not source:
            return ''
        if peek(source) == '{':
            return mapping(
                source,
                terminal_chars=terminal_chars,
            )
        elif peek(source) in '([':
            return sequence(
                source,
                terminal_chars=terminal_chars,
            )
        return terminal(
            source,
            terminal_chars=terminal_chars,
        )


def sequence(
    source: Union[str, MutableSequence[str]],
    terminal_chars: str = '',
    element_parser: _ParseFunction = element,
) -> Sequence:
    """Parse a single sequence of elements.

    See :func:`element` for defenition of an element.

    Elements should be separated by ``,``.
    The sequence should be enclosed in ``()`` or ``[]``.

    Arguments:
        source: The string source to parse
        terminal_chars: Expected characters that can succeed the part
            of the input string that contains the sequence. If not given,
            an exception is raised if there is anything other than whitespace
            after the sequence.
        element_parser: Each element of the sequence will be parsed using this parser.

    Returns:
        Sequence of elements.
    """
    with parsing(source, terminal_chars) as source:
        consume_whitespace(source)
        char = peek(source)
        if not (char and char in '(['):
            raise ParseError(
                'expected a sequence opening bracket `[` or parenthesis `(`',
                remaining=source,
            )
        closing_char = ']' if pop(source) == '[' else ')'
        consume_whitespace(source)
        value: List[marsh.element.ElementType] = []
        while peek(source) != closing_char:
            consume_whitespace(source)
            if value:
                if peek(source) != ',':
                    raise ParseError(
                        'expected `,` in sequence',
                        remaining=source,
                    )
                pop(source)
            consume_whitespace(source)
            value.append(
                element_parser(
                    source,
                    terminal_chars=',' + closing_char,
                ),
            )
        consume_whitespace(source)
        if peek(source) != closing_char:
            raise ParseError(
                f'expected `{closing_char}` as terminal character for sequence',
                remaining=source,
            )
        pop(source)
        return tuple(value)


def mapping(
    source: Union[str, MutableSequence[str]],
    terminal_chars: str = '',
    key_parser: _ParseFunction = string,
    value_parser: _ParseFunction = element,
) -> Mapping:
    """Parse a single mapping of strings to elements.

    See :func:`element` for defenition of an element.

    Keys and values should be separated by ``:``
    Key-value pairs should be separated by ``,``.
    The mapping should be enclosed in ``{}``.

    Arguments:
        source: The string source to parse
        terminal_chars: Expected characters that can succeed the part
            of the input string that contains the mapping. If not given,
            an exception is raised if there is anything other than whitespace
            after the mapping.
        key_parser: Each key of the mapping will be parsed using this parser.
        value_parser: Each value of the mapping will be parsed using this parser.

    Returns:
        The mapping of strings to elements.
    """
    with parsing(source, terminal_chars) as source:
        consume_whitespace(source)
        if peek(source) != '{':
            raise ParseError(
                'expected a mapping opening bracer `{`',
                remaining=source,
            )
        pop(source)
        consume_whitespace(source)
        value: Dict[Any, Any] = {}
        while peek(source) not in '}':
            if value:
                if peek(source) != ',':
                    raise ParseError(
                        'expected `,` in mapping',
                        remaining=source,
                    )
                pop(source)
            consume_whitespace(source)
            key = key_parser(
                source,
                terminal_chars=':',
            )
            consume_whitespace(source)
            if peek(source) != ':':
                raise ParseError(
                    (
                        'expected `:` in mapping' + (
                            f' after key "{key}"'
                            if key else ''
                        )
                    ),
                    remaining=source,
                )
            pop(source)
            consume_whitespace(source)
            value[key] = value_parser(
                source,
                terminal_chars=',}',
            )
            consume_whitespace(source)
        if peek(source) != '}':
            raise ParseError(
                'expected `}` as terminal character for mapping',
                remaining=source,
            )
        pop(source)
        return value
