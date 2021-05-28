#!/bin/sh

DEV=md0

if grep -q $DEV /proc/mdstat; then
  action="stop"
else
  action="assemble"
fi

pkexec mdadm --$action /dev/$DEV
