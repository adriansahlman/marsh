from typing import (
    Any,
    Optional,
    Type,
    TypedDict,
)

import pytest

import marsh.testing


class A(TypedDict):
    a: int
    b: str


class B(TypedDict, total=False):
    a: int
    b: str


@pytest.mark.parametrize(
    'type_,element,value',
    (
        (A, dict(a=1, b='test'), A(a=1, b='test')),
        (A, (1, 'test'), A(a=1, b='test')),
        (B, dict(a=1), B(a=1)),
        (B, marsh.MISSING, B()),
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
        (A, marsh.MISSING, None),
        (A, {}, None),
        (A, dict(a=1), None),
        (A, dict(a=1.5, b='test'), None),
        (A, dict(b='test'), None),
        (A, dict(a='test', b='test'), None),
        (A, (), None),
        (A, None, None),
        (A, dict(a=1, c=3), None),
        (B, dict(c=3), None),
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
