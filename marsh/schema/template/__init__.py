"""A set of template implementations of schemas.

These templates are useful as base classes when extending
the framework to support more types."""
from .callable import CallableUnmarshalSchema
from .mapping import MappingUnmarshalSchema
from .sequence import SequenceUnmarshalSchema
from .structured import StructuredUnmarshalSchema
from .union import UnionUnmarshalSchema


__all__ = (
    'CallableUnmarshalSchema',
    'MappingUnmarshalSchema',
    'SequenceUnmarshalSchema',
    'StructuredUnmarshalSchema',
    'UnionUnmarshalSchema',
)
