"""Collection of general utilities used throughout the framework."""
import ast
import base64
import collections.abc
import dataclasses
import difflib
import functools
import inspect
import os
import shutil
import sys
import weakref
import types
import typing
import typing_extensions
from typing import (
    Any,
    Callable,
    ClassVar,
    DefaultDict,
    Dict,
    Final,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    MutableMapping,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Set,
    SupportsIndex,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
    runtime_checkable,
)
from typing_extensions import (
    Annotated,
    TypeAlias,
    TypeGuard,
)

import omegaconf
import docstring_parser


_ProtocolTypes: list = []
_AnnotatedTypes: list = []
_LiteralTypes: list = []
_LiteralStringTypes: list = []
_TypeAliasTypes: list = []
_IsTypedDict: list = []


for module in (typing, typing_extensions):
    for attr, container in (
        ('Protocol', _ProtocolTypes),
        ('Annotated', _AnnotatedTypes),
        ('Literal', _LiteralTypes),
        ('LiteralString', _LiteralStringTypes),
        ('TypeAlias', _TypeAliasTypes),
        ('is_typeddict', _IsTypedDict),
    ):
        try:
            container.append(getattr(module, attr))
        except Exception:
            pass


# used by python 3.8 to determine when a typing alias
# is `Annotated`
_AnnotatedInstanceTypes: list = [
    type(ann[None, None])
    for ann
    in _AnnotatedTypes
]


_K = TypeVar('_K')
_K_contra = TypeVar('_K_contra', contravariant=True)
_V = TypeVar('_V')
_V_co = TypeVar('_V_co', covariant=True)
_T = TypeVar('_T')
_C = TypeVar('_C', bound=Callable)
_P = TypeVar('_P', int, float, bool, str)


@runtime_checkable
class SequenceProtocol(Protocol):
    """Protocol matching a sequence class."""

    def __contains__(
        self,
        value,
    ):
        ...

    def __getitem__(
        self,
        index,
    ):
        ...

    def __len__(
        self,
    ) -> int:
        ...


@runtime_checkable
class MappingProtocol(Protocol[_K_contra, _V_co]):
    """Protocol matching a mapping class."""

    def __contains__(
        self,
        key,
    ):
        ...

    def __getitem__(
        self,
        key,
    ):
        ...

    def __iter__(
        self,
    ):
        ...

    @overload
    def get(
        self,
        key: _K_contra,
    ) -> Optional[_V_co]:
        ...

    @overload
    def get(
        self,
        key: _K_contra,
        default: _T,
    ) -> Union[_V_co, _T]:
        ...

    def get(
        self,
        key,
        default=None,
    ):
        ...

    def items(
        self,
    ):
        ...

    def keys(
        self,
    ):
        ...

    def values(
        self,
    ):
        ...


@runtime_checkable
class NamedTupleProtocol(Protocol):
    """Protocol matching a namedtuple class."""

    __doc__: str
    _fields: Sequence[str]
    _field_defaults: Mapping[str, Any]

    def __contains__(
        self,
        value,
    ):
        ...

    def __getitem__(
        self,
        index,
    ):
        ...

    def __len__(
        self,
    ) -> int:
        ...


class SingletonMeta(type):
    """Converts a class into a singleton.

    When the constructor of the class is called
    the first time, an instance is constructed.
    After this, the constructor will always return
    that instance unless it is garbage collected.

    To allow for garbage collection of unused instances
    a weak reference is kept of the instance.
    """

    _instances: MutableMapping[Type[Any], Any] = \
        weakref.WeakKeyDictionary()

    def __call__(
        cls,
        *args,
        **kwargs,
    ) -> None:
        meta = type(cls)
        if cls not in meta._instances:
            meta._instances[cls] = super().__call__(*args, **kwargs)
        return meta._instances[cls]


class _CacheInfoInputType(Protocol):

    @property
    def hits(
        self,
    ) -> int:
        ...

    @property
    def misses(
        self,
    ) -> int:
        ...

    @property
    def maxsize(
        self,
    ) -> Optional[int]:
        ...

    @property
    def currsize(
        self,
    ) -> int:
        ...


class CacheInfo(NamedTuple):
    """Tuple with information for a cache."""
    hits: int = 0
    misses: int = 0
    maxsize: Optional[int] = None
    currsize: int = 0

    @classmethod
    def from_info(
        cls,
        info: _CacheInfoInputType,
    ) -> 'CacheInfo':
        """Create an instance of this class from any cache info
        that follows the same attribute pattern.

        Arguments:
            info: The cache info to use as source

        Returns:
            An instance of this class containing the same
            information as the input.
        """
        return cls(
            hits=info.hits,
            misses=info.misses,
            maxsize=info.maxsize,
            currsize=info.currsize,
        )


class CacheType(Protocol):
    """Represents the protocol for a cache in :mod:`marsh`."""

    def cache_info(
        self,
    ) -> CacheInfo:
        """Get info from the cache.

        Returns:
            The cache info.
        """
        ...

    def cache_clear(
        self,
    ) -> None:
        """Clear the content of the cache."""
        ...

    def cache_disable(
        self,
    ) -> None:
        """Disable the cache."""
        ...

    def cache_enable(
        self,
    ) -> None:
        """Enable the cache."""
        ...


@overload
def cache(
    *,
    maxsize: Optional[int] = None,
    typed: bool = False,
    safe: bool = True,
    binding: Optional[Literal['weak', 'ignore']] = None,
) -> Callable[[_C], _C]:
    ...


@overload
def cache(
    fn: _C,
    /,
    *,
    maxsize: Optional[int] = None,
    typed: bool = False,
    safe: bool = True,
    binding: Optional[Literal['weak', 'ignore']] = None,
) -> _C:
    ...


