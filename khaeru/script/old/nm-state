#!/bin/sh
state=`nm-tool | grep -e ^State | cut -d " " -f 2`

if [ state = "connected" ]; then
  exit 0;
else
  exit 1;
fi
