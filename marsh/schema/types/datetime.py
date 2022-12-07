import datetime
from typing import (
    Any,
    Optional,
    Union,
)

import dateparser

import marsh


@marsh.schema.register
class DatetimeMarshalSchema(marsh.schema.MarshalSchema):
    """Marshals into string formatted according to ISO."""

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(
                value,
                (
                    datetime.time,
                    datetime.date,
                ),
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return (
            ':class:`datetime.datetime`, '
            ':class:`datetime.time`, '
            ':class:`datetime.date`'
        )

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals a datetime object into formatted string '
            'according to ISO. See :func:`datetime.datetime.isoformat`, .'
            ':func:`datetime.time.isoformat` and :func:`datetime.date.isoformat`.'
        )

    def marshal(
        self,
    ) -> str:
        return self.value.isoformat()


@marsh.schema.register
class DatetimeUnmarshalSchema(
    marsh.schema.UnmarshalSchema[
        Union[datetime.date, datetime.time],
    ],
):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return issubclass(
                value,
                (
                    datetime.time,
                    datetime.date,
                ),
            )
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return (
            ':class:`datetime.datetime`, '
            ':class:`datetime.time`, '
            ':class:`datetime.date`'
        )

    @staticmethod
    def doc_static_description() -> str:
        return (
            'For string inputs the format must be compatible '
            'with :func:`dateparser.parse`. The date order is '
            'D M Y, not M D Y. A float value can also be '
            'used as input in which case it is treated as a unix '
            'timestamp. A mapping or sequence as input will be passed '
            'directly to datetime as keyword or positional arguments.'
        )

    def doc_type(
        self,
    ) -> str:
        return 'datetime'

    def doc_field_type(
        self,
    ) -> str:
        return '<datetime>'

    def doc_description(
        self,
    ) -> str:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> Union[datetime.time, datetime.date]:
        if marsh.utils.is_missing(element):
            raise marsh.errors.MissingValueError(
                type=self.value,
            )
        try:
            if marsh.utils.is_mapping(element):
                return self.value(**element)
            elif marsh.utils.is_sequence(element):
                return self.value(*element)
        except Exception as err:
            raise marsh.errors.UnmarshalError(
                f'failed to unmarshal: {err}',
                element=element,
                type=self.value,
            ) from err
        dt: Optional[datetime.datetime] = None
        try:
            ts = marsh.utils.cast_primitive(float, str(element))
            dt = datetime.datetime.fromtimestamp(
                ts,
                datetime.timezone.utc,
            )
        except ValueError:
            if isinstance(element, str):
                dt = dateparser.parse(element, settings={'DATE_ORDER': 'DMY'})
        if dt is None:
            raise marsh.errors.UnmarshalError(
                'failed to parse timestamp',
                element=element,
                type=self.value,
            )
        if self.value == datetime.time:
            return dt.time()
        # datetime is subclass of date
        return dt
