import typing
import typing_extensions
from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh.testing


_LiteralStringTypes: list = []


for mod in (typing, typing_extensions):
    try:
        _LiteralStringTypes.append(mod.LiteralString)
    except Exception:
        pass


@pytest.mark.parametrize(
    'value,element',
    (
        ('', ''),
        ('0', '0'),
        ('True', 'True'),
        (0, 0),
        (0., 0.),
        ('0.5', '0.5'),
        ('1e-5', '1e-5'),
        (True, True),
        (False, False),
        ('true', 'true'),
        ('false', 'false'),
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
        (str, '', ''),
        (str, 0, '0'),
        (str, 0.5, '0.5'),
        (str, True, 'True'),
        (int, 0, 0),
        (int, '0', 0),
        (int, 0.0, 0),
        (float, 0, 0.0),
        (float, 0.5, 0.5),
        (float, '1e-5', 1e-5),
        (bool, True, True),
        (bool, False, False),
        (bool, 1, True),
        (bool, '1', True),
        (bool, 'True', True),
        (bool, 'true', True),
        (bool, 'y', True),
        (bool, 'yes', True),
        (bool, 'on', True),
        (bool, 0, False),
        (bool, '0', False),
        (bool, 'False', False),
        (bool, 'false', False),
        (bool, 'n', False),
        (bool, 'no', False),
        (bool, 'off', False),
    ) + sum(
        (
            (
                (LiteralString, '', ''),
                (LiteralString, 0, '0'),
                (LiteralString, 0.5, '0.5'),
                (LiteralString, True, 'True'),
            ) for LiteralString in _LiteralStringTypes
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
    (
        (int, 'a', ValueError),
        (int, (), None),
        (int, {}, None),
        (float, 'a', ValueError),
        (float, (), None),
        (float, {}, None),
        (bool, 'a', ValueError),
        (bool, (), None),
        (bool, {}, None),
        (str, (), None),
        (str, {}, None),
        (int, marsh.MISSING, marsh.errors.MissingValueError),
        (float, marsh.MISSING, marsh.errors.MissingValueError),
        (bool, marsh.MISSING, marsh.errors.MissingValueError),
        (str, marsh.MISSING, marsh.errors.MissingValueError),
    ) + sum(
        (
            (
                (LiteralString, (), None),
                (LiteralString, {}, None),
                (LiteralString, marsh.MISSING, marsh.errors.MissingValueError),
            ) for LiteralString in _LiteralStringTypes
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
