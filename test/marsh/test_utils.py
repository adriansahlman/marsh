import collections.abc
import dataclasses
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Sequence,
    Tuple,
)

import pytest
import omegaconf

import marsh


BaseNamedTuple = collections.namedtuple('BaseNamedTuple', ['a'], defaults=(0,))


class TypingNamedTuple(NamedTuple):
    a: int = 0


@pytest.mark.parametrize(
    'value,is_missing',
    (
        (0, False),
        (1, False),
        (-1, False),
        ('0', False),
        ('', False),
        (None, False),
        (False, False),
        (True, False),
        ([0], False),
        ([], False),
        ({0: 0}, False),
        ({}, False),
        (object, False),
        (object(), False),
        (marsh.MISSING, True),
        (dataclasses.MISSING, True),
    ),
)
def test_is_missing(
    value: Any,
    is_missing: bool,
) -> None:
    assert marsh.utils.is_missing(value) == is_missing


@pytest.mark.parametrize(
    'value,is_primitive',
    (
        (0, True),
        (0.1, True),
        ('0', True),
        ('', True),
        (False, True),
        (True, True),
        (b'', False),
        ([0], False),
        ([], False),
        ({0: 0}, False),
        ({}, False),
        (object, False),
        (object(), False),
    ),
)
def test_is_primitive(
    value: Any,
    is_primitive: bool,
) -> None:
    assert marsh.utils.is_primitive(value) == is_primitive


@pytest.mark.parametrize(
    'value,type_',
    (
        (0, int),
        (int, int),
        (0.1, float),
        (float, float),
        (False, bool),
        (bool, bool),
        ([0], list),
        ([], list),
        (list, list),
        ({0: 0}, dict),
        ({}, dict),
        (dict, dict),
        (object, object),
        (object(), object),
        (Dict[str, int], dict),
        (List[int], list),
        (Mapping[str, str], collections.abc.Mapping),
        (Sequence[int], collections.abc.Sequence),
        (Tuple[int, ...], tuple),
        (Tuple[int, str], tuple),
    ),
)
def test_get_type(
    value: Any,
    type_: Any,
) -> None:
    assert marsh.utils.get_type(value) == type_


@pytest.mark.parametrize(
    'value,is_mapping',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], False),
        (set(), False),
        (dict, False),
        ({}, True),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), True),
        (Dict, False),
        (Dict[int, int], False),
        (Mapping, False),
        (Mapping[int, int], False),
        (BaseNamedTuple, False),
        (BaseNamedTuple(), False),
        (TypingNamedTuple, False),
        (TypingNamedTuple(), False),
    ),
)
def test_is_mapping(
    value: Any,
    is_mapping: bool,
) -> None:
    assert marsh.utils.is_mapping(value) == is_mapping


@pytest.mark.parametrize(
    'value,is_mapping_type',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], False),
        (set(), False),
        (dict, True),
        ({}, False),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, True),
        (omegaconf.DictConfig({}), False),
        (Dict, True),
        (Dict[int, int], True),
        (Mapping, True),
        (Mapping[int, int], True),
        (BaseNamedTuple, False),
        (BaseNamedTuple(), False),
        (TypingNamedTuple, False),
        (TypingNamedTuple(), False),
    ),
)
def test_is_mapping_type(
    value: Any,
    is_mapping_type: bool,
) -> None:
    assert marsh.utils.is_mapping_type(value) == is_mapping_type


@pytest.mark.parametrize(
    'value,is_sequence',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], True),
        (tuple, False),
        ((), True),
        (set(), False),
        (dict, False),
        ({}, False),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), True),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), False),
        (List, False),
        (List[int], False),
        (Tuple, False),
        (Tuple[int, ...], False),
        (Tuple[int, str], False),
        (Sequence, False),
        (Sequence[int], False),
        (BaseNamedTuple, False),
        (BaseNamedTuple(), True),
        (TypingNamedTuple, False),
        (TypingNamedTuple(), True),
    ),
)
def test_is_sequence(
    value: Any,
    is_sequence: bool,
) -> None:
    assert marsh.utils.is_sequence(value) == is_sequence


@pytest.mark.parametrize(
    'value,is_sequence_type',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, True),
        ([], False),
        (tuple, True),
        ((), False),
        (set(), False),
        (dict, False),
        ({}, False),
        (omegaconf.ListConfig, True),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), False),
        (List, True),
        (List[int], True),
        (Tuple, True),
        (Tuple[int, ...], True),
        (Tuple[int, str], True),
        (Sequence, True),
        (Sequence[int], True),
        (BaseNamedTuple, True),
        (BaseNamedTuple(), False),
        (TypingNamedTuple, True),
        (TypingNamedTuple(), False),
    ),
)
def test_is_sequence_type(
    value: Any,
    is_sequence_type: bool,
) -> None:
    assert marsh.utils.is_sequence_type(value) == is_sequence_type


