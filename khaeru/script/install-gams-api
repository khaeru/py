#!/bin/sh
# Takes at least three arguments:
# - Version of GAMS
# - Version of the API to install; this must match
# - Installer to use, such as 'pip', 'pip3', 'conda'
# - (optionally) Any arguments to pass to the installer

# Save required arguments
GAMS_VERSION=$1
PY_VERSION=$2
PIP=$3
shift; shift; shift


# Locate the GAMS Python API files
GAMS=$(dirname $(which gams))/apifiles/Python/api$PY_VERSION

# Create a temporary directory
TMP=$(mktemp --tmpdir -d gams-api.XXX)
# Copy the GAMS API files into the temporary directory in a structure
# more suited to setuptools
for cpackage in cfgm dctm gamsx gdx gevm gmd gmom idx opt; do
  mkdir $TMP/${cpackage}cc
  cp $GAMS/${cpackage}cc.py $TMP/${cpackage}cc/__init__.py
  cp $GAMS/_${cpackage}cc.so $TMP/${cpackage}cc/
done
cp -r $GAMS/gams $TMP/

# Write a rudimentary setup script
cat <<EOF >$TMP/setup.py
from setuptools import setup, find_packages

setup(name='GAMS APIs',
      version='${GAMS_VERSION}',
      packages=find_packages(),
      package_data={'': ['_*.so', '_*.pyd']},
      )
EOF

# Install
$PIP install $* $TMP

# Clean up
rm -r $TMP
