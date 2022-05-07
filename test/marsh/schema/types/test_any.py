from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh.testing


@pytest.mark.parametrize(
    'element,value',
    (
        ('', ''),
        (None, None),
        (0, 0),
        (0., 0.),
        (0.5, 0.5),
        (True, True),
        ((), ()),
        ({}, {}),
        ((0,), (0,)),
        ({'a': 0}, {'a': 0}),
        ({'a': 0, 'b': (1, 2, 3)}, {'a': 0, 'b': (1, 2, 3)}),
        (({},), ({},)),
    ),
)
def test_unmarshal_succeeds(
    element: marsh.element.ElementType,
    value: marsh.element.ElementType,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=Any,
        element=element,
        value=value,
    )


@pytest.mark.parametrize(
    'element,exception',
    (
        (marsh.MISSING, marsh.errors.MissingValueError),
        ((1, 2, 3, marsh.MISSING), marsh.errors.MissingValueError),
        (({marsh.MISSING: 0},), marsh.errors.MissingValueError),
        (({'a': marsh.MISSING},), marsh.errors.MissingValueError),
    ),
)
def test_unmarshal_fails(
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=Any,
        element=element,
        exception=exception,
    )
