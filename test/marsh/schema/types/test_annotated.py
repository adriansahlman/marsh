import typing
import typing_extensions
from typing import (
    Any,
    Dict,
    Optional,
    Type,
)

import pytest

import marsh
import marsh.testing


_AnnotatedTypes: list = []


for mod in (typing, typing_extensions):
    try:
        _AnnotatedTypes.append(mod.Annotated)
    except Exception:
        pass


class PreAnnotation(marsh.annotation.PreAnnotation):

    def __call__(
        self,
        element: marsh.element.ElementType,
    ) -> marsh.element.ElementType:
        if element == 'zero':
            return 0
        if element == 'one':
            return 1
        return element


@pytest.mark.parametrize(
    'type_,element,value',
    sum(
        (
            (
                (
                    Annotated[int, None, None],
                    1,
                    1,
                ),
                (
                    Annotated[Dict[int, float], None, None],
                    {1: 1.5},
                    {1: 1.5},
                ),
                (
                    Annotated[list, None],
                    marsh.MISSING,
                    [],
                ),
                (
                    Annotated[int, marsh.annotation.Positive],
                    1,
                    1,
                ),
                (
                    Annotated[float, marsh.annotation.Positive],
                    0.5,
                    0.5,
                ),
                (
                    Annotated[int, marsh.annotation.Negative],
                    -1,
                    -1,
                ),
                (
                    Annotated[float, marsh.annotation.Negative],
                    -0.5,
                    -0.5,
                ),
                (
                    Annotated[int, marsh.annotation.Unsigned],
                    0,
                    0,
                ),
                (
                    Annotated[float, marsh.annotation.Unsigned],
                    0.0,
                    0.0,
                ),
                (
                    Annotated[list, marsh.annotation.Populated],
                    (1, 2),
                    [1, 2],
                ),
                (
                    Annotated[int, marsh.annotation.Positive()],
                    1,
                    1,
                ),
                (
                    Annotated[float, marsh.annotation.Positive()],
                    0.5,
                    0.5,
                ),
                (
                    Annotated[int, marsh.annotation.Negative()],
                    -1,
                    -1,
                ),
                (
                    Annotated[float, marsh.annotation.Negative()],
                    -0.5,
                    -0.5,
                ),
                (
                    Annotated[int, marsh.annotation.Unsigned()],
                    0,
                    0,
                ),
                (
                    Annotated[float, marsh.annotation.Unsigned()],
                    0.0,
                    0.0,
                ),
                (
                    Annotated[list, marsh.annotation.Populated()],
                    (1, 2),
                    [1, 2],
                ),
                (
                    Annotated[int, PreAnnotation],
                    'zero',
                    0,
                ),
                (
                    Annotated[int, PreAnnotation()],
                    'one',
                    1,
                ),
                (
                    Annotated[int, PreAnnotation],
                    3,
                    3,
                ),
                (
                    Annotated[int, PreAnnotation()],
                    '1',
                    1,
                ),
            )
            for Annotated in _AnnotatedTypes
        ),
        (),
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
    sum(
        (
            (
                (
                    Annotated[int, None, None],
                    'a',
                    None,
                ),
                (
                    Annotated[Dict[int, float], None, None],
                    {'a': 1.5},
                    None,
                ),
                (
                    Annotated[Dict[int, float], None, None],
                    {1: 'a'},
                    None,
                ),
                (
                    Annotated[Dict[int, float], None, None],
                    {1: 'a'},
                    None,
                ),
                (
                    Annotated[int, marsh.annotation.Positive],
                    0,
                    ValueError,
                ),
                (
                    Annotated[float, marsh.annotation.Positive],
                    -0.5,
                    ValueError,
                ),
                (
                    Annotated[float, marsh.annotation.Unsigned],
                    -0.5,
                    ValueError,
                ),
                (
                    Annotated[int, marsh.annotation.Unsigned],
                    -1,
                    ValueError,
                ),
                (
                    Annotated[int, marsh.annotation.Negative],
                    0,
                    ValueError,
                ),
                (
                    Annotated[float, marsh.annotation.Negative],
                    0.5,
                    ValueError,
                ),
                (
                    Annotated[list, marsh.annotation.Populated],
                    (),
                    ValueError,
                ),
                (
                    Annotated[tuple, marsh.annotation.Populated],
                    (),
                    ValueError,
                ),
                (
                    Annotated[list, marsh.annotation.Populated],
                    marsh.MISSING,
                    ValueError,
                ),
                (
                    Annotated[int, marsh.annotation.Positive()],
                    0,
                    ValueError,
                ),
                (
                    Annotated[float, marsh.annotation.Positive()],
                    -0.5,
                    ValueError,
                ),
                (
                    Annotated[float, marsh.annotation.Unsigned()],
                    -0.5,
                    ValueError,
                ),
                (
                    Annotated[int, marsh.annotation.Unsigned()],
                    -1,
                    ValueError,
                ),
                (
                    Annotated[int, marsh.annotation.Negative()],
                    0,
                    ValueError,
                ),
                (
                    Annotated[float, marsh.annotation.Negative()],
                    0.5,
                    ValueError,
                ),
                (
                    Annotated[list, marsh.annotation.Populated()],
                    (),
                    ValueError,
                ),
                (
                    Annotated[tuple, marsh.annotation.Populated()],
                    (),
                    ValueError,
                ),
                (
                    Annotated[list, marsh.annotation.Populated()],
                    marsh.MISSING,
                    ValueError,
                ),
            )
            for Annotated in _AnnotatedTypes
        ),
        (),
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
