import sys
from typing import (
    Any,
    Literal,
    Optional,
    Type,
)

import pytest

import marsh.testing


@pytest.mark.parametrize(
    'value,element',
    (
        (Literal[5], 5),
        (Literal['5'], '5'),
    ),
)
def test_marshal_succeeds(
    value: Any,
    element: marsh.element.ElementType,
) -> None:
    marsh.testing.marshal_succeeds(
        value=value,
        element=element,
    )


@pytest.mark.parametrize(
    'type_,element,value',
    (
        (Literal['a'], 'a', 'a'),
        (Literal['a', 'b'], 'b', 'b'),
        (Literal['0'], 0, '0'),
        (Literal[0], '0', 0),
        (Literal[False], 0, False),
        (Literal[True], 1, True),
        (Literal[True], 'on', True),
        (Literal['0', 0], 0, '0'),
        (Literal[None], None, None),
        (Literal[None], marsh.MISSING, None),
    ) + (
        # in python 3.8 Literal[0] == Literal[False]
        # and pytest converts Literal[False] -> Literal[0]
        (
            (Literal[False], 'false', False),
        ) if sys.version_info.minor > 8 else ()
    ),
)
def test_unmarshal_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: Any,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=type_,
        element=element,
        value=value,
    )


@pytest.mark.parametrize(
    'type_,element,exception',
    (
        (Literal['a'], 'b', None),
        (Literal['0'], 0.1, None),
        (Literal[0], 0.1, None),
        (Literal[False], 0.1, None),
        (Literal['a', 'b'], 'c', None),
        (Literal['a', 'b'], None, None),
        (Literal['a', 'b'], marsh.MISSING, marsh.errors.MissingValueError),
    ),
)
def test_unmarshal_fails(
    type_: Any,
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=type_,
        element=element,
        exception=exception,
    )
