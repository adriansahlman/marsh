import os
from typing import (
    Final,
    Iterable,
    Iterator,
    Literal,
)

import marsh
import marsh.doc


HEADING_1: Final = '='
HEADING_2: Final = '-'
HEADING_3: Literal['^'] = '^'
TITLE: Final = 'Supported Types'
MARSHAL_TITLE: Final = 'Marshal'
UNMARSHAL_TITLE: Final = 'Unmarshal'
SUPPORTED_TYPES_PATH: Final = os.path.join(
    os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
        ),
    ),
    'supported_types.rst',
)


def lines() -> Iterator[str]:
    yield TITLE
    yield HEADING_1 * len(TITLE)
    yield '\n'
    yield MARSHAL_TITLE
    yield HEADING_2 * len(MARSHAL_TITLE)
    yield '\n'
    yield marsh.doc.restructuredtext.format_types_table(
        marsh.schema.MarshalSchema,
        title='Marshal Types',
    )
    yield '\n'
    yield UNMARSHAL_TITLE
    yield HEADING_2 * len(UNMARSHAL_TITLE) + '\n'
    yield marsh.doc.restructuredtext.format_types_table(
        marsh.schema.UnmarshalSchema,
        title='Unmarshal Types',
    )
    yield '\n'


def write(
    lines: Iterable[str],
) -> None:
    with open(SUPPORTED_TYPES_PATH, 'w') as fp:
        for line in lines:
            print(line, file=fp)


if __name__ == '__main__':
    write(lines())
