from typing import Sequence

import pytest

import marsh


@pytest.mark.parametrize(
    'path,splits,delimiter',
    (
        ('a', ['a'], '.'),
        ('a', ['a'], '/'),
        ('a.b', ['a', 'b'], '.'),
        ('a/b', ['a', 'b'], '/'),
        ('a.b', ['a.b'], '/'),
        ('"a.b"', ['a.b'], '.'),
        ('a\\.b', ['a.b'], '.'),
        ('"a\\.b"', ['a.b'], '.'),
        ('"a\\".b"', ['a".b'], '.'),
    ),
)
def test_split_suceeds(
    path: str,
    splits: Sequence[str],
    delimiter: str,
) -> None:
    assert tuple(marsh.path.split(path, delimiter=delimiter)) == tuple(splits)


@pytest.mark.parametrize(
    'path,delimiter',
    (
        ('"a".b"', '.'),
        ('a.b"', '.'),
        ('a.b\\', '.'),
    ),
)
def test_split_fails(
    path: str,
    delimiter: str,
) -> None:
    with pytest.raises(Exception):
        marsh.path.split(path, delimiter=delimiter)


@pytest.mark.parametrize(
    'path,head,remaining_path,delimiter',
    (
        ('a', 'a', '', '.'),
        ('a', 'a', '', '/'),
        ('a', 'a', '', 'b'),
        ('a.b', 'a', 'b', '.'),
        ('a.b', 'a.b', '', '/'),
        ('a.b.c', 'a', 'b.c', '.'),
        ('a.b.c', 'a.', '.c', 'b'),
        ('..a', 'a', '', '.'),
        ('a..', 'a', '', '.'),
        ('.a', 'a', '', '.'),
        ('a.', 'a', '', '.'),
        ('a.b.', 'a', 'b', '.'),
        ('.a.b', 'a', 'b', '.'),
        ('.a.', 'a', '', '.'),
        ('"a.b".c', 'a.b', 'c', '.'),
        ('"a.b."c', 'a.b.c', '', '.'),
    ),
)
def test_head(
    path: str,
    head: str,
    remaining_path: str,
    delimiter: str,
) -> None:
    _head, _remaining_path = marsh.path.head(path, delimiter=delimiter)
    assert _head == head
    assert _remaining_path == remaining_path
