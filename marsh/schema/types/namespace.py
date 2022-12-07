from typing import (
    Any,
    Sequence,
    TypeVar,
)

import marsh


_T = TypeVar('_T')


_PRIORITY = 10


@marsh.schema.register(priority=_PRIORITY)
class NamespaceMarshalSchema(marsh.schema.core.marshal.WrapperMarshalSchema):

    namespaces = marsh.schema.namespace.Namespaces()

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.name = self.namespaces.find_class(marsh.utils.get_type(self.value))

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return bool(cls.namespaces.find_class(marsh.utils.get_type(value)))
        except Exception:
            return False

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        element = self.schema.marshal()
        if not marsh.utils.is_mapping(element):
            raise marsh.errors.MarshalError(
                f'{marsh.utils.get_type_name(self.value)}: marshaling '
                'is not supported for registered component that '
                f'is not marshaled into a mapping element',
            )
        if 'name' in element:
            raise marsh.errors.MarshalError(
                'reserved component field `name` encountered',
            )
        return {
            **element,
            **dict(name=self.name),
        }


@marsh.schema.register(priority=_PRIORITY)
class NamespaceUnmarshalSchema(marsh.schema.core.unmarshal.WrapperUnmarshalSchema[_T]):

    namespaces = marsh.schema.namespace.Namespaces()

    def __str__(
        self,
    ) -> str:
        names = self.names()
        type_name = marsh.utils.get_type_name(self.value)
        if names:
            quoted_names = (f'"{name}"' for name in names)
            return f'{type_name}(name={" | ".join(quoted_names)})'
        return type_name

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        return bool(cls.namespaces.find_namespaces(value))

    def names(
        self,
    ) -> Sequence[str]:
        return sorted(
            {
                name
                for name, _
                in self.namespaces.find_subclasses(self.value)
            },
        )

    def doc_special_fields(
        self,
    ) -> Sequence[marsh.schema.UnmarshalSchema.Doc.SpecialField]:
        fields = []
        for name, namespace in self.namespaces.find_subclasses(self.value):
            schema = namespace[name]
            field = f'name = "{name}" -> {schema.doc_field_type()}'
            fields.append(
                marsh.schema.UnmarshalSchema.Doc.SpecialField(
                    value=field,
                    description=schema.doc_description(),
                ),
            )
        return fields

    def select(
        self,
        path: str,
    ) -> marsh.schema.UnmarshalSchema:
        if not path:
            return self
        field, path = marsh.path.head(path)
        for name, namespace in self.namespaces.find_subclasses(self.value):
            if name == field:
                return namespace[name].select(path)
        raise marsh.errors.PathError(
            marsh.utils.get_closest_error_message(
                field,
                self.names(),
                key='name',
            ),
        )

    def find_namespace(
        self,
        name: str,
    ) -> marsh.schema.namespace.Namespace:
        """Find namespace for a specified name.

        Raises an error if no namespace is found."""
        candidates = []
        for candidate, namespace in self.namespaces.find_subclasses(self.value):
            if candidate == name:
                return namespace
            candidates.append(candidate)
        raise marsh.errors.UnmarshalError(
            marsh.utils.get_closest_error_message(
                value=name,
                candidates=candidates,
                key='name',
            ),
            path='name',
        )

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        name: str = marsh.MISSING
        if marsh.utils.is_mapping(element):
            element = dict(element)
            name = element.pop('name', marsh.MISSING)
        if marsh.utils.is_missing(name):
            return self.schema.unmarshal(element)
        return self.find_namespace(name)[name].unmarshal(element)
