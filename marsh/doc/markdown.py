from . import common


def format_types(
    source: common.RegisteredSchemasType,
    heading: int = 3,
) -> str:
    """Return a markdown-formatted string containing
    registered schema types that have static documention.

    A description below each type is included when available.

    Arguments:
        source: The source of the schemas.
        heading: The heading number used for each types.

    Returns:
        The formatted markdown.
    """
    assert heading >= 1, '`heading` must be a positive integer'
    sections = []
    type_prefix = heading * '#' + ' '
    for schema in common.get_registered_schemas(source):
        type_ = schema.doc_static_type()
        if not type_:
            continue
        sections.append(
            f'{type_prefix}{type_}\n'
            f'{schema.doc_static_description() or ""}',
        )
    return '\n\n'.join(sections)
