import re
import os
from setuptools import (
    setup,
    find_packages,
)
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


root = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(root, 'README.md'), 'r') as fp:
    long_description = fp.read()


version = find_version(os.path.join(root, 'marsh/__init__.py'))
if not version:
    raise RuntimeError('could not find version of marsh')


setup(
    name='marsh',
    version=version,
    description='(Un)marshaling framework.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/adriansahlman/marsh',
    author='Adrian Sahlman',
    author_email='adrian.sahlman@gmail.com',
    license='MIT',
    packages=find_packages(include=('marsh', 'marsh.*')),
    package_data={'marsh': ['py.typed']},
    install_requires=(
        'typing-extensions >= 4.2',
        'omegaconf >= 2.1.1',
        'docstring-parser >= 0.7.3',
        'dateparser >= 1.1.1',
    ),
    python_requires='>=3.8',
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    keywords='marshal unmarshal configuration',
)