def cache(
    fn: Optional[_C] = None,
    /,
    *,
    maxsize: Optional[int] = None,
    typed: bool = False,
    safe: bool = True,
    binding: Optional[Literal['weak', 'ignore']] = None,
) -> Union[_C, Callable[[_C], _C]]:
    """Extended LRU cache decorator for functions.

    Allows for safe usage of lru cache, where the :class:`TypeError`
    produced by non-hashable types in the input arguments are caught
    before a new attempt is made to call the function, this time
    bypassing the cache compmletely.

    .. note::

        The bypass is triggered for :class:`TypeError`.
        If the function itself can raise this error it
        will be called twice before the final error is
        propagated.

    The wrapped function fulfills the :class:`CacheType`
    protocol.

    Arguments:
        fn: If :data:`None`, the wrapper is returned,
            otherwise this argument is wrapped and returned.
        maxsize: Maximum size of lru cache.
        typed: Differentiate between different types
            of values that produce the same hash.
        safe: Make a second attempt at calling the function
            and bypassing the cache if the first attempt fails
            with a :class:`TypeError`.
        binding: Should only be used when a method to a class
            is decorated with this function. ``'weak'`` will
            make sure that a weak reference to
            ``self``/``cls``/``metacls`` is stored in the cache
            instead of a strong reference. This allows for objects
            with lru_cache to be garbage collected when no longer
            used. ``'ignore'`` allows the first argument to bypass
            the cache, only performing a lookup on the other arguments.

    Returns:
        The wrapper, unless ``fn`` is given, which instead
        wraps the argument and returns it.
    """
    def wrapper(func: Callable[..., _T]):

        cached_func: Callable[..., _T]
        delegating_func: Callable[..., _T]
        disabled = False

        def cache_disable() -> None:
            nonlocal disabled
            disabled = True

        def cache_enable() -> None:
            nonlocal disabled
            disabled = False

        if binding == 'ignore':
            _self: Any = None

            def cached_func(
                *args,
                **kwargs,
            ) -> _T:
                return func(_self, *args, **kwargs)

            def delegating_func(
                self,
                *args,
                **kwargs,
            ) -> _T:
                if disabled:
                    return func(self, *args, **kwargs)
                nonlocal _self
                _self = self
                return cached_func(*args, **kwargs)

        elif binding == 'weak':

            def cached_func(
                self: weakref.ReferenceType,
                *args,
                **kwargs,
            ) -> _T:
                return func(self(), *args, **kwargs)

            def delegating_func(
                self,
                *args,
                **kwargs,
            ) -> _T:
                if disabled:
                    return func(self, *args, **kwargs)
                return cached_func(weakref.ref(self), *args, **kwargs)

        elif binding is None:
            cached_func = func

            def delegating_func(
                *args,
                **kwargs,
            ) -> _T:
                if disabled:
                    return func(*args, **kwargs)
                return cached_func(*args, **kwargs)

        else:
            raise ValueError(f'unexpected `binding` value: {binding}')
        cached_func = functools.lru_cache(maxsize=maxsize, typed=typed)(cached_func)
        if safe:
            unsafe_delegating_func = delegating_func

            def delegating_func(*args, **kwargs):
                try:
                    return unsafe_delegating_func(*args, **kwargs)
                except TypeError:
                    return func(*args, **kwargs)

        wrapped_func = functools.wraps(func)(delegating_func)
        wrapped_func.__wrapped__ = func  # type: ignore
        wrapped_func.cache_clear = cached_func.cache_clear  # type: ignore
        wrapped_func.cache_info = cached_func.cache_info  # type: ignore
        wrapped_func.cache_disable = cache_disable  # type: ignore
        wrapped_func.cache_enable = cache_enable  # type: ignore
        return wrapped_func
    if fn is None:
        return wrapper
    return wrapper(fn)


class _CachedHashKey(list):
    """Caches the hash value of an item.

    An instance of this class will always
    return this value from ``__hash__``
    without a new hash lookup.

    Arguments:
        value: Hashable value.
    """

    __slots__ = '_hash'

    def __init__(
        self,
        value,
    ):
        self._hash = hash(value)

    def __hash__(self):
        return self._hash


_HASH_KEY_KEYWORD_MARK: Final = (object(),)
_HASH_KEY_FAST_HASH_TYPES: Final = {int, str}


def make_hash_key(
    *args,
    **kwargs,
) -> Any:
    """Make a single cached hashable key from arguments.

    All arguments must be hashable.

    Returns:
        Hashable object that caches its hash, only caclulating it once.
    """
    key = args
    if kwargs:
        key += _HASH_KEY_KEYWORD_MARK
        for item in kwargs.items():
            key += item
    if len(key) == 1 and key[0] in _HASH_KEY_FAST_HASH_TYPES:
        return key[0]
    return _CachedHashKey(key)


def make_typed_hash_key(
    *args,
    **kwargs,
) -> Any:
    """Make a single cached hashable key from arguments.

    Includes the type of each value.

    All arguments must be hashable.

    Returns:
        Hashable object that caches its hash, only caclulating it once.
    """
    key = args + tuple(type(v) for v in args)
    if kwargs:
        key += _HASH_KEY_KEYWORD_MARK
        key += tuple(kwargs.keys())
        key += tuple(kwargs.values())
        key += tuple(type(v) for v in kwargs.values())
    return _CachedHashKey(key)


class SafeDict(MutableMapping[_K, _V]):
    """Dictionary that works with unhashable keys.

    Just like built-in :class:`dict` the order is kept."""

    def __init__(
        self,
    ) -> None:
        self._hashable_cache: Dict[_K, _V] = {}
        self._unhashable_cache: List[Tuple[_K, _V]] = []
        self._order: List[Tuple[bool, int]] = []

    def __getitem__(
        self,
        key: _K,
    ) -> _V:
        try:
            return self._hashable_cache[key]
        except TypeError:
            for k, v in reversed(self._unhashable_cache):
                if k == key:
                    return v
        raise KeyError(key)

    def __setitem__(
        self,
        key: _K,
        value: _V,
    ) -> None:
        try:
            prev_len = len(self._hashable_cache)
            self._hashable_cache[key] = value
            # keep track of order only if there are unhashable
            # keys in this container, otherwise the order is
            # already kept by the underlying dict.
            if not self._unhashable_cache:
                return
            if len(self._hashable_cache) > prev_len:
                self._order.append((True, prev_len))
        except TypeError:
            if not self._unhashable_cache:
                self._order = [(True, i) for i in range(len(self._hashable_cache))]
            for i, (k, _) in enumerate(reversed(self._unhashable_cache), start=1):
                if k == key:
                    self._unhashable_cache[-i] = (key, value)
            else:
                self._order.append((False, len(self._unhashable_cache)))
                self._unhashable_cache.append((key, value))

    def __delitem__(
        self,
        key: _K,
    ) -> None:
        try:
            if key in self._hashable_cache:
                # keep track of order only if there are unhashable
                # keys in this container, otherwise the order is
                # already kept by the underlying dict.
                if self._unhashable_cache:
                    for key_idx, k in enumerate(self._hashable_cache):
                        if k == key:
                            for order_idx, (hashable, idx) in enumerate(self._order):
                                if hashable and idx == key_idx:
                                    self._order.pop(order_idx)
                                    break
                            break
                del self._hashable_cache[key]
                return
        except TypeError:
            for key_idx, (k, _) in enumerate(reversed(self._unhashable_cache), start=1):
                if k == key:
                    self._unhashable_cache.pop(-key_idx)
                    for order_idx, (hashable, idx) in enumerate(self._order):
                        if not hashable and idx == key_idx:
                            self._order.pop(order_idx)
                            break
                    return
        raise KeyError(key)

    def _ordered_iter(
        self,
        reverse: bool,
    ) -> Iterator[_K]:
        if not self._unhashable_cache:
            # use order kept by underlying dict
            if reverse:
                yield from reversed(self._hashable_cache)
            else:
                yield from self._hashable_cache
            return
        hashable_keys = tuple(self._hashable_cache)
        unhashable_keys = tuple(key for key, _ in self._unhashable_cache)
        for hashable, index in (reversed(self._order) if reverse else self._order):
            if hashable:
                yield hashable_keys[index]
            else:
                yield unhashable_keys[index]

    def __iter__(
        self,
    ) -> Iterator[_K]:
        yield from self._ordered_iter(reverse=False)

    def __len__(
        self,
    ) -> int:
        return len(self._hashable_cache) + len(self._unhashable_cache)

    def __reversed__(
        self,
    ) -> Iterator[_K]:
        yield from self._ordered_iter(reverse=True)


