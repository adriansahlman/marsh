import re
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    Tuple,
)

import marsh


slice_pattern = re.compile(
    r'^\s*(-?\s*\d+\s*)?:\s*(-?\s*\d+\s*)?(:\s*(-?\s*\d+)?)?\s*$',
)


@marsh.schema.register
class SliceMarshalSchema(marsh.schema.MarshalSchema):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, slice)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`slice`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals a :class:`slice` into a mapping with '
            'the keys ``"start"``, ``"stop"`` and ``"step"``.'
        )

    def marshal(
        self,
    ) -> marsh.element.MappingElementType:
        return dict(
            start=self.value.start,
            stop=self.value.stop,
            step=self.value.step,
        )


@marsh.schema.register
class SliceUnmarshalSchema(marsh.schema.UnmarshalSchema[slice]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return value is slice
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`slice`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Accepts input as strings in the python slicing format '
            '(i.e. "1:2", "::-1" e.t.c). '
            'Also accepts keys "start", "stop" and/or "step" or '
            'a sequence of up to 3 optional integer values. '
            'If a single integer is given, it is treated as "stop"'
        )

    def doc_field_type(
        self,
    ) -> str:
        return '<slice>'

    def doc_description(self) -> Optional[str]:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> slice:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            element = ()
        args: Tuple[Optional[int], ...]
        if marsh.utils.is_mapping(element):
            kwargs: Dict[str, Optional[int]] = marsh.cast(
                Dict[Literal['start', 'stop', 'step'], Optional[int]],  # type: ignore
                element,
            )
            args = tuple(kwargs.get(key, None) for key in ('start', 'stop', 'step'))
        elif marsh.utils.is_sequence(element):
            args = marsh.cast(Tuple[Optional[int], ...], element)  # type: ignore
            if len(args) > 3:
                raise marsh.errors.UnmarshalError(
                    f'at most 3 optional integers may be used to construct a '
                    f'slice. Got {len(element)} values',
                )
        else:
            element = str(element)
            if not slice_pattern.match(element):
                raise marsh.errors.UnmarshalError(
                    'invalid slice syntax',
                    element=element,
                    type=self.value,
                )
            args = tuple(
                int(index) if index else None
                for index
                in element.split(':')
            )
        if not args:
            return slice(None)
        try:
            return slice(*args)
        except Exception as err:
            raise marsh.errors.UnmarshalError(
                f'failed to construct: {err}',
                element=element,
                type=self.value,
            ) from err
