
# Marsh

(Un)marshaling library for objects in Python 3.8+.

Tested on Ubuntu, Windows and Mac OSX for Python 3.8, 3.9 and 3.10.

Relies heavily on type-hint reflection. All (un)marshaling is performed recursively which allows for support of nested types.

Influenced by the work of [Omry Yadan](https://github.com/omry) on [hydra](hydra.cc).

The [documentation](https://marsh.readthedocs.io) is hosted on ReadTheDocs.

## Getting Started

### Install

marsh is available through pip
```shell
pip install marsh
```

### Entry point

Using the unmarshaling capabilities of ``marsh`` we can
create entry points for python code.

These entry points allow for arguments to be given on the command
line and/or through config files which are then validated, converted to the correct types and passed to the entry point function.

Most python types are supported (primitives, type aliases, dataclasses, namedtuple e.t.c.)

#### Create

Creating an entry point is as simple as decorating a function
and calling it without arguments.

```python
# app.py
import marsh
from typing import Sequence, Union


@marsh.main
def run(
    a: int,
    b: Union[float, Sequence[int]],
    c: dict[str, bool],
) -> None:
    """Example of an entry point.

    Arguments:
        a: An integer argument.
        b: A floating point value or a sequence of ints.
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
```

#### Run

When running the application we can use the positional arguments
on the command line to pass values to our function.

```shell
$ python app.py a=1 b=5e-1 c.key1=true c.key2=false
1 <class 'int'>
0.5 <class 'float'>
{'key1': True, 'key2': False} <class 'dict'>
```

#### Argument validation

When giving invalid values or when required arguments are missing an error message is printed and the application exits.

```shell
$ python app.py a=1.5 b=0 c.some_key=true
failed to unmarshal config: int: could not convert: 1.5
	path: a
```
```shell
$ python app.py b=0 c.some_key=true
failed to unmarshal config: MissingValueError
	path: a
```

#### Help

Using --help we can also get a help message for the arguments. Here the output was piped to `tail` to truncate the output into displaying only the arguments of our entry point.
```shell
$ python app.py --help | tail -n 11
fields:
  a: <int>              An integer argument.

  b: <float> | [<int>, ...]
                        A floating point value or a sequence of ints.

  c: {<str>: <bool>, ...}
                        A dictionary with string keys and bool values. If this
                        was python 3.8 we would instead use typing.Dict[str,
                        bool] as type hint as the builtin dict did not support
                        type annotations.
```



### Marshal
Marshaling values simply means taking a python object and turning it into JSON-like data.

```python
# marshal.py
import dataclasses
import marsh


@dataclasses.dataclass
class Config:
    a: int
    b: float


config = Config(1, 5e-1)
print(marsh.marshal(config))
```

```shell
$ python marshal.py
{'a': 1, 'b': 0.5}
```

### Unmarshal
Unmarshaling is the opposite of marshaling. A type is instantiated using JSON-like data.

```python
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
```

```shell
$ python umarshal.py
Config(a=1, b=1.5, c=Range(start=None, stop=5))
```

## License
[MIT License](LICENSE).
