#!/bin/sh
# Wrapper for shell editing of GnuPG-encrypted SQLite databases.
#
# Copyright © 2010-2011 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
# Made available under the GPLv3 (http://www.gnu.org/licenses/gpl-3.0.html)
#
# Usage: gpg-sqlite FILE [RECIPIENT]
#
# gpg-sqlite allows a user to edit a SQLite 3 database encrypted with GnuPG. The
# following steps are taken:
#
# 1. A temporary copy is made of the file to be edited with the owner set to
#    the invoking user.
# 2. The SQLirte 3 command-line interface sqlite3(1) is run to edit the
#    temporary file.
# 3. Whether or not it has been modified, the temporary file is re-encrypted
#    with GnuPG and returned to its original location and the temporary file is
#    removed.
#

cleanup () {
  # shred and remove the temporary, unencrypted file
  shred -u "$TEMPDIR/$BN.$$"
  # remove the temporary output; probably don't need to shred, as it's encrypted
  rm -f "$TEMPDIR/$BN"
}

# First and only argument is (or should be) the file to edit.
FILE=$1
if [ "$FILE" = "" ]; then
    echo "Usage: $(basename $0) filename"
    exit 1
fi
if [ "$2" = "" ]; then
  # encrypt to self to avoid tedious passphrase retyping
  ENCRYPT_FLAGS="-e --default-recipient-self"
  # comment out the above and uncomment the following to specify per-file
  # passphrases:
  #ENCRYPT_FLAGS="-c"
else
  ENCRYPT_FLAGS="-e -r $2"
fi

# use a temporary directory in the user's home directory, instead of in /tmp or
# /var/tmp
TEMPDIR=~/.cache/gpg-sqlite
umask 077
mkdir -p $TEMPDIR || exit 1

# strip directories for temporary file names
BN=`basename $FILE`
# if the file exists, try to decrypt it
if [ -e "$FILE" ]; then
  while ! gpg <"$FILE" >"$TEMPDIR/$BN.$$"; do
    echo "Uh"
  done
else
  # otherwise assume we're creating a new (empty) file
  touch "$TEMPDIR/$BN.$$"
fi

# edit the unencrypted data
if sqlite3 "$TEMPDIR/$BN.$$" .tables >/dev/null 2>&1 ; then
  # file actually contains a sqlite database!
  sqlite3 "$TEMPDIR/$BN.$$"
else
  echo "$(basename $0): $FILE does not contain a sqlite3 database."
  cleanup
  exit 1
fi

# if the file was modified, re-encrypt and overwrite the original
while ! gpg $ENCRYPT_FLAGS -a <"$TEMPDIR/$BN.$$" >"$TEMPDIR/$BN"; do
  echo "Uh, please try again..."
done 
cat "$TEMPDIR/$BN" >"$FILE"
cleanup
