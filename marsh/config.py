"""Tools for reading and writing config files.

Support for new file extensions may be added by registering more config schemas."""
import json
import os
import sys
from typing import (
    ClassVar,
    List,
    Optional,
)

import yaml
import marsh


meta_key: str = os.environ.get('MARSH_META_KEY', '_meta_')
"""This key is used to store any metadata in a config.

The metadata is typically dropped after variable interpolations
have been performed."""


class ConfigSchemaMeta(marsh.schema.core.SchemaMeta['ConfigSchema']):

    def __call__(
        cls,  # noqa: B902
        value,
        *args,
        **kwargs,
    ):
        if not all(os.path.splitext(value)):
            raise ValueError(
                'unable to select config schema, given '
                f'path misses name or extension: {value}',
            )
        if cls is not ConfigSchema:
            return type(object).__call__(cls, value, *args, **kwargs)
        return cls.registry.match(value).build(value, *args, **kwargs)


class ConfigSchema(
    marsh.schema.core.Schema,
    metaclass=ConfigSchemaMeta,
):

    registry: ClassVar[marsh.schema.core.SchemaRegistry['ConfigSchema']] = \
        marsh.schema.core.SchemaRegistry(error=marsh.errors.ConfigFileError)

    @classmethod
    def match(
        cls,
        value: str,
    ) -> bool:
        raise NotImplementedError

    def dump(
        self,
        element: marsh.element.ElementType,
    ) -> None:
        encoded = self.dumps(element)
        with open(self.value, 'w') as fp:
            fp.write(encoded)

    def load(
        self,
    ) -> marsh.element.ElementType:
        with open(self.value, 'r') as fp:
            encoded = fp.read()
        return self.loads(encoded)

    def dumps(
        self,
        element: marsh.element.ElementType,
    ) -> str:
        raise NotImplementedError

    def loads(
        self,
        encoded: str,
    ) -> marsh.element.ElementType:
        raise NotImplementedError


@ConfigSchema.registry.register
class JSONConfigIO(ConfigSchema):

    @classmethod
    def match(
        cls,
        value: str,
    ) -> bool:
        return get_ext(value).lower() == '.json'

    def dump(
        self,
        element: marsh.element.ElementType,
    ) -> None:
        with open(self.value, 'w') as fp:
            json.dump(element, fp)

    def load(
        self,
    ) -> marsh.element.ElementType:
        with open(self.value, 'r') as fp:
            return json.load(fp)

    def dumps(
        self,
        element: marsh.element.ElementType,
    ) -> str:
        return json.dumps(element)

    def loads(
        self,
        encoded: str,
    ) -> marsh.element.ElementType:
        return json.loads(encoded)


@ConfigSchema.registry.register
class YAMLConfigIO(ConfigSchema):

    @classmethod
    def match(
        cls,
        value: str,
    ) -> bool:
        return get_ext(value).lower() in ('.yaml', '.yml')

    def dump(
        self,
        element: marsh.element.ElementType,
    ) -> None:
        with open(self.value, 'w') as fp:
            yaml.safe_dump(element, fp)

    def load(
        self,
    ) -> marsh.element.ElementType:
        with open(self.value, 'r') as fp:
            return yaml.load(fp, Loader=yaml.SafeLoader)

    def dumps(
        self,
        element: marsh.element.ElementType,
    ) -> str:
        return yaml.safe_dump(element)

    def loads(
        self,
        encoded: str,
    ) -> marsh.element.ElementType:
        return yaml.load(encoded, Loader=yaml.SafeLoader)


def has_ext(
    path: str,
) -> bool:
    return bool(os.path.splitext(path)[-1])


def strip_ext(
    path: str,
) -> str:
    if has_ext(path):
        return os.path.splitext(path)[0]
    return path


def get_ext(
    path_or_ext: str,
) -> str:
    a, b = os.path.splitext(path_or_ext)
    return b or a


