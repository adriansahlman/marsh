from typing import (
    Any,
    Iterator,
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
