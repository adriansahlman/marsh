from typing import (
    Any,
    Iterator,
    Optional,
    Type,
)

import pytest

import marsh.testing


class IterableClass:

    def __iter__(
        self,
    ) -> Iterator[int]:
        for i in range(3):
            yield i


class IteratorClass:

    def __init__(
        self,
    ) -> None:
        self.i = -1

    def __next__(
        self,
    ) -> int:
        self.i += 1
        if self.i >= 3:
            raise StopIteration
        return self.i

    def __iter__(
        self,
    ) -> Iterator[int]:
        return self


class WithoutArgs:

    def __init__(
        self,
    ) -> None:
        pass

    def __eq__(
        self,
        other,
    ) -> bool:
        if type(other) == self.__class__:
            return True
        return False


class A:

    def __init__(
        self,
        a,
        b,
    ):
        self.a = a
        self.b = b

    def __eq__(
        self,
        other,
    ):
        if not isinstance(other, self.__class__):
            return False
        return (self.a, self.b) == (other.a, other.b)

    def __str__(
        self,
    ) -> str:
        return f'{self.__class__.__name__}(a={self.a}, b={self.b})'

    def __repr__(
        self,
    ) -> str:
        return str(self)


class B(A):  # noqa: B903

    def __init__(
        self,
        a: int,
        b: bool,
    ):
        self.a = a
        self.b = b


class X:

    def __init__(
        self,
        *args: bool,
        optional_keyword: Optional[Any] = None,
        **kwargs: float,
    ) -> None:
        self.args = args
        self.optional_keyword = optional_keyword
        self.kwargs = kwargs

    def __eq__(
        self,
        other,
    ):
        if not isinstance(other, self.__class__):
            return False
        return (self.args, self.optional_keyword, self.kwargs) == \
            (other.args, other.optional_keyword, other.kwargs)

    def __str__(
        self,
    ) -> str:
        return (
            f'C(args={self.args}, '
            f'optional_keyword={self.optional_keyword}, '
            f'kwargs={self.kwargs})'
        )

    def __repr__(
        self,
    ) -> str:
        return str(self)


class Echo:

    def __call__(
        self,
        x: int,
    ) -> int:
        return x


def echo(
    x: int,
) -> int:
    return x


def positional_only(
    x: int,
    /,
    y: int,
) -> int:
    return x + y


@pytest.mark.parametrize(
    'value,element',
    (
        (IteratorClass(), (0, 1, 2)),
        (IterableClass(), (0, 1, 2)),
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
        (WithoutArgs, {}, WithoutArgs()),
        (WithoutArgs, (), WithoutArgs()),
        (WithoutArgs, marsh.MISSING, WithoutArgs()),
        (A, {'a': 0, 'b': 1}, A(0, 1)),
        (A, {'a': '0', 'b': '1'}, A('0', '1')),
        (A, {'a': '"0"', 'b': '"1"'}, A('"0"', '"1"')),
        (B, {'a': '0', 'b': 'true'}, B(0, True)),
        (X, {}, X()),
        (X, marsh.MISSING, X()),
        (X, {'a': '0.5'}, X(a=0.5)),
        (X, ['false', True], X(False, True)),
        (X, {'optional_keyword': None, 'a': '0.5'}, X(a=0.5)),
        (X, {'optional_keyword': '0', 'a': '0.5'}, X(optional_keyword='0', a=0.5)),
        (Echo(), (5,), 5),
        (echo, (5,), 5),
        (positional_only, dict(x=5, y=3), 8),
        (positional_only, (5, 3), 8),
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
        (B, {'a': '0', 'b': None}, None),
        (A, marsh.MISSING, marsh.errors.MissingValueError),
        (B, marsh.MISSING, marsh.errors.MissingValueError),
        (X, {'args': None}, None),
        (X, {'args': {}}, None),
        (X, {'args': ('a')}, None),
        (X, {'kwargs': None}, None),
        (X, {'kwargs': ()}, None),
        (X, {'kwargs': {'a': 'b'}}, None),
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
