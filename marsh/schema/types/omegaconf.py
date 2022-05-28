from typing import (
    Any,
    Union,
    cast,
)

import omegaconf

import marsh


@marsh.schema.register
class OmegaconfMarshalSchema(marsh.schema.MarshalSchema):

    value: Union[omegaconf.DictConfig, omegaconf.ListConfig]

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, (omegaconf.DictConfig, omegaconf.ListConfig))
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`~omegaconf.DictConfig`, :class:`~omegaconf.ListConfig`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals an omegaconf :class:`~omegaconf.DictConfig` '
            'or :class:`~omegaconf.ListConfig`, converting '
            'all enums in the container to strings.'
        )

    def marshal(
        self,
    ) -> marsh.element.ElementType:
        return cast(
            marsh.element.ElementType,
            omegaconf.OmegaConf.to_container(
                self.value,
                enum_to_str=True,
            ),
        )
