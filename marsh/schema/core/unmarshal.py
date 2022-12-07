import collections
import dataclasses
import importlib
import threading
from typing import (
    Any,
    Callable,
    DefaultDict,
    ForwardRef,
    Generic,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    get_origin,
    overload,
)
from typing_extensions import TypeAlias

import marsh
from . import base


_T = TypeVar('_T')
_RelativePriority: TypeAlias = \
    marsh.utils.PriorityOrder.RelativePriority[Type['UnmarshalSchema']]


skip_cache_types = {
    int,
    float,
    str,
    bool,
    dict,
    list,
    tuple,
    None,
    set,
}


def resolve_forward_ref(
    ref: ForwardRef,
    cache: Iterable[Any],
) -> Any:
    name = ref.__forward_arg__
    mod = ''
    if '.' in name:
        mod, _, name = name.rpartition('.')
    if mod:
        try:
            return ref._evaluate(
                vars(importlib.import_module(mod)),
                None,
            )
        except Exception:
            pass
    for type_ in cache:
        if marsh.utils.get_type_name(type_) == name:
            return type_
        if hasattr(type_, '__module__'):
            try:
                return ref._evaluate(
                    vars(
                        importlib.import_module(
                            type_.__module__ + (f'.{mod}' if mod else ''),
                        ),
                    ),
                    None,
                )
            except Exception:
                pass
    raise marsh.errors.MarshError(f'could not resolve forward reference to a type: {ref}')


def resolve_type(
    value: Any,
    cache: Iterable[Any],
) -> Any:
    """Attempt to resolve unknown types (forward references).

    Returns the input type if it is not a forward reference.

    Arguments:
        value: The type to resolve.
        cache: A cache of types.

    Returns:
        The resolved type.
    """
    try:
        if isinstance(value, ForwardRef):
            value = resolve_forward_ref(
                value,
                cache,
            )
            return resolve_type(value, cache)
    except marsh.errors.MarshError:
        raise
    except Exception:
        pass
    return value


class UnmarshalSchemaRegistry(base.SchemaRegistry['UnmarshalSchema']):

    def cache_clear(
        self,
    ) -> None:
        self.match.cache_clear()  # type: ignore

    def cache_info(
        self,
    ) -> marsh.utils.CacheInfo:
        return self.match.cache_info,  # type: ignore

    @overload
    def register(
        self,
        schema: Type['UnmarshalSchema'],
        *,
        priority: int = 0,
        lower_priority: _RelativePriority = None,
        higher_priority: _RelativePriority = None,
        replace: bool = False,
    ) -> Type['UnmarshalSchema']:
        ...

    @overload
    def register(
        self,
        *,
        priority: int = 0,
        lower_priority: _RelativePriority = None,
        higher_priority: _RelativePriority = None,
        replace: bool = False,
    ) -> Callable[[Type['UnmarshalSchema']], Type['UnmarshalSchema']]:
        ...

    def register(
        self,
        schema: Optional[Type['UnmarshalSchema']] = None,
        *,
        priority: int = 0,
        lower_priority: _RelativePriority = None,
        higher_priority: _RelativePriority = None,
        replace: bool = False,
    ) -> Union[
        Callable[
            [Type['UnmarshalSchema']],
            Type['UnmarshalSchema'],
        ],
        Type['UnmarshalSchema'],
    ]:
        def wrapper(_schema):
            self.cache_clear()
            return self.priority.add(
                _schema,
                priority=priority,
                lower_priority=lower_priority,
                higher_priority=higher_priority,
                replace=replace,
            )
        if schema is None:
            return wrapper
        return wrapper(schema)

    @base.caches.new_callable_cache(
        name='marsh.schema.UnmarshalSchema.registry.match',
        typed=False,
        safe=True,
        binding='ignore',
    )
    def match(
        self,
        value: Any,
    ) -> base.SchemaSelection['UnmarshalSchema']:
        return super().match(value)


