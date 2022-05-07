import dataclasses
from typing import Optional

import pytest
import marsh


@pytest.fixture(autouse=True)
def clear_registry():
    for name in tuple(marsh.namespaces):
        marsh.namespaces[name].cache_clear()
        del marsh.namespaces[name]


def test_register():

    class Base:
        pass

    namespace = marsh.namespaces.new('test_register', Base)

    @namespace.register(name='a')
    class A(Base):
        pass

    @namespace.register(name='b')
    class B(Base):
        pass

    assert 'a' in namespace
    assert 'b' in namespace

    assert len(tuple(namespace.find_subclasses(Base))) == 2
    assert len(tuple(marsh.namespaces.find_subclasses(Base))) == 2

    a = marsh.unmarshal(Base, dict(name='a'))
    assert a.__class__ == A

    b = marsh.unmarshal(Base, dict(name='b'))
    assert b.__class__ == B

    with pytest.raises(Exception):
        @namespace.register(name='c')
        class CWithoutBase:
            pass

    with pytest.raises(Exception):
        @namespace.register(name='b')
        class CWithoutReplace(Base):
            pass

    @namespace.register(name='b', replace=True)
    class C(Base):
        pass

    b = marsh.unmarshal(Base, dict(name='b'))
    assert b.__class__ == C


def test_recursion():

    class Base:
        pass

    namespace = marsh.namespaces.new('test_recursion', Base)

    @namespace.register(name='b')
    @dataclasses.dataclass
    class B(Base):
        y: int = 1

    @namespace.register(name='a')
    @dataclasses.dataclass
    class A(Base):
        b: B
        a: Optional['A'] = None  # noqa: F821
        x: int = 0

    schema = marsh.schema.UnmarshalSchema(Base)

    a = schema.unmarshal(
        dict(
            name='a',
            b=dict(
                name='b',
                y=2,
            ),
            a=dict(
                name='a',
                x=3,
            ),
            x=4,
        ),
    )
    assert type(a) == A


def test_build() -> None:

    int_namespace = marsh.namespaces.new('int', int)

    @int_namespace.register(name='a')
    class AInt(int):
        pass

    @int_namespace.register(name='b')
    class BInt(int):
        pass

    integ = marsh.unmarshal(int, 1)
    assert type(integ) == int
    assert integ == 1

    a_int = int_namespace.build(1, name='a')
    assert type(a_int) == AInt
    assert a_int == 1

    b_int = int_namespace.build(1, name='b')
    assert type(b_int) == BInt
    assert b_int == 1

    list_namespace = marsh.namespaces.new('list', list)

    @list_namespace.register(name='a')
    class AList(list):
        pass

    @list_namespace.register(name='b')
    class BList(list):
        pass

    lst = marsh.unmarshal(list, [1, 2, 3])
    assert type(lst) == list
    assert lst == [1, 2, 3]

    a_list = list_namespace.build([1, 2, 3], name='a')
    assert type(a_list) == AList
    assert a_list == [1, 2, 3]

    b_list = list_namespace.build([1, 2, 3], name='b')
    assert type(b_list) == BList
    assert b_list == [1, 2, 3]


def test_many() -> None:

    @dataclasses.dataclass
    class A:
        pass

    @dataclasses.dataclass
    class B:
        pass

    namespace_a = marsh.namespaces.new('a', A)
    namespace_b = marsh.namespaces.new('b', B)

    # make sure separate cache wrappers are used.
    assert namespace_a.find_class is not namespace_b.find_class
    assert namespace_a.find_subclasses is not namespace_b.find_subclasses

    @namespace_a.register(name='1')
    class A1(A):
        pass

    @namespace_b.register(name='1')
    class B1(B):
        pass

    a1 = marsh.unmarshal(A, dict(name='1'))
    assert isinstance(a1, A1)
    b1 = marsh.unmarshal(B, dict(name='1'))
    assert isinstance(b1, B1)
    a1 = marsh.unmarshal(A, dict(name='1'))
    assert isinstance(a1, A1)
    b1 = marsh.unmarshal(B, dict(name='1'))
    assert isinstance(b1, B1)
