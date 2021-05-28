#!/bin/sh
# Options for Dell XPS 13

# inverted & faster two-finger scrolling on touchpad
xinput set-prop "CyPS/2 Cypress Trackpad" "Synaptics Scrolling Distance" -15 -15
# screen gamma correction
xgamma -quiet -gamma 0.75

exit 0
# below this line disabled

# Apple Bluetooth keyboard: use function keys as F1 etc. first
echo 2 | sudo tee /sys/module/hid_apple/parameters/fnmode

# set backlight to fix fn+f4/fn+f5 not working after suspend/resume (raring)
echo 0 | sudo tee /sys/class/backlight/intel_backlight/brightness

# start MIT VPN (for China)
nmcli con up uuid cba249e2-643d-4d81-9749-7741ba17933e