class ValueCache(Generic[_K, _V]):
    """A dict-like cache that allows for non-hashable keys.

    The hash for cachable keys are also hashed to improve
    lookup speed.

    Arguments:
        typed: The key type is also taken into consideration
            when matching keys.
    """

    def __init__(
        self,
        typed: bool = False,
    ) -> None:
        self._typed = typed
        self._hits: int = 0
        self._misses: int = 0
        self._disabled = False
        self._cache: SafeDict[Any, _V] = SafeDict()

    def __len__(
        self,
    ) -> int:
        """Get the number of items in the cache.

        Returns:
            Cache size.
        """
        return len(self._cache)

    def __getitem__(
        self,
        key: _K,
    ) -> _V:
        """Get an item from the cache.

        Raises :class:`KeyError` for unmatched keys.

        Arguments:
            key: The key associated with the item to fetch.

        Returns:
            The item.
        """
        if self._disabled:
            raise KeyError(key)
        try:
            self._hits += 1
            return self._cache[self._make_key(key)]
        except KeyError:
            self._hits -= 1
            self._misses += 1
            raise

    def __setitem__(
        self,
        key: _K,
        value: _V,
    ) -> None:
        """Store an item in the cache.

        Arguments:
            key: The key to associate with the item.
            value: The item to store.
        """
        if not self._disabled:
            self._cache[self._make_key(key)] = value

    def __delitem__(
        self,
        key: _K,
    ) -> None:
        """Remove an item from the cache.

        Raises :class:`KeyError` if the given key
        does not exist.

        Arguments:
            key: The key associated with the item.
        """
        del self._cache[self._make_key(key)]

    def _make_key(
        self,
        key: _K,
    ) -> Any:
        try:
            if self._typed:
                return make_typed_hash_key(key)
            return make_hash_key(key)
        except TypeError:
            if self._typed:
                return (key, type(key))
            return key

    def cache_clear(
        self,
    ) -> None:
        """Clear the cache, removing all stored items."""
        self._cache.clear()
        self._hits = self._misses = 0

    def cache_info(
        self,
    ) -> CacheInfo:
        """Get statistics for the cache."""
        return CacheInfo(
            hits=self._hits,
            misses=self._misses,
            currsize=len(self),
        )

    def cache_disable(
        self,
    ) -> None:
        """Disable the cache.

        Getting a value for a key raise :class:`KeyError`.
        Setting a value for a key is a no-op (the value is
        not stored).
        Deleting a value in the cache is still permitted.
        """
        self._disabled = True

    def cache_enable(
        self,
    ) -> None:
        """Enable the cache."""
        self._disabled = False


class CachePool(Mapping[str, CacheType]):
    """A collection of caches."""

    def __init__(
        self,
    ) -> None:
        self._caches: Dict[str, CacheType] = {}

    def __getitem__(
        self,
        key: str,
    ) -> CacheType:
        return self._caches[key]

    def __iter__(
        self,
    ) -> Iterator[str]:
        yield from self._caches

    def __len__(
        self,
    ) -> int:
        return len(self._caches)

    def add(
        self,
        name: str,
        cache: CacheType,
    ) -> None:
        """Add a cache to the collection.

        Arguments:
            name: A name for the cache being added.
            cached: The cache to add.
        """
        self._caches[name] = cache

    @overload
    def new_callable_cache(
        self,
        *,
        name: str,
        maxsize: Optional[int] = None,
        typed: bool = False,
        safe: bool = True,
        binding: Optional[Literal['weak', 'ignore']] = None,
    ) -> Callable[[_C], _C]:
        ...

    @overload
    def new_callable_cache(
        self,
        fn: _C,
        *,
        name: str,
        maxsize: Optional[int] = None,
        typed: bool = False,
        safe: bool = True,
        binding: Optional[Literal['weak', 'ignore']] = None,
    ) -> _C:
        ...

    def new_callable_cache(
        self,
        fn: Optional[_C] = None,
        *,
        name: str,
        maxsize: Optional[int] = None,
        typed: bool = False,
        safe: bool = True,
        binding: Optional[Literal['weak', 'ignore']] = None,
    ) -> Union[_C, Callable[[_C], _C]]:
        """Wrap a function with :func:`cache` while
        simultaneously adding it to this pool.

        See :func:`cache` for descriptions of arguments
        forwarded to the wrapper.

        Arguments:
            name: The name associated with the new cache.

        Returns:
            The cache wrapper.
        """
        def wrapper(func: _C) -> _C:
            wrapped = cache(
                func,
                maxsize=maxsize,
                typed=typed,
                safe=safe,
                binding=binding,
            )
            self.add(
                name=name,
                cache=wrapped,  # type: ignore
            )
            return wrapped
        if fn is None:
            return wrapper
        return wrapper(fn)

    def new_value_cache(
        self,
        name: str,
    ) -> ValueCache:
        """Create a new value cache and add it to
        this pool before returning it.

        Arguments:
            name: The name associated with the new cache.

        Returns:
            The value cache.
        """
        cache: ValueCache = ValueCache()
        self.add(
            name=name,
            cache=cache,
        )
        return cache

    def cache_clear(
        self,
    ) -> None:
        """Clear every cache in this container.

        This does not remove the caches from the container,
        it only calls the ``clear_cache()`` function on
        each cache.
        """
        for cache in self._caches.values():
            cache.cache_clear()

    def cache_info(
        self,
    ) -> Mapping[str, CacheInfo]:
        """Get the cache info for all caches
        in this container.

        Returns:
            A mapping of the name of each cache as key
            and its respective cache info as value.
        """
        return {
            name: cache.cache_info()
            for name, cache
            in self._caches.items()
        }

    def cache_disable(
        self,
    ) -> None:
        """Disable all caches in this container."""
        for cache in self._caches.values():
            cache.cache_disable()

    def cache_enable(
        self,
    ) -> None:
        """Enable all caches in this container."""
        for cache in self._caches.values():
            cache.cache_enable()


