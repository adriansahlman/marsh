from typing import (
    Any,
    Mapping,
    Sequence,
    Union,
)

import pytest
import omegaconf

import marsh


@pytest.mark.parametrize(
    'element,has_missing',
    (
        (None, False),
        (0, False),
        ('', False),
        ((), False),
        ({}, False),
        (marsh.MISSING, True),
        ((0, 1, marsh.MISSING), True),
        ({0: 0, 1: 1, 2: marsh.MISSING}, True),
        ({'a': {'b': (0, 1, {'c': marsh.MISSING})}}, True),
        ({'a': {'b': (0, 1, {'c': (0, 1, marsh.MISSING)})}}, True),
    ),
)
def test_has_missing(
    element: Any,
    has_missing: bool,
) -> None:
    assert marsh.element.has_missing(element) == has_missing


def test_select() -> None:
    element: Mapping[str, Any] = {
        'a': 0,
        'b': (
            0,
            (
                0,
                1,
                2,
            ),
            {
                'a': 0,
                'b': 1,
                'c': 2,
            },
        ),
        'c': {
            'a': 0,
            'b': (
                0,
                1,
                2,
            ),
            'c': {
                'a': 0,
                'b': 1,
                'c': 2,
            },
        },
    }
    assert marsh.element.select(element, '') == element

    selections = list(marsh.element.iterative_select(element, 'a'))
    assert len(selections) == 2
    assert selections[0].element == element
    assert selections[0].path == ''
    assert selections[0].remaining_path == 'a'
    assert selections[1].element == element['a']
    assert selections[1].path == 'a'
    assert selections[1].remaining_path == ''

    with pytest.raises(Exception):
        marsh.element.select(element, 'a.b')

    with pytest.raises(Exception):
        marsh.element.select(element, 'a.b.c')

    selections = list(marsh.element.iterative_select(element, 'b'))
    assert len(selections) == 2
    assert selections[0].element == element
    assert selections[0].path == ''
    assert selections[0].remaining_path == 'b'
    assert selections[1].element == element['b']
    assert selections[1].path == 'b'
    assert selections[1].remaining_path == ''

    selections = list(marsh.element.iterative_select(element, 'b.0'))
    assert len(selections) == 3
    assert selections[0].element == element
    assert selections[0].path == ''
    assert selections[0].remaining_path == 'b.0'
    assert selections[1].element == element['b']
    assert selections[1].path == 'b'
    assert selections[1].remaining_path == '0'
    assert selections[2].element == element['b'][0]
    assert selections[2].path == 'b.0'
    assert selections[2].remaining_path == ''

    selections = list(marsh.element.iterative_select(element, 'b.1'))
    assert len(selections) == 3
    assert selections[0].element == element
    assert selections[0].path == ''
    assert selections[0].remaining_path == 'b.1'
    assert selections[1].element == element['b']
    assert selections[1].path == 'b'
    assert selections[1].remaining_path == '1'
    assert selections[2].element == element['b'][1]
    assert selections[2].path == 'b.1'
    assert selections[2].remaining_path == ''

    selections = list(marsh.element.iterative_select(element, 'b.1.0'))
    assert len(selections) == 4
    assert selections[0].element == element
    assert selections[0].path == ''
    assert selections[0].remaining_path == 'b.1.0'
    assert selections[1].element == element['b']
    assert selections[1].path == 'b'
    assert selections[1].remaining_path == '1.0'
    assert selections[2].element == element['b'][1]
    assert selections[2].path == 'b.1'
    assert selections[2].remaining_path == '0'
    assert selections[3].element == element['b'][1][0]
    assert selections[3].path == 'b.1.0'
    assert selections[3].remaining_path == ''

    with pytest.raises(Exception):
        marsh.element.select(element, 'b.2.0')


@pytest.mark.parametrize(
    'element,path,result',
    (
        ({'0': 0}, '0', {}),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a', {}),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.0', {'a': ({'c': ('d',)},)}),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.1', {'a': ({'b': 0},)}),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.0.b', {'a': ({}, {'c': ('d',)})}),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.1.c', {'a': ({'b': 0}, {})}),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.1.c.0', {'a': ({'b': 0}, {'c': ()})}),
    ),
)
def test_remove_succeeds(
    element: Union[marsh.element.SequenceElementType, marsh.element.MappingElementType],
    path: str,
    result: marsh.element.ElementType,
) -> None:
    after_del = marsh.element.standardize(marsh.element.remove(element, path))
    assert after_del == marsh.element.standardize(result)


@pytest.mark.parametrize(
    'element,path',
    (
        (0, ''),
        ((), ''),
        ({}, ''),
        ({}, 'a'),
        ((), '1'),
        (0, 'a'),
        ('abc', 'a'),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.1.c.1'),
    ),
)
def test_remove_fails(
    element: Any,
    path: str,
) -> None:
    with pytest.raises(Exception):
        marsh.element.remove(element, path)