class UnmarshalSchemaMeta(base.SchemaMeta['UnmarshalSchema']):

    class CacheInfo(NamedTuple):
        registry: marsh.utils.CacheInfo
        recursion: marsh.utils.CacheInfo
        build: marsh.utils.CacheInfo

    _recursive_cache: DefaultDict[
        int,
        marsh.utils.ValueCache[
            Type[Any],
            base.SchemaSelection,
        ],
    ] = collections.defaultdict(marsh.utils.ValueCache)

    type_cache: marsh.utils.WeakTypeCache = \
        marsh.utils.WeakTypeCache(skip_types=skip_cache_types)

    registry: UnmarshalSchemaRegistry = UnmarshalSchemaRegistry(
        error=marsh.errors.UnmarshalError,
    )

    def __init_subclass__(
        metacls,  # noqa: B902
    ) -> None:
        metacls._recursive_cache = \
            collections.defaultdict(marsh.utils.ValueCache)
        metacls.type_cache = \
            marsh.utils.WeakTypeCache(skip_types=skip_cache_types)
        if (
            hasattr(metacls, 'registry')
            and metacls.registry is not UnmarshalSchema.registry
        ):
            return
        super().__init_subclass__()
        metacls.registry = UnmarshalSchemaRegistry()

    def __call__(
        cls,  # noqa: B902
        value,
        *args,
        **kwargs,
    ):
        if cls is not UnmarshalSchema:
            return type(object).__call__(cls, value, *args, **kwargs)
        metacls: 'UnmarshalSchemaMeta' = type(cls)
        value = resolve_type(value, cache=metacls.type_cache)
        if get_origin(value) is Union:
            return cls._build(
                value=value,
                *args,
                **kwargs,
            )
        return cls._cached_build(
            value=value,
            *args,
            **kwargs,
        )

    def _build(
        cls,  # noqa: B902
        value,
        *args,
        **kwargs,
    ):
        metacls: 'UnmarshalSchemaMeta' = type(cls)
        try:
            metacls.type_cache.add(value)
        except TypeError:
            pass
        recursive_cache = cls._recursive_cache[threading.get_ident()]
        if recursive_cache:
            try:
                return recursive_cache[value].build(value, *args, **kwargs)
            except KeyError:
                pass
        result = cls.registry.match(value)
        result.insert(0, RecursiveReferenceUnmarshalSchema)
        recursive_cache[value] = result
        return result[1:].build(value, *args, **kwargs)

    @base.caches.new_callable_cache(
        name='marsh.schema.UnmarshalSchema.__new__',
        safe=True,
        binding='ignore',
    )
    def _cached_build(
        cls,  # noqa: B902
        value,
        *args,
        **kwargs,
    ):
        return cls._build(
            value=value,
            *args,
            **kwargs,
        )

    def cache_clear(
        cls,  # noqa: B902
    ) -> None:
        cls.registry.cache_clear()
        cls._cached_build.cache_clear()  # type: ignore
        cls._recursive_cache.clear()
        cls.type_cache.clear()

    def cache_info(
        cls,  # noqa: B902
    ) -> 'UnmarshalSchemaMeta.CacheInfo':
        return dict(
            registry=cls.registry.cache_info(),
            recursion=cls._recursive_cache[threading.get_ident()].cache_info(),
            build=cls._cached_build.cache_info(),  # type: ignore
        )


