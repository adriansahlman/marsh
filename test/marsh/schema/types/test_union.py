from typing import (
    Any,
    List,
    Optional,
    Type,
    Union,
)

import pytest

import marsh.testing


@pytest.mark.parametrize(
    'type_,element,value',
    (
        (Optional[int], None, None),
        (Optional[int], 0, 0),
        (Optional[Union[int, str]], '0', 0),
        (Union[int, str], '0', 0),
        (Union[str, int], '0', '0'),
        (Union[List[str], str], 'abc', 'abc'),
        (Union[str, List[str]], ('abc',), ['abc']),
        (Optional[int], marsh.MISSING, None),
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
        (Union[str, int], marsh.MISSING, marsh.errors.MissingValueError),
        (Union[bool, int], 'abc', None),
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
