Getting Started
===============

Entry Points
------------

Create
^^^^^^

Normally when creating an entry point for a script
(or larger application) one uses :class:`argparse.ArgumentParser`
to accept arguments from the command line.

In :mod:`marsh` this can be done with a single decorator over
a function. The decorator inspects the function arguments,
including their types and any descriptions that can be linked
to them from the docstring of the function.

.. code-block:: python
    :caption: Creating an entry point

    # app.py
    import marsh


    @marsh.main
    def run(
        a: int,
        b: float,
        c: dict[str, bool],
    ) -> None:
        """Example of an entry point.

        Arguments:
            a: An integer argument.
            b: A floating point argument.
            c: A dictionary with string keys and
                bool values. If this was python 3.8
                we would instead use typing.Dict[str, bool] as
                type hint as the builtin dict did not support
                type annotations.
        """
        print(a, type(a))
        print(b, type(b))
        print(c, type(c))


    if __name__ == '__main__':
        run()


Run
^^^

When the decorated function is called without arguments
an :class:`argparse.ArgumentParser` is initialized and console
arguments are read in an attempt to populate the arguments
to our entry point function.

Calling the file on the command line using python allows us to
pass arguments to the application.

.. code-block:: shell
    :caption: Running the application

    $ python app.py a=1 b=5e-1 c.key1=true c.key2=false
    1 <class 'int'>
    0.5 <class 'float'>
    {'key1': True, 'key2': False} <class 'dict'>


Argument Validation
^^^^^^^^^^^^^^^^^^^

When giving invalid values or when required arguments
are missing an error message is printed and the application exits.

.. code-block:: shell
    :caption: Using an incorrect value

    $ python app.py a=1.5 b=0 c.some_key=true
    failed to unmarshal config: int: could not convert: 1.5
	path: a

.. code-block:: shell
    :caption: Missing a required value

    $ python app.py a=1 c.some_key=true
    failed to unmarshal config: MissingValueError
        path: b


Help
^^^^

Using --help we can also get a help message for the arguments.
Here the output was piped to ``tail`` to truncate the output into
displaying only the arguments of our entry point.

.. code-block:: shell
    :caption: Printing a help message

    $ python app.py --help | tail
    fields:
      a: <int>              An integer argument.

      b: <float>            A floating point argument.

      c: {<str>: <bool>, ...}
                            A dictionary with string keys and bool values. If this
                            was python 3.8 we would instead use typing.Dict[str,
                            bool] as type hint as the builtin dict did not support
                            type annotations.


Marshal
-------
Marshaling values simply means taking a python object
and turning it into JSON-like data.

.. code-block:: python
    :caption: Marshaling an object

    # marshal.py
    import dataclasses
    import marsh


    @dataclasses.dataclass
    class Config:
        a: int
        b: float


    config = Config(1, 5e-1)
    print(marsh.marshal(config))


.. code-block:: shell

    $ python marshal.py
    {'a': 1, 'b': 0.5}


Unmarshal
---------
Unmarshaling is the opposite of marshaling.
A type is instantiated using JSON-like data.

.. code-block:: python
    :caption: Unmarshaling a type

    # unmarshal.py
    import dataclasses
    import typing
    import marsh


    class Range(typing.NamedTuple):
        start: typing.Optional[int]
        stop: int


    @dataclasses.dataclass
    class Config:
        a: int
        b: float
        c: Range


    config = marsh.unmarshal(
        Config,
        {
            'a': 1,
            'b': 1.5,
            'c': {
                'start': None,
                'stop': 5,
            },
        }
    )
    print(config)


.. code-block:: shell

    $ python umarshal.py
    Config(a=1, b=1.5, c=Range(start=None, stop=5))
