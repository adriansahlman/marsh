import pytest
import marsh
import marsh.parse


@pytest.mark.parametrize(
    'text,element',
    (
        ('0', 0),
        ('1e-4', 1e-4),
        ('null', None),
        ('true', True),
        ('false', False),
        ('', ''),
        ('""', ''),
        ('\\"\\"', '""'),
        ('[]', []),
        ('{}', {}),
        (
            '{a: 1e-5, 0: true, 1.5: [0, "", 3\\,]}',
            {'a': 1e-5, '0': True, '1.5': (0, '', '3,')},
        ),
        ('(a:b)', ('a:b',)),
        (')', ')'),
        (']', ']'),
        ('}', '}'),
        ('{a:[}]}', {'a': ['}']}),
    ),
)
def test_element_suceeds(
    text: str,
    element: marsh.element.ElementType,
) -> None:
    parsed = marsh.element.standardize(marsh.parse.element(text))
    assert parsed == marsh.element.standardize(element)


@pytest.mark.parametrize(
    'text',
    (
        '"\\"',
        "(]",
        '{a,b}',
        '(',
        '[',
        '{',
    ),
)
def test_element_fails(
    text: str,
) -> None:
    with pytest.raises(Exception):
        marsh.parse.element(text)


@pytest.mark.parametrize(
    'text,result',
    (
        ('0@0', marsh.parse.SetConfig(combine=False, path='0', names=('0',))),
        ('0@0,0', marsh.parse.SetConfig(combine=False, path='0', names=('0', '0'))),
        ('a.b@0,0', marsh.parse.SetConfig(combine=False, path='a.b', names=('0', '0'))),
        ('@0', marsh.parse.SetConfig(combine=False, path='', names=('0',))),
        ('0+@0', marsh.parse.SetConfig(combine=True, path='0', names=('0',))),
        ('0+@0,0', marsh.parse.SetConfig(combine=True, path='0', names=('0', '0'))),
        ('a.b+@0,0', marsh.parse.SetConfig(combine=True, path='a.b', names=('0', '0'))),
        ('+@0', marsh.parse.SetConfig(combine=True, path='', names=('0',))),
        ('a=0', marsh.parse.SetValue(path='a', value=0, combine=False)),
        ('=0', marsh.parse.SetValue(path='', value=0, combine=False)),
        ('=', marsh.parse.SetValue(path='', value='', combine=False)),
        ('a=""', marsh.parse.SetValue(path='a', value='', combine=False)),
        ('a=\'\'', marsh.parse.SetValue(path='a', value='', combine=False)),
        ('a+=[]', marsh.parse.SetValue(path='a', value=(), combine=True)),
        ('+=[]', marsh.parse.SetValue(path='', value=(), combine=True)),
        ('a=\'\'', marsh.parse.SetValue(path='a', value='', combine=False)),
        ('\\+=[]', marsh.parse.SetValue(path='+', value=(), combine=False)),
        (
            'a={a: 1e-5, 0: true, 1.5: [0, "", 3\\,]}',
            marsh.parse.SetValue(
                path='a',
                value={'a': 1e-5, '0': True, '1.5': (0, '', '3,')},
                combine=False,
            ),
        ),
    ),
)
def test_override_suceeds(
    text: str,
    result: marsh.parse.Override,
) -> None:
    parsed = marsh.parse.override(text)
    if isinstance(parsed, marsh.parse.SetValue):
        parsed.value = marsh.element.standardize(parsed.value)
    if isinstance(result, marsh.parse.SetValue):
        result.value = marsh.element.standardize(result.value)
    if isinstance(parsed, marsh.parse.SetConfig):
        parsed.names = marsh.element.standardize(parsed.names)  # type: ignore
    if isinstance(result, marsh.parse.SetConfig):
        result.names = marsh.element.standardize(result.names)  # type: ignore
    assert parsed == result


@pytest.mark.parametrize(
    'text',
    (
        '',
        '0',
        'a',
        '(0, 1)',
        '{a: 0}',
        '+0=0',
    ),
)
def test_override_fails(
    text: str,
) -> None:
    with pytest.raises(marsh.parse.ParseError):
        marsh.parse.override(text)
