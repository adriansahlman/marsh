``marsh.element``
=================


.. automodule:: marsh.element


.. py:attribute:: ElementType
    :type: TypeAlias
    :value: Union[None, int, float, bool, str, Sequence[ElementType], Mapping[str, ElementType]]

    A type alias for any element value.


.. py:attribute:: SequenceElementType
    :type: TypeAlias
    :value: Sequence[ElementType]

    A type alias for a sequence element value.


.. py:attribute:: MappingElementType
    :type: TypeAlias
    :value: Mapping[str, ElementType]

    A type alias for a mapping element value.


.. py:attribute:: TerminalElementType
    :type: TypeAlias
    :value: Union[None, int, float, bool, str]

    A type alias for a terminal element value.


.. autofunction:: merge


.. autofunction:: override


.. autofunction:: remove


.. autofunction:: select


.. autofunction:: iterative_select


.. autofunction:: standardize


.. autofunction:: has_missing


.. autofunction:: resolve


.. autoclass:: ElementSelection
