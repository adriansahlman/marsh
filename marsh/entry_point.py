"""Tools for inserting entry points into python applications."""
import argparse
import contextlib
import datetime
import logging
import os
import shutil
import sys
import textwrap
from typing import (
    Any,
    Callable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
)

import marsh
import marsh.doc
import marsh.parse


FIELD_INDENT = 2
DESCRIPTION_INDENT = 24
DESCRIPTION_MARGIN = 4


class EntryPoint:

    LOGGING_LEVELS = [
        'CRITICAL',
        'ERROR',
        'WARNING',
        'INFO',
        'DEBUG',
        'NOTSET',
    ]

    def __init__(
        self,
        fn: Callable,
        config: Optional[Any] = None,
        setup_logging: bool = False,
        prog: Optional[str] = None,
        description: Optional[str] = None,
        epilog: Optional[str] = None,
        help_depth: int = 2,
    ) -> None:
        self.fn = fn
        self.config = config
        self.setup_logging = setup_logging
        self.prog = prog
        self.description = description
        self.epilog = epilog
        self.help_depth = help_depth
        self.schema: marsh.schema.UnmarshalSchema
        if config is None or marsh.utils.is_missing(config):
            self.schema = marsh.schema.argument.ArgumentsUnmarshalSchema(fn)
        else:
            self.schema = marsh.schema.UnmarshalSchema(config)

    @property
    def terminal_width(
        self,
    ) -> int:
        return max(
            shutil.get_terminal_size().columns - 2,
            11,
        )

    def get_arg_parser(
        self,
    ) -> argparse.ArgumentParser:
        description = self.description
        if description is None:
            description = self.schema.doc_description()
        if description:
            description = textwrap.fill(
                description,
                width=self.terminal_width,
            )
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description=description,
            epilog=self.epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
        )

        parser.add_argument(
            '-h',
            '--help',
            dest='help',
            type=str,
            metavar='PATH',
            nargs='?',
            const="",
            help=(
                'Show this message and exit. Optionally display '
                'config documentation for a path in the config '
                'structure'
            ),
            default=None,
        )

        parser.add_argument(
            '-c',
            '--config-dir',
            dest='path',
            type=str,
            metavar='PATH',
            help=(
                'Root directory for config files. '
                'Config paths given in override '
                'arguments will be evaluated relative '
                '`--config-dir`. Defaults '
                'to the working directory of the caller.'
            ),
            default=None,
        )

        parser.add_argument(
            '-o',
            '--output',
            type=str,
            nargs='?',
            default=None,
            const='jobs/%Y%m%dT%H%M%S.%fZ',
            metavar='PATH',
            help=(
                'Change the current working directory '
                'when launching the application '
                '(after loading the final configuration). '
                'If no path is given when using this '
                'argument it defaults to "%(const)s"'
            ),
        )

        parser.add_argument(
            '--config-out',
            type=str,
            nargs='?',
            default=None,
            const='-',
            metavar='PATH',
            help=(
                'Write the current input configuration, '
                'then proceed. If no path is specified, the '
                'configuration is written to stdout. '
                'Relative paths are affected by the '
                '--output argument.'
            ),
        )

        if self.setup_logging:
            parser.add_argument(
                '--logging-level',
                type=str,
                metavar='LEVEL',
                help=(
                    'Specify the logging level. '
                    'Default: %(default)s.'
                ),
                choices=self.LOGGING_LEVELS,
                default='INFO',
            )

            parser.add_argument(
                '--logging-format',
                type=str,
                metavar='FORMAT',
                help=(
                    'Specify the logging format. '
                    'Default: %(default)s.'
                ),
                default='%(asctime)s %(levelname)s: %(message)s',
            )

        parser.add_argument(
            'overrides',
            help=(
                'Assign new values for fields in the '
                'configuration using `=` or assign the '
                'content of a config file using `@`. '
                'Adding `+` in front (`+=`, `+@`) combines '
                'the current value of the specified field '
                'with its new assigned value. '
                'Prepending a field with `~` removes it.'
            ),
            type=str,
            nargs='*',
        )
        return parser

    def load_config(
        self,
        args: argparse.Namespace,
    ) -> marsh.element.ElementType:
        root = None
        config = marsh.MISSING
        if args.path:
            root = args.path
        for override in map(marsh.parse.override, args.overrides):
            config = override.apply(
                element=config,
                root=root,
                keep_meta=True,
            )
        config = marsh.element.resolve(config)
        return marsh.config.drop_meta(config)

    @contextlib.contextmanager
    def maybe_change_cwd(
        self,
        args: argparse.Namespace,
    ) -> Iterator[None]:
        prev_path: Optional[str] = None
        if args.output:
            path = datetime.datetime.now(datetime.timezone.utc).strftime(args.output)
            prev_path = os.getcwd()

            def handle_create_dir_error(
                error: Exception,
            ) -> None:
                print(f'failed to create output directory {path}: {error}')
                sys.exit(1)

            with marsh.errors.maybe_handle_error(handle_create_dir_error):
                os.makedirs(path, exist_ok=True)
            os.chdir(path)
        yield
        if prev_path is not None:
            os.chdir(prev_path)

    def maybe_print_help(
        self,
        args: argparse.Namespace,
        passthrough_args: Optional[Sequence] = None,
        passthrough_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if args.help is None:
            return
        if not args.help:
            self.get_arg_parser().print_help()
            if isinstance(
                self.schema,
                marsh.schema.template.StructuredUnmarshalSchema,
            ):
                doc = self.schema.doc(
                    depth=self.help_depth,
                    default_args=passthrough_args,
                    default_kwargs=passthrough_kwargs,
                )
            else:
                doc = self.schema.doc(depth=self.help_depth)
            field_help = marsh.doc.terminal.format_unmarshal_fields(
                source=doc,
                depth=self.help_depth,
            )
            if field_help:
                print('\nfields:')
                print(field_help)
            sys.exit(0)

        def handle_select_error(
            error: marsh.errors.MarshError,
        ) -> None:
            print(f'failed to traverse configuration: {error.pretty()}')
            sys.exit(1)

        with marsh.errors.maybe_handle_error(handle_select_error):
            schema = self.schema.select(args.help)

        help_msg = marsh.doc.terminal.format_unmarshal_help(
            source=schema,
            depth=self.help_depth,
        )
        if not help_msg:
            print(f'no help documention available for path: {args.help}')
            sys.exit(1)
        print(help_msg)
        sys.exit(0)

    def __call__(
        self,
        *args,
        **kwargs,
    ) -> Any:
        if args or kwargs:
            if not isinstance(
                self.schema,
                marsh.schema.argument.ArgumentsUnmarshalSchema,
            ):
                return self.fn(*args, **kwargs)
        cmd_args = self.get_arg_parser().parse_args()
        self.maybe_print_help(
            cmd_args,
            args,
            kwargs,
        )
        if self.setup_logging:
            logging.basicConfig(
                level=cmd_args.logging_level,
                format=cmd_args.logging_format,
            )

        def handle_load_config_error(
            error: marsh.errors.MarshError,
        ) -> None:
            print(f'failed to load configuration: {error.pretty(True)}')
            sys.exit(1)

        with marsh.errors.maybe_handle_error(handle_load_config_error):
            config = self.load_config(cmd_args)

        with self.maybe_change_cwd(cmd_args):
            if cmd_args.config_out:

                def handle_write_config_error(
                    error: Exception,
                ) -> None:
                    print('Failed to write input config to ', end='')
                    if cmd_args.config_out == '-':
                        print('stdout', end=': ')
                    else:
                        print(cmd_args.config_out, end=': ')
                    if isinstance(error, marsh.errors.MarshError):
                        print(error.pretty(True))
                    else:
                        print(error)
                    sys.exit(1)

                with marsh.errors.maybe_handle_error(
                    handle_write_config_error,
                    Exception,
                ):
                    marsh.config.write(config, path=cmd_args.config_out)

            def handle_unmarshal_error(
                error: marsh.errors.MarshError,
            ) -> None:
                print(f'failed to unmarshal config: {error.pretty(True)}')
                sys.exit(1)

            if isinstance(self.schema, marsh.schema.argument.ArgumentsUnmarshalSchema):
                with marsh.errors.maybe_handle_error(handle_unmarshal_error):
                    arguments = self.schema.unmarshal(
                        config,
                        default_args=args,
                        default_kwargs=kwargs,
                    )
                return self.fn(*arguments.args, **arguments.kwargs)
            with marsh.errors.maybe_handle_error(handle_unmarshal_error):
                value = self.schema.unmarshal(config)
            return self.fn(value)
