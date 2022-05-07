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