class IterableFromIterator(Generic[_T]):
    """Lazily stores results of an iterator.

    Allows for multiple iterations over the
    wrapped iterator while only consuming it
    once.

    Arguments:
        iterator: The iterator to cache.
    """

    def __init__(
        self,
        iterator: Iterator[_T],
    ) -> None:
        self._iter = iterator
        self._cache: list = []

    def __iter__(
        self,
    ) -> Iterator[_T]:
        yield from self._cache
        for item in self._iter:
            self._cache.append(item)
            yield item

    def __bool__(
        self,
    ) -> bool:
        for _ in self:
            return True
        return False


class PriorityOrder(Sequence[_T], Generic[_T]):
    """A mutable sequence of values ordered by priority.

    Higher priority items are moved forward while
    lower priority items are moved backward in the sequence.
    """

    RelativePriority: TypeAlias = Union[None, _V, int, Iterable[_V], Iterable[int]]
    """Relative priority input type."""

    class _RelativePriorityContainer:

        class _PriorityRelation(NamedTuple):
            lower: bool
            higher: bool

        name: str
        ident: int
        lower: Set[int]
        higher: Set[int]

        def __init__(
            self,
            name: str,
            ident: int,
            lower: Set[int],
            higher: Set[int],
        ) -> None:
            if lower.intersection(higher):
                raise ValueError(
                    f'circular priority in {name}',
                )
            self.name = name
            self.ident = ident
            self.lower = lower
            self.higher = higher

        def __lt__(
            self,
            other,
        ) -> bool:
            return self.get_relation(other).lower

        def __gt__(
            self,
            other,
        ) -> bool:
            return self.get_relation(other).higher

        def has_relation(
            self,
            other,
        ) -> bool:
            if not isinstance(other, PriorityOrder._RelativePriorityContainer):
                raise TypeError
            return (
                other.ident in self.lower
                or other.ident in self.higher
                or self.ident in other.lower
                or self.ident in other.higher
            )

        def get_relation(
            self,
            other,
        ) -> 'PriorityOrder._RelativePriorityContainer._PriorityRelation':
            if not isinstance(other, PriorityOrder._RelativePriorityContainer):
                raise TypeError
            lower = (
                self.ident in other.lower
                or other.ident in self.higher
            )
            higher = (
                self.ident in other.higher
                or other.ident in self.lower
            )
            if lower and higher:
                raise ValueError(
                    'circular relative priorities for '
                    f'{self.name} and {other.name}',
                )
            return self._PriorityRelation(
                lower=lower,
                higher=higher,
            )

    class _WrappedValue(Generic[_V]):
        """Wrapes a value, storing it with any contextual information."""

        value: _V
        """The value to wrap"""

        name: str
        """The name of the value"""

        ident: int
        """The hash of the value."""

        priority: int
        """The base priority."""

        relative_priority: 'PriorityOrder._RelativePriorityContainer'
        """The explicitly stated relative priorities."""

        index: int
        """Used to keep track of in what order values were added."""

        _counter: ClassVar[int] = 0
        """Keeps track of the current count which is used to set
        the `index` value."""

        def __init__(
            self,
            value: _V,
            priority: int,
            lower_priority: 'PriorityOrder.RelativePriority[_V]',
            higher_priority: 'PriorityOrder.RelativePriority[_V]',
        ) -> None:
            self.value = value
            self.name = str(value)
            self.ident = hash(value)
            self.priority = priority
            self.relative_priority = PriorityOrder._RelativePriorityContainer(
                name=self.name,
                ident=self.ident,
                lower=self.resolve_priorities(lower_priority),
                higher=self.resolve_priorities(higher_priority),
            )
            self.index = self.__class__._counter
            self.__class__._counter += 1

        def __str__(
            self,
        ) -> str:
            return self.name

        @staticmethod
        def resolve_priorities(
            priority: 'PriorityOrder.RelativePriority[_V]',
        ) -> Set[int]:
            if priority is None:
                return set()
            try:
                if (
                    isinstance(priority, collections.abc.Iterable)
                    and not isinstance(priority, (str, bytes))
                ):
                    return set(map(hash, priority))
            except Exception:
                pass
            return {hash(priority)}

    def __init__(
        self,
    ) -> None:
        self._values: List[PriorityOrder._WrappedValue[_T]] = []

    def __len__(
        self,
    ) -> int:
        return len(self._values)

    @overload
    def __getitem__(
        self,
        index: SupportsIndex,
    ) -> _T:
        ...

    @overload
    def __getitem__(
        self,
        index: slice,
    ) -> 'PriorityOrder[_T]':
        ...

    def __getitem__(
        self,
        index: Union[SupportsIndex, slice],
    ) -> Union[_T, 'PriorityOrder[_T]']:
        """Get a slice from this container or one of its values."""
        if isinstance(index, slice):
            new = self.__class__()
            new._values = self._values[index]
            return new
        return self._values[index].value

    def __delitem__(
        self,
        index: Union[SupportsIndex, slice],
    ) -> None:
        """Delete one or more values in this container.

        If the deleted value(s) had any relative priority relationship
        with the remaining values the entire priority order is recalculated."""
        if isinstance(index, slice):
            removed_values = self._values[index]
        else:
            removed_values = [self._values[index]]
        del self._values[index]
        # If removed value(s) had any relative priority relation
        # with current values recalculate the entire order instead
        # of doing something more fancy
        for value in self._values:
            for removed_value in removed_values:
                if value.relative_priority.has_relation(removed_value.relative_priority):
                    self.reload()
                    return

    def reload(
        self,
    ) -> None:
        """Reshuffle values in this container based on priority."""
        values = sorted(self._values, key=lambda x: x.index)
        del self._values[:]
        for value in values:
            self.add(
                value=value.value,
                priority=value.priority,
                lower_priority=value.relative_priority.lower,
                higher_priority=value.relative_priority.higher,
            )

    @overload
    def add(
        self,
        value: _T,
        *,
        priority: int = 0,
        lower_priority: 'PriorityOrder.RelativePriority[_T]' = None,
        higher_priority: 'PriorityOrder.RelativePriority[_T]' = None,
        replace: bool = False,
    ) -> _T:
        ...

    @overload
    def add(
        self,
        *,
        priority: int = 0,
        lower_priority: 'PriorityOrder.RelativePriority[_T]' = None,
        higher_priority: 'PriorityOrder.RelativePriority[_T]' = None,
        replace: bool = False,
    ) -> Callable[[_T], _T]:
        ...

    def add(
        self,
        value: Optional[_T] = None,
        *,
        priority: int = 0,
        lower_priority: 'PriorityOrder.RelativePriority[_T]' = None,
        higher_priority: 'PriorityOrder.RelativePriority[_T]' = None,
        replace: bool = False,
    ) -> Union[Callable[[_T], _T], _T]:

        def wrapper(value: _T) -> _T:
            wrapped = self._WrappedValue(
                value=value,
                priority=priority,
                lower_priority=lower_priority,
                higher_priority=higher_priority,
            )

            # does the value to be added already exist?
            for i in range(len(self._values)):
                if self._values[i] == wrapped:
                    if replace:
                        del self._values[i]
                        break
                    raise ValueError(
                        f'{wrapped} already exists.',
                    )

            # find insertion index for value based on priorities.
            # circular priorities with a length larger than 1 do
            # not raise an error.
            idx = 0
            for i, position in enumerate(self._values):
                if wrapped.relative_priority > position.relative_priority:
                    break
                if (
                    wrapped.relative_priority < position.relative_priority
                    or wrapped.priority < position.priority
                ):
                    idx = i + 1
            self._values.insert(idx, wrapped)
            return value
        if value is None:
            return wrapper
        return wrapper(value)


