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


_StaticTupleTypes: List[Any] = [
    tuple,
    typing.Tuple,
]
_StaticSequenceTypes: List[Any] = [
    typing.Sequence,
    collections.abc.Sequence,
]
_StaticMutableSequenceTypes: List[Any] = [
    list,
    typing.List,
    typing.MutableSequence,
    collections.abc.MutableSequence,
]
_DynamicTupleTypes: List[Any] = [
    typing.Tuple,
]
_DynamicSequenceTypes: List[Any] = [
    typing.Sequence,
]
_DynamicMutableSequenceTypes: List[Any] = [
    typing.List,
    typing.MutableSequence,
]

if sys.version_info.minor > 8:
    _DynamicTupleTypes = _StaticTupleTypes
    _DynamicSequenceTypes = _StaticSequenceTypes
    _DynamicMutableSequenceTypes = _StaticMutableSequenceTypes


@pytest.mark.parametrize(
    'value,element',
    (
        (('a', 0, b''), ('a', 0, '')),
        (['a', (0, b'')], ('a', (0, ''))),
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
    'type_',
    _StaticTupleTypes + _StaticSequenceTypes,
)
@pytest.mark.parametrize(
    'element,value',
    (
        ((), ()),
        (marsh.MISSING, ()),
        (('a', 0), ('a', 0)),
        (('a', 0, {'b': 1}), ('a', 0, {'b': 1})),
    ),
)
def test_unmarshal_static_sequence_type_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: Any,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=type_,
        element=element,
        value=value,
    )


@pytest.mark.parametrize('type_', _StaticMutableSequenceTypes)
@pytest.mark.parametrize(
    'element,value',
    (
        ((), []),
        (marsh.MISSING, []),
        (('a', 0), ['a', 0]),
        (('a', 0, {'b': 1}), ['a', 0, {'b': 1}]),
    ),
)
def test_unmarshal_static_mutable_sequence_type_succeeds(
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
                (t[Any, ...], (), ()),
                (t[Any, ...], marsh.MISSING, ()),
                (t[Any, ...], ('a', 0), ('a', 0)),
                (t[Any, ...], ('a', 0, {'b': 1}), ('a', 0, {'b': 1})),
                (t[int, ...], ('0', 1.), (0, 1)),
                (t[t[int, ...], ...], (('0', 1.), (2,)), ((0, 1), (2,))),
            ) for t in _DynamicTupleTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_tuple_type_succeeds(
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
                (s[Any], (), ()),
                (s[Any], marsh.MISSING, ()),
                (s[Any], ('a', 0), ('a', 0)),
                (s[Any], ('a', 0, {'b': 1}), ('a', 0, {'b': 1})),
                (s[int], ('0', 1.), (0, 1)),
                (s[s[int]], (('0', 1.), (2,)), ((0, 1), (2,))),
            ) for s in _DynamicSequenceTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_sequence_type_succeeds(
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
                (s[Any], (), []),
                (s[Any], marsh.MISSING, []),
                (s[Any], ('a', 0), ['a', 0]),
                (s[Any], ('a', 0, {'b': 1}), ['a', 0, {'b': 1}]),
                (s[int], ('0', 1.), [0, 1]),
                (s[s[int]], (('0', 1.), (2,)), [[0, 1], [2]]),
            ) for s in _DynamicMutableSequenceTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_mutable_sequence_type_succeeds(
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
    'type_',
    _StaticTupleTypes + _StaticSequenceTypes,
)
@pytest.mark.parametrize(
    'element,exception',
    (
        ('', None),
        ({}, None),
        ((marsh.MISSING,), None),
    ),
)
def test_unmarshal_static_sequence_type_fails(
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
                (t[int, ...], ('a',), None),
                (t[int, ...], (marsh.MISSING,), None),
            ) for t in _DynamicTupleTypes
        ),
        (),
    ),
)
def test_unmarshal_dynamic_tuple_type_fails(
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
                (s[int], ('a',), None),
                (s[int], (marsh.MISSING,), None),
            ) for s in (
                _DynamicSequenceTypes
                + _DynamicMutableSequenceTypes
            )
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
