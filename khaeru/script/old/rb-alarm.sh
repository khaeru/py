#!/bin/sh
# http://oracleabc.com/b/?p=278
# This script will start Rhythmbox properly so that media keys and other cron
# jobs can still access it. Save as anything but “rhythmbox”.

# Save as a script. Make it executable. Call the script, via Cron, with
# whatever regular rhythmbox-client option you want to e.g., --play, --pause

# Get the PID for existing Rhythmbox process.
PID=$(pgrep -u $LOGNAME -o -x rhythmbox)

# Rhythmbox is not running. Get PID of other DBUS process.
if [ -z "$PID" ] ; then
  PID=$(pgrep -u $LOGNAME -o -x notification-da)
fi

# Find DBUS session bus for this session and export it.
export $(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$PID/environ 2>/dev/null)

# Start Rhythmbox.
/usr/bin/rhythmbox-client --no-present

# Wait for Rhythmbox to finish loading. Adjust if necessary.
sleep 5

# Tell Rhythmbox to start playing.
/usr/bin/rhythmbox-client --play