def find_config(
    target: str,
) -> str:
    if has_ext(target):
        if not os.path.exists(target):
            raise marsh.errors.ConfigFileError(
                f'could not find config {target} ',
            )
        return target
    dpath = os.path.dirname(target)
    if not os.path.isdir(dpath):
        raise marsh.errors.ConfigFileError(
            f'unable to browse directory "{dpath}" '
            f'for named config "{target}"',
        )
    name = os.path.basename(target)
    names = []
    paths = []
    for candidate_fname in os.listdir(dpath):
        path = os.path.join(dpath, candidate_fname)
        if not os.path.isfile(path):
            continue
        if not config_type_is_supported(candidate_fname):
            continue
        candidate_name = strip_ext(candidate_fname)
        if candidate_name == name:
            paths.append(path)
        else:
            names.append(candidate_name)
    if paths:
        if len(paths) > 1:
            raise marsh.errors.ConfigFileError(
                f'ambiguous config "{target}" was resolved '
                'to more than one file: {}'.format(
                    ', '.join(f'"{os.path.basename(path)}"' for path in paths),
                ),
            )
        return paths[0]
    err_msg = (
        'could not find any supported config files in '
        f'directory "{dpath}" with name "{name}"'
    )
    closest = marsh.utils.get_closest(name, names)
    if closest:
        err_msg += f', did you mean "{os.path.join(dpath, closest)}"'
    raise marsh.errors.ConfigFileError(err_msg)


@marsh.utils.cache(maxsize=32, safe=False)
def config_type_is_supported(
    path: str,
) -> bool:
    try:
        ConfigSchema(path)
        return True
    except Exception:
        return False


def tree(
    path: str,
) -> str:
    """Get a tree representation of a directory recursively
    searched for configs.

    Arguments:
        path: The path to a directory.

    Returns:
        A tree representation of all available configs in that directory.
    """
    lines = [f'{os.path.basename(path)}']
    subtrees: List[str] = []
    configs: List[str] = []
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            subtree = tree(os.path.join(path, name))
            if subtree.count('\n') > 1:
                subtrees.append(name)
        else:
            if config_type_is_supported(name):
                configs.append(name)
    for i, config in enumerate(configs):
        prefix = '├── '
        if not subtrees and i == len(configs) - 1:
            prefix = '└── '
        lines.append(f'{prefix}{config}')
    for i, subtree in enumerate(subtrees):
        for j, line in enumerate(subtree.split('\n')):
            if j:
                prefix = '│   '
                if i == len(subtrees) - 1:
                    prefix = '    '
            else:
                prefix = '├── '
                if i == len(subtrees) - 1:
                    prefix = '└── '
            lines.append(f'{prefix}{line}')
    return '\n'.join(lines)


def load(
    name: str,
    *names: str,
    root: Optional[str] = None,
    resolve: bool = True,
    keep_meta: bool = False,
    concatenate: bool = False,
) -> marsh.element.ElementType:
    """Load one or more config files.

    When more than one config is loaded their
    contents are merged and the values of the
    succeeding config takes priority for fields
    where a merge can not be performed.

    File extensions may be omitted.

    Arguments:
        name: Name of a config file.
        *names: Any additional config files.
        root: A root working directory for the
            config files. Defaults to the current
            working directory.
        resolve: Resolve omegaconf interpolations.
        keep_meta: Keep meta field if it exists.
        concatenate: Concatenate sequences when
            multiple configs are loaded and merged
            instead of replacing the previous value.

    Returns:
        The loaded config.
    """
    configs = []
    for name in (name,) + names:
        if root and not name.startswith('/'):
            name = os.path.join(root, name)
        path = find_config(name)
        configs.append(ConfigSchema(path).load())
    config = marsh.element.merge(*configs, concatenate=concatenate)
    if (
        resolve
        and (
            marsh.utils.is_sequence(config)
            or marsh.utils.is_mapping(config)
        )
    ):
        config = marsh.element.resolve(config)
    if not keep_meta:
        config = drop_meta(config)
    return config


def write(
    config: marsh.element.ElementType,
    path: str = '-',
) -> None:
    """Write a config to a file.

    By default the config is written to
    stdout in YAML format.

    Arguments:
        config: The config to write.
        path: A filepath to write to.
            If not specified, stdout is used.
    """
    if path == '-':
        yaml.dump(config, sys.stdout)
    else:
        ConfigSchema(path).dump(config)


def drop_meta(
    config: marsh.element.ElementType,
) -> marsh.element.ElementType:
    """Drop the meta key with all its values if present.

    Arguments:
        config: Config to drop meta data from.

    Returns:
        Input config without meta data.
    """
    if (
        marsh.utils.is_mapping(config)
        and meta_key in config
    ):
        config = dict(config)
        del config[meta_key]
    return config
