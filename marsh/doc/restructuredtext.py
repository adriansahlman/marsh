from typing import (
    Iterable,
    Literal,
    Optional,
    Sequence,
)
from . import common


INDENT = ' ' * 4


def format_table(
    headers: Sequence,
    rows: Iterable[Sequence],
    title: Optional[str] = None,
    widths: Optional[Sequence] = None,
) -> str:
    """Create a RST list-table.

    Any newlines in the headers or rows are
    replaced with whitespace.

    Arguments:
        headers: The header names.
        rows: Iterable of rows, each
            row containing the same number
            of values as there are headers.
        title: A title for the table.
        widths: The width of columns. If given,
            must contain the same number of values
            as there are headers.

    Returns:
        The table in RST format.
    """
    title = (title or '') and f' {title}'
    table = (
        f'.. list-table::{title}\n'
        f'{INDENT}:header-rows: 1\n'
    )
    if widths:
        table += f'{INDENT}:widths: {", ".join(map(str, widths))}\n'
    table += '\n'
    table_rows = []
    for row in (headers,) + tuple(rows):
        for i, col in enumerate(row):
            if i:
                indent = f'{INDENT}  - '
            else:
                indent = f'{INDENT}* - '
            table_rows.append(f'{indent}{col}'.replace('\n', ' '))
    return table + '\n'.join(table_rows) + '\n'


def format_types(
    source: common.RegisteredSchemasType,
    section: Literal['#', '*', '=', '-', '^', '"'] = '^',
) -> str:
    """Return a RST-formatted string containing
    registered schema types that have static documention.

    A description below each type is included when available.

    Arguments:
        source: The source of the schemas.
        section: The section character.

    Returns:
        The formatted RST.
    """
    sections = []
    for schema in common.get_registered_schemas(source):
        type_ = schema.doc_static_type()
        if not type_:
            continue
        underline = section * len(type_)
        overline = ''
        if section in '#*':
            overline = underline + '\n'
        sections.append(
            f'{overline}{type_}\n{underline}\n\n'
            f'{schema.doc_static_description() or ""}',
        )
    return '\n\n'.join(sections)


def format_types_table(
    source: common.RegisteredSchemasType,
    title: Optional[str] = None,
) -> str:
    """Return a RST-formatted table containing
    registered schema types that have static documention.

    A description for each type is included when available.

    Arguments:
        source: The source of the schemas.

    Returns:
        The formatted RST table.
    """
    return format_table(
        headers=('Type', 'Description'),
        widths=(30, 50),
        rows=(
            (
                schema.doc_static_type(),
                schema.doc_static_description() or '',
            )
            for schema
            in common.get_registered_schemas(source)
            if schema.doc_static_type()
        ),
        title=title,
    )
