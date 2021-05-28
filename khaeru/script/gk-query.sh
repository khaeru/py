#!/bin/sh
# GNOME-Keyring query script
#
# Copyright © 2011, 2016 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
# Made available under the GPLv3 (http://www.gnu.org/licenses/gpl-3.0.html)
#
# Usage: gk-query TERM
#
# gk-query prompts the user for a passphrase to unlock the login keyring, then
# finds all keyring items with TERM in the display name. It prompts the user to
# display or skip the secret for each item, then clears the screen to erase the
# secrets.
#
# gk-query ensures that the DBus session bus is started, the
# gnome-keyring-daemon is running, and environment variables are set so that the
# keyring is accessible even when logged in to a remote system (e.g. via SSH)
# with no active X session.
#
# This file is a wrapping shell script; the file gk-query.py is also required.

# Check arguments
if [ $# -ne 1 ]; then
  echo "Usage: $0 SEARCH_STRING"
  exit 1
fi

# Start necessary services
if [ "$DBUS_SESSION_BUS_ADDRESS" = "" ]; then
  # The DBus session bus is not running; must start it
  RUN_DBUS=yes
  if [ "$DISPLAY" = "" ]; then
    # $DISPLAY is not set; dbus-launch fails without it
    export DISPLAY=:0
  fi
  # The option --exit-with-session is not used here, because the terminal
  #   seems to become unresponsive or randomly eat characters. As a result,
  #   -TERM needs to be used below instead of -HUP to terminate the session
  #   bus. stderr is redirected to suppress a complaint when $DISPLAY is faked
  #   (above)
  export `dbus-launch 2>/dev/null`
fi

# Invoke the actual script, which unlocks the keyring if necessary
$0.py $1

# Kill the services if they were started by this script
[ -z "$RUN_DBUS" ] || kill -QUIT $DBUS_SESSION_BUS_PID

