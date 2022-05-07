import collections
from typing import (
    Any,
    NamedTuple,
    Optional,
    Type,
)

import pytest

import marsh.testing


A_legacy = collections.namedtuple('A_legacy', ['a'])


B_legacy = collections.namedtuple('B_legacy', ['a'], defaults=(0,))


C_legacy = collections.namedtuple(
    'C_legacy',
    ['a', 'b'],
    defaults=(A_legacy(0), B_legacy()),
)


class NoArgs(NamedTuple):
    pass


class A(NamedTuple):
    a: int


class B(NamedTuple):
    a: int = 0


class C(NamedTuple):
    a: A
    b: B = B()


@pytest.mark.parametrize(
    'value,element',
    (
        # namedtuple
        (NoArgs(), {}),
        (A_legacy(0), {'a': 0}),
        (A(0), {'a': 0}),
        (C_legacy((2,), B_legacy(3)), dict(a=(2,), b=dict(a=3))),
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
        (NoArgs, (), NoArgs()),
        (NoArgs, marsh.MISSING, NoArgs()),
        (A_legacy, (0,), A_legacy(0)),
        (A_legacy, ('a',), A_legacy('a')),
        (A_legacy, ((0, 1, 2),), A_legacy((0, 1, 2))),
        (A_legacy, {'a': 0}, A_legacy(0)),
        (A_legacy, {'a': 'a'}, A_legacy('a')),
        (A_legacy, {'a': (0, 1, 2)}, A_legacy((0, 1, 2))),
        (B_legacy, marsh.MISSING, B_legacy()),
        (B_legacy, (marsh.MISSING,), B_legacy()),
        (B_legacy, {'a': marsh.MISSING}, B_legacy()),
        (C_legacy, ((2,), (3,)), C_legacy((2,), (3,))),
        (C_legacy, ((2,), marsh.MISSING), C_legacy((2,), B_legacy(0))),
        (C_legacy, {'a': (2,), 'b': (3,)}, C_legacy((2,), (3,))),
        (C_legacy, ((2,),), C_legacy((2,), B_legacy(0))),
        (C_legacy, {'a': {'a': 2}}, C_legacy({'a': 2}, B_legacy(0))),
        (A, (0,), A(0)),
        (A, ('0',), A(0)),
        (A, {'a': '0'}, A(0)),
        (B, (), B()),
        (B, ('1',), B(1)),
        (B, {'a': '1'}, B(1)),
        (B, marsh.MISSING, B()),
        (B, (marsh.MISSING,), B()),
        (B, {'a': marsh.MISSING}, B()),
        (C, ((2,), (3,)), C(A(2), B(3))),
        (C, {'a': ('2',), 'b': ('3',)}, C(A(2), B(3))),
        (C, (('2',),), C(A(2), B(0))),
        (C, {'a': {'a': '2'}}, C(A(2), B(0))),
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
        (A_legacy, (0, 1), None),
        (A_legacy, '', None),
        (A_legacy, (), None),
        (A_legacy, {}, None),
        (A_legacy, {'b': 0}, None),
        (A, (0, 1), None),
        (A, '', None),
        (A, (), None),
        (A, {}, None),
        (A, {'b': 0}, None),
        (B_legacy, '', None),
        (B, '', None),
        (B, (0.1,), None),
        (A_legacy, marsh.MISSING, marsh.errors.MissingValueError),
        (A_legacy, (marsh.MISSING,), marsh.errors.MissingValueError),
        (A_legacy, {'a': marsh.MISSING}, marsh.errors.MissingValueError),
        (A, marsh.MISSING, marsh.errors.MissingValueError),
        (A, (marsh.MISSING,), marsh.errors.MissingValueError),
        (A, {'a': marsh.MISSING}, marsh.errors.MissingValueError),
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
