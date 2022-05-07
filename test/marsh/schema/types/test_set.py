import sys
import typing
from typing import (
    Any,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

import pytest

import marsh
import marsh.testing


_StaticSetTypes: List[Any] = [
    set,
    typing.Set,
]
_DynamicSetTypes: List[Any] = [
    typing.Set,
]

if sys.version_info.minor > 8:
    _DynamicSetTypes = _StaticSetTypes


@pytest.mark.parametrize(
    'value,element',
    (
        (
            {'a', 0, b''},
            tuple({'a', 0, ''}),
        ),
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


@pytest.mark.parametrize('type_', _StaticSetTypes)
@pytest.mark.parametrize(
    'element,value',
    (
        (
            (),
            set(),
        ),
        (
            marsh.MISSING,
            set(),
        ),
        (
            ('a', 0),
            {'a', 0},
        ),
    ),
)
def test_unmarshal_static_type_succeeds(
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
    'type_,element,value',
    sum(
        (
            (
                (
                    s[Any],
                    (),
                    set(),
                ),
                (
                    s[Any],
                    marsh.MISSING,
                    set(),
                ),
                (
                    s[Any],
                    ('a', 0),
                    {'a', 0},
                ),
                (
                    s[int],
                    ('0', 1.),
                    {0, 1},
                ),
                (
                    s[Tuple[int, ...]],
                    (('0', 1.), (2,)),
                    {(0, 1), (2,)},
                ),
                (
                    s[Union[bool, float]],
                    ('false', '1.5'),
                    {False, 1.5},
                ),
            ) for s in _DynamicSetTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_type_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: Any,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=type_,
        element=element,
        value=value,
    )


@pytest.mark.parametrize('type_', _StaticSetTypes)
@pytest.mark.parametrize(
    'element,exception',
    (
        (
            '',
            None,
        ),
        (
            'a',
            None,
        ),
        (
            {},
            None,
        ),
        (
            (marsh.MISSING,),
            None,
        ),
    ),
)
def test_unmarshal_static_type_fails(
    type_: Any,
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=type_,
        element=element,
        exception=exception,
    )


@pytest.mark.parametrize(
    'type_,element,exception',
    sum(
        (
            (
                (
                    s[int],
                    ('a',),
                    None,
                ),
                (
                    s[int],
                    (marsh.MISSING,),
                    marsh.errors.MissingValueError,
                ),
            ) for s in _DynamicSetTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_type_fails(
    type_: Any,
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=type_,
        element=element,
        exception=exception,
    )
