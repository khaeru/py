#!/bin/sh
#
# Try to connect to each SSH host in succession

for host in $@;
do
  ssh $host
  # Exit after a connection has succeeded
  [ $? -eq 0 ] && exit 0
done

exit $?
