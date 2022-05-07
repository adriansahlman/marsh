import enum
from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh.testing


class T(enum.Enum):
    A: int = 0
    B = 'test'


@pytest.mark.parametrize(
    'value,element',
    (
        (T.A, 'A'),
        (T.B, 'B'),
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
    'value,exception',
    (
        (T, None),
    ),
)
def test_marshal_fails(
    value: Any,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.marshal_fails(
        value=value,
        exception=exception,
    )


@pytest.mark.parametrize(
    'type_,element,value',
    (
        (T.A, 'A', T.A),
        (T, 'A', T.A),
        (T.A, 0, T.A),
        (T, 0, T.A),
        (T.A, '0', T.A),
        (T, '0', T.A),
        (T.B, 'B', T.B),
        (T, 'B', T.B),
        (T.B, 'test', T.B),
        (T, 'test', T.B),
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
        (T.B, 'A', None),
        (T.B, 0, None),
        (T.B, '0', None),
        (T.A, 'B', None),
        (T.A, 'test', None),
        (T, 'a', None),
        (T.A, 'a', None),
        (T, marsh.MISSING, marsh.errors.MissingValueError),
        (T.A, marsh.MISSING, marsh.errors.MissingValueError),
        (T.B, marsh.MISSING, marsh.errors.MissingValueError),
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
