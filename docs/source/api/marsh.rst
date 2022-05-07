``marsh``
=========

.. automodule:: marsh


.. autofunction:: marshal


.. autofunction:: unmarshal


.. autofunction:: cast


.. autofunction:: unmarshal_args


.. autofunction:: cast_args


.. autofunction:: main(fn, *, **kwargs)


.. py:attribute:: MISSING

    Represents the missing value, i.e. when a value
    is unset (which is not equivalent to a value being :data:`None`).

    Useful for when a default value is required by python even
    though there should not be one. ``marsh`` treats this the
    same as if there were no default value.

    The concrete value of ``MISSING`` is the string ``'???'``.

    See :doc:`marsh.MISSING` for more info.


.. py:attribute:: namespaces
    :type: marsh.schema.namespace.Namespaces

    Gives access to all namespaces. Also allows for new
    namespaces to be created through its ``new(...)`` method.


.. py:attribute:: __version__
    :type: str

    The current version of ``marsh``.
