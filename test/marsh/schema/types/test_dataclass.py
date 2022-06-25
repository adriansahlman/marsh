import dataclasses
from typing import (
    Any,
    ClassVar,
    List,
    Optional,
    Tuple,
    Type,
)

import pytest

import marsh.testing


@dataclasses.dataclass
class A:
    int_field: int = 0
    str_field: str = 'a'
    int_sequence_field: Tuple[int, int] = (0, 1)
    float_sequence_field: List[float] = \
        dataclasses.field(default_factory=lambda: [0.5, 1.5])


@dataclasses.dataclass
class B:
    a: A = dataclasses.field(default_factory=A)
    a_sequence: List[A] = \
        dataclasses.field(default_factory=lambda: [A(), A()])


@dataclasses.dataclass
class E:
    a: A


@dataclasses.dataclass
class WithoutArgs:
    pass


@dataclasses.dataclass
class WithClassVar:

    a: ClassVar[int]


@dataclasses.dataclass
class WithClassVarWithDefault:

    a: ClassVar[int] = 3


@dataclasses.dataclass
class WithoutInit:

    a: int = dataclasses.field(init=False)

    def __post_init__(
        self,
    ) -> None:
        self.a = 0


@dataclasses.dataclass(eq=False)
class WithInitVar:

    a: dataclasses.InitVar[int] = 0

    def __post_init__(
        self,
        a,
    ) -> None:
        self.a = a

    def __eq__(
        self,
        other,
    ) -> bool:
        if not type(other) == type(self):
            return False
        return other.a == self.a


A_dict = {
    'int_field': 0,
    'str_field': 'a',
    'int_sequence_field': (0, 1),
    'float_sequence_field': (0.5, 1.5),
}

B_dict = {
    'a': A_dict,
    'a_sequence': (A_dict, A_dict),
}

A_altered_dict = A_dict.copy()
A_altered_dict['int_field'] = 3


@pytest.mark.parametrize(
    'value,element',
    (
        (A(), A_dict),
        (A(int_field=3), A_altered_dict),
        (B(), B_dict),
        (WithClassVar(), {}),
        (WithClassVarWithDefault(), {}),
        (WithoutInit(), {}),
        (WithInitVar(), {}),
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
        (A, marsh.MISSING, A()),
        (A, {}, A()),
        (A, (), A()),
        (A, A_dict, A()),
        (B, B_dict, B()),
        (WithClassVar, {}, WithClassVar()),
        (WithClassVarWithDefault, {}, WithClassVarWithDefault()),
        (WithoutInit, {}, WithoutInit()),
        (WithInitVar, marsh.MISSING, WithInitVar(0)),
        (WithInitVar, {}, WithInitVar(0)),
        (WithInitVar, {'a': 3}, WithInitVar(3)),
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
        (A, None, None),
        (A, '', None),
        (A, ('a',), None),
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
