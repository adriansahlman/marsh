"""Tools for working with the raw JSON-like data.

This type of data is refered to as `element` in
the marsh framework. It is what is produced when
marshaling a python value and it is given as
input when unmarshaling a python type."""
from typing import (
    Any,
    Iterator,
    Mapping,
    NamedTuple,
    Sequence,
    Type,
    Union,
)

import omegaconf

import marsh


TerminalElementType = Union[
    None,
    int,
    float,
    bool,
    str,
]


SequenceElementType = Sequence['ElementType']


MappingElementType = Mapping[str, 'ElementType']


# Recursive types are not supported by python.
# The true definition would be
# ElementType = Union[TerminalElementType, SequenceElementType, MappingElementType]
ElementType = Union[
    TerminalElementType,
    Sequence[Any],
    Mapping[str, Any],
]


class ElementSelection(NamedTuple):
    element: ElementType
    path: str
    remaining_path: str


def iterative_select(
    element: ElementType,
    path: str,
) -> Iterator[ElementSelection]:
    """Iterate through all elements in a specified path.

    At each step in the path a selection is yielded containing
    the current element, the path traversed and the remaining
    untraversed path.

    Arguments:
        element: The input element to yield subelements from
            based on the specified path.
        path: The path to traverse.

    Returns:
        Selection iterator.
    """
    yield ElementSelection(
        element=element,
        path='',
        remaining_path=path,
    )
    if not path:
        return
    field, remaining_path = marsh.path.head(path)
    if marsh.utils.is_mapping(element):
        if field not in element:
            raise marsh.errors.PathError(field)
        selections = iterative_select(
            element=element[field],
            path=remaining_path,
        )
    elif marsh.utils.is_sequence(element):
        try:
            index = int(field)
            if index < 0:
                index += len(element)
            if not (0 <= index < len(element)):
                raise IndexError
        except Exception:
            raise marsh.errors.PathError(
                'invalid index for sequence of '
                f'length {len(element)}: {field}',
            ) from None
        selections = iterative_select(
            element=element[index],
            path=remaining_path,
        )
    else:
        raise marsh.errors.PathError(
            'can not traverse the path '
            f'"{path}" for the element',
        )
    with marsh.errors.prepend(field):
        for selection in selections:
            yield selection._replace(
                path=marsh.path.prepend(
                    field=field,
                    path=selection.path,
                ),
            )


def select(
    element: ElementType,
    path: str,
) -> ElementType:
    """Retrieve the value for a specific path in an element.

    Arguments:
        element: The input element to retrieve a value from.
        path: The path to retrieve the value from.

    Returns:
        Value for the specified path.
    """
    return tuple(iterative_select(element=element, path=path))[-1].element


def _merge(
    element_a: ElementType,
    element_b: ElementType,
    *,
    concatenate: bool = False,
) -> ElementType:
    if (
        marsh.utils.is_mapping(element_a)
        and marsh.utils.is_mapping(element_b)
    ):
        return {
            key: _merge(
                element_a.get(key, marsh.MISSING),
                element_b.get(key, marsh.MISSING),
                concatenate=concatenate,
            )
            for key in set(element_a).union(element_b)
        }
    elif (
        concatenate
        and marsh.utils.is_sequence(element_a)
        and marsh.utils.is_sequence(element_b)
    ):
        return tuple(element_a) + tuple(element_b)
    elif marsh.utils.is_missing(element_b):
        return element_a
    return element_b


def merge(
    element: ElementType,
    *elements: ElementType,
    concatenate: bool = False,
) -> ElementType:
    """Combine two or more elements.

    Maps are combined recursively. All other
    types of values are replaced
    with the last element in the merge (with an exception
    for sequences if ``concatenate`` is ``True``).
    The final element in the inputs will be given the highest priority
    in the merge, i.e. if it contains a value for a specific path that
    exists in other elements in the input its value will be the one that
    exists in the final merged element (output).

    Arguments:
        element: The first element.
        elements: Remaining elements to merge into the first element.
        concatenate: Concatenate sequences with eachother when merging instead
            of replacing the old sequence with the new sequence.

    Returns:
        A new element which is the combination of all input elements.
    """
    for elem in elements:
        element = _merge(
            element,
            elem,
            concatenate=concatenate,
        )
    return element


def override(
    element: ElementType,
    value: ElementType,
    path: str,
    combine: bool = False,
) -> ElementType:
    """Set the value of a specific path in an element.

    If the path is already occupied by a value, it will be replaced.
    A copy of the input element is returned with the value set for the
    specified path.

    Arguments:
        element: The input element.
        value: The value to set for the path.
        path: The path for the new value.
        combine: If a previous value exists for the path, attempt
            to merge it with the new value. This only applies
            when both values are maps or sequences. For maps,
            the new element takes precedence when a key exists
            in both values. For sequences, the old value is concatenated
            with the new value (`old + new`).

    Returns:
        A copy of the element with a new value set for the specified path.
    """
    if not path:
        if combine:
            if (
                marsh.utils.is_mapping(element)
                and marsh.utils.is_mapping(value)
            ):
                return {
                    **element,
                    **value,
                }
            elif (
                marsh.utils.is_sequence(element)
                and marsh.utils.is_sequence(value)
            ):
                return tuple(element) + tuple(value)
        return value
    field, remaining_path = marsh.path.head(path)
    if marsh.utils.is_missing(element):
        element = {}
    if marsh.utils.is_mapping(element):
        element = dict(element)
        with marsh.errors.prepend(field):
            element[field] = override(
                element=element.get(field, {}),
                value=value,
                path=remaining_path,
            )
    elif marsh.utils.is_sequence(element):
        try:
            index = int(field)
            if index < 0:
                index += len(element)
            if not (0 <= index <= len(element)):
                raise IndexError
        except Exception:
            raise marsh.errors.PathError(
                'invalid index for sequence of '
                f'length {len(element)}: {field}',
            ) from None
        element = list(element)
        if index == len(element):
            element.append({})
        with marsh.errors.prepend(field):
            element[index] = override(
                element=element[index],
                value=value,
                path=remaining_path,
            )
        element = tuple(element)
    else:
        raise marsh.errors.PathError(
            'can not traverse the path '
            f'"{path}" for the element',
        )
    return element


