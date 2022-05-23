import datetime
from typing import (
    Any,
    Optional,
    Type,
)

import pytest

import marsh
import marsh.testing


dt = datetime.datetime.now(datetime.timezone.utc)


@pytest.mark.parametrize(
    'value,element',
    (
        (dt, dt.isoformat()),
        (dt.date(), dt.date().isoformat()),
        (dt.time(), dt.time().isoformat()),
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
        (
            datetime.datetime,
            dt.timestamp(),
            dt,
        ),
        (
            datetime.datetime,
            str(dt.timestamp()),
            dt,
        ),
        (
            datetime.date,
            dt.timestamp(),
            dt,
        ),
        (
            datetime.date,
            str(dt.timestamp()),
            dt,
        ),
        (
            datetime.time,
            dt.timestamp(),
            dt.time(),
        ),
        (
            datetime.time,
            str(dt.timestamp()),
            dt.time(),
        ),
        (
            datetime.datetime,
            '12/12/12',
            datetime.datetime(2012, 12, 12, 0, 0),
        ),
        (
            datetime.date,
            '12/12/12',
            datetime.datetime(2012, 12, 12, 0, 0),
        ),
        (
            datetime.time,
            '12/12/12',
            datetime.datetime(2012, 12, 12, 0, 0).time(),
        ),
        (
            datetime.datetime,
            'Fri, 12 Dec 2014 10:55:50',
            datetime.datetime(2014, 12, 12, 10, 55, 50),
        ),
        (
            datetime.datetime,
            '18-12-15 06:00',
            datetime.datetime(2015, 12, 18, 6, 0),
        ),
    ),
)
@pytest.mark.filterwarnings('ignore:The localize method')
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
        (datetime.datetime, 'abc', None),
        (datetime.datetime, marsh.MISSING, marsh.errors.MissingValueError),
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
