#!/bin/sh
BASE=http://lists.paul.kishimoto.name/private.cgi/aer407-paul.kishimoto.name/
# set on the command line
#PASS=

zgrep --no-filename "$BASE" Week-of-Mon-20071001.txt.gz | \
	sed "s/^URL.*: http/http/I" | \
	sed "s@$BASE@@" >attachlist.txt

for line in $(cat attachlist.txt);
do
  mkdir --parents `dirname $line`
  wget --output-document=$line --post-data="password=$PASS" $BASE$line
done

rm attachlist.txt
