#!/bin/sh
# Set up a Python environment on svante
# Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
#
# Currently (as of 2015-04-24) the svante head node has Python 2.7 with a
# limited selection of packages installed. This script installs some other items
# in the user's directory, including:
#  - Python 3.x
#  - The 'pip' Python package manager.
#  - NumPy, a popular mathematic library.
#
# Recommended usage is to create a temporary directory and run the script inside
# it, e.g.
#
#   mkdir tmp
#   cd tmp
#   /home/pnk/code/python.sh
#
# The script is exhaustively commented so that it can be easily customized.
# There are some TODO items, marked as such.

# Check http://www.python.org/download/releases/ to see if a newer version has
# been released.
P3VER=3.4.3
# MD5 checksum of the latest version. This should be available on the Python 3
# download page. Because this script downloads files from the Internet, this
# is used to check that nothing malicious is happening (e.g. a virus has been
# downloaded instead). If the checksum doesn't match, the script quits.
P3MD5=cea34079aeb2e21e7b60ee82a0ac286b

# Destination directory for local installation
DEST="$HOME/.local"

# Install the latest version of Python 3
py3k () {
  # Get the source code
  curl https://www.python.org/ftp/python/$P3VER/Python-$P3VER.tar.xz \
       https://www.python.org/ftp/python/$P3VER/Python-$P3VER.tar.xz.asc
  echo "$P3MD5  Python-$P3VER.tar.bz2" | md5sum --check --status || exit 1
  # extract the source code
  tar xJf Python-$P3VER.tar.xz
  cd Python-$P3VER
  # configure, build & install
  ./configure --prefix=$DEST
  make
  make install
  # clean up
  cd ..
  rm -r Python-$P3VER*

  # Update .bashrc so that the locally-installed Python 3 is available. This
  # isn't the best solution; for example, if $DEST is $HOME/local, what will be
  # written is something like:
  #   export PATH=/home/pnk/local/bin:$PATH
  # instead of:
  #   export PATH=$HOME/local/bin:$PATH
  # The latter is more proper (it will not break if the user's home directory is
  # moved) but a pain to do.
  cat >>.bashrc << EOF
export PATH=$DEST/bin:\$PATH
EOF
  # Update the PATH within this script, too
  export PATH=$DEST/bin:$PATH

  # distribute -- http://pypi.python.org/pypi/distribute
  https://bootstrap.pypa.io/get-pip.py

  # pip -- check http://pypi.python.org/pypi/pip to see if a newer version has
  # been released
  PIPVER=1.1
  wget http://pypi.python.org/packages/source/p/pip/pip-$PIPVER.tar.gz
  tar xzf pip-$PIPVER.tar.gz
  # clean up
  cd pip-$PIPVER
  rm -r pip-$PIPVER*
}

# The actual script. Comment out lines to disable parts.
mkdir tmp
cd tmp
py3k
cd ..
rm -r tmp

# Packages
# numpy -- http://numpy.scipy.org
# Export the paths to the svante ATLAS (linear algebra) libraries, which are
# needed by both numpy and scipy. These are found via 'module display atlas'.
export ATLAS=/home/software/atlas/atlas-3.8.4/lib
export ATLAS_SRC=/home/software/atlas/atlas-3.8.4/lib
export BLAS=/home/software/atlas/atlas-3.8.4/include
export BLAS_SRC=/home/software/atlas/atlas-3.8.4/include
pip_both numpy

## scipy -- http://www.scipy.org
pip_both "git+git://github.com/scipy/scipy.git@5635506ef63958cc7a958abccf6e89a8d04c954f#egg=Package"

# TODO: (maybe) add matplotlib here

# netCDF4 -- http://code.google.com/p/netcdf4-python/ ,
#   http://pypi.python.org/pypi/netCDF4
pip_both netCDF4

# TODO: add py-gdx here

# iPython -- http://ipython.org , http://pypi.python.org/pypi/ipython
pip_both ipython
