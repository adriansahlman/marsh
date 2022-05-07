import collections.abc
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


_StaticMappingTypes: List[Any] = [
    dict,
    collections.abc.Mapping,
    collections.abc.MutableMapping,
    typing.Dict,
    typing.Mapping,
    typing.MutableMapping,
]
_DynamicMappingTypes: List[Any] = [
    typing.Dict,
    typing.Mapping,
    typing.MutableMapping,
]

if sys.version_info.minor > 8:
    _DynamicMappingTypes = _StaticMappingTypes


@pytest.mark.parametrize(
    'value,element',
    (
        ({}, {}),
        ({'a': 0, 'b': 1}, {'a': 0, 'b': 1}),
        ({'a': {'b': (0, 1, 2)}, 'b': 1}, {'a': {'b': (0, 1, 2)}, 'b': 1}),
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


@pytest.mark.parametrize('type_', _StaticMappingTypes)
@pytest.mark.parametrize(
    'element,value',
    (
        (
            {},
            {},
        ),
        (
            {'a': 0, 'b': 1},
            {'a': 0, 'b': 1},
        ),
        (
            {'a': {'b': (0, 1, 2)}, 'b': 1},
            {'a': {'b': (0, 1, 2)}, 'b': 1},
        ),
        (
            marsh.MISSING,
            {},
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
                    d[str, Any],
                    {'a': {'b': (0, 1, 2)}, 'b': 1},
                    {'a': {'b': (0, 1, 2)}, 'b': 1},
                ),
                (
                    d[int, float],
                    {'0': '1e-1'},
                    {0: 1e-1},
                ),
                (
                    d[int, d[int, bool]],
                    {'0': {'1': 'true'}},
                    {0: {1: True}},
                ),
            ) for d in _DynamicMappingTypes
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


@pytest.mark.parametrize('type_', _StaticMappingTypes)
@pytest.mark.parametrize(
    'element,exception',
    (
        (
            '',
            None,
        ),
        (
            (),
            None,
        ),
        (
            {'a': marsh.MISSING},
            marsh.errors.MissingValueError,
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
                    d[int, Any],
                    {'a': 0},
                    None,
                ),
            ) for d in _DynamicMappingTypes
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
