#!/bin/bash
#
# lux-from-webcam.bash - guess lux value based on a webcam image
# ==================================================================
# Copyright (C) 2023 Michael Hamilton
#
# This script will read lux/brightness values from ~/.config/lux-from-webcam.data
# Add as many discrete values as you require: name lux value. The name is
# simple a comment and should have no spaces.
#
# A default config file is created when the script is first run, please alter
# it to match your own ambient lighting conditions.
#
# The script will optionally include ~/.config/lux-from-webcam.config
# and can be used to override any of the follow constants:
#
#    DATA_FILE=~/.config/lux-from-webcam.data
#    CAMERA_DEVICE=/dev/video0
#    MANUAL_EXPOSURE_OPTION=1
#    MANUAL_EXPOSURE_TIME=64
#    IMAGE_LOCATION=$HOME/tmp/out.jpg
#
# Exposure time is 1/s seconds, so 64 is 1/64 of a second.
# The appropriate manual exposure option (if there is one) can be
# discovered by running
#
#    v4l2-ctl -d /dev/video0 --list-ctrls-menus
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

CONFIG_FILE=~/.config/lux-from-webcam.config
DATA_FILE=~/.config/lux-from-webcam.data
CAMERA_DEVICE=/dev/video0
MANUAL_EXPOSURE_OPTION=1
MANUAL_EXPOSURE_TIME=64
IMAGE_LOCATION=/tmp/lux-from-webcam.jpg

if [ -f $CONFIG_FILE ]
then
    echo "INFO: including config file: $CONFIG_FILE" >&2
    . $CONFIG_FILE
fi

if [ \! -f $DATA_FILE ]
then
    echo "INFO: creating $DATA_FILE based on the Logitech Webcam C270, please customise to your local conditions." >&2
    cat > $DATA_FILE <<EOF
SUNLIGHT       100000 250
DAYLIGHT        10000 160
OVERCAST         1000 110
SUNRISE_SUNSET    400  50
DARK_OVERCAST     100  20
LIVING_ROOM        50   5
NIGHT               5   0  
EOF
fi

existing_settings=$(v4l2-ctl --device $CAMERA_DEVICE --get-ctrl auto_exposure,exposure_time_absolute | awk '
{setting[++i]=$2} END {printf "auto_exposure=%s,exposure_time_absolute=%s", setting[1], setting[2]}')

trap "v4l2-ctl --device $CAMERA_DEVICE --set-ctrl $existing_settings" EXIT

# Decide on exposure settings based on the output of v4l2-ctl --device /dev/video0 --list-ctrls-menus
# and trial images samples.

current_exposure_mode=$(v4l2-ctl --device $CAMERA_DEVICE --get-ctrl auto_exposure | awk '{print $2}')

v4l2-ctl  --device $CAMERA_DEVICE  \
  --set-ctrl auto_exposure=$MANUAL_EXPOSURE_OPTION,exposure_time_absolute=$MANUAL_EXPOSURE_TIME \
  --set-fmt-video=width=1280,height=720,pixelformat=MJPG \
  --stream-mmap --stream-to=$IMAGE_LOCATION --stream-count=1

# Fix issues in MJPG that bother ImageMagick
convert $IMAGE_LOCATION $IMAGE_LOCATION-fixed 1>/dev/null 2>&1
# Compute average brightness 0..255.
brightness=$(convert $IMAGE_LOCATION-fixed -colorspace gray -resize 1x1 -format "%[fx:255*mean]" info:)
brightness=$(echo $brightness | sed 's/[.].*//')
echo "INFO: camera-brightness: $brightness/255" >&2

while read name lux value
do
  if [ $brightness -ge $value ]
  then
    if [ "$previous_value" != '' ]
    then
        # Interpolate on a log10 scale - at least that's what I think this is (idea from chatgpt)
        echo "INFO: log10 interpolating $brightness over $value..$previous_value to lux $lux..$previous_lux" >&2
        lux=$(awk -v b=$brightness  -v v=$value -v pv=$previous_value -v lx=$lux -v plx=$previous_lux '
        BEGIN { print(lx + 10 ** ((b - v) / (pv - v) * log(plx - lx)/log(10))); exit 0; }' < /dev/null)
    fi
    echo "INFO: brightness=$brightness, value=$value, lux=$lux, name=$name" >&2
    echo $lux
    break
  fi
  previous_value=$value
  previous_lux=$lux
done < $DATA_FILE