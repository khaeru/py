#!/bin/sh
# Some snippets to assist with removing duplicate tasks in taskwarrior

task diagnostics | grep "Found duplicate" | sed -e "s/^\s*Found duplicate //" >dupes.txt

while read uuid; do
  if [ $(grep "uuid:\""$uuid completed.data | uniq | wc -l) -gt 1 ]; then
    # look for duplicate UUIDs with *different* content*
    grep "uuid:\""$uuid completed.data | uniq
    echo " "
  elif [ $(grep "uuid:\""$uuid completed.data | uniq | wc -l) -eq 1 ]; then
    # look for duplicate UUIDs with *different* content*
    sed -i -e "0,/uuid:.$uuid/{//d;}" completed.data.tmp
  fi
done < dupes.txt