class WeakTypeCache:
    """A type cache that holds its values as weak references.

    When iterated over the types are yielded in reverse order,
    the most recently added is yielded first.

    Arguments:
        skip_types: Any types to ignore. If attempting
            to store one of these types it becomes a no-op.
    """

    def __init__(
        self,
        skip_types: Iterable[Any] = (),
    ) -> None:
        self._types: MutableMapping[weakref.ReferenceType, None] = \
            weakref.WeakKeyDictionary()
        self._skip_types = set(skip_types)

    def __len__(
        self,
    ) -> int:
        return len(self._types)

    def __iter__(
        self,
    ) -> Iterator[Any]:
        data = getattr(self._types, 'data', None)
        if isinstance(data, dict):
            for ref in reversed(data):
                type_ = ref()
                if type_ is not None:
                    yield type_
        else:
            yield from reversed(tuple(self._types))

    def __contains__(
        self,
        type_: Any,
    ) -> bool:
        return type_ in self._types

    def add(
        self,
        type_: Any,
    ) -> None:
        """Add a type to the cache.

        Arguments:
            type_: The type to add.
        """
        if is_typing_alias(type_):
            return
        if type_ in self._skip_types:
            return
        try:
            del self._types[type_]
        except KeyError:
            pass
        self._types[type_] = None

    def clear(
        self,
    ) -> None:
        """Clear the cache, removing all stored types."""
        self._types.clear()


def is_missing(
    value: Any,
) -> bool:
    """Determine if a value is missing.

    Supports :attr:`marsh.MISSING`, :attr:`omegaconf.MISSING`
    and :attr:`dataclasses.MISSING`.

    Arguments:
        value: Any value to test for missing.

    Returns:
        ``True`` if missing, else ``False``.
    """
    return value in (omegaconf.MISSING, dataclasses.MISSING)


def is_sequence(
    value: Any,
) -> TypeGuard[Sequence]:
    """Determine if a value is a sequence (excluding string, bytes).

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a sequence, else ``False``.
    """
    try:
        return (
            not is_mapping(value)
            and not isinstance(value, (str, bytes))
            and isinstance(value, SequenceProtocol)
            and is_obj_instance(value)
        )
    except TypeError:
        return False


def is_sequence_type(
    value: Any,
) -> TypeGuard[Type[Sequence]]:
    """Determine if a value is a sequence type (excluding string, bytes types).

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a sequence type, else ``False``.
    """
    if (origin := get_origin(value)) is not None:
        return is_sequence_type(origin)
    try:
        return (
            not is_mapping_type(value)
            and not issubclass(value, (str, bytes))
            and isinstance(value, SequenceProtocol)
            and not is_obj_instance(value)
        )
    except TypeError:
        return False


def is_empty_tuple_type(
    value: Any,
) -> TypeGuard[Type[Tuple[()]]]:
    """Determine if a value is an empty tuple type
    (``typing.Tuple[()]``, ``tuple[()]``).

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a an empty tuple type, else ``False``.
    """
    # only type aliases can specify contents of tuple
    if get_origin(value) is not tuple:
        return False
    # type alias without arguments is considered Tuple[Any, ...]
    if value is Tuple:
        return False
    args = get_args(value)
    # Empty args is considered empty tuple in 3.9+ when using
    # tuple[()] instead of typing.Tuple[()]
    if not args:
        return True
    # For typing.Tuple[()] the empty tuple argument is retained.
    return args == ((),)


def is_fixed_size_tuple_type(
    value,
) -> bool:
    """Determine if a value is fixed size tuple type.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a a fixed size tuple type, else ``False``.
    """
    return (
        (
            value is tuple
            or get_origin(value) is tuple
        )
        and (
            (
                (args := get_args(value))
                and ... not in args
            )
            or is_empty_tuple_type(value)
        )
    )


def is_mapping(
    value: Any,
) -> TypeGuard[Mapping]:
    """Determine if a value is a mapping.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a mapping, else ``False``.
    """
    try:
        return (
            isinstance(value, MappingProtocol)
            and is_obj_instance(value)
        )
    except TypeError:
        return False


def is_mapping_type(
    value: Any,
) -> TypeGuard[Type[Mapping]]:
    """Determine if a value is a mapping type.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a mapping, else ``False``.
    """
    if (origin := get_origin(value)) is not None:
        return is_mapping_type(origin)
    try:
        return (
            isinstance(value, MappingProtocol)
            and not is_obj_instance(value)
        )
    except TypeError:
        return False


def is_primitive(
    value: Any,
) -> TypeGuard[Union[int, float, bool, str]]:
    """Determine if a value is primitive.

    ``PrimitiveElement: int | float | bool | str``

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is primitive, else ``False``.
    """
    try:
        return isinstance(value, (int, float, str, bool))
    except TypeError:
        return False


def is_primitive_type(
    value: Any,
) -> TypeGuard[Union[Type[int], Type[float], Type[bool], Type[str]]]:
    """Determine if a value is primitive type.

    ``PrimitiveElement: int | float | bool | str``

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a primitive type, else ``False``.
    """
    try:
        return issubclass(value, (int, float, str, bool))
    except TypeError:
        return False


def is_namedtuple(
    value: Any,
) -> TypeGuard[NamedTupleProtocol]:
    """Determine if a value is a namedtuple.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a namedtuple, else ``False``.
    """
    return (
        is_obj_instance(value)
        and is_namedtuple_type(get_type(value))
    )


