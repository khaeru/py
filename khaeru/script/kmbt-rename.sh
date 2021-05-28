#!/bin/sh
# Rename and rotate scan PDFs e-mailed by a particular scanner at MIT…
#
for f in $(ls KMBT222*[0-9].pdf);
do
  OUT_FN=`echo "$f" | sed -rn "s/^KMBT222(....)(..)(..)(..)(..)(..)/\1-\2-\3T\4:\5:\6/p"`

  if [ "$1" != "-n" ];
  then
    pdftk $f cat 1-endleft output $OUT_FN
  else
    echo "pdftk $f cat 1-endleft output $OUT_FN"
  fi
done
