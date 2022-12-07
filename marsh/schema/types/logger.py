import logging
from typing import (
    Any,
    Literal,
    Mapping,
    Union,
)

import marsh


Arg = Union[str, Mapping[Literal['name', 'level'], Union[int, str]]]


@marsh.schema.register
class LoggerMarshalSchema(marsh.schema.MarshalSchema):

    value: logging.Logger

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, logging.Logger)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~logging.Logger`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals a python logger into a mapping '
            'with keys ``"name"`` and ``"level"``.'
        )

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        element: dict = dict(name=self.value.name)
        level = logging.getLevelName(self.value.level)
        if level == 'NOTSET':
            return element
        element.update(level=level)
        try:
            if level.startswith('Level '):
                element.update(level=int(level.split(' ')[-1]))
        except Exception:
            pass
        return element


@marsh.schema.register
class LoggerUnmarshalSchema(marsh.schema.UnmarshalSchema[logging.Logger]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return value is logging.Logger

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~logging.Logger`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'A python logging.Logger. If no '
            'arguments are given the root '
            'logger is used. Takes either '
            'a single string which is used as name '
            'for the logger or a mapping with optional '
            'keys "name" and "level". The level can be '
            'given as a string or an integer.'
        )

    def doc_field_type(
        self,
    ) -> str:
        return 'Logger(...)'

    def doc_description(
        self,
    ) -> str:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> logging.Logger:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            return logging.getLogger()
        try:
            arg: Arg = marsh.unmarshal(Arg, element)  # type: ignore
        except Exception:
            raise marsh.errors.UnmarshalError(
                (
                    'failed to unmarshal input element into a '
                    'string or mapping with optional keys `name` '
                    'and `level`'
                ),
                element=element,
                type=self.value,
            )
        if isinstance(arg, str):
            return logging.getLogger(arg)
        if 'name' in arg:
            logger = logging.getLogger(str(arg['name']))
        else:
            logger = logging.getLogger()
        if 'level' in arg:
            try:
                logger.setLevel(arg['level'])
            except Exception:
                raise marsh.errors.UnmarshalError(
                    f'could not set logging level to "{arg["level"]}"',
                    element=element,
                    type=type,
                )
        return logger
