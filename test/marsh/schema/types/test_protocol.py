from typing import (
    Any,
    Optional,
    SupportsAbs,
    SupportsComplex,
    SupportsFloat,
    SupportsIndex,
    SupportsRound,
    Type,
)

import pytest

import marsh
import marsh.testing


@pytest.mark.parametrize(
    'value,exception',
    (
        (SupportsAbs, None),
        (SupportsIndex, None),
        (SupportsFloat, None),
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
        (SupportsAbs, -1.5, -1.5),
        (SupportsFloat, -1.5, -1.5),
        (SupportsIndex, '1', 1),
        (SupportsComplex, '1e-1', complex(0.1)),
        (SupportsRound, 1.5, 1.5),
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