@pytest.mark.parametrize(
    'value,is_namedtuple',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], False),
        (tuple, False),
        ((), False),
        (set(), False),
        (dict, False),
        ({}, False),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), False),
        (List, False),
        (List[int], False),
        (Tuple, False),
        (Tuple[int, ...], False),
        (Tuple[int, str], False),
        (Sequence, False),
        (Sequence[int], False),
        (BaseNamedTuple, False),
        (BaseNamedTuple(), True),
        (TypingNamedTuple, False),
        (TypingNamedTuple(), True),
    ),
)
def test_is_namedtuple(
    value: Any,
    is_namedtuple: bool,
) -> None:
    assert marsh.utils.is_namedtuple(value) == is_namedtuple


@pytest.mark.parametrize(
    'value,is_namedtuple_type',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], False),
        (tuple, False),
        ((), False),
        (set(), False),
        (dict, False),
        ({}, False),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), False),
        (List, False),
        (List[int], False),
        (Tuple, False),
        (Tuple[int, ...], False),
        (Tuple[int, str], False),
        (Sequence, False),
        (Sequence[int], False),
        (BaseNamedTuple, True),
        (BaseNamedTuple(), False),
        (TypingNamedTuple, True),
        (TypingNamedTuple(), False),
    ),
)
def test_is_namedtuple_type(
    value: Any,
    is_namedtuple_type: bool,
) -> None:
    assert marsh.utils.is_namedtuple_type(value) == is_namedtuple_type


@pytest.mark.parametrize(
    'value,is_typed_namedtuple',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], False),
        (tuple, False),
        ((), False),
        (set(), False),
        (dict, False),
        ({}, False),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), False),
        (List, False),
        (List[int], False),
        (Tuple, False),
        (Tuple[int, ...], False),
        (Tuple[int, str], False),
        (Sequence, False),
        (Sequence[int], False),
        (BaseNamedTuple, False),
        (BaseNamedTuple(), False),
        (TypingNamedTuple, False),
        (TypingNamedTuple(), True),
    ),
)
def test_is_typed_namedtuple(
    value: Any,
    is_typed_namedtuple: bool,
) -> None:
    assert marsh.utils.is_typed_namedtuple(value) == is_typed_namedtuple


@pytest.mark.parametrize(
    'value,is_typed_namedtuple_type',
    (
        (0, False),
        (str, False),
        ('', False),
        (list, False),
        ([], False),
        (tuple, False),
        ((), False),
        (set(), False),
        (dict, False),
        ({}, False),
        (omegaconf.ListConfig, False),
        (omegaconf.ListConfig([]), False),
        (omegaconf.DictConfig, False),
        (omegaconf.DictConfig({}), False),
        (List, False),
        (List[int], False),
        (Tuple, False),
        (Tuple[int, ...], False),
        (Tuple[int, str], False),
        (Sequence, False),
        (Sequence[int], False),
        (BaseNamedTuple, False),
        (BaseNamedTuple(), False),
        (TypingNamedTuple, True),
        (TypingNamedTuple(), False),
    ),
)
def test_is_typed_namedtuple_type(
    value: Any,
    is_typed_namedtuple_type: bool,
) -> None:
    assert marsh.utils.is_typed_namedtuple_type(value) == is_typed_namedtuple_type


class DescrInMainDocstring:
    """Initial docstring

    Arguments:
        a: the description
    """

    a: int


class DescrInSeparateDocstring:
    """Initial docstring"""

    a: int
    """the description"""


class DummyDocstringClass:
    """Used for cluttering.

    Arguments:
        b: first unused description
    """

    b: int

    c: int
    """second unused description"""


class DescrInMainDocstringInherited(
    DummyDocstringClass,
    DescrInMainDocstring,
):
    pass


class DescrInSeparateDocstringInherited(
    DummyDocstringClass,
    DescrInSeparateDocstring,
):
    pass


class MultilineSeparateDocstring:
    """Some docstring"""

    a: int
    """multiline
    docstring
    of
    attribute"""


@pytest.mark.parametrize(
    'cls,descr',
    (
        (DescrInMainDocstring, 'the description'),
        (DescrInSeparateDocstring, 'the description'),
        (DescrInMainDocstringInherited, 'the description'),
        (DescrInSeparateDocstringInherited, 'the description'),
        (MultilineSeparateDocstring, 'multiline\ndocstring\nof\nattribute'),
    ),
)
def test_get_attribute_description(
    cls,
    descr: str,
) -> None:
    fetched_descr = marsh.utils.get_attribute_description(cls, 'a')
    assert fetched_descr == descr
