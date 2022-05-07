Namespaces
==========

Namespaces enable covariance in the type returned by unmarshaling.
This means that a superclass can be specified as the type and one
of its subclasses is constructed.

A namespace is a set of types, each associated with its own unique name.
There are no other limitations to the inheritance hierarchy beyond that all types
must be subtypes of the base class of the namespace.

.. note::

    Namespaces are applied through the entire framework. In the examples below
    :func:`marsh.unmarshal(...)` is used but the namespace functionality is applied
    recursively and thus affects nested types (for example, the types of the
    attributes of a dataclass) as well.


A new namespace is created by supplying a name and a base class.

.. code-block:: python

    import marsh

    class Model:

        def predict(
            self,
            input: List[float]
        ) -> float:
            raise NotImplementedError

    namespace = marsh.namespaces.new('model', Model)


Types can be added to the namespace through the registration function.

.. code-block:: python

    @namespace.register(name='a')
    class ModelA(Model):

        def __init__(
            self,
            layers: int
        ) -> None:
            ...

    @namespace.register(name='b')
    class ModelB(Model):

        def __init__(
            self,
            clusters: int
        ) -> None:
            ...


Once added, the types can be selected during unmarshaling by specifying
a ``'name'`` field in the input. The name field is stripped before the rest
of the inputs are passed to the constructor of the type corresponding to the name.

.. code-block:: python
    :caption: Covariant return type

    model = marsh.unmarshal(Model, dict(name='a', layers=3))
    assert isinstance(model, ModelA)


If no name is supplied with the input when unmarshaling the return type
is invariant relative to the input type.

.. code-block:: python
    :caption: Invariant return type

    model = marsh.unmarshal(Model, {})
    assert isinstance(model, Model)


It is not required that the type given to :func:`marsh.unmarshal` is the base
class of the namespace. Other classes in the inheritance hierarchy may be
provided (even if they themselves are not registered to the namespace).

.. code-block:: python

    class StatefulModel(Model):
    """Part of inheritance hierarchy but not registered
    to the namespace."""

        def get_state(
            self
        ) -> bytes:
            raise NotImplementedError


    @namespace.register(name='c')
    class ModelC(StatefulModel):
        ...

    @namespace.register(name='d')
    class ModelD(StatefulModel):
        ...

    # here we can use name='c' or name='d'. The other models
    # do not inherit `StatefulModel` and specifying their names
    # would result in an error.
    model = marsh.unmarshal(StatefulModel, dict(name='c'))
    assert isinstance(model, ModelC)
