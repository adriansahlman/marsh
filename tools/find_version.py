import argparse
import re
import sys
from typing import Optional


def find_version(
    fpath: str,
) -> Optional[str]:
    with open(fpath, 'r') as fp:
        match = re.search(
            r'(?<=__version__ = [\'"])([^\'"]+)(?=[\'"])',
            fp.read(),
        )
    if not match:
        return None
    return match.group(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='find version',
        description=(
            'find the value of __version__ by parsing a python file.'
        ),
    )
    parser.add_argument(
        'filename',
    )
    args = parser.parse_args()
    version = find_version(args.filename)
    if not version:
        print(f'no version could be find in {args.filename}')
        sys.exit(1)
    print(version)


if __name__ == '__main__':
    main()
