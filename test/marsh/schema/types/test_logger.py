import logging
from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh.testing

loggerAlevelDEBUG = logging.getLogger(name='A')
loggerAlevelDEBUG.setLevel(logging.DEBUG)
loggerBlevelINFO = logging.getLogger(name='B')
loggerBlevelINFO.setLevel(logging.INFO)
loggerClevelCRITICAL = logging.getLogger(name='C')
loggerClevelCRITICAL.setLevel(logging.CRITICAL)
loggerDlevelNOTSET = logging.getLogger(name='D')
loggerElevel17 = logging.getLogger(name='E')
loggerElevel17.setLevel(17)
logger_levelWARNING = logging.getLogger()


@pytest.mark.parametrize(
    'value,element',
    (
        (loggerAlevelDEBUG, dict(name='A', level='DEBUG')),
        (loggerBlevelINFO, dict(name='B', level='INFO')),
        (loggerClevelCRITICAL, dict(name='C', level='CRITICAL')),
        (loggerDlevelNOTSET, dict(name='D')),
        (loggerElevel17, dict(name='E', level=17)),
        (logger_levelWARNING, dict(name='root', level='WARNING')),
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
    'element,value',
    (
        (dict(name='A', level='DEBUG'), loggerAlevelDEBUG),
        (dict(name='B', level='INFO'), loggerBlevelINFO),
        (dict(name='C', level='CRITICAL'), loggerClevelCRITICAL),
        (dict(name='D'), loggerDlevelNOTSET),
        ('D', loggerDlevelNOTSET),
        (dict(name='E', level=17), loggerElevel17),
        ({}, logger_levelWARNING),
        (marsh.MISSING, logger_levelWARNING),
    ),
)
def test_unmarshal_succeeds(
    element: marsh.element.ElementType,
    value: Any,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=logging.Logger,
        element=element,
        value=value,
    )


@pytest.mark.parametrize(
    'element,exception',
    (
        (dict(wrong=3), None),
        (None, None),
    ),
)
def test_unmarshal_fails(
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=logging.Logger,
        element=element,
        exception=exception,
    )
