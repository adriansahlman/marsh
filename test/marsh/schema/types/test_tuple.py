import sys
import typing
from typing import (
    Any,
    List,
    Optional,
    Type,
)

import pytest

import marsh.testing


_TupleTypes: List[Any] = [
    typing.Tuple,
]

if sys.version_info.minor > 8:
    _TupleTypes.append(tuple)


@pytest.mark.parametrize(
    'type_,element,value',
    sum(
        (
            (
                (
                    t[int, float, str, bool],
                    ('0', '1e-1', 'a', 'true'),
                    (0, 1e-1, 'a', True),
                ),
                (t[int], ('3',), (3,)),
                (t[int, str], ('3', 4), (3, '4')),
                (t[()], marsh.MISSING, ()),
                (t[()], (), ()),
            ) for t in _TupleTypes
        ),
        (),
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
    sum(
        (
            (
                (t[()], (3,), None),
                (t[int], ('3', 4), None),
                (t[int], marsh.MISSING, marsh.errors.MissingValueError),
                (t[int], (marsh.MISSING,), marsh.errors.MissingValueError),
                (t[int, str], ('3'), None),
                (t[int, str], marsh.MISSING, marsh.errors.MissingValueError),
                (t[int, str], (marsh.MISSING, 4), marsh.errors.MissingValueError),
            ) for t in _TupleTypes
        ),
        (),
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
