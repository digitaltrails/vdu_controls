#!/bin/bash
#
# lux-from-brightness.bash - guess lux value based on a webcam image
# ==================================================================
# Copyright (C) 2023 Michael Hamilton
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

DEVICE=/dev/video0
IMAGE_LOCATION=$HOME/tmp/out.jpg
existing_settings=$(v4l2-ctl --device $DEVICE --get-ctrl auto_exposure,exposure_time_absolute | awk '
{setting[++i]=$2} END {printf "auto_exposure=%s,exposure_time_absolute=%s", setting[1], setting[2]}')

trap "v4l2-ctl --device $DEVICE --set-ctrl $existing_settings" EXIT

# Decide on exposure settings based on the output of v4l2-ctl --device /dev/video0 --list-ctrls-menus
# and trial images samples.
v4l2-ctl  --device $DEVICE  \
  --set-ctrl auto_exposure=1,exposure_time_absolute=64 \
  --set-fmt-video=width=1280,height=720,pixelformat=MJPG \
  --stream-mmap --stream-to=$IMAGE_LOCATION --stream-count=1

# Fix issues in MJPG that bother ImageMagick
convert $IMAGE_LOCATION $IMAGE_LOCATION-fixed 1>/dev/null 2>&1
ambient=$(convert $IMAGE_LOCATION-fixed -colorspace gray -resize 1x1 -evaluate-sequence Max -format "%[fx:100*mean]" info:)
ambient=$(echo $ambient | sed 's/[.].*//')
echo "INFO: camera-ambient: $ambient" > /dev/stderr

while read name lux brightness
do
  if [ $ambient -ge $brightness ]
  then
    echo "INFO: ambient=$ambient brightness=$brightness lux=$lux" > /dev/stderr
    echo $lux
    break
  fi
done <<EOF
SUNLIGHT       100000 140
DAYLIGHT        10000 120
OVERCAST         1000 110
SUNRISE_SUNSET    400  40
DARK_OVERCAST     100  20
LIVING_ROOM        50   5
NIGHT               5   0
EOF
# Logitech, Inc. Webcam C270 settings for my study
# Customise the above table to your desktop and webcam
