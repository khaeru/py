#!/bin/sh
# Open a new gnome-terminal window with one tab for every existing profile

# List of tabs:
# - Read list of profiles from dconf
# - Reformat as "--tab-with-profile=<UUID>"
TABS=$(dconf read /org/gnome/terminal/legacy/profiles:/list | tr -d "[]' " | tr "," "\0" | xargs -0 -I X echo --tab-with-profile=X)

# Launch terminal
# - Give a specific app-id to aid gnome-shell window matching; see
#   gnome-terminal-tabs.desktop in khaeru/dotfiles
gnome-terminal --app-id name.kishimoto.paul.scripts $TABS
