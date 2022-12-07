from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
)

import marsh
from .. import UnmarshalSchema


_T = TypeVar('_T')


class StructuredUnmarshalSchema(UnmarshalSchema[_T]):
    """A schema for types with fixed attributes
    that are recursively unmarshaled.

    Supports both positional arguments and keyword
    arguments. Variable versions of these arguments
    (typically ``*args``/``**kwargs``) are also supported
    and are marked by ``*`` or ``**`` infront of their
    names in the :attr:`schemas` attribute of this class."""

    schemas: Mapping[str, UnmarshalSchema]
    """The schemas for the fixed attributes."""

    positional: Sequence[str] = ()
    """Names of attributes that can only be used as positional arguments."""

    def __str__(
        self,
    ) -> str:
        return (
            f'{marsh.utils.get_type_name(self.value)}('
            + ', '.join(
                f'{name}: {schema}'
                for name, schema
                in self.schemas.items()
            )
            + ')'
        )

    def __repr__(
        self,
    ) -> str:
        return (
            f'{super().__repr__()[:-1]}, '
            f'schemas={repr(self.schemas)})'
        )

    def validate_defaults(
        self,
        args: Optional[Sequence] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if args and kwargs:
            for i, name in enumerate(self.schemas):
                if i < len(args) and name in kwargs:
                    raise TypeError(
                        'received the same argument twice '
                        'through `default_args` and '
                        f'`default_kwargs`: {name}',
                    )

    def select(
        self,
        path: str,
    ) -> UnmarshalSchema:
        if not path:
            return self
        field, path = marsh.path.head(path)
        if not field:
            if not path:
                return self
            return self.select(path)
        for name, schema in self.schemas.items():
            if field.strip('*') == name.strip('*'):
                with marsh.errors.prepend(field):
                    return schema.select(path)
        raise marsh.errors.PathError(
            marsh.utils.get_closest_error_message(
                value=field,
                candidates=self.schemas,
                key='key',
            ),
        )

    def doc(
        self,
        depth: int = 0,
        default_args: Optional[Sequence] = None,
        default_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> UnmarshalSchema.Doc:
        return self.Doc(
            type=self.doc_type(),
            default=self.doc_default(),
            description=self.doc_description(),
            fields=self.doc_fields(
                max(0, depth),
                default_args=default_args,
                default_kwargs=default_kwargs,
            ),
            special_fields=self.doc_special_fields(),
        )

    def doc_field_type(
        self,
    ) -> str:
        return f'{marsh.utils.get_type_name(self.value)}(...)'

    def doc_fields(
        self,
        depth: int,
        default_args: Optional[Sequence] = None,
        default_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, UnmarshalSchema.Doc.Field]]:
        if depth <= 0:
            return None
        self.validate_defaults(
            args=default_args,
            kwargs=default_kwargs,
        )
        default_args = list(default_args or ())
        default_kwargs = dict(default_kwargs or {})
        fields: Dict[str, UnmarshalSchema.Doc.Field] = {}
        for i, (name, schema) in enumerate(self.schemas.items()):
            fields[name] = UnmarshalSchema.Doc.Field(
                doc=schema.doc(depth - 1),
                type=schema.doc_field_type(),
                description=marsh.utils.get_attribute_description(
                    self.value,
                    name.strip('*'),
                ),
            )
            default = None
            if name.startswith('**'):
                if default_kwargs:
                    default = str(default_kwargs)
                    default_kwargs = {}
            elif name.startswith('*'):
                if default_args:
                    default = str(default_args)
                    default_args = []
            if i < len(default_args):
                default = str(default_args.pop(0))
            if name in default_kwargs:
                default = str(default_kwargs.pop(name))
            if default:
                fields[name].doc.default = default
        return fields

    def unmarshal(
        self,
        element: marsh.element.ElementType,
        default_args: Optional[Sequence] = None,
        default_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> _T:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            element = {}
        element_list: List[Any] = []
        element_dict: Dict[str, Any] = {}
        args: List = []
        kwargs: Dict[str, Any] = {}
        if marsh.utils.is_mapping(element):
            element_dict = dict(element)
        elif marsh.utils.is_sequence(element):
            element_list = list(element)
        else:
            raise marsh.errors.UnmarshalError(
                (
                    'expected a mapping or sequence element, got: '
                    f'{marsh.utils.get_type_name(element)}'
                ),
                element=element,
                type=self.value,
            )
        self.validate_defaults(
            args=default_args,
            kwargs=default_kwargs,
        )
        default_args = list(default_args or ())
        default_kwargs = dict(default_kwargs or {})
        for name, schema in self.schemas.items():
            with marsh.errors.prepend(name.strip('*')):
                if name.startswith('**'):
                    for key in tuple(default_kwargs):
                        value = default_kwargs.pop(key)
                        if key not in element_dict:
                            kwargs[key] = value
                    for key in tuple(element_dict):
                        with marsh.errors.prepend(key):
                            kwargs[key] = schema.unmarshal(element_dict.pop(key))
                elif name.startswith('*'):
                    for i in range(len(element_list)):
                        with marsh.errors.prepend(i):
                            args.append(schema.unmarshal(element_list.pop(0)))
                    args.extend(default_args)
                    default_args = []
                else:
                    if element_list:
                        args.append(schema.unmarshal(element_list.pop(0)))
                        default_args and default_args.pop(0)
                    else:
                        if default_args:
                            value = default_args.pop(0)
                            if name not in element_dict:
                                kwargs[name] = value
                        if name in default_kwargs:
                            value = default_kwargs.pop(name)
                            if name not in element_dict:
                                kwargs[name] = value
                        if name not in kwargs:
                            kwargs[name] = schema.unmarshal(
                                element_dict.pop(
                                    name,
                                    marsh.MISSING,
                                ),
                            )
                        if name in self.positional:
                            args.append(kwargs.pop(name))
        for key in element_dict:
            raise marsh.errors.UnmarshalError(
                marsh.utils.get_closest_error_message(
                    key,
                    self.schemas,
                    key='key',
                ),
                element=element,
                type=self.value,
            )
        if element_list:
            raise marsh.errors.UnmarshalError(
                f'received too many arguments ({len(element_list)}).',
                element=element,
                type=self.value,
            )
        return self.construct(*args, **kwargs)

    def construct(
        self,
        *args,
        **kwargs,
    ) -> _T:
        """Takes the unmarshaled arguments to the type as input and
        initializes an instance of the type using these arguments.

        Returns:
            The initialized value.
        """
        return self.value(*args, **kwargs)
