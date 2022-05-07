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
        (slice(None), dict(start=None, stop=None, step=None)),
        (slice(5), dict(start=None, stop=5, step=None)),
        (slice(1, 3), dict(start=1, stop=3, step=None)),
        (slice(1, 3, 2), dict(start=1, stop=3, step=2)),
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
        (slice, marsh.MISSING, slice(None)),
        (slice, (), slice(None)),
        (slice, {}, slice(None)),
        (slice, ':', slice(None)),
        (slice, '::', slice(None)),
        (slice, '5:', slice(5, None, None)),
        (slice, ':5', slice(None, 5, None)),
        (slice, '::-1', slice(None, None, -1)),
        (slice, '5:10', slice(5, 10, None)),
        (slice, '5:10:-1', slice(5, 10, -1)),
        (slice, (None,), slice(None)),
        (slice, (None, None), slice(None)),
        (slice, (None, None, None), slice(None)),
        (slice, (5, None), slice(5, None, None)),
        (slice, (5, None, None), slice(5, None, None)),
        (slice, (5,), slice(None, 5, None)),
        (slice, (None, 5), slice(None, 5, None)),
        (slice, (None, 5, None), slice(None, 5, None)),
        (slice, (None, None, -1), slice(None, None, -1)),
        (slice, (5, 10), slice(5, 10, None)),
        (slice, (5, 10, None), slice(5, 10, None)),
        (slice, (5, 10, -1), slice(5, 10, -1)),
        (slice, dict(stop=None), slice(None)),
        (slice, dict(start=None, stop=None), slice(None)),
        (slice, dict(start=None, stop=None, step=None), slice(None)),
        (slice, dict(start=5), slice(5, None, None)),
        (slice, dict(start=5, stop=None), slice(5, None, None)),
        (slice, dict(start=5, stop=None, step=None), slice(5, None, None)),
        (slice, dict(stop=5), slice(None, 5, None)),
        (slice, dict(stop=5, start=None), slice(None, 5, None)),
        (slice, dict(stop=5, start=None, step=None), slice(None, 5, None)),
        (slice, dict(step=-1), slice(None, None, -1)),
        (slice, dict(start=None, step=-1), slice(None, None, -1)),
        (slice, dict(start=None, stop=None, step=-1), slice(None, None, -1)),
        (slice, dict(start=5, stop=10), slice(5, 10, None)),
        (slice, dict(start=5, stop=10, step=None), slice(5, 10, None)),
        (slice, dict(start=5, stop=10, step=-1), slice(5, 10, -1)),
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
        (slice, '', None),
        (slice, ':::', None),
        (slice, '0:::', None),
        (slice, '0:1::', None),
        (slice, '0:1:2:', None),
        (slice, '0:1:2:3', None),
        (slice, '0', None),
        (slice, (1, 2, 3, 4), None),
        (slice, {'a': 1}, None),
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