def remove(
    element: Union[SequenceElementType, MappingElementType],
    path: str,
) -> ElementType:
    """Remove a subelement in the input specified by a path.

    A copy of the input element is returned with the final
    subelement referenced by the path removed.

    Arguments:
        element: The element containing a value to be removed.

    Returns:
        A copy of the element with the value for the specified path removed.
    """
    if not path:
        raise ValueError('no path specified')
    field, remaining_path = marsh.path.head(path)
    if marsh.utils.is_mapping(element):
        if field not in element:
            raise marsh.errors.PathError(field)
        element = dict(element)
        if not remaining_path:
            del element[field]
        else:
            value = element[field]
            if not (
                marsh.utils.is_mapping(value)
                or marsh.utils.is_sequence(value)
            ):
                raise marsh.errors.PathError(
                    'terminal element encountered, can '
                    f'not traverse the remaining path: "{remaining_path}"',
                    path=field,
                )
            with marsh.errors.prepend(field):
                element[field] = remove(
                    element=value,
                    path=remaining_path,
                )
    elif marsh.utils.is_sequence(element):
        try:
            index = int(field)
            if index < 0:
                index += len(element)
            if not (0 <= index < len(element)):
                raise IndexError(field)
        except Exception:
            raise marsh.errors.PathError(
                'invalid index for sequence of '
                f'length {len(element)}: {field}',
            ) from None
        element = list(element)
        if not remaining_path:
            del element[index]
        else:
            value = element[index]
            if not (
                marsh.utils.is_mapping(value)
                or marsh.utils.is_sequence(value)
            ):
                raise marsh.errors.PathError(
                    'terminal element encountered, can '
                    f'not traverse the remaining path: "{remaining_path}"',
                    path=field,
                )
            with marsh.errors.prepend(field):
                element[index] = remove(
                    element=value,
                    path=remaining_path,
                )
        element = tuple(element)
    else:
        raise ValueError(
            f'expected a sequence or mapping element, got {type(element)}',
        )
    return element


def standardize(
    element: ElementType,
    *,
    mapping_type: Type[Mapping] = dict,
    sequence_type: Type[Sequence] = tuple,
) -> ElementType:
    """Standardize the sequence/mapping types through an entire element.

    Copy the element and replace all sequences with the specified
    sequence type and all mappings with the specified mapping type recursively.

    Arguments:
        element: The element to standardize sequence and mapping types for.
        sequence_type: The type to use for sequences.
        mapping_type: The type to use for mappings.

    Returns:
        The standardized element.
    """
    if marsh.utils.is_mapping(element):
        element = {
            key: standardize(
                element[key],
                mapping_type=mapping_type,
                sequence_type=sequence_type,
            )
            for key in element
        }
        if mapping_type is not dict:
            element = mapping_type(element)  # type: ignore
    elif marsh.utils.is_sequence(element):
        element = sequence_type(  # type: ignore
            standardize(item, mapping_type=mapping_type, sequence_type=sequence_type)
            for item in element
        )
    return element


def has_missing(
    element: ElementType,
) -> bool:
    """Recursively look for missing values in an element.

    Returns ``True`` if the element is missing or contains any missing values,
    otherwise ``False`` is returned.
    A missing value is represented by ``marsh.MISSING`` or ``dataclasses.MISSING``.

    Arguments:
        element: Element to check for missing values in.

    Returns:
        Boolean representing if the element is missing or contains missing values.
    """
    if marsh.utils.is_missing(element):
        return True
    elif marsh.utils.is_mapping(element):
        return any(map(has_missing, element)) or any(map(has_missing, element.values()))
    elif marsh.utils.is_sequence(element):
        return any(map(has_missing, element))
    return False


def resolve(
    element: ElementType,
) -> ElementType:
    """Resolve any variable interpolation using omegaconf resolvers.

    Arguments:
        element: The element to resolve any variable interpolations for.

    Returns:
        The element with variable interpolations performed.
    """
    if element is None or marsh.utils.is_primitive(element):
        return element
    try:
        return omegaconf.OmegaConf.to_container(  # type: ignore
            omegaconf.OmegaConf.create(
                standardize(element),  # type: ignore
            ),
            resolve=True,
            enum_to_str=True,
        )
    except omegaconf.errors.OmegaConfBaseException:
        raise
    except Exception as err:
        raise marsh.errors.MarshError(
            f'failed to resolve element: {err}',
        )
