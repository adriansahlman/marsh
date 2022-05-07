from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh.testing


@pytest.mark.parametrize(
    'value,element',
    (
        (b'', ''),
        (b'hello', 'aGVsbG8='),
        (b'\xff\xff\xff', '____'),
        (b'\xfb\xef\xbe', '----'),
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
    'element,value',
    (
        ('', b''),
        ('aGVsbG8=', b'hello'),
        ('////', b'\xff\xff\xff'),
        ('++++', b'\xfb\xef\xbe'),
    ),
)
def test_unmarshal_succeeds(
    element: marsh.element.ElementType,
    value: Any,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=bytes,
        element=element,
        value=value,
    )


@pytest.mark.parametrize(
    'element,exception',
    (
        ('a', None),
        (None, None),
        (marsh.MISSING, marsh.errors.MissingValueError),
    ),
)
def test_unmarshal_fails(
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=bytes,
        element=element,
        exception=exception,
    )
