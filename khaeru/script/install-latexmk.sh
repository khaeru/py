#!/bin/sh
# Install the latest version of latexmk

# Create a temporary directory
TMP=$(mktemp --tmpdir -d install-latexmk.XXX)
cd $TMP

# Get the release
curl -O -L http://mirrors.ctan.org/support/latexmk.zip
unzip -q latexmk.zip
cd latexmk

# Echo the version
head -n1 README

# Create target directories
LOCAL=$HOME/.local
mkdir -p $LOCAL/bin $LOCAL/man/man1

# Install latexmk.pl
cp latexmk.pl $LOCAL/bin/
ln -fsr $LOCAL/bin/latexmk.pl $LOCAL/bin/latexmk

# Install latexmk.1
gzip latexmk.1
cp latexmk.1.gz $LOCAL/man/man1/

# Tidy up temporary directory
rm -r $TMP
