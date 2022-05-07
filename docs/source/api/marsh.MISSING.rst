``marsh.MISSING``
=================

This value is treated as the unset value by :mod:`marsh`
(not to be confused with :data:`None` which may be a valid
value).

This can be useful when a default value is required by python
even though the programmer wants the value to be required (missing).

.. code-block:: python

    import dataclasses
    import marsh

    @dataclasses.dataclass
    class Config:
        a: int = 3

    @dataclasses.dataclass
    class ExpandedConfig(Config):
        b: str


The code above will fail to run, throwing
``TypeError: non-default argument 'b' follows default argument``

Instead we can use :attr:`marsh.MISSING`

.. code-block:: python

    ...

    @dataclasses.dataclass
    class ExpandedConfig(Config):
        b: str  = marsh.MISSING


Trying to unmarshal this code we get the correct behavior

.. code-block:: python

    ...

    # fails with marsh.errors.MissingValueError
    marsh.unmarshal(ExpandedConfig, {'a': 2})


.. note::

    Using :attr:`marsh.MISSING` as input when unmarshaling
    is sometimes allowed. For example, :data:`None` accepts
    :attr:`marsh.MISSING`. Mappings and sequences
    will also default to an empty instance when the input
    is :attr:`marsh.MISSING`.


The value of :attr:`marsh.MISSING` is the same as
:attr:`omegaconf.MISSING`, represented by the string
``'???'``.
