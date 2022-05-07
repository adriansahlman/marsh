from typing import (
    Any,
    AnyStr,
    Optional,
    Type,
    TypeVar,
)

import pytest

import marsh
import marsh.testing


Unbound = TypeVar('Unbound')
BoundInt = TypeVar('BoundInt', bound=int)


@pytest.mark.parametrize(
    'type_,element,value',
    (
        (AnyStr, 'hello', 'hello'),
        (AnyStr, marsh.utils.bytes_to_base64(b'hello'), b'hello'),
        (BoundInt, '0', 0),
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
        (Unbound, {}, None),
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
