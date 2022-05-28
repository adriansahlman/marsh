import inspect
import types
from typing import (
    Any,
    ForwardRef,
    TypeVar,
    get_type_hints,
)

import marsh
from . import structured


_T = TypeVar('_T')


class CallableUnmarshalSchema(structured.StructuredUnmarshalSchema[_T]):
    """Unmarshals the arguments to a callable and uses them to call it."""

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        try:
            sig = inspect.signature(self.value)
        except Exception:
            raise ValueError(
                f'failed to retrieve callable signature: {self.value}',
            )
        try:
            if inspect.isclass(self.value):
                annotations = get_type_hints(self.value.__init__)
            else:
                annotations = get_type_hints(self.value)
        except Exception:
            annotations = {}
        positional = {}
        keyword = {}
        var_positional = None
        var_keyword = None
        for name, param in sig.parameters.items():
            if (
                param.annotation is param.empty
                or isinstance(param.annotation, (str, ForwardRef))
            ):
                type_ = annotations.get(name, Any)
            else:
                type_ = param.annotation
            default = marsh.MISSING
            if param.default is not param.empty:
                default = param.default
            with marsh.errors.prepend(name):
                schema = marsh.schema.UnmarshalSchema(type_, default=default)
            if param.kind == param.POSITIONAL_ONLY:
                positional[name] = schema
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                keyword[name] = schema
            elif param.kind == param.KEYWORD_ONLY:
                keyword[name] = schema
            elif param.kind == param.VAR_POSITIONAL:
                var_positional = (name, schema)
            elif param.kind == param.VAR_KEYWORD:
                var_keyword = (name, schema)
        self.positional = tuple(positional)
        schemas = {}
        schemas.update(positional)
        if var_positional:
            name, schema = var_positional
            schemas[f'*{name}'] = schema
        schemas.update(keyword)
        if var_keyword:
            name, schema = var_keyword
            schemas[f'**{name}'] = schema
        self.schemas = types.MappingProxyType(schemas)
