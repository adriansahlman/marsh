import collections
import numbers
import sys
import typing
from typing import (
    Any,
    Callable,
    Dict,
    List,
)

import pytest

import marsh.testing


_StaticDefaultDictTypes: List[Any] = [
    collections.defaultdict,
    typing.DefaultDict,
]
_DynamicDefaultDictTypes: List[Any] = [
    typing.DefaultDict,
]

if sys.version_info.minor > 8:
    _DynamicDefaultDictTypes = _StaticDefaultDictTypes


d = collections.defaultdict(list)
d['a'] = [1, 2, 3]
d['b'] = [4, 5, 6]


@pytest.mark.parametrize(
    'value,element',
    (
        (d, dict(a=(1, 2, 3), b=(4, 5, 6))),
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


@pytest.mark.parametrize('type_', _StaticDefaultDictTypes)
@pytest.mark.parametrize(
    'element,value,default_factory',
    (
        (
            dict(a=3, b=(1, 2)),
            collections.defaultdict(lambda: None, dict(a=3, b=(1, 2))),
            lambda: None,
        ),
    ),
)
def test_unmarshal_static_type_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: Any,
    default_factory: Callable[..., Any],
) -> None:
    dd = marsh.testing.unmarshal_succeeds(
        type_=type_,
        element=element,
        value=value,
    )
    default = default_factory()
    assert dd[object()] == default


@pytest.mark.parametrize(
    'type_,element,value,default_factory',
    sum(
        (
            (
                (
                    d[str, Any],
                    dict(a=3, b=(1, 2)),
                    collections.defaultdict(lambda: None, dict(a=3, b=(1, 2))),
                    lambda: None,
                ),
                (
                    d[str, list],
                    dict(a=[1]),
                    collections.defaultdict(list, dict(a=[1])),
                    list,
                ),
                (
                    d[str, dict],
                    dict(a=dict(b=3)),
                    collections.defaultdict(dict, dict(a=dict(b=3))),
                    dict,
                ),
                (
                    d[str, Dict[str, float]],
                    dict(a=dict(b=1.5)),
                    collections.defaultdict(list, dict(a=dict(b=1.5))),  # type: ignore
                    dict,
                ),
                (
                    d[str, numbers.Complex],
                    dict(a=5),
                    collections.defaultdict(complex, dict(a=complex(5))),
                    complex,
                ),
            ) for d in _DynamicDefaultDictTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_type_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: Any,
    default_factory: Callable[..., Any],
) -> None:
    dd = marsh.testing.unmarshal_succeeds(
        type_=type_,
        element=element,
        value=value,
    )
    default = default_factory()
    assert dd[object()] == default