def is_namedtuple_type(
    value: Any,
) -> TypeGuard[Type[NamedTupleProtocol]]:
    """Determine if a value is a namedtuple type.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a namedtuple type, else ``False``.
    """
    try:
        if not isinstance(value, NamedTupleProtocol):
            return False
        for cls in inspect.getmro(value):  # type: ignore
            if tuple in cls.__bases__:
                return True
    except Exception:
        pass
    return False


def is_typed_namedtuple(
    value: Any,
) -> TypeGuard[NamedTupleProtocol]:
    """Determine if a value is a typed namedtuple.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a namedtuple, else ``False``.
    """
    try:
        return (
            is_namedtuple(value)
            and bool(get_type_hints(value))
        )
    except TypeError:
        return False


def is_typed_namedtuple_type(
    value: Any,
) -> TypeGuard[Type[NamedTupleProtocol]]:
    """Determine if a value is a typed namedtuple type.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a typed namedtuple type, else ``False``.
    """
    try:
        return (
            is_namedtuple_type(value)
            and bool(get_type_hints(value))
        )
    except TypeError:
        return False


def is_typeddict_type(
    value: Any,
) -> bool:
    """Determine if a value is a typed dict type.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a typed dict type, else ``False``.
    """
    return any(is_td(value) for is_td in _IsTypedDict)


def is_defaultdict_type(
    value: Any,
) -> bool:
    """Determine if a value is a default dict type.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a default dict type, else ``False``.
    """
    if (
        value is DefaultDict
        or get_origin(value) is collections.defaultdict
    ):
        return True
    try:
        return issubclass(value, collections.defaultdict)
    except TypeError:
        return False


def is_callable(
    value: Any,
) -> bool:
    """Determine if a value is callable.

    Always returns ``False`` if the value is
    a protocol or typing alias.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a callable,
        else ``False``.
    """
    try:
        return (
            callable(value)
            and not is_protocol(value)
            and not is_typing_alias(value)
        )
    except Exception:
        return False


def is_obj_instance(
    value: Any,
) -> bool:
    """Determine if a value is an instantiated object.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is an iinstantiated object,
        else ``False``.
    """
    if is_typing_alias(value):
        return False
    try:
        return not issubclass(type(value), type)
    except Exception:
        return False


def is_annotated(
    value: Any,
) -> bool:
    """Determine if a value originates from :data:`typing.Annotated`.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value originates from :data:`typing.Annotated`, else ``False``.
    """
    return (
        get_origin(value) is Annotated  # python 3.9+
        or typing_extensions.get_origin(value) is Annotated  # python 3.8
    )


def get_annotations(
    value: Any,
) -> Sequence:
    """Extract the additional arguments of an instance of :data:`typing.Annotated`

    Arguments:
        value: The :data:`typing.Annotated` instance.

    Returns:
        The annotations.
    """
    if not is_annotated(value):
        raise ValueError(
            f'expected `Annotated` type, got {value}',
        )
    if get_origin(value) is Annotated:
        return get_args(value)[1:]
    return typing_extensions.get_args(value)[1:]


def is_protocol(
    value: Any,
) -> bool:
    """Determine if a value is a protocol.

    Any class that has :class:`typing.Protocol` in its
    immediate bases is considered a protocol.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a protocol, else ``False``.
    """
    for cls in getattr(value, '__bases__', ()):
        if cls in _ProtocolTypes:
            return True
    return False


def is_literal(
    value: Any,
) -> bool:
    """Determine if a value is a typing.Literal.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a typing.Literal, else ``False``.
    """
    return get_origin(value) in _LiteralTypes


def is_literal_string(
    value: Any,
) -> bool:
    """Determine if a value is a typing.LiteralString.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a typing.LiteralString, else ``False``.
    """
    return value in _LiteralStringTypes


def is_typing_alias(
    value: Any,
) -> bool:
    """Determine if a value is a typing alias.

    If the class name ends with ``'_GenericAlias'``,
    ``'_SpecialForm'`` or ``'_AnnotatedAlias'``
    the value is considered a typing alias.

    For python 3.9+ a check is made against :class:`types.GenericAlias`.

    Arguments:
        value: Any value to evaluate.

    Returns:
        ``True`` if value is a typing alias, else ``False``.
    """
    return (
        get_origin(value) is not None
        or type(value) is getattr(types, 'GenericAlias', None)
        or value in _TypeAliasTypes
        or hasattr(value, '__class__')
        and (
            value.__class__.__name__.endswith('_GenericAlias')
            or value.__class__.__name__.endswith('_SpecialForm')
            or value.__class__.__name__.endswith('_AnnotatedAlias')
        )
    )


def is_optional(
    type_: Any,
) -> bool:
    """Determine if a type is a optional.

    Arguments:
        type: The type to evaluate.

    Returns:
        ``True`` if value is ``typing.Union`` and
        :data:`None` is in its arguments, else ``False``.
    """
    if is_annotated(type_):
        type_ = get_origin(type_)
    return get_origin(type_) is Union \
        and type(None) in get_args(type_)


def get_type(
    value: Any,
) -> Any:
    """Attempt to retrieve the type of an object.

    If the value is a generic typing alias, the origin type is returned.
    I.e. ``get_type(typing.List[str])`` returns the builtins ``list`` type.

    If the value is an instance of a class, the class is returned.

    If the value is a class, it is directly returned.

    >>> assert get_type([1, 2, 3]) == get_type(list)

    Arguments:
        value: Value to retrieve type from.

    Returns:
        The type.
    """
    if (origin := get_origin(value)) is not None:
        return get_type(origin)
    if is_typing_alias(value):
        return value
    try:
        if issubclass(type(value), type):
            return value
    except Exception:
        pass
    return type(value)


def get_optional_type(
    type_: Any,
) -> Any:
    """Get the non-optional version of
    an optional type.

    Arguments:
        type: The optional type.

    Returns:
        The type as non-optional.
    """
    if not is_optional(type_):
        raise ValueError(
            'attempted to fetch optional type '
            'from non-optional type variable: '
            f'{type_}',
        )
    if is_annotated(type_):
        type_ = get_origin(type_)
    args = []
    for arg in get_args(type_):
        if arg not in (None, type(None)):  # noqa: E721
            args.append(arg)
    if len(args) == 1:
        return args[0]
    return Union[tuple(args)]  # pyright: ignore


def get_type_name(
    value: Any,
) -> str:
    """Get a string representation for the type of a value.

    Arguments:
        value: A type or instance of a type to get
            a string representation for.

    Returns:
        The string representation of the value.
    """
    if is_annotated(value):
        value = get_origin(value)
    if is_typing_alias(value):
        return str(value).replace('typing.', '')
    return getattr(get_type(value), '__name__', str(value))


