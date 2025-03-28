#!/bin/bash
# laptop-ddcutil-emulator.bash - laptop panel virtual ddcutil
# ==========================================================
# Copyright (C) 2025 Michael Hamilton
#
# This script is a template for integrating a laptop panel into vdu_controls
# by emulating a basic ddcutil command set.
#
# This template needs editing to create an implementation specific to
# actual hardware, such as Intel or AMD driven laptop-panels.
#
# The bash getvcp and setvcp functions need completing with what ever
# command line code is appropriate for getting and setting the brightness
# on the targeted laptop.  The capabilities function can optionally be
# edited to reduce/increase the capabilities offered to vdu_controls.
#
# The script needs to be executable, and can be tested on the command
# line as follows:
#
#   chmod u+x laptop-ddcutil-emulator.bash
#   ./laptop-ddcutil-emulator.bash getvcp 10 12
#   ./laptop-ddcutil-emulator.bash setvcp 10 75
#   ./laptop-ddcutil-emulator.bash setvcp 12 60
#   ./laptop-ddcutil-emulator.bash setvcp 12 x3C
#   ./laptop-ddcutil-emulator.bash detect
#   ./laptop-ddcutil-emulator.bash capabilities
#
# GNU License
# ===========
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see https://www.gnu.org/licenses/.
#

# See https://wiki.archlinux.org/title/Backlight
function getvcp() {
    # get the brightness and/or contrast.
    shift
    for vcp_code in "$@"
    do
        if [[ "$vcp_code" =~ ^[0-9a-zA-Z][0-9a-zA-Z]$ ]]
        then
            if [ "$vcp_code" == "10" ]
            then
                # TODO Add code to get brightness
                brightness=90
                max_brightness=100
                echo "VCP 10 C $brightness $max_brightness"
            elif  [ "$vcp_code" == "12" ]
            then
                # TODO Add code to get contrast - optional, only if using?
                contrast=80
                max_contrast=100
                echo "VCP 12 C $contrast $max_contrast"
            else
                echo "WARN: getvcp vcp-code $vcp_code is unsupported" 1>&2
                exit 1
            fi
        fi
    done
    exit 0
}

setvcp() {
    vcp_code="$1"
    vcp_value="$2"
    if [[ "$vcp_value" =~ ^x ]]
    then  # Convert hex to decimal for script use
        vcp_value=$((16#${2:1}))
    fi
    if [ "$vcp_code" == "10" ]
    then
        # TODO Add code to set brightness
        echo "do what ever changes brightness to $vcp_value" 2>&1
    elif [ "$vcp_code" == "12" ]
    then
        # TODO Add code to set contrast - optional, only if using
        echo "do what ever changes contrast to $vcp_value" 2>&1
    else
        echo "ERROR: setvcp $vcp_code is unsupported" 1>&2
        exit 1
    fi
    exit 0
}

capabilities() {
    # The 'Feature:' lines list what features are supported - no need to edit.
    cat <<EOF
Model: AB_12345
MCCS version: 2.2
Commands:
   Op Code: 01 (VCP Request)
   Op Code: 02 (VCP Response)
   Op Code: 03 (VCP Set)
   Op Code: 07 (Timing Request)
   Op Code: 0C (Save Settings)
   Op Code: F3 (Capabilities Request)
VCP Features:
   Feature: 10 (Brightness)
   Feature: 12 (Contrast)
   Feature: FF (Dummy to finish)
EOF
    exit 0
}

detect() {
    # No changes are needed (not all of the following is necessary)
    # Could set the 'Display' number if you wish, but zero is OK because
    # the real ddcutil starts the numbering from one.
    cat <<EOF
Display 0
   I2C bus:  /dummy/abc-999
      DRM connector:                         dummy
      Driver:                                dummy
      EDID exists:                           true
   EDID synopsis:
      Mfg id:               MyMake - My Make Long Name
      Model:                Laptop
      Product code:         12345  (0x0000)
      Serial number:        Screen
      Binary serial number: 16843009 (0x01010101)
      Manufacture year:     2022,  Week: 8
      EDID version:         1.4
      Extra descriptor:
      Video input definition:    0xa5 - Digital Input (DisplayPort), Bit depth: 8
      Supported features:
         DPMS active-off
         Digital display type: RGB 4:4:4 + YCrCb 4:4:4
         Standard sRGB color space: False
      White x,y:        0.312, 0.329
      Red   x,y:        0.644, 0.335
      Green x,y:        0.304, 0.613
      Blue  x,y:        0.146, 0.070
      Extension blocks: 0
   EDID source: I2C
   EDID hex dump:
        +0          +4          +8          +c            0   4   8   c
+0000   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0010   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0020   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0030   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0040   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0050   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0060   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
+0070   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
   VCP version:         2.2
   Controller mfg:      Mstar
   Firmware version:    2.0
   Monitor uses invalid feature flag in DDC reply packet to indicate unsupported feature.
   Current dynamic sleep adjustment multiplier:  0.00
   Monitor Model Id:  XYZ-AB_12345-12345
   Feature definition file XYZ-AB_12345-12345.mccs not found.
EOF
    exit 0
}

for arg in "$@"
    do
        if [ "$arg" == "--display" ]
    then
        shift
        display_num="$1"
        shift
    fi
    if [ "$arg" == "--edid" ]
    then
        shift
        edid_txt="$1"
        shift
    fi
    if [ "$arg" == "getvcp" ]
    then
        shift
        getvcp "$@"
    fi
    if [ "$arg" == "setvcp" ]
    then
        shift
        setvcp "$@"
    fi
    if [ "$arg" == "capabilities" ]
    then
        capabilities
    fi

    if [ "$arg" == "--version" ]
    then
        echo "ddcutil 1.2.0"
        exit 0
    fi
    if [ "$arg" == "detect" ]
    then
        detect
    fi
done
