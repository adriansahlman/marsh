Extending
=========

It is possible to increase the number of types that are supported
by the framework (or customize how certain types are marshaled/unmarshaled).


Schema
------

All (un)marshaling is supported through the :class:`marsh.schema.core.Schema` class
(there are two separate variants of this, one for marshaling and one for unmarshaling).

The common part of the schema is their matching function which always takes a single value
and returns a boolean based on if the schema class matched the value or not. If the schema
matched the value it will be initialized with the same value which is accessible through
``self.value``.


Registration
------------

A new implementation of a schema must be registered if it is to be available
for use by :mod:`marsh`. This is done through the function :func:`marsh.schema.register` which
acts as a decorator for a registered schema class.

Priority
^^^^^^^^

Registered schemas are ordered by their priority which can
be set during registration. The priority order affects which
schemas are matched before others.

The base priority is an integer value. Higher values correspond to higher priority.
There is also a relative priority where a schema may preceed or succeed one or more other
schemas. The relative priority is considered before the base priority.


Marshal
-------

Lets consider the steps for supporting marshaling of :class:`complex` values.
We need to implement and register a new schema. This schema should inherit
the base class :class:`marsh.schema.MarshalSchema`.

.. code-block:: python

    import marsh


    @marsh.schema.register
    class ComplexMarshalSchema(marsh.schema.MarshalSchema):

        @classmethod
        def match(
            cls,
            value
        ) -> bool:
            # we match an instance of `complex`, not its type
            return isinstance(value, complex)

        def marshal(
            self
        ) -> dict:
            return {
                'real': self.value.real,
                'imag': self.value.imag,
            }


Marshaling for the :class:`complex` type is now supported through the framwork.


Unmarshal
---------

For unmarshaling we perform similar steps as with marshaling but with slight differences.
For starters, we need to use a different base class; :class:`marsh.schema.UnmarshalSchema`.
We also need to consider returning a default value when the input is missing. For example,
if a field in a dataclass is of type :class:`complex` and has a default value of ``complex(1, 2)``
then our schema class would match that field and contain the type as well as the default value.

.. code-block:: python

    import marsh


    @marsh.schema.register
    class ComplexUnmarshalSchema(marsh.schema.UnmarshalSchema[complex]):

        @classmethod
        def match(
            cls,
            value
        ) -> bool:
            # We match the type of `complex`, not its instance
            return value == complex

        def unmarshal(
            self,
            element: marsh.element.ElementType
        ) -> complex:
            # we first need to check if the input value is missing
            if marsh.utils.is_missing(element):
                # if there is a default value we return it instead
                if self.has_default():
                    return self.get_default()
                # otherwise we raise an error since we did not get
                # a value to unmarshal.
                raise marsh.errors.MissingValueError
            if isinstance(element, float):
                return complex(element)
            if marsh.utils.is_mapping(element):
                return complex(**element)
            if marsh.utils.is_sequence(element):
                return complex(*element)
            raise marsh.errors.UnmarshalError(element)


In the above example we allow sequence and mapping inputs without checking their actual values. We could instead
take advantage of :mod:`marsh`'s ability to unmarshal typing constructs as a way to validate our input.

.. code-block:: python

    from typing import (
        Tuple,
        TypedDict,
        Union,
    )
    import marsh


    class Kwargs(TypedDict, total=False):
        real: float
        imag: float


    Args = Union[Tuple[float], Tuple[float, float]]


    InputType = Union[float, Args, Kwargs]


    @marsh.schema.register
    class ComplexUnmarshalSchema(marsh.schema.UnmarshalSchema[complex]):

        @classmethod
        def match(
            cls,
            value
        ) -> bool:
            return value == complex

        def unmarshal(
            self,
            element: marsh.element.ElementType
        ) -> complex:
            if marsh.utils.is_missing(element):
                if self.has_default():
                    return self.get_default()
                raise marsh.errors.MissingValueError
            arg = marsh.unmarshal(InputType, element)
            if isinstance(arg, float):
                return complex(arg)
            if marsh.utils.is_mapping(arg):
                return complex(**arg)
            else:
                return complex(*arg)
