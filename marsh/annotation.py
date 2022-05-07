"""Annotations that can be used with :data:`typing.Annotated`.

Annotations may be used to customize the unmarshaling behavior
through transforms or validations.

.. code-block:: python

    from typing import Annotated
    import marsh

    UnsignedInt = Annotated[int, marsh.annotation.Unsigned]
    value = marsh.unmarshal(UnsignedInt, 5)  # works
    value = marsh.unmarshal(UnsignedInt, -5)  # fails


Create your own annotations by inheriting :class:`~marsh.annotation.Annotation`.

.. code-block:: python

    from typing import Annotated
    import marsh

    class Abs(marsh.annotation.Annotation):

        def __call__(
            self,
            value
        ):
            return abs(value)

    AbsInt = Annotated[int, Abs]
    assert marsh.unmarshal(AbsInt, -5) == 5
"""
import numbers
from typing import (
    Any,
    Sized,
    TypeVar,
)


_T = TypeVar('_T', bound=Any)
_NumberType = TypeVar('_NumberType', bound=numbers.Number)
_SizedType = TypeVar('_SizedType', bound=Sized)


class Annotation:
    """Base class for annotations recognized by :mod:`marsh`.

    These can be used with :data:`typing.Annotated` to include
    validation or transformation of the unmarshal result."""

    def __call__(
        self,
        value: _T,
    ) -> _T:
        """Validate and/or transform the input value.

        Arguments:
            value: The input value.

        Returns:
            The validated and/or transformed value.
        """
        return value


class Positive(Annotation):
    """Validate that a number is non-zero and positive."""

    def __call__(
        self,
        value: _NumberType,
    ) -> _NumberType:
        if value <= 0:  # type: ignore
            raise ValueError(
                f'positive value required, got {value}',
            )
        return value


class Negative(Annotation):
    """Validate that a number is non-zero and negative."""

    def __call__(
        self,
        value: _NumberType,
    ) -> _NumberType:
        if value >= 0:  # type: ignore
            raise ValueError(
                f'negative value required, got {value}',
            )
        return value


class Unsigned(Annotation):
    """Validate that a number is zero or higher."""

    def __call__(
        self,
        value: _NumberType,
    ) -> _NumberType:
        if value < 0:  # type: ignore
            raise ValueError(
                f'unsigned value required, got {value}',
            )
        return value


class Populated(Annotation):
    """Validate that a collection contains at least one item."""

    def __call__(
        self,
        value: _SizedType,
    ) -> _SizedType:
        if len(value) == 0:
            raise ValueError(
                f'value must have size larger than 0: {value}',
            )
        return value
