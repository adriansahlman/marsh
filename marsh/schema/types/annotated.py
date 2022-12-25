from typing import (
    Any,
    List,
    Mapping,
    Optional,
    Sequence,
    get_args,
)


import marsh


@marsh.schema.register(priority=5)
class AnnotatedUnmarshalSchema(marsh.schema.UnmarshalSchema[Any]):

    schema: marsh.schema.UnmarshalSchema

    def __init__(
        self,
        value: Any,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(value, *args, **kwargs)
        self.schema = marsh.schema.UnmarshalSchema(
            get_args(self.value)[0],
            *args,
            **kwargs,
        )

    @classmethod
    def match(
        cls,
        value: Any,
    ) -> bool:
        try:
            return marsh.utils.is_annotated(value)
        except Exception:
            return False

    @staticmethod
    def doc_static_type() -> str:
        return ':data:`~typing.Annotated`'

    @staticmethod
    def doc_static_description() -> str:
        return (
            'Unwraps and delegates unmarshaling '
            'to the underlying type.'
        )

    def __str__(
        self,
    ) -> str:
        return str(self.schema)

    def __repr__(
        self,
    ) -> str:
        return repr(self.schema)

    def select(
        self,
        path: str,
    ) -> marsh.schema.UnmarshalSchema:
        return self.schema.select(path)

    def doc(
        self,
        depth: int = 0,
    ) -> marsh.schema.UnmarshalSchema.Doc:
        return self.schema.doc(depth)

    def doc_type(
        self,
    ) -> str:
        return self.schema.doc_type()

    def doc_field_type(
        self,
    ) -> str:
        return self.schema.doc_field_type()

    def doc_default(
        self,
    ) -> Optional[str]:
        return self.schema.doc_default()

    def doc_description(
        self,
    ) -> Optional[str]:
        return self.schema.doc_description()

    def doc_fields(
        self,
        depth: int,
    ) -> Optional[Mapping[str, marsh.schema.UnmarshalSchema.Doc.Field]]:
        return self.schema.doc_fields(depth)

    def doc_special_fields(
        self,
    ) -> Optional[Sequence[marsh.schema.UnmarshalSchema.Doc.SpecialField]]:
        return self.schema.doc_special_fields()

    def unmarshal(
        self,
        element: marsh.element.ElementType,
    ) -> Any:
        pre_annotations: List[marsh.annotation.PreAnnotation] = []
        annotations: List[marsh.annotation.Annotation] = []
        for ann in marsh.utils.get_annotations(self.value):
            try:
                if issubclass(
                    ann,
                    (
                        marsh.annotation.Annotation,
                        marsh.annotation.PreAnnotation,
                    ),
                ):
                    ann = ann()
            except TypeError:
                pass
            try:
                if isinstance(
                    ann,
                    marsh.annotation.Annotation,
                ):
                    annotations.append(ann)
                elif isinstance(
                    ann,
                    marsh.annotation.PreAnnotation,
                ):
                    pre_annotations.append(ann)
            except TypeError:
                continue
        for ann in pre_annotations:
            try:
                element = ann(element)
            except marsh.errors.MarshError:
                raise
            except Exception as err:
                raise marsh.errors.UnmarshalError(
                    f'custom pre-annotation {ann.__class__.__name__}'
                    f' failed: {err}',
                ) from err
        value = self.schema.unmarshal(element)
        for ann in annotations:
            try:
                value = ann(value)
            except marsh.errors.MarshError:
                raise
            except Exception as err:
                raise marsh.errors.UnmarshalError(
                    f'custom annotation {ann.__class__.__name__}'
                    f' failed: {err}',
                ) from err
        return value
