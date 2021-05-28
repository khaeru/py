#!/bin/sh
# Install the latest version of Basemap

# Ensure the libgeos headers are installed
sudo apt install libgeos-dev

# Symlink libgeos, since the Basemap installer doesn't detect it correctly
LIB=/usr/lib/x86_64-linux-gnu
sudo ln -fs $LIB/libgeos-3.5.0.so $LIB/libgeos.so

# Create a temporary directory
TMP=$(mktemp --tmpdir -d install-basemap.XXX)
cd $TMP

# Get the release
curl -L -O https://github.com/matplotlib/basemap/archive/v1.0.7rel.tar.gz
tar zxf v*.tar.gz
cd basemap-*

# Install
python3 setup.py install --user

# Tidy up temporary directory
rm -r $TMP
