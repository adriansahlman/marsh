#!/bin/sh
set -eux

tempdir=$(mktemp -d)

cp -r ./* "${tempdir}"

cd "${tempdir}"

pip install .

rm -r marsh

cd /

# Test that installed and importable
python -c 'import marsh; print(marsh.__version__)'

cd "${tempdir}"

pip install -r requirements.txt

(pytest ${TEST:-test} && rm -rf ${tempdir}) || rm -rf ${tempdir}
