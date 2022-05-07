import textwrap
from typing import Optional

import marsh
from . import common


def format_terminal_value(
    value: str,
    width: Optional[int] = None,
    description: Optional[str] = None,
    indent: int = 2,
    description_indent: int = 24,
    description_margin: int = 4,
) -> str:
    """Create a help message in the same style as
    :class:`argparse.ArgumentParser` for a value and
    its description

    Arguments:
        value: The string value.
        width: The width of the message.
        description: A text description for the value.
        indent: The indentation of the value
            in number of blank spaces.
        description_indent: The indentation of the
            description in number of blank spaces.
        description_margin: The minimum number of
            blank spaces between the description
            and the value. The description will be
            started on the next line if the resulting
            margin would be smaller than this on the
            line containing the argument.

    Returns:
        The help message.
    """
    if width is None:
        width = marsh.utils.get_terminal_width()
    elif width <= 0:
        raise ValueError('`width` must be a positive integer')
    value = f'{" " * indent}{value}'
    value = '\n'.join(textwrap.wrap(value, width=width))
    if not description:
        return value
    fill_indent = ' ' * description_indent
    fill_init_indent = fill_indent
    value_len = len(value.split('\n')[-1])
    if description_indent - value_len >= description_margin:
        fill_init_indent = fill_indent[value_len:]
    else:
        value = f'{value}\n'
    description = textwrap.fill(
        text=description,
        width=width,
        initial_indent=fill_init_indent,
        subsequent_indent=fill_indent,
    )
    return f'{value}{description}'


def format_unmarshal_fields(
    source: common.UnmarshalDocType,
    prefix_path: str = '',
    width: Optional[int] = None,
    depth: int = 1,
    indent: int = 2,
    depth_indent_factor: int = 2,
    description_indent: int = 24,
    description_margin: int = 4,
) -> str:
    if width is None:
        width = marsh.utils.get_terminal_width()
    description_indent = min(description_indent, width - 1)

    def format_fields(
        doc: marsh.schema.UnmarshalSchema.Doc,
        path: str = '',
        current_depth: int = 0,
    ) -> str:
        if current_depth >= depth:
            return ''
        fields = []
        for name, field in (doc.fields or {}).items():
            name = marsh.path.append(path, name)
            value = name
            if field.type:
                value = f'{value}: {field.type}'
            if field.doc.default:
                value = f'{value} = {field.doc.default}'
            fields.append(
                format_terminal_value(
                    value=value,
                    width=width,
                    description=field.description,
                    indent=indent + current_depth * depth_indent_factor,
                    description_indent=description_indent,
                    description_margin=description_margin,
                ),
            )
            fields.append(
                format_fields(
                    doc=field.doc,
                    path=name,
                    current_depth=current_depth + 1,
                ),
            )
        for special_field in (doc.special_fields or ()):
            fields.append(
                format_terminal_value(
                    value=special_field.value,
                    width=width,
                    description=special_field.description,
                    indent=indent + current_depth * depth_indent_factor,
                    description_indent=description_indent,
                    description_margin=description_margin,
                ),
            )
        return '\n\n'.join(filter(None, fields))
    return format_fields(
        doc=common.get_unmarshal_doc(
            source=source,
            depth=depth,
        ),
        path=prefix_path,
    )


def format_unmarshal_help(
    source: common.UnmarshalDocType,
    prefix_path: str = '',
    width: Optional[int] = None,
    depth: int = 1,
    field_indent: int = 2,
    depth_indent_factor: int = 2,
    description_indent: int = 24,
    description_margin: int = 4,
    omit_type: bool = False,
    omit_description: bool = False,
) -> str:
    help_msg = ''
    doc = common.get_unmarshal_doc(
        source=source,
        depth=depth,
    )
    if doc.type and not omit_type:
        help_msg = doc.type
    if doc.description and not omit_description:
        if help_msg:
            help_msg = f'{help_msg}\n\n{doc.description}'
        else:
            help_msg = doc.description
    fields_msg = format_unmarshal_fields(
        source=doc,
        prefix_path=prefix_path,
        width=width,
        depth=depth,
        indent=field_indent,
        depth_indent_factor=depth_indent_factor,
        description_indent=description_indent,
        description_margin=description_margin,
    )
    if fields_msg:
        if help_msg:
            help_msg = f'{help_msg}\n\n{fields_msg}'
        else:
            help_msg = fields_msg
    return help_msg