class UnmarshalSchema(
    base.Schema,
    Generic[_T],
    metaclass=UnmarshalSchemaMeta,
):
    """Unmarshals JSON-like inputs into its value type.

    .. note::

        Static type checkers may give an error for
        abstract types
        (`issue <https://github.com/python/mypy/issues/5374>`_).

        Some type aliases are also not recognized as types.
        For the moment there is not better solution than
        using a simple ``# type: ignore`` comment.

    Arguments:
        value: The value to match/unmarshal.
        default: An immutable default value. Mutually
            exclusive with ``default_factory``.
        default_factory: Factory function for a mutable
            default value. Mutually exclusive with
            ``default``.
    """

    @dataclasses.dataclass
    class Doc:
        """Structured unmarshal documentation for a type."""

        @dataclasses.dataclass
        class Field:
            """Unmarshal documentation for a field/attribute
            of a type."""

            doc: 'UnmarshalSchema.Doc'
            """The field unmarshal documentation."""

            type: Optional[str] = None
            """Type string as should be displayed when this is
            a field of a parent."""

            description: Optional[str] = None
            """Description for field by parent."""

        @dataclasses.dataclass
        class SpecialField:
            """Unmarshal documentation for a special field.

            A special field may document any value.
            """

            value: str
            """The name of the value being documented."""

            description: Optional[str] = None
            """Its description."""

        type: Optional[str] = None
        """String representation of the type."""

        default: Optional[str] = None
        """Default value."""

        description: Optional[str] = None
        """Description for type."""

        fields: Optional[Mapping[str, 'UnmarshalSchema.Doc.Field']] = None
        """Named internal fields of the documented type."""

        special_fields: Optional[Sequence['UnmarshalSchema.Doc.SpecialField']] = None
        """Any other fields that do not follow the name/type/default
        style."""

    value: Type[_T]
    default: _T
    default_factory: Callable[..., _T]

    def __init__(
        self,
        *args,
        default: _T = marsh.MISSING,
        default_factory: Callable[..., _T] = marsh.MISSING,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.default = default
        self.default_factory = default_factory

    def __str__(
        self,
    ) -> str:
        return f'<{self.doc_type()}>'

    def __repr__(
        self,
    ) -> str:
        return (
            f'{self.__class__.__name__}(value={self.value}, '
            f'default={self.default}, default_factory={self.default_factory})'
        )

    def has_default(
        self,
    ) -> bool:
        """Evaluates if this schema holds a default value.

        Returns:
            ``True`` if there is a default value, else ``False``.
        """
        return not (
            marsh.utils.is_missing(self.default)
            and marsh.utils.is_missing(self.default_factory)
        )

    def get_default(
        self,
    ) -> _T:
        """Get the default value of this schema.

        If default value exists `marsh.MISSING`
        is returned instead.

        Returns:
            The default value or `marsh.MISSING`.
        """
        if not marsh.utils.is_missing(self.default_factory):
            return self.default_factory()
        return self.default

    def select(
        self,
        path: str,
    ) -> 'UnmarshalSchema':
        """Select a nested schema from this schema based on
        a dot-separated path. If not all of the path is consumed
        by this schema it is forwarded to the `select` method
        of the nested schema.

        Arguments:
            path: The path to traverse.

        Returns:
            The schema at the end of the path.
        """
        if not path:
            return self
        raise marsh.errors.PathError(
            f'{marsh.utils.get_type_name(self.value)}: '
            f'can not traverse the path "{path}"',
        )

    def doc(
        self,
        depth: int = 0,
    ) -> Doc:
        """Get the documentation for the type unmarshaled
        by this schema.

        Arguments:
            depth: How deep should documentation be fetched
                in nested schemas. If ``0``, only the fields
                and info for the type of this schema is returned.

        Returns:
            The documentation.
        """
        return self.Doc(
            type=self.doc_type(),
            default=self.doc_default(),
            description=self.doc_description(),
            fields=self.doc_fields(max(0, depth)),
            special_fields=self.doc_special_fields(),
        )

    def doc_type(
        self,
    ) -> str:
        """The name of the type unmarshaled by this schema.

        Returns:
            The type name.
        """
        return marsh.utils.get_type_name(self.value)

    def doc_field_type(
        self,
    ) -> str:
        """Alternative name of the type unmarshaled by this schema.

        This corresponds to the type that should be display in parent
        documentation when this is one of its fields.

        Returns:
            Alternative type name.
        """
        return self.doc_type()

    def doc_default(
        self,
    ) -> Optional[str]:
        """Document default value.

        The default implementation of this method
        returns :data:`None` if no default value exists
        and ``'...'`` if the default value is mutable.
        If the default value is immutable, an
        attempt is first made to marshal the default
        value before returning a string of its marshaled
        state. If this fails, a string of the default
        is returned.

        Returns:
            String of default.
        """
        if not self.has_default():
            return None
        if marsh.utils.is_missing(self.default):
            return '...'
        try:
            return str(marsh.marshal(self.default))
        except Exception:
            return str(self.default)

    def doc_description(
        self,
    ) -> Optional[str]:
        """A description for the type unmarshaled by this schema.

        Returns:
            The description.
        """
        if marsh.utils.is_typing_alias(self.value):
            return None
        try:
            if self.value in (int, float, bool, str, bytes, tuple, list, dict):
                return None
        except Exception:
            pass
        return marsh.utils.get_description(self.value)

    def doc_fields(
        self,
        depth: int,
    ) -> Optional[Mapping[str, Doc.Field]]:
        """Documentation for the fields of the type unmarshaled
        by this schema.

        No documentation is returned if no fields exist.

        Returns:
            Field documentation.
        """
        return None

    def doc_special_fields(
        self,
    ) -> Optional[Sequence[Doc.SpecialField]]:
        """Documentation for the special fields of the type unmarshaled
        by this schema.

        No documentation is returned if no special fields exist.

        Returns:
            Special field documentation.
        """
        return None

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        """Construct the object of this schema.

        Arguments:
            element: The input JSON-style data.

        Returns:
            The object initialized with the input data.
        """
        raise NotImplementedError


class WrapperUnmarshalSchema(
    UnmarshalSchema[_T],
    base.WrapperSchema[UnmarshalSchema[_T]],
):

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        base.WrapperSchema.__init__(self, *args, **kwargs)

    def __str__(
        self,
    ) -> str:
        return str(self.schema)

    def __repr__(
        self,
    ) -> str:
        return repr(self.schema)

    def select(
        self,
        path: str,
    ) -> 'UnmarshalSchema':
        return self.schema.select(path)

    def doc(
        self,
        depth: int = 0,
    ) -> UnmarshalSchema.Doc:
        return self.schema.doc(depth)

    def doc_type(
        self,
    ) -> str:
        return self.schema.doc_type()

    def doc_field_type(
        self,
    ) -> str:
        return self.schema.doc_field_type()

    def doc_default(
        self,
    ) -> Optional[str]:
        return self.schema.doc_default()

    def doc_description(
        self,
    ) -> Optional[str]:
        return self.schema.doc_description()

    def doc_fields(
        self,
        depth: int,
    ) -> Optional[Mapping[str, UnmarshalSchema.Doc.Field]]:
        return self.schema.doc_fields(depth)

    def doc_special_fields(
        self,
    ) -> Optional[Sequence[UnmarshalSchema.Doc.SpecialField]]:
        return self.schema.doc_special_fields()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> _T:
        return self.schema.unmarshal(element)


class RecursiveReferenceUnmarshalSchema(WrapperUnmarshalSchema):

    def __str__(
        self,
    ) -> str:
        return UnmarshalSchema.__str__(self)

    def __repr__(
        self,
    ) -> str:
        return UnmarshalSchema.__repr__(self)

    def doc(
        self,
        depth: int = 0,
    ) -> UnmarshalSchema.Doc:
        # Dont include fields in the documentation
        # of recursive types as that would repeat
        # the same documentation over when depth > 0
        return self.Doc(
            type=self.schema.doc_type(),
            default=self.schema.doc_default(),
            description=self.schema.doc_description(),
        )
