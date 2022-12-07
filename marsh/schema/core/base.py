from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    SupportsIndex,
    Type,
    TypeVar,
    Union,
    overload,
    cast,
)

import marsh


_S = TypeVar('_S', bound='Schema')


class SchemaSelection(List[Type[_S]], Generic[_S]):
    """A sequence of schema types that were matched against a value.

    Contains one or more schema types, with all but the last one
    being wrapper classes."""

    @overload
    def __getitem__(
        self,
        index: SupportsIndex,
    ) -> Type[_S]:
        ...

    @overload
    def __getitem__(
        self,
        index: slice,
    ) -> 'SchemaSelection[_S]':
        ...

    def __getitem__(
        self,
        index: Union[SupportsIndex, slice],
    ) -> Union[Type[_S], 'SchemaSelection[_S]']:
        if isinstance(index, slice):
            return self.__class__(super().__getitem__(index))
        return super().__getitem__(index)

    def __add__(  # type: ignore
        self,
        other,
    ) -> 'SchemaSelection[_S]':
        return self.__class__(list(self) + list(other))

    def build(
        self,
        *args,
        **kwargs,
    ) -> _S:
        """Build the selected schema(s) into a single schema.

        Arguments:
            args: Any positional arguments to pass
                on to the schema constructor.
            kwargs: Any keyword arguments to pass
                on to the schema constructor.

        Returns:
            Schema instance.
        """
        if len(self) > 1:
            return self[0](
                *args,
                wrapped=self[1:],
                **kwargs,
            )
        return self[0](
            *args,
            **kwargs,
        )


class SchemaRegistry(Generic[_S]):
    """Holds schema classes in a prioritized order.

    Arguments:
        error: Type of the error to throw
            when no schema could be matched
            during selection.
    """

    priority: marsh.utils.PriorityOrder[Type[_S]]

    def __init__(
        self,
        error: Type[Exception] = marsh.errors.MarshError,
    ) -> None:
        self.priority = marsh.utils.PriorityOrder()
        self.error = error

    def __iter__(
        self,
    ) -> Iterator[Type[_S]]:
        yield from self.priority

    @overload
    def register(
        self,
        schema: Type[_S],
        *,
        priority: int = 0,
        lower_priority: marsh.utils.PriorityOrder.RelativePriority[Type[_S]] = None,
        higher_priority: marsh.utils.PriorityOrder.RelativePriority[Type[_S]] = None,
        replace: bool = False,
    ) -> Type[_S]:
        ...

    @overload
    def register(
        self,
        *,
        priority: int = 0,
        lower_priority: marsh.utils.PriorityOrder.RelativePriority[Type[_S]] = None,
        higher_priority: marsh.utils.PriorityOrder.RelativePriority[Type[_S]] = None,
        replace: bool = False,
    ) -> Callable[[Type[_S]], Type[_S]]:
        ...

    def register(
        self,
        schema: Optional[Type[_S]] = None,
        *,
        priority: int = 0,
        lower_priority: marsh.utils.PriorityOrder.RelativePriority[Type[_S]] = None,
        higher_priority: marsh.utils.PriorityOrder.RelativePriority[Type[_S]] = None,
        replace: bool = False,
    ) -> Union[Callable[[Type[_S]], Type[_S]], Type[_S]]:
        if schema is not None:
            return self.priority.add(
                schema,
                priority=priority,
                lower_priority=lower_priority,
                higher_priority=higher_priority,
                replace=replace,
            )
        return self.priority.add(
            priority=priority,
            lower_priority=lower_priority,
            higher_priority=higher_priority,
            replace=replace,
        )

    def match(
        self,
        value: Any,
    ) -> SchemaSelection[_S]:
        """Match a value to one or more schemas types.

        Selected schema types are returned in the order
        they were match. The matching is canceled and
        the results are returned when the first non-wrapper
        schema type has been matched.

        Raises an error if no non-wrapper schema could be matched.

        Arguments:
            value: Value to match against schema types.

        Returns:
            Selection of schema types.
        """
        schemas: SchemaSelection[_S] = SchemaSelection()
        for schema in self.priority:
            try:
                if schema.match(value):
                    schemas.append(schema)
                    if not issubclass(schema, WrapperSchema):
                        return schemas
            except TypeError:
                pass
        raise self.error(
            f'no schema matched value: {value}',
        )


class SchemaMeta(type, Generic[_S]):
    """Metaclass for schemas.

    If calling the constructor on the base schema class
    it will instead match the input with all registered
    schemas and return an instance of a subclass."""

    registry: SchemaRegistry[_S] = SchemaRegistry()
    """The registered schema types."""

    def __call__(
        cls,
        value,
        *args,
        **kwargs,
    ):
        if cls is not Schema:
            return type(object).__call__(cls, value, *args, **kwargs)
        return cls.registry.match(value).build(value, *args, **kwargs)

    def __init_subclass__(
        metacls,
    ) -> None:
        super().__init_subclass__()
        if hasattr(metacls, 'registry') and metacls.registry is not Schema.registry:
            return
        metacls.registry = SchemaRegistry()


