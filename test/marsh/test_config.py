import os
from typing import Sequence

import pytest
import yaml

import marsh


@pytest.fixture(scope='function')
def config_dir(
    tmp_path,
) -> str:
    dpath = str(tmp_path.absolute())

    def dump(
        path,
        value,
    ) -> None:
        with open(os.path.join(dpath, path), 'w') as fp:
            yaml.dump(value, fp)

    os.makedirs(os.path.join(dpath, 'a'))
    os.makedirs(os.path.join(dpath, 'a', 'b'))
    os.makedirs(os.path.join(dpath, 'a', 'c'))

    dump('config1.yaml', dict(a=0))
    dump('a/config1.yaml', dict(b=1, c=dict(d=2)))
    dump('a/config2.yaml', dict(b=3, c=dict(d=4)))
    dump('a/b/config1.yaml', dict(c=dict(d=5)))
    dump('a/b/config2.yaml', dict(c=dict(e=6)))
    dump('a/c/config1.yaml', dict(c=dict(d=7)))
    dump('a/c/config2.yaml', dict(c=dict(e=8)))

    return dpath


@pytest.mark.parametrize(
    'name,expected',
    (
        ('config1', dict(a=0)),
    ),
)
@pytest.mark.parametrize('with_root', (True, False))
@pytest.mark.parametrize('with_ext', (True, False))
def test_load_single(
    config_dir: str,
    name: str,
    expected: marsh.element.ElementType,
    with_root: bool,
    with_ext: bool,
) -> None:
    name = 'config1'
    root = None
    if with_root:
        root = config_dir
    else:
        name = os.path.join(config_dir, name)
    if with_ext:
        name = name + '.yaml'
    cfg = marsh.config.load(name, root=root)
    expected = dict(a=0)
    assert marsh.element.standardize(cfg) == marsh.element.standardize(expected)


@pytest.mark.parametrize(
    'names,expected',
    (
        (('config1',), dict(a=0)),
        (('config1', 'a/config1'), dict(a=0, b=1, c=dict(d=2))),
        (('config1', 'a/config1', 'a/config2'), dict(a=0, b=3, c=dict(d=4))),
        (('config1', 'a/config2', 'a/config1'), dict(a=0, b=1, c=dict(d=2))),
        (('config1', 'a/b/config1', 'a/config1'), dict(a=0, b=1, c=dict(d=2))),
    ),
)
@pytest.mark.parametrize('with_root', (True, False))
@pytest.mark.parametrize('with_ext', (True, False))
def test_load(
    config_dir: str,
    names: Sequence[str],
    expected: marsh.element.ElementType,
    with_root: bool,
    with_ext: bool,
) -> None:
    root = None
    if with_root:
        root = config_dir
    else:
        names = tuple(os.path.join(config_dir, name) for name in names)
    if with_ext:
        names = tuple(name + '.yaml' for name in names)
    cfg = marsh.config.load(*names, root=root)
    assert marsh.element.standardize(cfg) == marsh.element.standardize(expected)