@pytest.mark.parametrize(
    'elements,result,concatenate',
    (
        ((None,), None, False),
        ((None,), None, True),
        ((0, 1, 2), 2, False),
        ((0, 1, 2), 2, True),
        (((0,), (1,), (2,)), (2,), False),
        (((0,), (1,), (2,)), (0, 1, 2), True),
        (({}, {}), {}, False),
        (({}, {}), {}, True),
        (({'a': 0}, {'a': 1}), {'a': 1}, False),
        (({'a': 0}, {'a': 1}), {'a': 1}, True),
        (({'a': 0}, {'b': 1}), {'a': 0, 'b': 1}, False),
        (({'a': 0}, {'b': 1}), {'a': 0, 'b': 1}, True),
        (({'a': (0,), 'b': -1}, {'a': (1, 2), 'b': 0}), {'a': (1, 2), 'b': 0}, False),
        (({'a': (0,), 'b': -1}, {'a': (1, 2), 'b': 0}), {'a': (0, 1, 2), 'b': 0}, True),
        (
            ({'a': {'b': 0}, 0: {1: 2}}, {'a': {'c': 0}, 0: {1: 3}}),
            {'a': {'b': 0, 'c': 0}, 0: {1: 3}},
            False,
        ),
        (
            ({'a': {'b': 0}, 0: {1: 2}}, {'a': {'c': 0}, 0: {1: 3}}),
            {'a': {'b': 0, 'c': 0}, 0: {1: 3}},
            True,
        ),
        ((marsh.MISSING, 'a'), 'a', False),
        ((marsh.MISSING, 'a'), 'a', True),
        (('a', marsh.MISSING), 'a', False),
        (('a', marsh.MISSING), 'a', True),
        ((marsh.MISSING, ()), (), False),
        ((marsh.MISSING, ()), (), True),
        (((), marsh.MISSING), (), False),
        (((), marsh.MISSING), (), True),
        ((marsh.MISSING, {'a': 0}), {'a': 0}, False),
        ((marsh.MISSING, {'a': 0}), {'a': 0}, True),
        (({'a': 0}, marsh.MISSING), {'a': 0}, False),
        (({'a': 0}, marsh.MISSING), {'a': 0}, True),
        ((0, ()), (), False),
        ((0, ()), (), True),
        ((0, {}), {}, False),
        ((0, {}), {}, True),
        (({}, ()), (), False),
        (({}, ()), (), True),
        (((), {}), {}, False),
        (((), {}), {}, True),
    ),
)
def test_merge(
    elements: Sequence[marsh.element.ElementType],
    result: marsh.element.ElementType,
    concatenate: bool,
) -> None:
    merged = marsh.element.standardize(
        marsh.element.merge(
            *elements,
            concatenate=concatenate,
        ),
    )
    assert merged == marsh.element.standardize(result)


@pytest.mark.parametrize(
    'element,path,value,result,combine',
    (
        (0, '', 1, 1, False),
        (0, '', {}, {}, False),
        (0, '', 1, 1, False),
        ({'a': 0}, 'a', 1, {'a': 1}, False),
        ({'a': {'b': 0}}, 'a.b', 1, {'a': {'b': 1}}, False),
        ((0, 1), '2', 3, (0, 1, 3), False),
        ((0, 1), '', (2, 3), (2, 3), False),
        ((0, 1), '', (2, 3), (0, 1, 2, 3), True),
        ({'a': 0}, '', {'b': 1}, {'b': 1}, False),
        ({'a': 0}, '', {'b': 1}, {'a': 0, 'b': 1}, True),
        ({'a': {'b': 0}}, '', {'a': {'c': 0}}, {'a': {'c': 0}}, True),
        ({}, 'a.b', 0, {'a': {'b': 0}}, False),
        (marsh.MISSING, 'a.b.c', (), {'a': {'b': {'c': ()}}}, False),
        ({'a': marsh.MISSING}, 'a.b.c', (), {'a': {'b': {'c': ()}}}, False),
        ({}, 'a.b.c', (), {'a': {'b': {'c': ()}}}, False),
        ({}, 'a.b.c', (), {'a': {'b': {'c': ()}}}, True),
        ({}, 'a.b', 0, {'a': {'b': 0}}, True),
        ({}, 'a.b.c', 0, {'a': {'b': {'c': 0}}}, True),
    ),
)
def test_override_succeeds(
    element: marsh.element.ElementType,
    path: str,
    value: marsh.element.ElementType,
    result: marsh.element.ElementType,
    combine: bool,
) -> None:
    ovr = marsh.element.standardize(
        marsh.element.override(
            element,
            value=value,
            path=path,
            combine=combine,
        ),
    )
    assert ovr == marsh.element.standardize(result)


@pytest.mark.parametrize('combine', (True, False))
@pytest.mark.parametrize(
    'element,path,value',
    (
        ((), '1', None),
        (0, 'a', None),
        ('abc', 'a', None),
        ({'a': ({'b': 0}, {'c': ('d',)})}, 'a.1.c.2', None),
    ),
)
def test_override_fails(
    element: marsh.element.ElementType,
    path: str,
    value: marsh.element.ElementType,
    combine: bool,
) -> None:
    with pytest.raises(marsh.errors.MarshError):
        marsh.element.override(
            element,
            value=value,
            path=path,
            combine=combine,
        )


@pytest.mark.parametrize(
    'element,result',
    (
        ({'a': 0, 'b': '${a}'}, {'a': 0, 'b': 0}),
        ((0, '${0}'), (0, 0)),
        ({'a': {'b': 0}, 'c': '${a.b}'}, {'a': {'b': 0}, 'c': 0}),
    ),
)
def test_resolve_succeeds(
    element: Union[Sequence, Mapping[str, Any]],
    result: Union[Sequence, Mapping[str, Any]],
) -> None:
    resolved = marsh.element.standardize(marsh.element.resolve(element))
    assert resolved == marsh.element.standardize(result)


@pytest.mark.parametrize(
    'element',
    (
        (0, '${1}'),
        (0, '${2}'),
        {'a': 0, 'b': '${c}'},
    ),
)
def test_resolve_fails(
    element: Union[Sequence, Mapping[str, Any]],
) -> None:
    with pytest.raises(
        (
            marsh.errors.MarshError,
            omegaconf.errors.OmegaConfBaseException,
        ),
    ):
        marsh.element.resolve(element)
