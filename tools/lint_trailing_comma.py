"""Run add-trailing-comma without changing the input files."""
import argparse
import os
import shutil
import sys
import tempfile
from typing import Iterable

from add_trailing_comma import _main


def lint(
    filenames: Iterable[str],
) -> int:
    argv = ['--py36-plus']
    relpaths = []
    cwd = os.getcwd()
    for fpath in filenames:
        abspath = os.path.abspath(fpath)
        if not abspath.startswith(cwd):
            print('can only lint files under the current working directory')
            sys.exit(1)
        relpaths.append(os.path.relpath(abspath, cwd))
    with tempfile.TemporaryDirectory() as tempdir:
        for fpath in relpaths:
            argv.append(os.path.join(tempdir, fpath))
        shutil.copytree(cwd, tempdir, dirs_exist_ok=True)
        return _main.main(argv)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='trailing comma linter',
        description=(
            'lint python files using add-trailing-comma'
            'without altering any files. A non-zero exit code '
            'is returned if linting did not go through.'
        ),
    )
    parser.add_argument(
        'filenames',
        nargs='*',
    )
    args = parser.parse_args()
    sys.exit(lint(args.filenames))


if __name__ == '__main__':
    main()
