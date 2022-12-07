"""Root of the marsh framework.

Exposes the basic functionality and modules of the framework."""
from omegaconf import MISSING
from . import errors
from . import utils
from . import element
from . import path
from . import schema
from . import config
from . import annotation
from ._functional import (
    marshal,
    unmarshal,
    unmarshal_args,
    cast,
    cast_args,
    main,
)

# import module containing baseline type schemas
# which are then registered and available in the framework
# for marshaling and unmarshaling.
import marsh.schema.types  # noqa: F401


__version__ = '0.2.4'


# singleton class, create a reference for easy access
namespaces = schema.namespace.Namespaces()
"""Allows access to any registered namespace."""


__all__ = (
    'MISSING',
    'errors',
    'utils',
    'element',
    'path',
    'shema',
    'config',
    'marshal',
    'unmarshal',
    'unmarshal_args',
    'cast',
    'cast_args',
    'main',
    '__version__',
    'namespaces',
    'annotation',
)
