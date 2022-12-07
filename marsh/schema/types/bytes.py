from typing import Any

import marsh


@marsh.schema.register
class BytesMarshalSchema(marsh.schema.MarshalSchema):
    """Marshals into URL-safe base64 encodings from bytes."""

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return isinstance(value, bytes)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`bytes`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Marshals bytes into a URL-safe '
            'base64-encoded string.'
        )

    def marshal(
        self,
    ) -> str:
        return marsh.utils.bytes_to_base64(self.value)


@marsh.schema.register
class BytesUnmarshalSchema(marsh.schema.UnmarshalSchema[bytes]):

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return issubclass(value, bytes)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':class:`bytes`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'A valid (optionally URL-safe) base64-encoded '
            'string is expected as input.'
        )

    def doc_type(
        self,
    ) -> str:
        return 'bytes'

    def doc_field_type(
        self,
    ) -> str:
        return '<bytes>'

    def doc_description(
        self,
    ) -> str:
        return self.doc_static_description()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> bytes:
        if marsh.utils.is_missing(element):
            if self.has_default():
                return self.get_default()
            raise marsh.errors.MissingValueError(
                type=self.value,
            )
        if not marsh.utils.is_primitive(element):
            raise marsh.errors.UnmarshalError(
                (
                    f'expected a primitive value, got: '
                    f'{marsh.utils.get_type_name(element)}'
                ),
                element=element,
                type=self.value,
            )
        try:
            return marsh.utils.base64_to_bytes(str(element))
        except Exception:
            raise marsh.errors.UnmarshalError(
                'failed to unmarshal bytes',
                element=element,
                type=self.value,
            )