def bytes_to_base64(
    value: bytes,
) -> str:
    """Encode bytes to a base64 string.

    Follows the format used by protobuf.

    Arguments:
        value: The bytes to encode.

    Returns:
        The base64 string representing the bytes argument.
    """
    return base64.urlsafe_b64encode(value).decode('utf-8')


def base64_to_bytes(
    value: str,
) -> bytes:
    """Decode a base64 string to bytes.

    Follows the format used by protobuf.

    Arguments:
        value: The base64 string to decode.

    Returns:
        The bytes representation of the base64 string argument.
    """
    encoded = value.encode('utf-8')
    padded_value = encoded + b'=' * (4 - len(encoded) % 4)
    return base64.urlsafe_b64decode(padded_value)


def primitive_to_bool(
    value: Union[int, float, bool, str],
) -> bool:
    """Convert a primitive value to a bool.

    Follows the YAML convention instead of
    using ``__bool__`` function of the object,
    see :func:`str_to_bool` for more info.

    Raises :class:`ValueError` on failure.

    Arguments:
        value: The primitive value to convert
            into bool.

    Returns:
        The bool representation of the value argument.
    """
    if isinstance(value, bool):
        return value
    if value == 1:
        return True
    elif value == 0:
        return False
    return str_to_bool(str(value))


def str_to_bool(
    value: str,
) -> bool:
    """Cast a string to a boolean.

    ``True: 1 | [Tt][Rr][Uu][Ee] | [Yy] | [Yy][Ee][Ss] | [Oo][Nn]``

    ``False: 0 | [Ff][Aa][Ll][Ss][Ee] | [Nn] | [Nn][Oo] | [Oo][Ff][Ff]``

    Inspired by https://yaml.org/type/bool.html

    Raises :class:`ValueError` if the string does not
    conform to this format.

    Arguments:
        value: String to cast.

    Returns:
        The input string parsed as a bool.
    """
    if value.lower() in ('1', 'true', 'y', 'yes', 'on'):
        return True
    elif value.lower() in ('0', 'false', 'n', 'no', 'off'):
        return False
    raise ValueError(
        'Expected 1 | 0 | [Tt][Rr][Uu][Ee] | '
        '[Yy] | [Yy][Ee][Ss] | [Oo][Nn] | '
        '[Ff][Aa][Ll][Ss][Ee] | [Nn] | '
        f'[Nn][Oo] | [Oo][Oo][Ff], got: {value}',
    )


def str_to_int(
    value: str,
) -> int:
    """Cast a string to an int.

    Compared to using :class:`int` to cast the value
    this function allows values such as ``"0.0"`` by
    first parsing the value as a float before casting
    it to an int (unless it contains decimals).

    Raises :class:`ValueError` if the input string can not be
    parsed as an int.

    Arguments:
        value: String input to parse as int.

    Returns:
        The parsed int.
    """
    try:
        return int(value)
    except ValueError as err:
        try:
            return float_to_int(float(value))
        except ValueError:
            raise err from None


def float_to_int(
    value: float,
) -> int:
    """Cast a float to an int.

    Raises :class:`ValueError` if the input float is not
    an integer (contains decimal values).
    This differs from using :class:`int`
    to cast a float since decimal values
    produce an error instead of being dropped.

    Raises :class:`ValueError` on failure.

    Arguments:
        value: Float input to cast as int.

    Returns:
        Integer of the input value.
    """
    if not value.is_integer():
        raise ValueError(
            f'could not convert to int: {value}',
        )
    return int(value)


def cast_primitive(
    type_: Type[_P],
    value: Union[int, float, bool, str],
) -> _P:
    """Cast a primitive value to a specified primitive type.

    Uses :func:`primitive_to_bool`, :func:`str_to_int`
    and :func:`float_to_int` when applicable.

    Raises :class:`ValueError` if unsuccessful.

    Arguments:
        primitive: The primitive type (:class:`int`, :class:`float`,
            :class:`bool` or :class:`str`).
        value: A primitive value to cast.

    Returns:
        The casted value.
    """
    if not issubclass(type_, (int, float, bool, str)):
        raise ValueError(f'only primitive (sub)types are valid: {type_}')
    if not is_primitive(value):
        raise ValueError(f'only primitive values are valid: {value}')
    if issubclass(type_, bool):
        return primitive_to_bool(value)
    if issubclass(type_, int) and isinstance(value, str):
        return str_to_int(value)
    if issubclass(type_, int) and isinstance(value, float):
        return float_to_int(value)
    return type_(value)


def cast_literal(
    literal: _P,
    value: Union[int, float, bool, str],
) -> _P:
    """Attempts to cast a primtive value to the same type as a primitive
    literal and match it.

    Raises :class:`ValueError` if not able to match.

    Arguments:
        literal: The primitive literal to cast to.
        value: The value to cast.

    Returns:
        The literal.
    """
    if cast_primitive(type(literal), value) != literal:
        raise ValueError(f'could not convert to {literal}: {value}')
    return literal


def match_literal(
    literals: Iterable[Union[int, float, bool, str]],
    value: Union[int, float, bool, str],
) -> Union[int, float, bool, str]:
    """Attempts to cast and match a value to a set of primitive literals.

    Raises :class:`ValueError` if not able to match.

    Arguments:
        literals: The primitive literals to match.
        value: The value to cast and match.

    Returns:
        The literal that was matched.
    """
    for literal in literals:
        try:
            return cast_literal(
                literal=literal,  # type: ignore
                value=value,
            )
        except ValueError:
            pass
    raise ValueError(
        'could not match any of the literals '
        f'{tuple(literals)}: {value}',
    )


def cast_none(
    value: Any,
) -> None:
    """Attempt to cast a value to :data:`None`.

    Allowed values are case insensitive
    strings ``"null"`` and ``"none"``
    or a missing value.

    Raises :class:`ValueError` on failure.

    Arguments:
        value: The value to cast to :data:`None`

    Returns:
        The casted value.
    """
    if (
        is_missing(value)
        or value in (None, type(None))
    ):
        return None
    if str(value).lower() in ('null', 'none'):
        return None
    raise ValueError(f'could not cast to `None`: {value}')


def extract_description(
    doc: str,
) -> str:
    """Omit all but the main text in a docstring.

    Attempts to omit things such as arguments and
    return value from a docstring.

    Arguments:
        doc: Docstring.

    Returns:
        The description if found, else the entire docstring.
    """
    description = ''
    if not doc:
        return description
    try:
        parsed = docstring_parser.parse(doc)
        try:
            if parsed.short_description:
                description = parsed.short_description
        except Exception:
            pass
        if parsed.long_description:
            if description:
                description = f'{description}\n\n{parsed.long_description}'
            else:
                description = parsed.long_description
    except Exception:
        pass
    return description or doc


