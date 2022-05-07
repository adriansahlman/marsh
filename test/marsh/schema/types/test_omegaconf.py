from typing import (
    Any,
    Optional,
    Type,
)

import omegaconf
import pytest

import marsh.testing


@pytest.mark.parametrize(
    'value,element',
    (
        (omegaconf.OmegaConf.create([0, 1, 2]), (0, 1, 2)),
        (omegaconf.OmegaConf.create({'a': 0, 'b': 1}), {'a': 0, 'b': 1}),
        (omegaconf.OmegaConf.create({'a': [{'b': 1}]}), {'a': ({'b': 1},)}),
    ),
)
def test_marshal_succeeds(
    value: Any,
    element: marsh.element.ElementType,
) -> None:
    marsh.testing.marshal_succeeds(
        value=value,
        element=element,
    )


@pytest.mark.parametrize(
    'type_,element,value',
    (
        (
            omegaconf.ListConfig,
            (0, 1, 2),
            omegaconf.OmegaConf.create([0, 1, 2]),
        ),
        (
            omegaconf.DictConfig,
            {'a': 0, 'b': 1},
            omegaconf.OmegaConf.create({'a': 0, 'b': 1}),
        ),
        (
            omegaconf.DictConfig,
            {'a': ({'b': 1},)},
            omegaconf.OmegaConf.create({'a': [{'b': 1}]}),
        ),
        (
            omegaconf.ListConfig,
            marsh.MISSING,
            omegaconf.OmegaConf.create([]),
        ),
        (
            omegaconf.DictConfig,
            marsh.MISSING,
            omegaconf.OmegaConf.create({}),
        ),
    ),
)
def test_unmarshal_succeeds(
    type_: Any,
    element: marsh.element.ElementType,
    value: Any,
) -> None:
    marsh.testing.unmarshal_succeeds(
        type_=type_,
        element=element,
        value=value,
    )


@pytest.mark.parametrize(
    'type_,element,exception',
    (
        (omegaconf.ListConfig, 'a', None),
        (omegaconf.ListConfig, {}, None),
        (omegaconf.DictConfig, 'a', None),
        (omegaconf.DictConfig, (), None),
    ),
)
def test_unmarshal_fails(
    type_: Any,
    element: marsh.element.ElementType,
    exception: Optional[Type[Exception]],
) -> None:
    marsh.testing.unmarshal_fails(
        type_=type_,
        element=element,
        exception=exception,
    )
