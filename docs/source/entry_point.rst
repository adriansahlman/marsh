Entry Point
===========

Please see :doc:`getting_started` for an introduction to entry points.

Customization
-------------

When wrapping a function in :func:`marsh.main` some functionality
can be configured through keyword arguments to the decorator.

Descriptions for these keyword arguments can be found in the
docstring of :func:`marsh.main`. One of them is showcased below.

Config type
^^^^^^^^^^^

If a config object is to be passed around in the application
it might be preferable to use that as a single argument to the entry point.


.. code-block:: python
    :caption: Using a configuration class

    # app.py
    import dataclasses
    import marsh


    @dataclasses.dataclass
    class Config:
        a: int
        b: float


    @marsh.main
    def main(
        config: Config
    ) -> None:
        print(config)


However, this requires us to use the keyword ``'config'`` before each
argument on the command line. It also creates an unnecessary nesting
of arguments in the help message.


.. code-block:: shell
    :caption: Help message with nested fields

    $ python app.py --help | tail -n 6
    fields:
      config: Config(...)

        config.a: <int>

        config.b: <float>


.. code-block:: shell
    :caption: Longer path for arguments

    $ python app.py config.a=0 config.b=1.5
    Config(a=0, b=1.5)


Specifying a type for the ``config`` argument to :func:`marsh.main` makes
the entry point use the fields/arguments of that type instead of
the function being wrapped.


.. code-block:: python
    :caption: Specifying the config type

    # app.py
    ...

    @marsh.main(config=Config)
    def main(
        config: Config
    ) -> None:
        print(config)


.. code-block:: shell
    :caption: Help message without nested fields

    $ python app.py --help | tail -n 4
    fields:
      a: <int>

      b: <float>


.. code-block:: shell
    :caption: Shorter path for arguments

    $ python app.py a=0 b=1.5
    Config(a=0, b=1.5)


Command Line
------------

Help
^^^^

The basic help message that is included looks as follows.

.. code-block:: shell
    :caption: Standard help message

    usage: prog [-h [PATH]] [-c PATH] [-o [PATH]] [--config-out [PATH]]
                   [overrides [overrides ...]]

    positional arguments:
      overrides             Assign new values for fields in the configuration
                            using `=` or assign the content of a config file
                            using `@`. Adding `+` in front (`+=`, `+@`) combines
                            the current value of the specified field with its
                            new assigned value. Prepending a field with `~`
                            removes it.

    optional arguments:
      -h [PATH], --help [PATH]
                            Show this message and exit. Optionally display
                            config documentation for a path in the config
                            structure
      -c PATH, --config-dir PATH
                            Root directory for config files. Config paths given
                            in override arguments will be evaluated relative
                            `--config-dir`. Defaults to the working directory of
                            the caller.
      -o [PATH], --output [PATH]
                            Change the current working directory when launching
                            the application (after loading the final
                            configuration). If no path is given when using this
                            argument it defaults to "jobs/%Y%m%dT%H%M%S.%fZ"
      --config-out [PATH]   Write the current input configuration, then proceed.
                            If no path is specified, the configuration is
                            written to stdout. Relative paths are affected by
                            the --output argument.


.. note::

    Setting ``setup_logging=True`` in the :func:`marsh.main` decorator adds
    the keyword arguments ``--logging-level`` and ``--logging-format``.

After this part of the documentation the arguments of the decorated function (or
a config class if specified) are printed.
By default, only 2 levels nested fields are documented in the help message. If the
types of the entry point arguments are rich with deeply nested subfields these might
not be shown.

To allow for all type documentation to be viewed ``--help`` supports an optional
argument which is a path to a nested part of the entry point argument types.


.. code-block:: python
    :caption: Nested types

    # app.py
    import dataclasses
    import marsh


    @dataclasses.dataclass
    class A:
        """Example of a nested documentation class."""
        some_int: int
        some_str: str
        some_bool: bool


    @dataclasses.dataclass
    class B:
        a: A


    @dataclasses.dataclass
    class C:
        b: B


    @marsh.main
    def main(
        a: A,
        b: B,
        c: C,
    ) -> None:
        ...


.. code-block:: shell
    :caption: Help message

    $ python app.py --help | tail -n 4
    fields:
      c: C(...)

        c.b: B(...)


Using the optional path argument we can display the documentation
for the ``A`` class.


.. code-block:: shell
    :caption: Help message

    $ python app.py --help c.b.a
    A

    Example of a nested documentation class.

      some_int: <int>

      some_str: <str>

      some_bool: <bool>


Overrides
^^^^^^^^^

An override sets or alters the values passed on to the unmarshaler
before being passed to the entry point function.

All overrides are supplied as positional arguments.

Path
****

The path of an override is a set of dot-separated fields.

If the combination of input values produce

.. code-block:: python

    {'a': 0, 'b': {'c': 1}}

then the path ``'a.b.c'`` would point to the integer ``1``.

For sequences such as lists and tuples the index is specified directly
in the path:

.. code-block:: python

    {'a': [1, {'b': 2}]}

The path ``'a.1'`` would point to the dictionary ``{'b': 2}`` in the above value.

.. note::

    An empty path is valid and points at the root of the values.
    This is the same as using a single dot ``'.'``


Values
******
Values can be set, combined or removed.

.. note::

    Some of the characters needed for specifying container objects (mappings or sequences)
    may be reserved by the shell. Use quotes or escape characters that are consumed by the shell.

See :func:`marsh.parse.element` for information on parsing rules for the values.

To set the value for a path directly on the command line use ``path.to.field=value``.

To combine the value with any existing value on the same path, use ``path.to.field+=value``.
This will fail unless the previous value and new value both are mappings or sequences.

To remove an existing value, use ``~path.to.field``.

.. note::

    Containers such as mappings may be specified as a single value
    or by specifying the each nested value separately.
    ``a_map={a:0,b:1}`` is the same as ``a_map.a=0 a_map.b=1``.

Configs
*******

Config paths are absolute if they start with ``/``. Otherwise they are
relative to the current working directory (unless ``--config-dir`` has been
specified, in which case the paths are relative to the specified directory).

Currently supported config types are files ending with ``.json``, ``.yml`` and ``.yaml``
(can be extended to accept more types). When specifying a path to a config it is
possible to omit the file extension in which cast marsh will attempt look for files
with the same path and a supported extension.

Configs are specified in a similar way to values. To set the value of specific path
to the content of a config, use ``path.to.field@path/to/config``.

To combine the current value with the content of a config, use
``path.to.field+@path/to/config``.

.. note::

    The root path of input values is the empty string so if a config
    contains the entire configuration it would be set without specifying
    a path (``@path/to/config``).


Variable Interpolation
**********************

marsh uses the variable interpolation supplied by omegaconf.
Please see its documentation for how to use or extend this functionality.


Meta Data
*********

Any values under the path ``_meta_.`` are removed before the input
values are being used for unmarshaling.

The meta field may be useful for storing constants and other values
used for variable interpolation.