def get_description(
    cls,
) -> Optional[str]:
    """Get the docstring for a class.

    An attempt is made to omit all but the
    main text in the docstring. This means
    that the return value should be missing
    things such as arguments and return value
    descriptions.

    Arguments:
        cls: Class to retrieve description from.

    Returns:
        The description if found, else :data:`None`.
    """
    doc = getattr(cls, '__doc__', None)
    if not doc:
        return None
    return extract_description(doc)


def _get_attribute_description(
    cls,
    name: str,
) -> Optional[str]:
    doc = getattr(cls, '__doc__', None)
    if doc:
        try:
            for param in docstring_parser.parse(doc).params:
                try:
                    if param.arg_name == name and param.description:
                        return param.description
                except Exception:
                    pass
        except Exception:
            pass
    try:
        ast_body = ast.parse(inspect.getsource(cls)).body[0].body  # type: ignore
    except Exception:
        return None
    node_iter = iter(ast_body)
    while True:
        try:
            node = next(node_iter)
        except StopIteration:
            break
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            try:
                node = next(node_iter)
                if not isinstance(node, ast.Expr):
                    continue
                if isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        return inspect.cleandoc(node.value.value)
            except StopIteration:
                pass
            break
    return None


def get_attribute_description(
    cls,
    name: str,
) -> Optional[str]:
    """Get the docstring for an attribute of
    a class.

    Arguments:
        cls: Class for which an attribute description
            should be fetched.
        name: The name of the attribute.

    Returns:
        The attribute description if found, else :data:`None`.
    """
    try:
        for base in inspect.getmro(cls):
            if base == object:
                continue
            descr = _get_attribute_description(
                base,
                name=name,
            )
            if descr:
                return descr
    except Exception:
        try:
            return _get_attribute_description(
                cls,
                name=name,
            )
        except Exception:
            pass
    return None


def as_dataclass(
    cls: Type[_T],
) -> Type[_T]:
    """Safely convert a class into a dataclass.

    This function can be called multiple times on the same
    class without it raising an error the second time.

    Arguments:
        cls: Class to convert into dataclass.

    Returns:
        Dataclass.
    """
    assert not is_obj_instance(cls)
    if not hasattr(cls, '__dataclass_fields__'):
        return dataclasses.dataclass(cls)
    for field in dataclasses.fields(cls):
        if (
            field.name in getattr(cls, '__annotations__', {})
            and field.default_factory != dataclasses.MISSING
        ):
            setattr(cls, field.name, field)
    return dataclasses.dataclass(cls)


def get_closest(
    value: str,
    candidates: Iterable[str],
) -> Optional[str]:
    """Get the closest value to some input from a set of candidates.

    If no close value is found, :data:`None` is returned.

    Arguments:
        value: The input value.
        candidates: The values to evaluate closeness to.

    Returns:
        The closest candidate. :data:`None` if no candidate is close.
    """
    close = difflib.get_close_matches(
        value,
        candidates,
        n=1,
    )
    if close:
        return close[0]
    return None


def get_closest_error_message(
    value: str,
    candidates: Iterable[str],
    key: str = 'key',
) -> str:
    """Get an error message for a key.

    The error message can take two forms, the
    first being ``'unknown "{key}"'`` and the
    second being ``'unknown "{key}", did you mean "{closest}"?'``
    which is only returned when a close match is found
    among the candidates.

    Arguments:
        value: The input value.
        candidates: The values to evaluate closeness to.
        key: A name for the key value.

    Returns:
        The error message.
    """
    message = f'unknown {key} "{value}"'
    closest = get_closest(
        value=value,
        candidates=candidates,
    )
    if closest:
        message += f', did you mean "{closest}"?'
    return message


def inspect_sequence_type(
    sequence_type: Any,
) -> Any:
    """Get the type of the content of a sequence type.

    Expects a single content type.
    If no content type is found or there are multiple content
    types ``typing.Any`` is returned.

    Arguments:
        type_: The type variable of a sequence.

    Returns:
        The type for the content of the input sequence type.

    >>> get_sequence_type(typing.List[int])
    <class 'int'>
    >>> get_sequence_type(typing.Tuple[str, ...])
    <class 'str'>
    >>> get_sequence_type(list)
    typing.Any
    >>> get_sequence_type(typing.Tuple[str, int, float])
    typing.Any
    """
    if is_annotated(sequence_type):
        sequence_type = get_origin(sequence_type)
    orig_bases = getattr(
        sequence_type,
        '__orig_bases__',
        (),
    )
    for base in (sequence_type,) + orig_bases:
        if is_sequence_type(base):
            t_args = get_args(base)
            if (
                len(t_args) == 1
                or len(t_args) == 2 and ... in t_args
            ):
                for t in t_args:
                    if t != ...:
                        return t
    return Any


class _MappingKeyValueTypesInfo(NamedTuple):
    key: Any
    value: Any


def inspect_mapping_type(
    mapping_type: Any,
) -> _MappingKeyValueTypesInfo:
    """Get the key and value type from a mapping type.

    Returns ``typing.Any`` for types that could not be inferred.

    Arguments:
        type_: The type variable of a mapping.

    Returns:
        The key and value type.

    >>> get_sequence_type(typing.Dict[str, int])
    (<class 'str'>, <class 'int'>)
    >>> get_sequence_type(typing.Mapping[str, typing.List[int]]])
    (<class 'str'>, typing.List[int])
    >>> get_sequence_type(dict)
    (typing.Any, typing.Any)
    """
    if is_annotated(mapping_type):
        mapping_type = get_origin(mapping_type)
    orig_bases = getattr(
        mapping_type,
        '__orig_bases__',
        getattr(
            get_type(mapping_type),
            '__orig_bases__',
            (),
        ),
    )
    for base in (mapping_type, get_type(mapping_type)) + orig_bases:
        if is_mapping_type(base):
            t_args = get_args(base)
            if len(t_args) == 2:
                return _MappingKeyValueTypesInfo(t_args[0], t_args[1])
    return _MappingKeyValueTypesInfo(Any, Any)


def is_testing() -> bool:
    """Discover if the current runtime is for testing with Pytest."""
    return (
        'PYTEST_CURRENT_TEST' in os.environ
        or 'pytest' in sys.modules
    )


def get_terminal_width() -> int:
    """Attempt to get the width of the current terminal.

    The terminal size is preprocessed in a similar way
    to :mod:`argparse`.
    """
    return max(
        shutil.get_terminal_size().columns - 2,
        11,
    )
