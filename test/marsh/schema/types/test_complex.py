import numbers
from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh
import marsh.testing


class CustomComplex(numbers.Complex):

    def __init__(
        self,
        real: float = 0,
        imag: float = 0,
    ) -> None:
        self._real = real
        self._imag = imag

    def __complex__(
        self,
    ) -> complex:
        return complex(self._real, self._imag)

    @property
    def real(self):
        return self._real

    @property
    def imag(self):
        return self._imag

    def __add__(self, other):
        ...

    def __hash__(self):
        ...

    def __radd__(self, other):
        ...

    def __neg__(self):
        ...

    def __pos__(self):
        ...

    def __mul__(self, other):
        ...

    def __rmul__(self, other):
        ...

    def __truediv__(self, other):
        ...

    def __rtruediv__(self, other):
        ...

    def __pow__(self, exponent):
        ...

    def __rpow__(self, base):
        ...

    def __abs__(self):
        ...

    def conjugate(self):
        ...

    def __eq__(self, other):
        ...


@pytest.mark.parametrize(
    'value,element',
    (
        (complex(), dict(real=0, imag=0)),
        (complex(1.5), dict(real=1.5, imag=0)),
        (complex(imag=2.5), dict(real=0, imag=2.5)),
        (CustomComplex(1.1, 2.2), dict(real=1.1, imag=2.2)),
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
    (
        complex,
        numbers.Complex,
    ),
)
@pytest.mark.parametrize(
    'element,value',
    (
        (1.5, complex(1.5)),
        ('1.5e+1', complex(15)),
        ((), complex()),
        ({}, complex()),
        (('1.5',), complex(1.5)),
        ((0, '2.5'), complex(imag=2.5)),
        (('1e-1', 2.5), complex(0.1, 2.5)),
        (dict(real='1.5e+0'), complex(1.5)),
        (dict(imag=1.5), complex(imag=1.5)),
        (dict(real=0.5, imag=1.5), complex(0.5, 1.5)),
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
    'type_',
    (
        complex,
        numbers.Complex,
    ),
)
@pytest.mark.parametrize(
    'element,exception',
    (
        (marsh.MISSING, marsh.errors.MissingValueError),
        (dict(real='test'), None),
        (dict(real=0, wrong=1), None),
        ((1, 2, 3), None),
        (None, None),
        ('test', None),
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
