"""This module creates support for inheritance-based type matching.

For all types in a namespace each subclass of a type being
that is being unmarshaled is considered."""
import collections.abc
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    ItemsView,
    Iterator,
    KeysView,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    ValuesView,
    cast,
    overload,
)

import marsh
from . import core
from .core.base import caches


_T = TypeVar('_T')
_K = TypeVar('_K')
_V = TypeVar('_V')


class _SingletonMapping(
    Generic[_K, _V],
    metaclass=marsh.utils.SingletonMeta,
):

    def __getitem__(
        self,
        key: _K,
    ) -> _V:
        raise NotImplementedError

    def __len__(
        self,
    ) -> int:
        raise NotImplementedError

    def __iter__(
        self,
    ) -> Iterator[_K]:
        raise NotImplementedError

    def get(
        self,
        key,
        default: Any = None,
    ) -> Union[_V, Any]:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def keys(
        self,
    ) -> KeysView[_K]:
        return collections.abc.KeysView(self)  # type: ignore

    def items(
        self,
    ) -> ItemsView[_K, _V]:
        return collections.abc.ItemsView(self)  # type: ignore

    def values(
        self,
    ) -> ValuesView[_V]:
        return collections.abc.ValuesView(self)  # type: ignore

    def __eq__(
        self,
        other: Any,
    ) -> bool:
        if not isinstance(other, _SingletonMapping):
            return NotImplemented
        return dict(self.items()) == dict(other.items())


class Namespaces(_SingletonMapping[str, 'Namespace']):
    """Singleton class holding all namespaces.

    Includes functionality for matching a type
    against the classes of all namespaces. These
    matching functions are cached for improved
    performance."""

    class CacheInfo(TypedDict):
        find_class: marsh.utils.CacheInfo
        find_subclasses: marsh.utils.CacheInfo
        find_namespaces: marsh.utils.CacheInfo

    class FullCacheInfo(CacheInfo):
        names: Mapping[str, 'Namespace.CacheInfo']

    def __init__(
        self,
    ) -> None:
        self._namespaces: Dict[str, 'Namespace'] = {}

    def __getitem__(
        self,
        name: str,
    ) -> 'Namespace':
        if name not in self:
            raise KeyError(
                marsh.utils.get_closest_error_message(
                    value=name,
                    candidates=self,
                    key='namespace',
                ),
            )
        return self._namespaces[name]

    def __delitem__(
        self,
        name,
    ) -> None:
        del self._namespaces[name]

    def __contains__(
        self,
        name,
    ) -> bool:
        return name in self._namespaces

    def __len__(
        self,
    ) -> int:
        return len(self._namespaces)

    def __iter__(
        self,
    ) -> Iterator[str]:
        yield from self._namespaces

    def find_subclasses_iter(
        self,
        cls: Any,
    ) -> Iterator[Tuple[str, 'Namespace']]:
        """Yield results from finding subclasses of an input type
        in all namespaces.

        This method provides results for the same but cached
        method :func:`~Namespaces.find_subclasses`.

        Arguments:
            cls: The input type.

        Returns:
            Iterator of result.
        """
        for namespace in self.values():
            for name in namespace.find_subclasses(cls):
                yield name, namespace

    def find_namespaces_iter(
        self,
        cls: Any,
    ) -> Iterator['Namespace']:
        """Yield results from finding namespaces matching an input type.

        This method provides results for the same but cached
        method :func:`~Namespaces.find_namespaces`.

        Arguments:
            cls: The input type.

        Returns:
            Iterator of result.
        """
        for namespace in self._namespaces.values():
            try:
                if issubclass(cls, namespace.base):
                    yield namespace
            except Exception:
                pass

    def new(
        self,
        name: str,
        base: Type[_T],
    ) -> 'Namespace[_T]':
        """Create a new namespace.

        The created namespace has functions for registering
        new items and building them.

        Arguments:
            name: Name of namespace.
            base: Base class for namespace.

        Returns:
            The namespace.
        """
        if name in self:
            raise marsh.errors.MarshError(
                f'namespace "{name}" already exists',
            )
        self._namespaces[name] = (
            namespace := Namespace(
                name=name,
                base=base,
            )
        )
        return namespace

    def cache_clear(
        self,
        full: bool = False,
    ) -> None:
        """Clear the cache of this class.

        Arguments:
            full: If ``True``, also clear the cache
                of all namespaces.
        """
        self.find_class.cache_clear()  # type: ignore
        self.find_subclasses.cache_clear()  # type: ignore
        self.find_namespaces.cache_clear()  # type: ignore
        if full:
            for namespace in self._namespaces.values():
                namespace.cache_clear()

    @overload
    def cache_info(
        self,
        full: Literal[True],
    ) -> 'Namespaces.FullCacheInfo':
        ...

    @overload
    def cache_info(
        self,
    ) -> 'Namespaces.CacheInfo':
        ...

    def cache_info(
        self,
        full: bool = False,
    ) -> Union['Namespaces.CacheInfo', 'Namespaces.FullCacheInfo']:
        """Get info for the cache of this class.

        Arguments:
            full: If ``True``, return the cache info
                for all namespaces as well.

        Returns:
            The cache info.
        """
        info: dict = dict(
            find_class=marsh.utils.CacheInfo.from_info(
                self.find_class.cache_info(),  # type: ignore
            ),
            find_subclasses=marsh.utils.CacheInfo.from_info(
                self.find_subclasses.cache_info(),  # type: ignore
            ),
            find_namespaces=marsh.utils.CacheInfo.from_info(
                self.find_namespaces.cache_info(),  # type: ignore
            ),
        )
        if full:
            names = {}
            for name, namespace in self.items():
                names[name] = namespace.cache_info()
            info['names'] = names
        return info  # type: ignore

    @caches.new_callable_cache(
        name='marsh.namespaces.find_class',
        safe=True,
        binding='weak',
    )
    def find_class(
        self,
        cls: Any,
    ) -> Optional[str]:
        """Search through all namespaces and return
        the name of the first class that equals the given type.

        Arguments:
            cls: The type to find a name for.

        Returns:
            A name if found, else :data:`None`.
        """
        for namespace in reversed(self._namespaces.values()):
            if (name := namespace.find_class(cls)):
                return name
        return None

    @caches.new_callable_cache(
        name='marsh.namespaces.find_subclasses',
        safe=True,
        binding='weak',
    )
    def find_subclasses(
        self,
        cls: Any,
    ) -> marsh.utils.IterableFromIterator[Tuple[str, 'Namespace']]:
        """Search for all subclasses of the given type.

        Argument:
            cls: The type to find subclasses for.

        Returns:
            Iterable of names and namespaces.
        """
        return marsh.utils.IterableFromIterator(self.find_subclasses_iter(cls))

    @caches.new_callable_cache(
        name='marsh.namespaces.find_namespaces',
        safe=True,
        binding='weak',
    )
    def find_namespaces(
        self,
        cls: Any,
    ) -> marsh.utils.IterableFromIterator['Namespace']:
        """Find the namespaces with base classes that
        are superclasses of the given type.

        Arguments:
            cls: The type to find namespaces for.

        Returns:
            Iterable of namespaces found.
        """
        return marsh.utils.IterableFromIterator(self.find_namespaces_iter(cls))