class Schema(metaclass=SchemaMeta):
    """Base class for schemas.

    A schema is a class that can be matched
    against a value and then initialized with
    that value and any other arguments.

    The base class works as a factory when
    its called as a constructor, selecting
    the correctly matched schema and returning
    an instance of it.

    Arguments:
        value: The value to match.
        args: Unused but caught positional arguments.
        kwargs: Unused but caught keyword arguments.
    """

    def __init__(
        self,
        value: Any,
        *args,
        **kwargs,
    ) -> None:
        self.value = value

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        """Match this class against a value.

        Arguments:
            value: The value to match against.

        Returns:
            ``True`` if matched, else ``False``.
        """
        raise NotImplementedError

    @staticmethod
    def doc_static_type() -> Optional[str]:
        """Get a static string representation
        of the type supported by this schema.

        Returns:
            The name of the type.
        """
        return None

    @staticmethod
    def doc_static_description() -> Optional[str]:
        """Get a static string description
        of how the type supported by this schema
        is used.

        Returns:
            The description.
        """
        return None


class WrapperSchema(Schema, Generic[_S]):
    """Wraps another schema, potentially
    manipulating calls and return values to/from it.

    The wrapper will lazily initialize its wrapped schema,
    holding its type and input arguments instead of an
    instance of the schema up until the first time
    the schema is accessed.

    Arguments:
        args: Positional arguments stored and passed
            to the constructor of the schema being
            wrapped.
        wrapped: A schema type or an iterable of schema
            types in wrapping order.
        kwargs: Keyword arguments stored and passed
            to the constructor of the schema being
            wrapped.
    """

    wrapped: Sequence[Type[_S]]
    """The types of the schemas that are wrapped."""

    @property
    def schema(
        self,
    ) -> _S:
        """Lazy reference to inner schema. Constructed the first time it is
        being accessed."""
        if getattr(self, '_schema', None) is None:
            if not (
                hasattr(self, 'wrapped')
                and hasattr(self, '_args')
                and hasattr(self, '_kwargs')
            ):
                raise AttributeError(
                    'can not access attribute "schema" before '
                    'WrapperSchema.__init__() call',
                )
            wrapped = self.wrapped[1:]
            schema_type = self.wrapped[0]
            if marsh.utils.is_missing(schema_type):
                raise ValueError(
                    f'{self.__class__.__name__}: wrapped internal '
                    'schema type is missing',
                )
            if wrapped:
                self._schema = schema_type(
                    *self._args,
                    wrapped=wrapped,
                    **self._kwargs,
                )
            else:
                self._schema = schema_type(
                    *self._args,
                    **self._kwargs,
                )
        return self._schema

    @schema.setter
    def schema(
        self,
        value: _S,
    ) -> None:
        self._schema = value

    @property
    def inner_schema(
        self,
    ) -> _S:
        """Bypass any wrapper succeeding wrapper schemas
        to extract the most inner schema."""
        schema = self.schema
        while isinstance(schema, WrapperSchema):
            schema = schema.schema
        return schema

    _args: tuple
    """Positional arguments which are passed to the schema type
    being wrapped when constructed."""

    _kwargs: Mapping
    """Keyword arguments which are passed to the schema type
    being wrapped when constructed."""

    def __init__(
        self,
        *args,
        wrapped: Union[Type[_S], Iterable[Type[_S]]],
        **kwargs,
    ) -> None:
        try:
            if issubclass(wrapped, Schema):  # type: ignore
                wrapped = (cast(Type[_S], wrapped),)
            else:
                wrapped = tuple(cast(Iterable[Type[_S]], wrapped))
        except Exception:
            wrapped = tuple(cast(Iterable[Type[_S]], wrapped))
        if not wrapped:
            raise ValueError(
                f'{self.__class__.__name__}: at least one schema '
                'type must be given to a wrapper schema',
            )
        if issubclass(wrapped[-1], WrapperSchema):
            raise ValueError(
                f'{self.__class__.__name__}: the final schema type '
                'being wrapped may not be a wrapper itself: '
                f'{wrapped[-1].__name__}',
            )
        super().__init__(*args, **kwargs)
        self.wrapped = wrapped
        self._args = args
        self._kwargs = kwargs


caches: marsh.utils.CachePool = marsh.utils.CachePool()
"""Pool of caches used throughout :mod:`marsh.schema`"""
