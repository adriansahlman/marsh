import inspect
from typing import (
    Any,
    Iterable,
    Mapping,
    Sequence,
    TypeVar,
)


import marsh


_T = TypeVar('_T')


GENERIC_PRIORITY = -10


@marsh.schema.register(priority=GENERIC_PRIORITY)
class GenericMappingMarshalSchema(marsh.schema.MarshalSchema):

    value: marsh.utils.MappingProtocol

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~marsh.utils.MappingProtocol`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals mapping values matched through ducktyping.'
            'Uses :class:`~marsh.utils.MappingProtocol` as reference '
            'for the ducktyped match. Marshaling outputs a JSON-style '
            'map.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_mapping(value)

    def marshal(
        self,
    ) -> dict:
        return {
            str(key): marsh.marshal(self.value[key])
            for key in self.value.keys()
        }


@marsh.schema.register(priority=GENERIC_PRIORITY)
class GenericSequenceMarshalSchema(marsh.schema.MarshalSchema):

    value: marsh.utils.SequenceProtocol

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~marsh.utils.SequenceProtocol`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals sequence values matched through ducktyping.'
            'Uses :class:`~marsh.utils.SequenceProtocol` as reference '
            'for the ducktyped match. Marshaling outputs a JSON-style '
            'list.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_sequence(value)

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return tuple(
            marsh.marshal(self.value[i])
            for i in range(len(self.value))
        )


@marsh.schema.register(
    priority=GENERIC_PRIORITY,
    higher_priority=(
        GenericMappingMarshalSchema,
        GenericSequenceMarshalSchema,
    ),
)
class GenericIterableMarshalSchema(marsh.schema.MarshalSchema):

    value: Iterable

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        if not marsh.utils.is_obj_instance(value):
            return False
        try:
            iter(value)
            return True
        except TypeError:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return '``Iterable``'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Fetches and marshals all items in an iterable.'
        )

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return tuple(marsh.marshal(item) for item in self.value)


@marsh.schema.register(priority=GENERIC_PRIORITY)
class GenericCallableUnmarshalSchema(marsh.schema.template.CallableUnmarshalSchema[_T]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            if not marsh.utils.is_callable(value):
                return False
            # make sure value can have signature inspected
            inspect.signature(value)
            return True
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return '``Callable``'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Covers anything that is callable, be it a class, '
            'function or callable class instance. '
            'Callable arguments are inspected and the input '
            'should be a sequence or mapping(similar to '
            '`*args` or `**kwargs`).'
        )


@marsh.schema.register(
    priority=GENERIC_PRIORITY,
    higher_priority=GenericCallableUnmarshalSchema,
)
class GenericMappingUnmarshalSchema(
    marsh.schema.template.MappingUnmarshalSchema[marsh.utils.MappingProtocol],
):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        k, v = marsh.utils.inspect_mapping_type(self.value)
        self.key_schema = marsh.schema.UnmarshalSchema(k)
        self.value_schema = marsh.schema.UnmarshalSchema(v)

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~marsh.utils.MappingProtocol`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals mapping types matched through ducktyping.'
            'Uses :class:`~marsh.utils.MappingProtocol` as reference '
            'for the ducktyped match. Expects input to be a JSON-style '
            'map during unmarshaling.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_mapping_type(value)

    def construct(
        self,
        value: Mapping[Any, Any],
    ) -> marsh.utils.MappingProtocol:
        value_type = marsh.utils.get_type(self.value)
        is_abstract = False
        try:
            is_abstract = inspect.isabstract(value_type)
        except Exception:
            pass
        if not is_abstract:
            return super().construct(value)
        return dict(value)


@marsh.schema.register(
    priority=GENERIC_PRIORITY,
    higher_priority=GenericCallableUnmarshalSchema,
)
class GenericSequenceUnmarshalSchema(
    marsh.schema.template.SequenceUnmarshalSchema[marsh.utils.SequenceProtocol],
):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.value_schema = marsh.schema.UnmarshalSchema(
            marsh.utils.inspect_sequence_type(self.value),
        )

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~marsh.utils.SequenceProtocol`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unmarshals sequence types matched through ducktyping.'
            'Uses :class:`~marsh.utils.SequenceProtocol` as reference '
            'for the ducktyped match. Expects input to be a JSON-style '
            'list during unmarshaling.'
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return marsh.utils.is_sequence_type(value)

    def construct(
        self,
        value: Sequence,
    ) -> marsh.utils.SequenceProtocol:
        value_type = marsh.utils.get_type(self.value)
        try:
            is_abstract = inspect.isabstract(value_type)
        except Exception:
            pass
        if is_abstract:
            return list(value)
        return super().construct(value)