class Namespace(Mapping[str, core.unmarshal.UnmarshalSchema[_T]]):
    """Holds a group of subclasses for a base class which are each
    associated with a name.

    This class should be initialized via :func:`Namespaces.new`.

    Includes functionality for matching a type against
    the classes held by this namespace. This functionality
    is cached for improved performance.

    Arguments:
        base: The base class for the namespace.
    """

    class CacheInfo(TypedDict):
        find_class: marsh.utils.CacheInfo
        find_subclasses: marsh.utils.CacheInfo

    components: Dict[str, Type[_T]]
    _namespaces: Namespaces = Namespaces()

    def __init__(
        self,
        name: str,
        base: Type[_T],
    ) -> None:
        self.name = name
        self.base = base
        self.components = {}
        self._schemas: Dict[str, core.unmarshal.UnmarshalSchema[_T]] = {}
        # when wrapping functions on an instance the `self`
        # argument is not included until the most inner
        # wrapped function is called which means that we
        # skip setting `binding='ignore'`
        self.find_class = caches.new_callable_cache(  # type: ignore
            self.find_class,
            name=f'marsh.namespaces.{name}.find_class',
            safe=True,
        )
        self.find_subclasses = caches.new_callable_cache(  # type: ignore
            self.find_subclasses,
            name=f'marsh.namespaces.{name}.find_subclasses',
            safe=True,
        )

    def __getitem__(
        self,
        name: str,
    ) -> core.unmarshal.UnmarshalSchema[_T]:
        if name not in self:
            raise KeyError(
                marsh.utils.get_closest_error_message(
                    value=name,
                    candidates=self,
                    key='name',
                ),
            )
        if name not in self._schemas:
            # instead of picking out the matched
            # schema types we need to run the normal
            # constructor so that the type is cached.
            # If not, the recursive tests for namespace
            # components fail.
            schema = marsh.schema.UnmarshalSchema[_T](
                self.components[name],
            )
            # extract inner schema
            while isinstance(
                schema,
                marsh.schema.types.namespace.NamespaceUnmarshalSchema,
            ):
                schema = schema.schema
            self._schemas[name] = schema
        return self._schemas[name]

    def __iter__(
        self,
    ) -> Iterator[str]:
        yield from self.components

    def __len__(
        self,
    ) -> int:
        return len(self.components)

    def __contains__(
        self,
        name: object,
    ) -> bool:
        return name in self.components

    def cache_clear(
        self,
    ) -> None:
        """Clear the cache."""
        self.find_class.cache_clear()  # type: ignore
        self.find_subclasses.cache_clear()  # type: ignore

    def cache_info(
        self,
    ) -> 'Namespace.CacheInfo':
        """Get info for the cache.

        Returns:
            The cache info.
        """
        return dict(
            find_class=self.find_class.cache_info(),  # type: ignore
            find_subclasses=self.find_subclasses.cache_info(),  # type: ignore
        )

    def find_class(
        self,
        cls: Type[_T],
    ) -> Optional[str]:
        """Find the name of a class maybe held by this namespace.

        Arguments:
            cls: The type to find a name for.

        Returns:
            :data:`None` if no class was matched, else the name
            associated with the type
        """
        if not issubclass(cls, self.base):
            return None
        for name, component in self.components.items():
            if component == cls:
                return name
        return None

    def find_subclasses_iter(
        self,
        cls: Type[_T],
    ) -> Iterator[str]:
        """Yield names of components in this namespace that are
        subclasses of the input type.

        This method provides results for the same but cached
        method :func:`~Namespace.find_subclasses`.

        Arguments:
            cls: The input type.

        Returns:
            Iterator of string names.
        """
        for name, component in self.components.items():
            try:
                if issubclass(component, cls):
                    yield name
            except Exception:
                pass

    def find_subclasses(
        self,
        cls: Type[_T],
    ) -> marsh.utils.IterableFromIterator[str]:
        """Get the names of all classes held by this namespace
        that are subclasses of the input.

        Arguments:
            cls: The type to find subclasses for.

        Returns:
            The names of the subclasses.
        """
        return marsh.utils.IterableFromIterator(self.find_subclasses_iter(cls))

    @overload
    def register(
        self,
        component: Type[_T],
        *,
        name: str,
        replace: bool = False,
    ) -> Type[_T]:
        ...

    @overload
    def register(
        self,
        *,
        name: str,
        replace: bool = False,
    ) -> Callable[[Type[_T]], Type[_T]]:
        ...

    def register(
        self,
        component: Optional[Type[_T]] = None,
        *,
        name: str,
        replace: bool = False,
    ) -> Union[Callable[[Type[_T]], Type[_T]], Type[_T]]:
        """Register a new type for this namespace.

        Arguments:
            name: The name to associate with the type.
            replace: Allow replacing any existing value
                with the same name.

        Returns:
            A decorator for registering the type if no
            type was given else the type itself.
        """
        if name in self:
            if not replace:
                raise marsh.errors.MarshError(
                    f'a component with the name "{name}" '
                    'already exists',
                )
            self._schemas.pop(name, None)

        def _register(
            component: Type[_T],
        ) -> Type[_T]:
            if not issubclass(component, self.base):
                raise ValueError(
                    'registered component must be '
                    F'a subclass of {self.base}: {component}',
                )
            self.components[name] = component
            self.cache_clear()
            self._namespaces.cache_clear()
            marsh.schema.UnmarshalSchema.cache_clear()
            return component

        if component is None:
            return _register
        return _register(component)

    @overload
    def build(
        self,
        element: marsh.element.ElementType = marsh.MISSING,
        *,
        name: str,
    ) -> _T:
        ...

    @overload
    def build(
        self,
        element: Optional[marsh.element.SequenceElementType] = marsh.MISSING,
        *args,
        name: str,
    ) -> _T:
        ...

    @overload
    def build(
        self,
        element: Optional[marsh.element.MappingElementType] = marsh.MISSING,
        *,
        name: str,
        **kwargs,
    ) -> _T:
        ...

    def build(
        self,
        element: marsh.element.ElementType = marsh.MISSING,
        *args,
        name: str,
        **kwargs,
    ) -> _T:
        """Unmarshal a type held by this namespace."""
        if name not in self:
            raise marsh.errors.UnmarshalError(
                marsh.utils.get_closest_error_message(
                    value=name,
                    candidates=self,
                    key='name',
                ),
                element=element,
            )
        if args and kwargs:
            raise TypeError(
                'variable positional arguments can not be used '
                'simultaneously as variable keyword arguments',
            )
        if args:
            if marsh.utils.is_sequence(element):
                element = list(element or ())
                element.extend(cast(Sequence, marsh.marshal(args)))
            elif element is None or marsh.utils.is_missing(element):
                element = marsh.marshal(args)
            else:
                raise TypeError(
                    'variable positional arguments can only be used '
                    'when `element` is a sequence.',
                )
        if kwargs:
            if marsh.utils.is_mapping(element):
                element = dict(element)
                element.update(cast(Mapping, marsh.marshal(kwargs)))
            elif element is None or marsh.utils.is_missing(element):
                element = marsh.marshal(kwargs)
            else:
                raise TypeError(
                    'variable keyword arguments can only be used '
                    'when `element` is a mapping.',
                )
        return self[name].unmarshal(element)
