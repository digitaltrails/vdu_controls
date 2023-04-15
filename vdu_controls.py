#!/usr/bin/python3
"""
vdu_controls - a DDC control panel for monitors
===============================================

A control panel for external monitors (*Visual Display Units*).

Usage:
======

        vdu_controls [-h]
                     [--about] [--detailed-help]
                     [--show {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--hide {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--enable-vcp-code vcp_code] [--system-tray] [--debug] [--warnings] [--syslog]
                     [--location latitude,longitude] [--translations] [--lux-meter]
                     [--no-schedule] [--no-weather] [--no-splash]
                     [--sleep-multiplier multiplier]
                     [--create-config-files] [--install] [--uninstall]

Optional arguments:
-------------------

      -h, --help            show this help message and exit
      --detailed-help       full help in Markdown format
      --about               about vdu_controls
      --show control_name
                            show specified control only (--show may be specified multiple times)
      --hide control_name
                            hide/disable a control (--hide may be specified multiple times)
      --enable-vcp-code vcp_code
                            enable a control for a vcp-code unavailable via hide/show (maybe specified multiple times)
      --system-tray         start up as an entry in the system tray
      --location latitude,longitude
                            local latitude and longitude for triggering presets by solar elevation
      --translations
                            enable language translations
      --no-schedule         disable preset schedule
      --no-weather          disable weather lookups
      --lux-meter           enable hardware light metering
      --debug               enable debug output to stdout
      --warnings            popup a warning when a VDU lacks an enabled control
      --syslog              repeat diagnostic output to the syslog (journald)
      --no-splash           don't show the splash screen
      --sleep-multiplier multiplier
                            protocol reliability multiplier for ddcutil (typically 0.1 .. 2.0, default is 1.0)
      --create-config-files  if they do not exist, create template config INI files in $HOME/.config/vdu_controls/
      --install             installs the vdu_controls in the current user's path and desktop application menu.
      --uninstall           uninstalls the vdu_controls application menu file and script for the current user.

Description
===========

``vdu_controls`` is a virtual control panel for externally connected VDU's.  The application detects
DVI, DP, HDMI, or USB connected VDU's.  It provides controls for settings such as brightness and contrast.

The application interacts with VDU's via the VESA *Display Data Channel* (*DDC*) *Virtual Control Panel*  (*VCP*)
commands set.  DDC VCP interactions are mediated by the ``ddcutil`` command line utility.  ``Ddcutil`` provides
a robust interface that is tolerant of the vagaries of the many OEM DDC implementations.

By default, ``vdu_controls`` offers a subset of controls including brightness, contrast and audio controls.  Additional
controls can be enabled via the ``Settings`` dialog.

``vdu_controls`` may optionally run as an entry in the system tray of KDE, Deepin, GNOME, and Xfce (and possibly
others). The UI attempts to adapt to the quirks of the different tray implementations.

Named ``Preset`` configurations can be saved for later recall. For example, a user could create
presets for night, day, photography, movies, and so forth.  Presets may be automatically triggered
according to solar elevation, and can be further constrained by local weather conditions. Presets can
be set to transition immediately or gradually.  Presets may also be activated by UNIX signals.

The UI's look-and-feel dynamically adjusts to the desktop theme.  Colors and icons automatically
reconfigure without the need for a restart when changing between light and dark themes.

A context menu containing this help is available by pressing the right-mouse button either in the main
control panel or on the system-tray icon.  The context menu is also available via a hamburger-menu item on the
bottom right of the main control panel.

Builtin laptop displays normally don't implement DDC and those displays are not supported, but a laptop's
externally connected VDU's are likely to be controllable.

Some controls change the number of connected devices (for example, some VDU's support a power-off command). If
such controls are used, ``vdu_controls`` will detect the change and will reconfigure the controls
for the new situation (for example, DDC VDU 2 may now be DD VDU 1).  If you change settings independently of
``vdu_controls``, for example, by using a VDU's physical controls,  the ``vdu_controls`` UI includes a refresh
button to force it to assess the new configuration.

Note that some VDU settings may disable or enable other settings. For example, setting a monitor to a specific
picture-profile might result in the contrast-control being disabled, but ``vdu_controls`` will not be aware of
the restriction resulting in its contrast-control erring or appearing to do nothing.

Configuration
=============

Configuration changes can be made via the ``Settings`` dialog or via command line parameters (or by editing the
config-files directly).  The command line provides an immediate way to temporarily alter the behaviour of
the application. The Settings-Dialog and config files provide a more comprehensive and permanent
solution for altering the application's configuration.

Settings Menu and Config files
------------------------------

The right-mouse - context-menu - ``Settings`` accesses the Settings dialog which can be used to
customise the application by writing to a set of config files.  The ``Settings`` dialog features a tab for
editing a config file specific to each VDU.  The config files are named according
to the following scheme:

 - Application wide default config: ``$HOME/.config/vdu_controls/vdu_controls.conf``
 - VDU model and serial number config: ``$HOME/.config/vdu_controls/<model>_<serial|display_num>.conf``
 - VDU model only config: ``$HOME/.config/vdu_controls/<model>.conf``

The application wide default file can be used to alter application settings and the set of default VDU controls.

The VDU-specific config files can be used to:

 - Correct manufacturer built-in metadata.
 - Customise which controls are to be provided for each VDU.
 - Set an optimal ``ddcutil`` DDC communication speed-multiplier for each VDU.

It should be noted that config files can only be used to alter definitions of VCP codes already supported
by ``ddcutil``.  If a VCP code is listed as a *manufacturer specific feature* it is not supported. Manufacturer
specific features should not be experimented with, some may have destructive or irreversible consequences that
may brick the hardware. It is possible to enable any codes by  creating a  ``ddcutil`` user
definition (``--udef``) file, BUT THIS SHOULD ONLY BE USED WITH EXTREME CAUTION AND CANNOT BE RECOMMENDED.

The config files are in INI-format divided into a number of sections as outlined below::

    [vdu-controls-globals]
    # The vdu-controls-globals section is only required in $HOME/.config/vdu_controls/vdu_controls.conf
    system-tray-enabled = yes|no
    splash-screen-enabled = yes|no
    translations-enabled = yes|no
    weather-enabled = yes|no
    schedule-enabled = yes|no
    lux-options-enabled = yes|no
    warnings-enabled = yes|no
    debug-enabled = yes|no
    syslog-enabled = yes|no

    [vdu-controls-widgets]
    # Yes/no for each of the control options that vdu_controls normally provides by default.
    brightness = yes|no
    contrast = yes|no
    audio-volume = yes|no
    audio-mute = yes|no
    audio-treble = yes|no
    audio-bass = yes|no
    audio-mic-volume = yes|no
    input-source = yes|no
    power-mode = yes|no
    osd-language = yes|no

    # Enable ddcutil supported codes not enabled in vdu_controls by default, CSV list of two-digit hex values.
    enable-vcp-codes = NN, NN, NN

    [ddcutil-parameters]
    # Useful values appear to be >=0.1
    sleep-multiplier = 0.5

    [ddcutil-capabilities]
    # The (possibly edited) output from "ddcutil --display N capabilities" with leading spaces retained.
    capabilities-override =

As well as using the ``Settings``, config files may also be created by the command line option::

    vdu_controls --create-config-files

which will create initial templates based on the currently connected VDU's.

The config files are completely optional, they need not be used if the existing command line options are found to be
adequate to the task at hand.

Adding value restrictions to the config file
--------------------------------------------

If a VDU's DDC reported feature minimum and maximum values are incorrect,
the vdu_controls user interface can be restricted to the correct range. For example,
say a VDU reports it supports a brightness range of 0 to 100, but in fact only
practically supports 20 to 90. In such cases, this can be corrected by bringing up
the vdu_controls settings and editing that VDU's **capabilities override**:

 1. locate the feature, in this example the brightness,
 2. add a __Values:__ ***min..max*** specification to line the following the feature definition,
 3. save the changes.

For the brightness example the completed edit would look like::

    Feature: 10 (Brightness)
        Values: 20..80


The vdu_controls slider for that value will now be restricted to the specified range.

Presets
-------

A custom named preset can be used to save the current VDU settings for later recall. Any number of presets can be
created to suit different lighting conditions or different applications, for example: *Night*, *Day*, *Overcast*,
*Sunny*, *Photography*, and *Video*.

Presets can be assigned a name and icon.  If the current monitor settings match a preset, the preset's name will show
in the window-title and tray tooltip, the preset's icon will overlay the normal tray icon.

The ``Presets`` item in right-mouse ``context-menu`` will bring up a ``Presets`` dialog for managing and applying
presets.  The ``context-menu`` also includes a shortcut for applying each existing presets.

Any small SVG or PNG can be assigned as a preset's icon.  Monochrome SVG icons that conform to the Plasma color
conventions will be automatically inverted if the desktop them is changed from dark to light. If a preset lacks
an icon, it will be assigned one created from the letters of its name (the first letter of the first and last words).

Presets may be set to transition immediately (the default); gradually on schedule (solar elevation); or gradually
always (when triggered by schedule, context menu, or UNIX signal).  The speed of transition is determined by
how quickly the VDU's can respond to adjustment (which is generally quite slowly).  During a transition,
the transition will be abandoned if the controls involved in the transition are manually altered, or another
preset is manually invoked.

Each preset is stored in the application config directory as ``$HOME/.config/vdu_controls/Preset_<preset_name>.conf``.
Preset files are saved in INI-file format for ease of editing.  Each preset file contains a section for each connected
VDU, for example::

    [preset]
    icon = /usr/share/icons/breeze/status/16/cloudstatus.svg
    solar-elevation = eastern-sky 40
    transition-type = scheduled
    transition-step-interval-seconds = 5

    [HP_ZR24w_CNT008]
    brightness = 50
    osd-language = 02

    [LG_HDR_4K_89765]
    brightness = 13
    audio-speaker-volume = 16

When the GUI is used to create a preset file, you may select which controls to save.  For example, you
might create a preset that includes the brightness, but not the contrast or audio-volume. Keeping
the included controls to a minimum speeds up the transtion and reduces the chances of the VDU failing
to keep up with the associated stream of DDC commands.

Presets - solar elevation triggers
----------------------------------

A preset may be set to automatically trigger when the sun rises to a specified elevation.
The idea being to allow a preset to trigger relative to dawn or dusk, or when the sun rises
above some surrounding terrain (the time of which will vary as the seasons change).

To assign a trigger, use the Preset Dialog to set a preset's ``solar-elevation``.
A solar elevation may range from -19 degrees in the eastern sky (morning/ascending)
to -19 degrees in the western sky (afternoon/descending), with a maximum nearing
90 degrees at midday.

If a preset has an elevation, it will be triggered each day at a time calculated
by using the latitude and longitude specified by in the ``vdu-controls-globals``
``location`` option.

By choosing an appropriate ``solar-elevation`` a preset may be confined to specific
times of the year.  For example, a preset with a positive solar elevation will
not trigger at mid-winter in the Arctic circle (because the sun never gets that
high).  Such a preset may always be manually selected regardless of its specified
solar elevations.

On any given day, the user may temporarily override any trigger, in which case the
trigger is suspended until the following day.  For example, a user might choose to
disable a trigger intended for the brightest part of the day if the day is particularly
dull,

At startup ``vdu_controls`` will restore the most recent preset that would have been
triggered for this day (if any).  For example, say a user has ``vdu_controls``
set to run at login, and they've also set a preset to trigger at dawn, but
they don't actually log in until just after dawn, the overdue dawn preset will be
triggered at login.

Presets - Smooth Transitions
----------------------------

A preset may be set to ``Transition Smoothly``, in which case changes to controls
slider controls such as brightness and contrast will be stepped by one until the
final values are reached.  Any non-continuous values will be set after all continuous
values have reached their final values.

The Preset Dialog includes controls to set a Preset's transition type to a
combination these values:

    * ``None`` transition, values change immediately;
    * ``On schedule`` according to a solar elevation trigger;
    * ``On signal`` on the appropriate UNIX signal;
    * ``On menu`` when selected in the context-menu;

In the Presets Dialog, the preset activation and edit buttons will activate any
preset immediately regardless of the transition settings.

Normally a transition single-steps the controls as quickly as possible.  In practice
this means each step takes one or more seconds and increases linearly depending on the
number of VDU's and number of controls being altered.  The Presets Dialog includes
a ``Transition Step seconds`` control that can be used to increase the step interval
and extend a transition over a longer period of time.

If any transitioning controls change independently of the transition, the
transition will cease.  In that manner a transition can be abandoned by dragging
a slider or choosing a different preset.

Presets - supplementary weather requirements
--------------------------------------------

A solar elevation trigger can have a weather requirement which will be checked
against the weather reported by https://wttr.in.

By default, there are three possible weather requirements: ``good``,
``bad``, and ``all weather``.  Each  requirement is defined by a
file containing a list of WWO (https://www.worldweatheronline.com) weather
codes, one per line.  The three default requirements are contained in
the files ``$HOME/.config/vdu_controls/{good,bad,all}.weather``.  Additional
weather requirements can be created by using a text editor to create further
files.  The ``all.weather`` file exists primarily as a convenient resource
that lists all possible codes.

Because reported current weather conditions may be inaccurate or out of date,
it's best to use weather requirements as a coarse measure. Going beyond good
and bad may not be very practical.  What's possible might depend on you local
weather conditions.

To ensure ``wttr.in`` supplies the weather for your location, please ensure
that ``Settings`` ``Location`` includes a place-name suffix.  The ``Settings``
``Location`` ``Detect`` button has been enhanced to fill out a place-name for
you.  Should ``wttr.in`` not recognise a place-name, the place-name can be
manually edited to something more suitable. The nearest big city or an
airport-code will do, for example: LHR, LAX, JFK.  You can use a web browser
to test a place-name, for example: https://wttr.in/JFK

When weather requirements are in use, ``vdu_controls`` will check that the
coordinates in ``Settings`` ``Location`` are a reasonable match for
those returned from ``wttr.in``, a warning will be issued if they are more
than 200 km (124 miles) apart.

If the place-name is left blank, the ``wttr.in`` server will try to guess
you location from your external IP address.  The guess may vary due to
the state of the ``wttr.in`` server. It's best to fill out a place-name
to ensure stable results.

Presets - remote control
------------------------

UNIX/Linux signals may be used to instruct a running ``vdu_controls`` to invoke a preset.  This feature is
provided so that scripts, cron or systemd-timer might be used to change the preset based on some measured
condition appropriate for local circumstances.

Signals in the range 40 to 55 correspond to first to last presets (if any are defined).  Additionally, SIGHUP can
be used to initiate "Refresh settings from monitors".  For example:

    Identify the running vdu_controls (assuming it is installed as /usr/bin/vdu_controls)::

        ps axwww | grep '[/]usr/bin/vdu_controls'

    Combine this with kill to trigger a preset change::

        kill -40 $(ps axwww | grep '[/]usr/bin/vdu_controls' | awk '{print $1}')
        kill -41 $(ps axwww | grep '[/]usr/bin/vdu_controls' | awk '{print $1}')

    Or if some other process has changed a monitors settings, trigger vdu_controls to update it's UI::

        kill -HUP $(ps axwww | grep '[/]usr/bin/vdu_controls' | awk '{print $1}')

Any other signals will be handled normally (in many cases they will result in process termination).

Triggers that might be considered include the time of day, the ambient light level, or the prevailing
cloud conditions. For example:

    * Ambient light level as measured by a webcam::

        ffmpeg -y -s 1024x768 -i /dev/video0 -frames 1 $HOME/tmp/out.jpg 1>&2
        ambient=$(convert $HOME/tmp/out.jpg -colorspace gray -resize 1x1 -evaluate-sequence Max -format "%[fx:100*mean]" info:)
        echo $ambient

    * Local cloud conditions from https://github.com/chubin/wttr.in::

        curl 'wttr.in?format=%C'

    * Local time/sunrise/sunset again from wttr.in::

        curl 'wttr.in?format="dawn=%D,dusk=%d,weather=%C"'

Light/Lux Metering
------------------

``vdu_controls`` can a hardware lux metering device to adjust VDU brightness according
to a specified lux/brightness profile.

The Settings Dialog includes an option enable lux metering options.  When enabled, the
Content Menu will include Light Meter option to access a Light-Meter Dialog.
The dialog can be used to define the metering device and the Lux Brightness Response
Profile for each VDU.

The metering device must a readable character device, a UNIX fifo (named-pipe), or a
runnable script.  The character device or fifo must periodically supply one floating point
lux reading per line.  Each line must be terminated by carriage-return newline (character
device) or just newline (fifo/named-pipe). The runnable script will be run each time a
value is needed, it must output a single line containing a lux value.

Possible hardware devices include the GY-30/BH1750 lux meter wired to an Arduino which may
act as a character device.  It may be possible use webcam/camera output to compute an
approximate lux value, ether by analysing image content, or examining image settings that
contribute to exposure such ISO values, apertures, and shutter speed, the result could be
feed to a fifo.

Example scripts for mapping webcam average brightness to approximate lux values are
available in ``/usr/share/vdu_controls/sample-scripts/`` or they can be downloaded
from https://github.com/digitaltrails/vdu_controls/tree/master/sample-scripts.  They
will require customising for your own webcam and lighting conditions.

In creating an "lux meter" for used with vdu_controls, theres is no need to produce
standard lux values.  It is sufficient to produce log10-like values from 1 to 10000
that can be used to create a VDU profile that changes according to your own ambient
conditions.  Metered values need not be continuous, a set of appropriate stepped
values might serve just as well as a continuous measure. Potential step values might
include typical lux values, for example:

    Lighting conditions and lux values::

        sunlight       100000
        daylight        10000
        overcast         1000
        sunrise/sunset    400
        dark-overcast     100
        living-room        50
        night               5

Due to the limitations of DDC protocol, gradual/stepping changes in brightness
are quite likely to noticeable and potentially annoying.  For this reason lux/brightness
profiles define set steps of brightness values so that brightness levels remain constant
over set ranges of lux values.  Achieving an acceptable profile will require some
experimentation with the step lux-thresholds and lux-ranges.

If light-levels are changing frequently and extremely, for example, as the sun passes
behind a succession of clouds, the main panel, context-menu, and light-metering dialog
each contain Manual/Auto controls for disabling/enabling lux metering.  Additionally,
you might tune the lux/brightness profile to eliminate the issue.

Light metering settings and profiles are stored in::

    $HOME/.config/vdu_controls/AutoLux.conf

A typical example follows::

    [lux-meter]
    automatic-brightness = yes
    lux-device = /dev/ttyUSB0
    interval-minutes = 2

    [lux-profile]
    hp_zr24w_cnt008 = [(1, 90), (29, 90), (926, 100), (8414, 100), (100000, 100)]
    lg_hdr_4k_8 = [(1, 13), (60, 25), (100, 50), (299, 70), (1000, 90), (10000, 100), (100000, 100)]

Light/Lux Metering and Presets
-------------------------------

The Light-Meter Dialog includes the ability to set a Preset to trigger at
a lux value.  This feature is accessed by hovering under the bottom axis
of the Lux Profile Chart.

When a Preset is tied to a lux value, the Preset's VDU brightness values become
fixed points on the Lux Profile Chart.  When the specified metered lux value is
achieved, the metered stepping process will restore the Preset's brightness
values and then follow that by triggering the Preset restoration.  This ordering
of events reduces the likelihood of metered-stepping, and Preset-restoration from
clashing.

If a Preset is attached to a lux value and then detached, the Preset's profile
points will be converted to normal (editable) profile points. Attach/detach is
a quick way to copy VDU brightness values from Presets if you don't want to
permanently attach them.

If you utilise light-metered auto-brightness and Preset-scheduling together,
their combined effects may conflict. For example, a scheduled Preset may set a
reduced brightness, but soon after, light-metering might increase it.  If you wish
to use the two together, design your lux/brightness profile steps to match the
brightness levels of specific Presets, for example, a full-sun Preset and the
matching step in a lux/brightness Profile might both be assigned the same brightness
level.

Improving Response Time
-----------------------

DDC/I2C is not the speediest form of communication and VDU's may also be sluggish to respond.  This
means that the responsiveness and smoothness of ``vdu_controls`` is somewhat limited by the underlying
technologies.

If your VDU's are modern, you may find a smaller ``sleep-multiplier`` will speed up the ``ddcutil``/VDU protocol
exchanges making both ``ddcutil`` and ``vdu_controls`` much more responsive.  In a multi-VDU setup where the VDU's
are quite different, individual multipliers can be configured (see previous section).  Reducing the multipliers
will increase the possibility of errors, a bit of experimentation will be required.

The startup-speed is increased by caching each VDU's capabilities and eliminate the need to run ``ddcutil``
to retrieve each VDU's capabilities.  When the `settings-editor` is used to save a VDU's configuration, it
will automatically cache the VDU's capabilities in the ``capabilities-override`` field (as will
the ``--create-config-files`` command line option).

Reducing the number of enabled controls can greatly speed up the initialisation, reduce the time taken when the
refresh button is pressed, and reduce the time taken to restore presets.

Examples
========

    vdu_controls
        All default controls.

    vdu_controls --show brightness --show contrast
        Specified controls only:

    vdu_controls --hide contrast --hide audio-volume
        All default controls except for those to be hidden.

    vdu_controls --system-tray --no-splash --show brightness --show audio-volume
        Start as a system tray entry without showing the splash-screen.

    vdu_controls --create-config-files --system-tray --no-splash --show brightness --show audio-volume
        Create template config files in $HOME/.config/vdu_controls/ that include the other settings.

    vdu_controls --enable-vcp-code 63 --enable-vcp-code 93 --warnings --debug
        All default controls, plus controls for VCP_CODE 63 and 93, show any warnings, output debugging info.

    vdu_controls --sleep-multiplier 0.4
        All default controls, speed up ddcutil-VDU interaction by passing a sleep multiplier.

This script often refers to displays and monitors as VDU's in order to
disambiguate the noun/verb duality of "display" and "monitor"

Prerequisites
=============

Described for OpenSUSE, similar for other distros:

Software::

        zypper install python3 python3-qt5 noto-sans-math-fonts noto-sans-symbols2-fonts
        zypper install ddcutil

Kernel Modules::

        modprobe i2c_dev
        lsmod | grep i2c_dev

Get ddcutil working first. Check that the detect command detects your VDU's without issuing any
errors:

        ddcutil detect

Read ddcutil readme concerning config of i2c_dev with nvidia GPU's. Detailed ddcutil info at https://www.ddcutil.com/

If you wish to use a serial-port lux metering device, the ``pyserial`` module is a runtime requirement.

Environment
===========

    LC_ALL, LANG, LANGUAGE
        These  variables specify the locale for language translations and units
        of distance. LC_ALL is used by python, LANGUAGE is used by Qt.
        Normally, they should all have the same value, for example: ``Da_DK``.
        For these to have any effect on language, ``Settings`` ``Translations Enabled``
        must also be enabled.

    VDU_CONTROLS_IPINFO_URL
        This variable overrides the default ip-address to location service
        URL (``https://ipinfo.io/json``).

    VDU_CONTROLS_WTTR_URL
        This variable overrides default weather service URL (``https://wttr.in``).

    VDU_CONTROLS_WEATHER_KM
        This variable overrides the default maximum permissible spherical
        distance (in kilometres) between the ``Settings`` ``Location``
        and ``wttr.in`` reported location (``200 km``, 124 miles).

    VDU_CONTROLS_DEVELOPER
        This variable changes some search paths to be more convenient in
        a development scenario. (``no`` or yes)

Reporting Bugs
==============
https://github.com/digitaltrails/vdu_controls/issues

GNU License
===========

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/.
"""

# vdu_controls Copyright (C) 2021 Michael Hamilton

from __future__ import annotations

import argparse
import base64
import configparser
import glob
import inspect
import io
import json
import locale
import math
import os
import pathlib
import pickle
import random
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import syslog
import termios
import textwrap
import threading
import time
import traceback
import urllib.request
from ast import literal_eval
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from enum import Enum, IntFlag
from functools import partial
from importlib import import_module
from pathlib import Path
from threading import Lock
from typing import List, Tuple, Mapping, Type, Dict, Callable
from urllib.error import URLError

from PyQt5 import QtNetwork
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QRegExp, QPoint, QObject, QEvent, \
    QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP, QVariant
from PyQt5.QtGui import QPixmap, QIcon, QCursor, QImage, QPainter, QRegExpValidator, \
    QPalette, QGuiApplication, QColor, QValidator, QPen, QFont, QFontMetrics, QMouseEvent, QResizeEvent

from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
    QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction, QMainWindow, QToolBar, QToolButton, QFileDialog, \
    QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter, QSpinBox, QDoubleSpinBox, QInputDialog

APPNAME = "VDU Controls"
VDU_CONTROLS_VERSION = '1.10.0'

WESTERN_SKY = 'western-sky'
EASTERN_SKY = 'eastern-sky'

IP_ADDRESS_INFO_URL = os.getenv('VDU_CONTROLS_IPINFO_URL', default='https://ipinfo.io/json')
WEATHER_FORECAST_URL = os.getenv('VDU_CONTROLS_WTTR_URL', default='https://wttr.in')

TIME_CLOCK_SYMBOL = '\u25F4'  # WHITE CIRCLE WITH UPPER LEFT QUADRANT
WEATHER_RESTRICTION_SYMBOL = '\u2614'  # UMBRELLA WITH RAIN DROPS
TOO_HIGH_SYMBOL = '\u29BB'  # CIRCLE WITH SUPERIMPOSED X
DEGREE_SYMBOL = '\u00B0'  # DEGREE SIGN
SUN_SYMBOL = '\u2600'  # BLACK SUN WITH RAYS
WEST_ELEVATION_SYMBOL = '\u29A9'  # MEASURED ANGLE WITH OPEN ARM ENDING IN ARROW POINTING UP AND RIGHT
EAST_ELEVATION_SYMBOL = '\u29A8'  # MEASURED ANGLE WITH OPEN ARM ENDING IN ARROW POINTING UP AND LEFT
TIMER_RUNNING_SYMBOL = '\u23F3'  # HOURGLASS WITH FLOWING SAND
WEATHER_CANCELLATION_SYMBOL = '\u2744'  # HEAVY CHECK MARK
SKIPPED_SYMBOL = '\u2718'  # HEAVY BALLOT X
SUCCESS_SYMBOL = '\u2714'  # SNOWFLAKE
PRESET_APP_SEPARATOR_SYMBOL = '\u2014'  # EM DASH
MENU_SYMBOL = '\u2630'  # TRIGRAM FOR HEAVEN - hamburger menu
TRANSITION_SYMBOL = '\u25b9'  # WHITE RIGHT POINTING SMALL TRIANGLE
TRANSITION_ALWAYS_SYMBOL = '\u25b8\u2732'  # BLACK RIGHT POINTING SMALL TRIANGLE + OPEN CENTER ASTERIX
SIGNAL_SYMBOL = '\u26a1'  # HIGH VOLTAGE - lightning bolt

SolarElevationKey = namedtuple('SolarElevationKey', ['direction', 'elevation'])
SolarElevationData = namedtuple('SolarElevationData', ['azimuth', 'zenith', 'when'])

gui_thread: QThread | None = None


def is_running_in_gui_thread():
    return QThread.currentThread() == gui_thread


def zoned_now() -> datetime:
    return datetime.now().astimezone()


def format_solar_elevation_abbreviation(elevation: SolarElevationKey) -> str:
    direction_char = EAST_ELEVATION_SYMBOL if elevation.direction == EASTERN_SKY else WEST_ELEVATION_SYMBOL
    return f"{SUN_SYMBOL} {direction_char} {elevation.elevation}{DEGREE_SYMBOL}"


def format_solar_elevation_description(elevation: SolarElevationKey) -> str:
    # Note - repeating the constants here to force them to be included by pylupdate5 internationalisation
    direction_text = tr('eastern-sky') if elevation.direction == EASTERN_SKY else tr('western-sky')
    return f"{direction_text} {elevation.elevation}{DEGREE_SYMBOL}"


def format_solar_elevation_ini_text(elevation: SolarElevationKey | None):
    return f"{elevation.direction} {elevation.elevation}" if elevation is not None else ''


def parse_solar_elevation_ini_text(ini_text: str):
    parts = ini_text.strip().split(' ')
    if len(parts) != 2:
        raise ValueError(f"Invalid SolarElevation: '{ini_text}'")
    if parts[0] not in [EASTERN_SKY, WESTERN_SKY]:
        raise ValueError(f"Invalid value for  SolarElevation direction: '{parts[0]}'")
    solar_elevation = SolarElevationKey(parts[0], int(parts[1]))
    return solar_elevation


def proper_name(*args):
    return re.sub(r'[^A-Za-z0-9._-]', '_', '_'.join([arg.strip() for arg in args]))


def tr(source_text: str, disambiguation: str | None = None):
    """
    This function is named tr() so that it matches what pylupdate5 is looking for.
    If this method is ever renamed to something other than tr(), then you must
    pass -ts-function=new_name to pylupdate5.

    For future internationalization:
    1) Generate template file from this code, for example for French:
       ALWAYS BACKUP THE CURRENT .ts FILE BEFORE RUNNING AN UPDATE - it can go wrong!
           pylupdate5 vdu_controls.py -ts translations/fr_FR.ts
       where translations is a subdirectory of your current working directory.
    2) Edit that using a text editor or the linguist-qt5 utility.
       If using an editor, remove the 'type="unfinished"' as you complete each entry.
    3) Convert the .ts to a binary .qm file
           lrelease-qt5 translations/fr_FR.ts
           mkdir -p $HOME/.config/vdu_controls/translations/
           translations/fr_FR.qm $HOME/.config/vdu_controls/translations/
    4) Test using by setting LC_ALL for python and LANGUAGE for Qt
           LC_ALL=fr_FR LANGUAGE=fr_FR python3 vdu_controls.py
       At startup the app will log several messages as it searches for translation files.
    5) Completed .qm files can reside in $HOME/.config/vdu_controls/translations/
       or  /user/share/vdu_controls/translations/
    """
    # If the source .ts file is newer, we load messages from the XML into ts_translations
    # and use the most recent translations. Using the .ts files in production may be a good
    # way to allow the users to help themselves.
    if ts_translations:
        if source_text in ts_translations:
            return ts_translations[source_text]
    # the context @default is what is generated by pylupdate5 by default
    return QCoreApplication.translate('@default', source_text, disambiguation=disambiguation)


def translate_option(option_text):
    # We can't be sure of the case in capability descriptions retrieved from the monitors.
    # If there is no direct translation, we try canonical version of the name (all lowercase
    # with '-' replaced with ' ').
    result = tr(option_text)
    if result != option_text:
        # Probably a command line option
        return result.replace('-', ' ')
    canonical = option_text.lower().replace('-', ' ')
    result = tr(canonical)
    return result


ABOUT_TEXT = f"""

<b>vdu_controls version {VDU_CONTROLS_VERSION}</b>
<p>
A virtual control panel for external Visual Display Units.
<p>
Visit <a href="https://github.com/digitaltrails/vdu_controls">https://github.com/digitaltrails/vdu_controls</a> for
more details.
<p>
Release notes: <a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VDU_CONTROLS_VERSION}">
v{VDU_CONTROLS_VERSION}.</a>
<p>
<hr>
<small>
<b>vdu_controls Copyright (C) 2021 Michael Hamilton</b>
<br><br>
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.
<br><br>

<bold>
This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.
</bold>
<br><br>
You should have received a copy of the GNU General Public License along
with this program. If not, see <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.
</small>
<hr>
<p><p>
<quote>
<small>
Vdu_controls relies on <a href="https://www.ddcutil.com/">ddcutil</a>, a robust interface to DDC capable VDU's.
<br>
At your request, your geographic location may be retrieved from <a href="{IP_ADDRESS_INFO_URL}">{IP_ADDRESS_INFO_URL}</a>.
<br>
At your request, weather for your location may be retrieved from <a href="{WEATHER_FORECAST_URL}">{WEATHER_FORECAST_URL}</a>.
</small>
</quote>
"""

RELEASE_ANNOUNCEMENT = """
<h3>{WELCOME}</h3>

{NOTE}<br>
<a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}">
https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}</a>
<hr>
"""

# Use Linux/UNIX signals for interprocess communication to trigger preset changes - 16 presets should be enough
# for anyone.
PRESET_SIGNAL_MIN = 40
PRESET_SIGNAL_MAX = 55

signal_wakeup_handler: Callable | None = None

# On Plasma Wayland the system tray may not be immediately available at login - so keep trying for...
SYSTEM_TRAY_WAIT_SECONDS = 20

SVG_LIGHT_THEME_COLOR = b"#232629"
SVG_DARK_THEME_COLOR = b"#f3f3f3"

BRIGHTNESS_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <style id="current-color-scheme" type="text/css">
        .ColorScheme-Text { color:#232629; }
    </style>
  </defs>
  <g transform="translate(1,1)">
    <g shape-rendering="auto">
      <path d="m11 7c-2.2032167 0-4 1.7967833-4 4 0 2.203217 1.7967833 4 4 4 2.203217 0 4-1.796783 4-4 0-2.2032167-1.796783-4-4-4zm0 1c1.662777 0 3 1.3372234 3 3 0 1.662777-1.337223 3-3 3-1.6627766 0-3-1.337223-3-3 0-1.6627766 1.3372234-3 3-3z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m10.5 3v3h1v-3h-1z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m10.5 16v3h1v-3h-1z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m3 10.5v1h3v-1h-3z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m16 10.5v1h3v-1h-3z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m14.707031 14-0.707031 0.707031 2.121094 2.121094 0.707031-0.707031-2.121094-2.121094z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="M 5.7070312 5 L 5 5.7070312 L 7.1210938 7.828125 L 7.828125 7.1210938 L 5.7070312 5 z " class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="M 7.1210938 14 L 5 16.121094 L 5.7070312 16.828125 L 7.828125 14.707031 L 7.1210938 14 z " class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="M 16.121094 5 L 14 7.1210938 L 14.707031 7.828125 L 16.828125 5.7070312 L 16.121094 5 z " class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <g>
        <path d="m11.000001 7.7500005v6.4999985h2.166665l1.083333-2.166666v-2.1666663l-1.083333-2.1666662z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
        <path d="m10.984375 7.734375v0.015625 6.515625h2.191406l1.089844-2.177734v-2.1757816l-1.089844-2.1777344h-2.191406zm0.03125 0.03125h2.140625l1.078125 2.1542969v2.1601561l-1.078125 2.154297h-2.140625v-6.46875z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      </g>
    </g>
  </g>
</svg>
"""

CONTRAST_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <style type="text/css" id="current-color-scheme">
      .ColorScheme-Text { color:#232629; }
    </style>
  </defs>
  <g transform="translate(1,1)">
    <path style="fill:currentColor;fill-opacity:1;stroke:none" transform="translate(-1,-1)" d="m 12,7 c -2.761424,0 -5,2.2386 -5,5 0,2.7614 2.238576,5 5,5 2.761424,0 5,-2.2386 5,-5 0,-2.7614 -2.238576,-5 -5,-5 z m 0,1 v 8 C 9.790861,16 8,14.2091 8,12 8,9.7909 9.790861,8 12,8" class="ColorScheme-Text" id="path79" />
  </g>
</svg>
"""

AUTO_LUX_ON_SVG = BRIGHTNESS_SVG.replace(b'viewBox="0 0 24 24"', b'viewBox="3 3 18 18"').replace(b'#232629', b'#ff8500')
AUTO_LUX_OFF_SVG = BRIGHTNESS_SVG.replace(b'viewBox="0 0 24 24"', b'viewBox="3 3 18 18"').replace(b'#232629', b'#84888c')

COLOR_TEMPERATURE_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
  <defs>
    <clipPath>
      <path d="m7 1023.36h1v1h-1z" style="fill:#f2f2f2"/>
    </clipPath>
  </defs>
  <g transform="translate(1,1)">
    <path d="m11.5 9c-1.213861 0-2.219022.855928-2.449219 2h-6.05078v1h6.05078c.230197 1.144072 1.235358 2 2.449219 2 1.213861 0 2.219022-.855928 2.449219-2h5.05078v-1h-5.05078c-.230197-1.144072-1.235358-2-2.449219-2" style="fill:#2ecc71"/>
    <path d="m5.5 14c-1.385 0-2.5 1.115-2.5 2.5 0 1.385 1.115 2.5 2.5 2.5 1.21386 0 2.219022-.855928 2.449219-2h11.05078v-1h-11.05078c-.230196-1.144072-1.235358-2-2.449219-2m0 1c.831 0 1.5.669 1.5 1.5 0 .831-.669 1.5-1.5 1.5-.831 0-1.5-.669-1.5-1.5 0-.831.669-1.5 1.5-1.5" style="fill:#1d99f3"/>
    <path d="m14.5 3c-1.21386 0-2.219022.855928-2.449219 2h-9.05078v1h9.05078c.230197 1.144072 1.235359 2 2.449219 2 1.21386 0 2.219022-.855928 2.449219-2h2.050781v-1h-2.050781c-.230197-1.144072-1.235359-2-2.449219-2m0 1c.831 0 1.5.669 1.5 1.5 0 .831-.669 1.5-1.5 1.5-.831 0-1.5-.669-1.5-1.5 0-.831.669-1.5 1.5-1.5" style="fill:#da4453"/>
  </g>
</svg>
"""

VOLUME_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-7 -7 40 40" width="24" height="24">
  <style id="current-color-scheme" type="text/css">
        .ColorScheme-Text { color:#232629; }
    </style>
  <g transform="translate(1,1)">
    <g class="ColorScheme-Text" fill="currentColor">
      <path d="m14.324219 7.28125-.539063.8613281a4 4 0 0 1 1.214844 2.8574219 4 4 0 0 1 -1.210938 2.861328l.539063.863281a5 5 0 0 0 1.671875-3.724609 5 5 0 0 0 -1.675781-3.71875z"/>
      <path d="m13.865234 3.5371094-.24414.9765625a7 7 0 0 1 4.378906 6.4863281 7 7 0 0 1 -4.380859 6.478516l.24414.974609a8 8 0 0 0 5.136719-7.453125 8 8 0 0 0 -5.134766-7.4628906z"/>
      <path d="m3 8h2v6h-2z" fill-rule="evenodd"/>
      <path d="m6 14 5 5h1v-16h-1l-5 5z"/>
    </g>
  </g>
</svg>
"""

MENU_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <defs id="defs3051">
    <style type="text/css" id="current-color-scheme">
      .ColorScheme-Text {
        color:#232629;
      }
      </style>
  </defs>
  <g transform="translate(1,1)">
    <path style="fill:currentColor;fill-opacity:1;stroke:none" d="m3 5v2h16v-2h-16m0 5v2h16v-2h-16m0 5v2h16v-2h-16" class="ColorScheme-Text"/>
  </g>
</svg>
"""

REFRESH_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <style type="text/css" id="current-color-scheme">.ColorScheme-Text {
        color:#232629;
      }</style>
  </defs>
  <g transform="translate(1,1)">
    <path class="ColorScheme-Text" fill="currentColor" d="m 19,11 c 0,1.441714 -0.382922,2.789289 -1.044922,3.955078 l -0.738281,-0.738281 c 0,0 0.002,-0.0019 0.002,-0.0019 l -2.777344,-2.779297 0.707032,-0.707031 2.480468,2.482422 C 17.861583,12.515315 18,11.776088 18,11 18,7.12203 14.878,4 11,4 9.8375,4 8.746103,4.285828 7.783203,4.783203 L 7.044922,4.044922 C 8.210722,3.382871 9.5583,3 11,3 c 4.432,0 8,3.568034 8,8 z m -4.044922,6.955078 C 13.789278,18.617129 12.4417,19 11,19 6.568,19 3,15.431966 3,11 3,9.558286 3.382922,8.210711 4.044922,7.044922 l 0.683594,0.683594 0.002,-0.002 2.828125,2.828126 L 6.851609,11.261673 4.373094,8.783157 C 4.139126,9.480503 4,10.221736 4,11 c 0,3.87797 3.122,7 7,7 1.1625,0 2.253897,-0.285829 3.216797,-0.783203 z"/>
  </g>
</svg>
"""

TRANSITION_ICON_SOURCE = b"""
<svg  xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <rect width="10" height="10" rx="4" x="6" y="6" stroke="black" stroke-width="1" fill="#80ff00" />
</svg>
"""

SWATCH_ICON_SOURCE = b"""
<svg  xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <rect width="20" height="20" rx="4" x="2" y="3" stroke="black" stroke-width="1" fill="#ffffff" />
</svg>
"""

'''Creates a SVG of grey rectangles typical of the sort used for VDU calibration.'''
GREY_SCALE_SVG = f'''
<svg xmlns="http://www.w3.org/2000/svg" version="1.1"  width="256" height="152" viewBox="0 0 256 152">
    <rect width="256" height="152" x="0" y="0" style="fill:rgb(128,128,128);stroke-width:0;" />
    {"".join(
    [f'<rect width="16" height="32" x="{x}" y="38" style="fill:rgb({v},{v},{v});stroke-width:0;" />'
     for x, v in list(zip([x + 48 for x in range(0, 160, 16)], [v for v in range(0, 120, 12)]))]
)}
    {"".join(
    [f'<rect width="16" height="32" x="{x}" y="80" style="fill:rgb({v},{v},{v});stroke-width:0;" />'
     for x, v in list(zip([x + 48 for x in range(0, 160, 16)], [v for v in range(147, 256, 12)]))]
)}
</svg>
'''.encode()

#: A high resolution image, will fall back to an internal SVG if this file isn't found on the local system
DEFAULT_SPLASH_PNG = "/usr/share/icons/hicolor/256x256/apps/vdu_controls.png"

#: Assuming ddcutil is somewhere on the PATH.
DDCUTIL = "ddcutil"

#: Internal special exit code used to signal that the exit handler should restart the program.
EXIT_CODE_FOR_RESTART = 1959

# Number of times to retry getting attributes - in case a monitor is slow after being powered up.
GET_ATTRIBUTES_RETRIES = 3

# All kinds of startup slowness may cause problems - how many times to wait and retry
SLIDER_REFRESH_RETRIES = 4

DANGER_AGREEMENT_NON_STANDARD_VCP_CODES = """
If you are attempting to enable non-standard VCP-codes for write, you must read and
consider this notice before proceeding any further.

Enabling ddcutil for VCP-codes not in the Display Data Channel (DDC) Virtual Control
Panel (VCP) standard may result in irreversible damage to any connected monitors and
any devices they are connected to (including the driving PC).  Before enabling
non-standard codes one should consider that these codes may need to be operated
in conjunction with other settings or codes. One should also be mindful that some
settings or combinations of settings may cause physical effects including and not
limited to overheating, screen-burn-in, shortened backlight lifetime, and cease
of function (bricking).

It is your responsibility to assess and ensure the safety and wisdom of enabling
unsupported VCP codes and your responsibility for dealing with the consequences.

Note that this software is licenced under the GPL Version 3 WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE.
"""
ASSUMED_CONTROLS_CONFIG_VCP_CODES = ['10', '12']
ASSUMED_CONTROLS_CONFIG_TEXT = ('\n'
                                'capabilities-override = Model: unknown\n'
                                '	MCCS version: 2.2\n'
                                '	Commands:\n'
                                '       Command: 01 (VCP Request)\n'
                                '       Command: 02 (VCP Response)\n'
                                '       Command: 03 (VCP Set)\n'
                                '	VCP Features:\n'
                                '	   Feature: 10 (Brightness)\n'
                                '	   Feature: 12 (Contrast)\n'
                                '	   Feature: 60 (Input Source)')


def is_dark_theme():
    # Heuristic for checking for a dark theme.
    # Is the sample text lighter than the background?
    label = QLabel("am I in the dark?")
    text_hsv_value = label.palette().color(QPalette.WindowText).value()
    bg_hsv_value = label.palette().color(QPalette.Background).value()
    dark_theme_found = text_hsv_value > bg_hsv_value
    # debug(f"is_dark_them text={text_hsv_value} bg={bg_hsv_value} is_dark={dark_theme_found}") if debugging else None
    return dark_theme_found


def get_splash_image() -> QPixmap:
    """Get the splash pixmap from the installed png, failing that, the internal splash png."""
    pixmap = QPixmap()
    if os.path.isfile(DEFAULT_SPLASH_PNG) and os.access(DEFAULT_SPLASH_PNG, os.R_OK):
        pixmap.load(DEFAULT_SPLASH_PNG)
    else:
        pixmap.loadFromData(base64.decodebytes(FALLBACK_SPLASH_PNG_BASE64), 'PNG')
    return pixmap


def clamp(v, min_v, max_v):
    return max(min(max_v, v), min_v)


#: Could be a str enumeration of VCP types
CONTINUOUS_TYPE = 'C'
SIMPLE_NON_CONTINUOUS_TYPE = 'SNC'
COMPLEX_NON_CONTINUOUS_TYPE = 'CNC'
# The GUI treats SNC and CNC the same - only DdcUtil needs to distinguish them.
GUI_NON_CONTINUOUS_TYPE = SIMPLE_NON_CONTINUOUS_TYPE

log_to_syslog = False
log_debug_enabled = False


def log_wrapper(severity, *args):
    prefix = {syslog.LOG_INFO: "INFO:", syslog.LOG_ERR: "ERROR:",
              syslog.LOG_WARNING: "WARNING:", syslog.LOG_DEBUG: "DEBUG:"}[severity]
    with io.StringIO() as output:
        print(*args, file=output, end='')
        message = output.getvalue()
        print(prefix, message)
        if log_to_syslog:
            syslog_message = prefix + " " + message if severity == syslog.LOG_DEBUG else message
            syslog.syslog(severity, syslog_message)


def log_debug(*args):
    if log_debug_enabled:
        log_wrapper(syslog.LOG_DEBUG, *args)


def log_info(*args):
    log_wrapper(syslog.LOG_INFO, *args)


def log_warning(*args):
    log_wrapper(syslog.LOG_WARNING, *args)


def log_error(*args):
    log_wrapper(syslog.LOG_ERR, *args)


class VcpCapability:
    """Representation of a VCP (Virtual Control Panel) capability for a VDU."""

    def __init__(self, vcp_code: str, vcp_name: str, vcp_type: str, values: List | None = None,
                 causes_config_change: bool = False, icon_source: bytes | None = None, enabled: bool = False,
                 can_transition: bool = False):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.vcp_type = vcp_type
        self.icon_source = icon_source
        self.causes_config_change = causes_config_change
        # Default config enablement
        self.enabled = enabled
        self.can_transition = can_transition
        # For future use if we want to implement non-continuous types of VCP (VCP types SNC or CNC)
        self.values = [] if values is None else values

    def property_name(self) -> str:
        return re.sub('[^A-Za-z0-9_-]', '-', self.name).lower()


class DdcUtilDisplayNotFound(Exception):
    pass


class DdcUtil:
    """
    Interface to the command line ddcutil Display Data Channel Utility for interacting with VDU's.
    The exception callback can return True if we should retry after errors (after the callback takes
    corrective action such as increasing the sleep_multiplier).
    """

    def __init__(self, debug: bool = False, common_args=None, default_sleep_multiplier: float = 1.0) -> None:
        super().__init__()
        self.debug = debug
        self.supported_codes: Dict[str, str] | None = None
        self.default_sleep_multiplier = default_sleep_multiplier
        self.common_args = [] if common_args is None else common_args
        self.vcp_type_map: Dict[str, str] = {}
        self.use_edid = os.getenv('VDU_CONTROLS_USE_EDID', default="yes") == 'yes'
        log_info(f"Use_edid={self.use_edid} (to disable it: export VDU_CONTROLS_USE_EDID=no)")
        self.edid_map: Dict[str, str] = {}
        self.lock = Lock()

    def change_settings(self, debug: bool, default_sleep_multiplier: float):
        self.debug = debug
        self.default_sleep_multiplier = default_sleep_multiplier

    def id_key_args(self, display_id: str) -> List[str]:
        if display_id in self.edid_map:
            return ['--edid', self.edid_map[display_id]]
        return ['--display', display_id]

    def __run__(self, *args, sleep_multiplier: float | None = None) -> subprocess.CompletedProcess:
        with self.lock:
            multiplier = self.default_sleep_multiplier if sleep_multiplier is None else sleep_multiplier
            multiplier_args = ['--sleep-multiplier', str(multiplier)] if multiplier > 0.01 else ['--dsa2']
            process_args = [DDCUTIL] + multiplier_args + self.common_args + list(args)
            try:
                result = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                if self.debug:  # Shorten EDID to 30 characters when logging it (it will be the only long argument)
                    log_debug("subprocess result: ", [arg if len(arg) < 30 else arg[:30] + "..." for arg in result.args],
                              f"rc={result.returncode}", f"stdout={result.stdout}")
            except subprocess.SubprocessError as spe:
                if spe.stderr.decode('utf-8').lower().find("display not found") >= 0:
                    raise DdcUtilDisplayNotFound(' '.join(args))
                log_error("subprocess result: ", [arg if len(arg) < 30 else arg[:30] + "..." for arg in process_args],
                          f"exception={spe}")
                raise
            return result

    def detect_monitors(self, issue_warnings: bool = True) -> List[Tuple[str, str, str, str]]:
        """Return a list of (vdu_id, desc) tuples."""
        display_list = []
        result = self.__run__('detect', '--verbose')
        # Going to get rid of anything that is not a-z A-Z 0-9 as potential rubbish
        rubbish = re.compile('[^a-zA-Z0-9]+')
        # This isn't efficient, it doesn't need to be, so I'm keeping re-defs close to where they are used.
        key_prospects: Dict[Tuple[str, str], Tuple[str, str]] = {}
        for display_str in re.split("\n\n", result.stdout.decode('utf-8')):
            display_match = re.search(r'Display ([0-9]+)', display_str)
            if display_match is not None:
                vdu_id = display_match.group(1)
                log_debug(f"checking possible ID's for display {vdu_id}") if log_debug_enabled else None
                fields = {fm.group(1).strip(): fm.group(2).strip() for fm in re.finditer(r'[ \t]*([^:\n]+):[ \t]+([^\n]*)',
                                                                                         display_str)}
                model_name = rubbish.sub('_', fields.get('Model', 'unknown_model'))
                manufacturer = rubbish.sub('_', fields.get('Mfg id', 'unknown_mfg'))
                serial_number = rubbish.sub('_', fields.get('Serial number', ''))
                bin_serial_number = rubbish.sub('_', fields.get('Binary serial number', '').split('(')[0].strip())
                man_date = rubbish.sub('_', fields.get('Manufacture year', ''))
                i2c_bus_id = fields.get('I2C bus', '').replace("/dev/", '').replace("-", "_")
                if self.use_edid:
                    edid = self.parse_edid(display_str)
                    # check for duplicate edid, any duplicate will use the display Num
                    if edid is not None and edid not in self.edid_map.values():
                        self.edid_map[vdu_id] = edid
                for candidate in serial_number, bin_serial_number, man_date, i2c_bus_id, f"DisplayNum{vdu_id}":
                    if candidate.strip() != '':
                        possibly_unique = (model_name, candidate)
                        if possibly_unique in key_prospects:
                            # Not unique - it's already been encountered.
                            log_info(f"Ignoring non-unique key {possibly_unique[0]}_{possibly_unique[1]}"
                                     f" - it matches displays {vdu_id} and {key_prospects[possibly_unique][0]}")
                            del key_prospects[possibly_unique]
                        else:
                            # log_debug(possibly_unique)
                            key_prospects[possibly_unique] = vdu_id, manufacturer
            elif len(display_str.strip()) != 0 and issue_warnings:
                if display_str.startswith('Invalid display'):
                    log_warning(f"Ignoring one display (probably switched off)")
                else:
                    log_warning(f"Ignoring unparsable: id='{display_str}'")

        # Try and pin down a unique id that won't change even if other monitors are turned off.
        # Ideally this should yield the same result for the same monitor - DisplayNum is the worst
        # for that, so it's the fallback.
        key_already_assigned = {}
        for model_and_main_id, vdu_id_and_manufacturer in key_prospects.items():
            vdu_id, manufacturer = vdu_id_and_manufacturer
            if vdu_id not in key_already_assigned:
                model_name, main_id = model_and_main_id
                log_debug(
                    f"Unique key for display={vdu_id} mfg={manufacturer} is (model={model_name} id={main_id})") if log_debug_enabled else None
                display_list.append((vdu_id, manufacturer, model_name, main_id))
                key_already_assigned[vdu_id] = 1

        # For testing bad VDU's:
        # display_list.append(("3", "maker_y", "model_z", "1234"))
        return display_list

    def parse_edid(self, display_str: str) -> str | None:
        edid_match = re.search(r'EDID hex dump:\n[^\n]+(\n([ \t]+[+]0).+)+', display_str)
        if edid_match:
            edid = "".join(re.findall('((?: [0-9a-f][0-9a-f]){16})', edid_match.group(0))).replace(' ', '')
            log_info(f"EDID={edid}") if self.debug else None
            return edid
        return None

    def query_capabilities(self, vdu_id: str) -> str:
        """Return a vpc capabilities string."""
        result = self.__run__(*['capabilities'] + self.id_key_args(vdu_id))
        capability_text = result.stdout.decode('utf-8')
        return capability_text

    def get_type(self, vcp_code):
        return self.vcp_type_map[vcp_code] if vcp_code in self.vcp_type_map else None

    def get_attribute(self, vdu_id: str, vcp_code: str, sleep_multiplier: float | None = None) -> Tuple[str, str]:
        """
        Given a VDU id and vcp_code, retrieve the attribute's current value from the VDU.

        Two values are returned, the monitor reported current value, and the monitor reported maximum value. Only
        attributes with "Continuous" values have a maximum, for consistency the method will return a zero maximum
        for "Non-Continuous" attributes.
        """
        result = self.get_attributes(vdu_id, [vcp_code], sleep_multiplier=sleep_multiplier)
        if result is not None:
            return result[0]
        raise ValueError(
            f"ddcutil returned an invalid value for monitor {vdu_id} vcp_code {vcp_code}, try increasing --sleep-multiplier")

    def set_attribute(self, vdu_id: str, vcp_code: str, new_value: str, sleep_multiplier: float | None = None) -> None:
        """Send a new value to a specific VDU and vcp_code."""
        if self.get_type(vcp_code) == COMPLEX_NON_CONTINUOUS_TYPE:
            new_value = 'x' + new_value
        self.__run__(*['setvcp', vcp_code, new_value] + self.id_key_args(vdu_id), sleep_multiplier=sleep_multiplier)

    def vcp_info(self) -> str:
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return self.__run__('--verbose', 'vcpinfo').stdout.decode('utf-8')

    def get_supported_vcp_codes(self) -> Dict[str, str]:
        """Returns a map of descriptions keyed by vcp_code, the codes that ddcutil appears to support."""
        if self.supported_codes is not None:
            return self.supported_codes
        self.supported_codes = {}
        info = DdcUtil().vcp_info()
        code_definitions = info.split("\nVCP code ")
        for code_def in code_definitions[1:]:
            lines = code_def.split('\n')
            vcp_code, vcp_name = lines[0].split(': ', 1)
            ddcutil_feature_subsets = None
            for line in lines[2:]:
                line = line.strip()
                if line.startswith('ddcutil feature subsets:'):
                    ddcutil_feature_subsets = line.split(": ", 1)
            if ddcutil_feature_subsets is not None:
                if vcp_code not in self.supported_codes:
                    self.supported_codes[vcp_code] = vcp_name
        return self.supported_codes

    def get_attributes(self,
                       vdu_id: str,
                       vcp_code_list: List[str],
                       sleep_multiplier: float | None = None) -> List[Tuple[str, str]] | None:
        """
        Returns None if there is an error communicating with the VDU
        """
        # Try a few times in case there is a glitch due to a monitor being turned-off/on or slow to respond
        # Should we loop here, or higher up - maybe it doesn't matter.
        vcp_code_regexp = re.compile(r"^VCP ([0-9A-F]{2}) ")  # VCP 2-digit-hex
        for i in range(GET_ATTRIBUTES_RETRIES):
            args = ['--brief', 'getvcp'] + vcp_code_list + self.id_key_args(vdu_id)
            try:
                from_ddcutil = self.__run__(*args, sleep_multiplier=sleep_multiplier)
                unordered_results: Dict[str, str] = {}
                for line in from_ddcutil.stdout.split(b"\n"):
                    line_utf8 = line.decode('utf-8') + '\n'
                    vcp_code_match = vcp_code_regexp.match(line_utf8)
                    if vcp_code_match is not None:
                        unordered_results[vcp_code_match.group(1)] = line_utf8
                # Order results into vcp_code_list order:
                result_list: List[Tuple[str, str]] = []
                for vcp_code in vcp_code_list:
                    if vcp_code not in unordered_results:
                        log_warning(f"getvcp '{vcp_code}' missing result, try {i + 1}, will try again.")
                        continue
                    value_max_pair: Tuple[str, str] | None = self.__parse_value(vdu_id, vcp_code, unordered_results[vcp_code])
                    if value_max_pair is None:
                        log_warning(
                            f"getvcp '{vcp_code}' parse failed '{unordered_results[vcp_code]}', try {i + 1}, will try again.")
                        continue
                    result_list.append(value_max_pair)
                return result_list
            except subprocess.SubprocessError as e:
                # log_warning("Subprocess error: ", args, str(e))  # duplicates existing logging
                if i + 1 == GET_ATTRIBUTES_RETRIES:
                    raise  # Too many failures, pass the buck upstairs
            log_warning(f"ddcutil maybe running too fast for monitor {vdu_id}, try increasing --sleep-multiplier.")
            time.sleep(2)
        return None

    def __parse_value(self, vdu_id: str, vcp_code: str, result: str) -> Tuple[str, str] | None:
        value_pattern = re.compile(r'VCP ' + vcp_code + r' ([A-Z]+) (.+)\n')
        c_pattern = re.compile(r'([0-9]+) ([0-9]+)')
        snc_pattern = re.compile(r'x([0-9a-f]+)')
        cnc_pattern = re.compile(r'x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+)')
        value_match = value_pattern.match(result)
        if value_match is not None:
            type_indicator = value_match.group(1)
            self.vcp_type_map[vcp_code] = type_indicator
            if type_indicator == CONTINUOUS_TYPE:
                c_match = c_pattern.match(value_match.group(2))
                if c_match is not None:
                    return c_match.group(1), c_match.group(2)
            elif type_indicator == SIMPLE_NON_CONTINUOUS_TYPE:
                snc_match = snc_pattern.match(value_match.group(2))
                if snc_match is not None:
                    return snc_match.group(1), '0'
            elif type_indicator == COMPLEX_NON_CONTINUOUS_TYPE:
                cnc_match = cnc_pattern.match(value_match.group(2))
                if cnc_match is not None:
                    return '{:02x}'.format(int(cnc_match.group(3), 16) << 8 | int(cnc_match.group(4), 16)), '0'
            else:
                raise TypeError(f'Unsupported VCP type {type_indicator} for monitor {vdu_id} vcp_code {vcp_code}')
        return None


def si(widget: QWidget, icon_number: QStyle.StandardPixmap):
    return widget.style().standardIcon(icon_number)


class DialogSingletonMixin:
    """
    A mixin that can augment a QDialog or QMessageBox with code to enforce a singleton UI.
    For example, it is used so that only ones settings editor can be active at a time.
    """
    _dialogs_map: Dict[str, DialogSingletonMixin] = {}
    debug = False

    def __init__(self) -> None:
        """Registers the concrete class as a singleton, so it can be reused later."""
        super().__init__()
        class_name = self.__class__.__name__
        if class_name in DialogSingletonMixin._dialogs_map:
            raise TypeError(f"ERROR: More than one instance of {class_name} cannot exist.")
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog created for {class_name}')
        DialogSingletonMixin._dialogs_map[class_name] = self

    def closeEvent(self, event) -> None:
        """Subclasses that implement their own closeEvent must call this closeEvent to deregister the singleton"""
        class_name = self.__class__.__name__
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog remove {class_name} '
                      f'registered={class_name in DialogSingletonMixin._dialogs_map}')
        if class_name in DialogSingletonMixin._dialogs_map:
            del DialogSingletonMixin._dialogs_map[class_name]
        event.accept()

    def make_visible(self):
        """ If the dialog exists(), call this to make it visible by raising it.
        Internal, used by the class method show_existing_dialog()"""
        self.show()
        self.raise_()
        self.activateWindow()

    @classmethod
    def show_existing_dialog(cls: Type):
        """If the dialog exists(), call this to make it visible by raising it."""
        class_name = cls.__name__
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog show existing {class_name}')
        instance = DialogSingletonMixin._dialogs_map[class_name]
        instance.make_visible()

    @classmethod
    def exists(cls: Type) -> bool:
        """Returns true if the dialog has already been created."""
        class_name = cls.__name__
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog exists {class_name} {class_name in DialogSingletonMixin._dialogs_map}')
        return class_name in DialogSingletonMixin._dialogs_map

    @classmethod
    def get_instance(cls: Type):
        class_name = cls.__name__
        if class_name in DialogSingletonMixin._dialogs_map:
            return DialogSingletonMixin._dialogs_map[class_name]
        return None


class VduGuiSupportedControls:
    """Maps of controls supported by name on the command line and in config files."""
    by_code = {
        '10': VcpCapability('10', QT_TR_NOOP('brightness'), 'C', icon_source=BRIGHTNESS_SVG, enabled=True, can_transition=True),
        '12': VcpCapability('12', QT_TR_NOOP('contrast'), 'C', icon_source=CONTRAST_SVG, enabled=True, can_transition=True),
        '62': VcpCapability('62', QT_TR_NOOP('audio volume'), 'C', icon_source=VOLUME_SVG, can_transition=True),
        '8D': VcpCapability('8D', QT_TR_NOOP('audio mute'), 'SNC', icon_source=VOLUME_SVG),
        '8F': VcpCapability('8F', QT_TR_NOOP('audio treble'), 'C', icon_source=VOLUME_SVG, can_transition=True),
        '91': VcpCapability('91', QT_TR_NOOP('audio bass'), 'C', icon_source=VOLUME_SVG, can_transition=True),
        '64': VcpCapability('91', QT_TR_NOOP('audio mic volume'), 'C', icon_source=VOLUME_SVG, can_transition=True),
        '60': VcpCapability('60', QT_TR_NOOP('input source'), 'SNC', causes_config_change=True),
        'D6': VcpCapability('D6', QT_TR_NOOP('power mode'), 'SNC', causes_config_change=True),
        'CC': VcpCapability('CC', QT_TR_NOOP('OSD language'), 'SNC'),
        '0C': VcpCapability('0C', QT_TR_NOOP('color temperature'), 'CNC', icon_source=COLOR_TEMPERATURE_SVG, enabled=True),
    }

    # Purely here to force inclusion of additional messages in the output of pylupdate5 (internationalisation).
    aliases = {
        'audio volume': [QT_TR_NOOP('audio speaker volume'), ],
    }

    by_arg_name = {c.property_name(): c for c in by_code.values()}
    ddcutil_supported = None

    def __init__(self) -> None:
        pass
        # Uncommenting this would enable anything supported by ddcutil - but is that safe for the
        # hardware given the weird settings that appear to be available and the sometimes dodgy
        # VDU-vendor DDC implementations.
        #
        # if self.ddcutil_supported is None:
        #     ddcutil = DdcUtil()
        #     self.ddcutil_supported = ddcutil.get_supported_vcp_codes()
        #     for code, name in self.ddcutil_supported.items():
        #         if code not in self.by_code:
        #             self.by_code[code] = VduGuiControlDef(code, name)
        #             self.by_arg_name = {c.arg_name(): c for c in self.by_code.values()}


VDU_SUPPORTED_CONTROLS = VduGuiSupportedControls()

CONFIG_DIR_PATH = Path.home().joinpath('.config', 'vdu_controls')
PRESET_NAME_FILE = CONFIG_DIR_PATH.joinpath('current_preset.txt')
LOCALE_TRANSLATIONS_PATHS = [
    Path.cwd().joinpath('translations')] if os.getenv('VDU_CONTROLS_DEVELOPER', default="no") == 'yes' else [] + [
    Path(CONFIG_DIR_PATH).joinpath('translations'),
    Path("/usr/share/vdu_controls/translations"), ]


def get_config_path(config_name: str) -> Path:
    return CONFIG_DIR_PATH.joinpath(config_name + '.conf')


class ConfigIni(configparser.ConfigParser):
    """ConfigParser is a little messy and its classname is a bit misleading, wrap it and bend it to our needs."""

    METADATA_SECTION = "metadata"
    METADATA_VERSION_OPTION = "version"
    METADATA_TIMESTAMP_OPTION = "timestamp"

    def __init__(self):
        super().__init__()
        if not self.has_section(ConfigIni.METADATA_SECTION):
            self.add_section(ConfigIni.METADATA_SECTION)

    def data_sections(self) -> List:
        """Section other than metadata and DEFAULT - real data."""
        return [s for s in self.sections() if s != configparser.DEFAULTSECT and s != ConfigIni.METADATA_SECTION]

    def get_version(self) -> Tuple:
        if self.has_option(ConfigIni.METADATA_SECTION, ConfigIni.METADATA_VERSION_OPTION):
            version = self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_VERSION_OPTION]
            try:
                return tuple([int(i) for i in version.split('.')])
            except ValueError:
                log_error(f"Illegal version number {version} should be i.j.k where i, j and k are integers.")
        return 1, 6, 0

    def is_version_ge(self, version_text: str = VDU_CONTROLS_VERSION):
        major, minor, release = [int(i) for i in version_text.split(".")]
        current_major, current_minor, current_release = self.get_version()
        if current_major < major:
            return False
        if current_minor < minor:
            return False
        if current_release < release:
            return False
        return True

    def save(self, config_path) -> None:
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        with open(config_path, 'w', encoding="utf-8") as config_file:
            self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_VERSION_OPTION] = VDU_CONTROLS_VERSION
            self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_TIMESTAMP_OPTION] = str(zoned_now())
            self.write(config_file)
        log_info(f"Wrote config to {config_path.as_posix()}")

    def duplicate(self, new_ini=None):
        if new_ini is None:
            new_ini = ConfigIni()
        for section in self:
            if section != configparser.DEFAULTSECT and section != ConfigIni.METADATA_SECTION:
                new_ini.add_section(section)
            for option in self[section]:
                new_ini[section][option] = self[section][option]
        return new_ini


class GeoLocation:
    def __init__(self, latitude: float, longitude: float, place_name: str | None):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.place_name: str | None = place_name

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, GeoLocation):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self.latitude == other.latitude and self.longitude == other.longitude and \
            self.place_name == other.place_name


class GlobalOption(Enum):
    SYSTEM_TRAY_ENABLED = QT_TR_NOOP('system-tray-enabled'), 'no', 'restart'
    TRANSLATIONS_ENABLED = QT_TR_NOOP('translations-enabled'), 'no', 'restart'
    WEATHER_ENABLED = QT_TR_NOOP('weather-enabled'), 'yes', ''
    SCHEDULE_ENABLED = QT_TR_NOOP('schedule-enabled'), 'yes', ''
    LUX_OPTIONS_ENABLED = QT_TR_NOOP('lux-options-enabled'), 'no', 'restart'
    SPLASH_SCREEN_ENABLED = QT_TR_NOOP('splash-screen-enabled'), 'yes', ''
    WARNINGS_ENABLED = QT_TR_NOOP('warnings-enabled'), 'no', ''
    DEBUG_ENABLED = QT_TR_NOOP('debug-enabled'), 'no', ''
    SYSLOG_ENABLED = QT_TR_NOOP('syslog-enabled'), 'no', ''
    LOCATION = QT_TR_NOOP('location'), ''

    def name(self) -> str:
        return self.value[0]

    def arg_name(self, with_prefix_no=False) -> str:
        return ("no_" if with_prefix_no else "") + self.value[0].replace("-enabled", "").replace("-", "_")

    def is_bool(self) -> bool:
        return self.name().endswith("-enabled")

    def requires_restart(self):
        return self.value[2] == 'restart'

    def default_value(self) -> str:
        return self.value[1]


class VduControlsConfig:
    """
    A vdu_controls config that can be read or written from INI style files by the standard configparser package.
    Includes a method that can fold in values from command line arguments parsed by the standard argparse package.
    """

    def __init__(self, config_name: str, default_enabled_vcp_codes: List | None = None, include_globals: bool = False) -> None:
        self.config_name = config_name
        self.ini_content = ConfigIni()
        # augment the configparser with type-info for run-time widget selection (default type is 'boolean')
        self.config_type_map = {
            QT_TR_NOOP('enable-vcp-codes'): 'csv', QT_TR_NOOP('sleep-multiplier'): 'float',
            QT_TR_NOOP('capabilities-override'): 'text',
            QT_TR_NOOP('location'): 'location',
        }

        self.boolean_options = {}

        if include_globals:
            self.ini_content[QT_TR_NOOP('vdu-controls-globals')] = {}
            for option in GlobalOption:
                self.ini_content[QT_TR_NOOP('vdu-controls-globals')][option.name()] = option.default_value()

        self.ini_content[QT_TR_NOOP('vdu-controls-widgets')] = {}
        self.ini_content[QT_TR_NOOP('ddcutil-parameters')] = {}
        self.ini_content[QT_TR_NOOP('ddcutil-capabilities')] = {}

        for item in VDU_SUPPORTED_CONTROLS.by_code.values():
            self.ini_content['vdu-controls-widgets'][item.property_name()] = 'yes' if item.enabled else 'no'

        self.ini_content['vdu-controls-widgets']['enable-vcp-codes'] = ''
        self.ini_content['ddcutil-parameters']['sleep-multiplier'] = str(1.0)
        self.ini_content['ddcutil-capabilities']['capabilities-override'] = ''

        if default_enabled_vcp_codes is not None:
            for code in default_enabled_vcp_codes:
                if code in VDU_SUPPORTED_CONTROLS.by_code:
                    self.enable_supported_vcp_code(code)
                else:
                    self.enable_unsupported_vcp_code(code)
        self.file_path: Path | None = None

    def get_config_data_type(self, option: str) -> str:
        if option in self.config_type_map:
            return self.config_type_map[option]
        return 'boolean'

    def restrict_to_actual_capabilities(self, vdu_capabilities: Dict[str, VcpCapability]) -> None:
        for option in self.ini_content['vdu-controls-widgets']:
            if self.get_config_data_type(option) == 'boolean':
                if option in VDU_SUPPORTED_CONTROLS.by_arg_name and \
                        VDU_SUPPORTED_CONTROLS.by_arg_name[option].vcp_code not in vdu_capabilities:
                    del self.ini_content['vdu-controls-widgets'][option]
                elif option.startswith('unsupported-') and option[len('unsupported-'):] not in vdu_capabilities:
                    del self.ini_content['vdu-controls-widgets'][option]

    def get_config_name(self) -> str:
        return self.config_name

    def is_set(self, option: GlobalOption) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', option.name())

    def set_global(self, option: GlobalOption, value):
        self.ini_content['vdu-controls-globals'][option.name()] = value

    def get_sleep_multiplier(self) -> float:
        return self.ini_content.getfloat('ddcutil-parameters', 'sleep-multiplier', fallback=1.0)

    def get_capabilities_alt_text(self) -> str:
        return self.ini_content['ddcutil-capabilities']['capabilities-override']

    def set_capabilities_alt_text(self, alt_text: str) -> None:
        self.ini_content['ddcutil-capabilities']['capabilities-override'] = alt_text.replace("%", "%%")

    def enable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content['vdu-controls-widgets'][VDU_SUPPORTED_CONTROLS.by_code[vcp_code].property_name()] = 'yes'

    def enable_unsupported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content['vdu-controls-widgets'][f'unsupported-{vcp_code}'] = 'yes'

    def disable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content['vdu-controls-widgets'][VDU_SUPPORTED_CONTROLS.by_code[vcp_code].property_name()] = 'no'

    def get_all_enabled_vcp_codes(self) -> List[str]:
        # No very efficient
        enabled_vcp_codes = []
        for control_name, control_def in VDU_SUPPORTED_CONTROLS.by_arg_name.items():
            if self.ini_content['vdu-controls-widgets'].getboolean(control_name, fallback=False):
                enabled_vcp_codes.append(control_def.vcp_code)
        enable_codes_str = self.ini_content['vdu-controls-widgets']['enable-vcp-codes']
        for vcp_code in enable_codes_str.split(","):
            code = vcp_code.strip().upper()
            if code != '':
                if code not in enabled_vcp_codes:
                    enabled_vcp_codes.append(code)
                else:
                    log_warning(f"supported enabled vcp_code {code} is redundantly listed "
                                f"in enabled_vcp_codes ({enable_codes_str})")
        return enabled_vcp_codes

    def get_location(self) -> GeoLocation | None:
        spec = self.ini_content.get('vdu-controls-globals', 'location', fallback=None)
        if spec is None or spec.strip() == '':
            return None
        parts = spec.split(',')
        return GeoLocation(float(parts[0]), float(parts[1]), None if len(parts) < 3 else parts[2])

    def parse_file(self, config_path: Path) -> None:
        """Parse config values from file"""
        self.file_path = config_path
        basename = os.path.basename(config_path)
        config_text = Path(config_path).read_text()
        log_info("Using config file '" + config_path.as_posix() + "'")
        if re.search(r'(\[ddcutil-capabilities])|(\[ddcutil-parameters])|(\[vdu-controls-\w])', config_text) is None:
            log_info(f"Old style config file {basename} overrides ddcutils capabilities")
            self.ini_content['ddcutil-capabilities']['capabilities-override'] = config_text
            return
        self.ini_content.read_string(config_text)
        # Manually extract the text preserving meaningful indentation
        preserve_indents_match = \
            re.search(r'\[ddcutil-capabilities](?:.|\n)*\ncapabilities-override[ \t]*[:=]((.*)(\n[ \t].+)*)',
                      config_text)
        alt_text = preserve_indents_match.group(1) if preserve_indents_match is not None else ''
        # Remove excess indentation while preserving the minimum existing indentation.
        alt_text = inspect.cleandoc(alt_text)
        self.ini_content['ddcutil-capabilities']['capabilities-override'] = alt_text

    def reload(self):
        log_info(f"Reloading config: {self.file_path}")
        if self.file_path:
            for section in list(self.ini_content.data_sections()):
                self.ini_content.remove_section(section)
            self.parse_file(self.file_path)

    def debug_dump(self) -> None:
        origin = 'configuration' if self.file_path is None else os.path.basename(self.file_path)
        for section in self.ini_content.sections():
            for option in self.ini_content[section]:
                log_debug(f"config: {origin} [{section}] {option} = {self.ini_content[section][option]}")

    def write_file(self, config_path: Path, overwrite: bool = False) -> None:
        """Write the config to a file.  Used for creating initial template config files."""
        self.file_path = config_path
        if config_path.is_file():
            if not overwrite:
                log_error(f"{config_path.as_posix()} exists, remove the file if you really want to replace it.")
                return
        log_info(f"Creating new config file {config_path.as_posix()}")
        self.ini_content.save(config_path)

    def parse_global_args(self, args=None) -> argparse.Namespace:
        """Parse command line arguments and integrate the results into this config"""
        if args is None:
            args = sys.argv[1:]
        parser = argparse.ArgumentParser(
            description=textwrap.dedent("""
            VDU Controls
              Uses ddcutil to issue Display Data Channel (DDC) Virtual Control Panel (VCP) commands.
              Controls DVI/DP/HDMI/USB connected monitors (but not builtin laptop displays)."""),
            formatter_class=argparse.RawTextHelpFormatter)
        parser.epilog = textwrap.dedent("""
            As well as command line arguments, individual VDU controls and optimisations may be
            specified in monitor specific configuration files, see --detailed-help for details.

            See the --detailed-help for important licencing information.
            """)
        parser.add_argument('--detailed-help', default=False, action='store_true',
                            help='Detailed help (in markdown format).')
        parser.add_argument('--about', default=False, action='store_true',
                            help='about vdu_controls window')
        parser.add_argument('--show', default=[], action='append',
                            choices=[vcp.property_name() for vcp in VDU_SUPPORTED_CONTROLS.by_code.values()],
                            help='show specified control only (--show may be specified multiple times)')
        parser.add_argument('--hide', default=[], action='append',
                            choices=[vcp.property_name() for vcp in VDU_SUPPORTED_CONTROLS.by_code.values()],
                            help='hide/disable a control (--hide may be specified multiple times)')
        parser.add_argument('--enable-vcp-code', type=str, action='append',
                            help='enable controls for an unsupported vcp-code hex value (may be specified multiple times)')
        # Python 3.9 parser.add_argument('--debug',  action=argparse.BooleanOptionalAction, help='enable debugging')
        parser.add_argument('--system-tray', default=False, action='store_true',
                            help='start up as an entry in the system tray')
        parser.add_argument('--location', default=None, type=str, help='latitude,longitude')
        parser.add_argument('--translations', default=False, action='store_true',
                            help='enable language translations')
        parser.add_argument('--no-schedule', default=False, action='store_true', help='disable preset schedule')
        parser.add_argument('--no-weather', default=False, action='store_true', help='disable weather lookups')
        parser.add_argument('--lux-options', default=False, action='store_true', help='enable hardware light metering')
        parser.add_argument('--debug', default=False, action='store_true', help='enable debug output to stdout')
        parser.add_argument('--warnings', default=False, action='store_true',
                            help='popup a warning when a VDU lacks an enabled control')
        parser.add_argument('--syslog', default=False, action='store_true', help='enable diagnostic output to syslog')
        parser.add_argument('--no-splash', default=False, action='store_true', help="don't show the splash screen")
        parser.add_argument('--sleep-multiplier', type=float, default="1.0",
                            help='protocol reliability multiplier for ddcutil (typically 0.1 .. 2.0, default is 1.0)')
        parser.add_argument('--create-config-files', action='store_true',
                            help="create template config files, one global file and one for each detected VDU.")
        parser.add_argument('--install', action='store_true',
                            help="installs the vdu_controls in the current user's path and desktop application menu.")
        parser.add_argument('--uninstall', action='store_true',
                            help='uninstalls the vdu_controls application menu file and script for the current user.')
        parsed_args = parser.parse_args(args=args)
        if parsed_args.install:
            install_as_desktop_application()
            sys.exit()
        if parsed_args.uninstall:
            install_as_desktop_application(uninstall=True)
            sys.exit()
        if parsed_args.detailed_help:
            print(__doc__)
            sys.exit()

        arg_values = vars(parsed_args)
        for option in GlobalOption:
            if option.is_bool():
                if option.arg_name() in arg_values and arg_values[option.arg_name()]:
                    self.set_global(option, "yes")
                if option.arg_name(with_prefix_no=True) in arg_values and arg_values[option.arg_name(with_prefix_no=True)]:
                    self.set_global(option, "no")
            elif option.arg_name() in arg_values and arg_values[option.arg_name()] is not None:
                self.set_global(option, arg_values[option.arg_name()])

        if len(parsed_args.show) != 0:
            for control_def in VDU_SUPPORTED_CONTROLS.by_arg_name.values():
                if control_def.property_name() in parsed_args.show:
                    self.enable_supported_vcp_code(control_def.vcp_code)
                else:
                    self.disable_supported_vcp_code(control_def.vcp_code)
        if len(parsed_args.hide) != 0:
            for control_def in VDU_SUPPORTED_CONTROLS.by_code.values():
                if control_def.property_name() in parsed_args.hide:
                    self.disable_supported_vcp_code(control_def.vcp_code)

        if parsed_args.enable_vcp_code is not None:
            for code in parsed_args.enable_vcp_code:
                self.enable_unsupported_vcp_code(code)

        return parsed_args


class VduController(QObject):
    """
    Holds model+controller specific to an individual VDU including a map of its capabilities. A model object in
    MVC speak.

    The model configuration can optionally be read from an INI-format config file held in $HOME/.config/vdu-control/

    Capabilities are either extracted from ddcutil output or read from the INI-format files.  File read
    capabilities are provided so that the output from "ddcutil --display N capabilities" can be corrected (because
    it is sometimes incorrect due to sloppy implementation by manufacturers). For example, my LG monitor reports
    two Display-Port inputs, and it only has one.
    """

    vdu_setting_changed = pyqtSignal()

    def __init__(self, vdu_id: str, vdu_model_name: str, vdu_unique_text_id: str, manufacturer: str,
                 default_config: VduControlsConfig, ddcutil: DdcUtil, vdu_exception_handler: Callable,
                 ignore_monitor: bool = False, assume_standard_controls: bool = False) -> None:
        super().__init__()
        self.vdu_stable_id = proper_name(vdu_model_name, vdu_unique_text_id)
        log_info(f"Initializing controls for monitor={vdu_id} model={vdu_model_name} text_id={self.vdu_stable_id}")
        self.vdu_id = vdu_id
        self.model_name = vdu_model_name
        self.serial = vdu_unique_text_id
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.vdu_exception_handler = vdu_exception_handler
        self.sleep_multiplier: float | None = None
        self.enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text: str | None = None
        self.config = None
        for config_name in (self.vdu_stable_id, self.vdu_model_id):
            config_path = get_config_path(config_name)
            log_debug("checking for config file '" + config_path.as_posix() + "'") if log_debug_enabled else None
            if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
                config = VduControlsConfig(config_name,
                                           default_enabled_vcp_codes=default_config.get_all_enabled_vcp_codes())
                config.parse_file(config_path)
                if default_config.is_set(GlobalOption.DEBUG_ENABLED):
                    config.debug_dump()
                self.sleep_multiplier = config.get_sleep_multiplier()
                self.enabled_vcp_codes = config.get_all_enabled_vcp_codes()
                self.capabilities_text = config.get_capabilities_alt_text()
                self.config = config
                break
        if self.capabilities_text is None:
            if ignore_monitor:
                self.capabilities_text = ''
            elif assume_standard_controls:
                self.enabled_vcp_codes = ASSUMED_CONTROLS_CONFIG_VCP_CODES
                self.capabilities_text = ASSUMED_CONTROLS_CONFIG_TEXT
            else:
                self.capabilities_text = ddcutil.query_capabilities(vdu_id)
        self.capabilities = self._parse_capabilities(self.capabilities_text)
        if self.config is None:
            # In memory only config - in case it's needed by a future config editor
            self.config = VduControlsConfig(self.vdu_stable_id,
                                            default_enabled_vcp_codes=self.enabled_vcp_codes)
            self.config.set_capabilities_alt_text(self.capabilities_text)
        self.config.restrict_to_actual_capabilities(self.capabilities)

    def write_template_config_files(self) -> None:
        """Write template config files to $HOME/.config/vdu_controls/"""
        for config_name in (self.vdu_stable_id, self.vdu_model_id):
            save_config_path = get_config_path(config_name)
            config = VduControlsConfig(config_name, default_enabled_vcp_codes=self.enabled_vcp_codes)
            config.set_capabilities_alt_text(self.capabilities_text if self.capabilities_text is not None else '')
            config.write_file(save_config_path)
            self.config = config

    def get_vdu_description(self) -> str:
        """Return a unique description using the serial-number (if defined) or vdu_id."""
        return self.model_name + ':' + (self.serial if len(self.serial) != 0 else self.vdu_id)

    def get_full_id(self) -> Tuple[str, str, str, str]:
        """Return a tuple that defines this VDU: (vdu_id, manufacturer, model, serial-number)."""
        return self.vdu_id, self.manufacturer, self.model_name, self.serial

    def get_attributes(self, attributes: List[str]):
        try:
            if len(attributes) == 0:
                return []
            # raise subprocess.SubprocessError("get_attributes")  # for testing
            return self.ddcutil.get_attributes(self.vdu_id, attributes, sleep_multiplier=self.sleep_multiplier)
        except (subprocess.SubprocessError, ValueError, DdcUtilDisplayNotFound) as e:
            raise VduException(vdu_description=self.get_vdu_description(), vcp_code=",".join(attributes), exception=e,
                               operation="get_attributes")

    def get_attribute(self, vcp_code: str) -> Tuple[str, str]:
        try:
            # raise subprocess.SubprocessError("get_attribute")  # for testing
            return self.ddcutil.get_attribute(self.vdu_id, vcp_code, sleep_multiplier=self.sleep_multiplier)
        except (subprocess.SubprocessError, ValueError, DdcUtilDisplayNotFound) as e:
            raise VduException(vdu_description=self.get_vdu_description(), vcp_code=vcp_code, exception=e,
                               operation="get_attribute")

    def set_attribute(self, vcp_code: str, value: str) -> None:
        try:
            # raise subprocess.SubprocessError("set_attribute")  # for testing
            self.ddcutil.set_attribute(self.vdu_id, vcp_code, value, sleep_multiplier=self.sleep_multiplier)
            self.vdu_setting_changed.emit()
        except (subprocess.SubprocessError, ValueError, DdcUtilDisplayNotFound) as e:
            raise VduException(vdu_description=self.get_vdu_description(), vcp_code=vcp_code, exception=e,
                               operation="set_attribute")

    def _parse_capabilities(self, capabilities_text=None) -> Dict[str, VcpCapability]:
        """Return a map of vpc capabilities keyed by vcp code."""

        def parse_values(values_str: str) -> List[str]:
            stripped = values_str.strip()
            values_list = []
            if len(stripped) != 0:
                lines_list = stripped.split('\n')
                if len(lines_list) == 1:
                    range_pattern = re.compile(r'Values:\s+([0-9]+)..([0-9]+)')
                    range_match = range_pattern.match(lines_list[0])
                    if range_match:
                        values_list = ["%%Range%%", range_match.group(1), range_match.group(2)]
                    else:
                        space_separated = lines_list[0].replace('(interpretation unavailable)', '').strip().split(' ')
                        values_list = [(v, 'unknown ' + v) for v in space_separated[1:]]
                else:
                    values_list = [(key, desc) for key, desc in
                                   (v.strip().split(": ", 1) for v in lines_list[1:])]
            return values_list

        feature_pattern = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\s(.*)', re.DOTALL | re.MULTILINE)
        feature_map = {}
        for feature_text in capabilities_text.split(' Feature: '):
            feature_match = feature_pattern.match(feature_text)
            if feature_match:
                vcp_code = feature_match.group(1)
                vcp_name = feature_match.group(2)
                values = parse_values(feature_match.group(3))
                # Guess type from existence or not of value list
                vcp_type = CONTINUOUS_TYPE if len(values) == 0 or values[0] == "%%Range%%" else GUI_NON_CONTINUOUS_TYPE
                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None,
                                           can_transition=vcp_type == CONTINUOUS_TYPE)
                feature_map[vcp_code] = capability
        return feature_map


class SettingsEditor(QDialog, DialogSingletonMixin):
    """
    Application Settings Editor, edits a default global settings file, and a settings file for each VDU.
    The files are in INI format.  Internally the settings are VduControlsConfig wrappers around
    the standard class ConfigIni.
    """

    @staticmethod
    def invoke(default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig], change_callback: Callable) -> None:
        SettingsEditor.show_existing_dialog() if SettingsEditor.exists() else SettingsEditor(default_config,
                                                                                             vdu_config_list, change_callback)

    def __init__(self, default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig],
                 change_callback) -> None:
        super().__init__()
        self.setWindowTitle(tr('Settings'))
        self.setMinimumWidth(1024)
        self.setLayout(QVBoxLayout())
        tabs = QTabWidget()
        self.layout().addWidget(tabs)
        self.editor_tab_list = []
        self.change_callback = change_callback
        for config in [default_config, ] + vdu_config_list:
            tab = SettingsEditorTab(self, config, change_callback)
            tab.save_all_clicked.connect(self.save_all)
            tabs.addTab(tab, config.get_config_name())
            self.editor_tab_list.append(tab)
        # .show() is non-modal, .exec() is modal
        self.make_visible()

    def save_all(self, warn_if_nothing_to_save: bool = True):
        all_changes: Dict[str, str] = {}
        try:
            nothing_to_save = True
            # Do the main config last - it may cause a restart of the app
            self.setEnabled(False)
            save_order = self.editor_tab_list[1:] + [self.editor_tab_list[0]]
            for editor in save_order:
                if editor.is_unsaved():
                    nothing_to_save = False
                    if editor.save(all_changes=all_changes) == QMessageBox.Cancel:
                        return QMessageBox.Cancel
            if warn_if_nothing_to_save and nothing_to_save:
                alert = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Yes | QMessageBox.No, default=QMessageBox.No)
                alert.setText(tr("Nothing needs saving. Do you wish to save anyway?"))
                if alert.exec() == QMessageBox.Yes:
                    for editor in save_order:
                        if editor.save(force=True, all_changes=all_changes) == QMessageBox.Cancel:
                            return QMessageBox.Cancel
        finally:
            self.setEnabled(True)
            if len(all_changes) > 0:
                self.change_callback(all_changes)
        return QMessageBox.Ok

    def closeEvent(self, event) -> None:
        if self.save_all(warn_if_nothing_to_save=False) == QMessageBox.Cancel:
            event.ignore()
        else:
            super().closeEvent(event)


class SettingsEditorTab(QWidget):
    """A tab corresponding to a settings file, generates UI widgets for each tab based on what's in the config. """

    save_all_clicked = pyqtSignal()

    def __init__(self, parent: QWidget, vdu_config: VduControlsConfig, change_callback: Callable) -> None:
        super().__init__()
        editor_layout = QVBoxLayout()
        self.change_callback = change_callback
        self.changed: Dict[Tuple[str, str], Tuple[str, str]] = {}
        self.setLayout(editor_layout)
        self.config_path = get_config_path(vdu_config.config_name)
        self.ini_before = vdu_config.ini_content
        self.ini_editable = self.ini_before.duplicate()
        self.field_list: List[SettingsEditorFieldBase] = []

        def field(widget: SettingsEditorFieldBase) -> QWidget:
            self.field_list.append(widget)
            return widget

        for section in self.ini_editable.data_sections():
            title = tr(section).replace('-', ' ')
            editor_layout.addWidget(QLabel(f"<b>{title}</b>"))
            booleans_panel = QWidget()
            booleans_grid = QGridLayout()
            booleans_panel.setLayout(booleans_grid)
            editor_layout.addWidget(booleans_panel)
            n = 0
            for option in self.ini_editable[section]:
                data_type = vdu_config.get_config_data_type(option)
                if data_type == 'boolean':
                    booleans_grid.addWidget(field(SettingsEditorBooleanWidget(self, option, section)), n // 3, n % 3)
                    n += 1
                elif data_type == 'float':
                    editor_layout.addWidget(field(SettingsEditorFloatWidget(self, option, section)))
                elif data_type == 'text':
                    editor_layout.addWidget(field(SettingsEditorTextEditorWidget(self, option, section)))
                elif data_type == 'csv':
                    editor_layout.addWidget(field(SettingsEditorCsvWidget(self, option, section)))
                elif data_type == 'location':
                    editor_layout.addWidget(field(SettingsEditorLocationWidget(self, option, section)))

        def save_clicked() -> None:
            if self.is_unsaved():
                self.save()
            else:
                decline_save_alert = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Ok)
                decline_save_alert.setText(tr('No unsaved changes for {}.').format(vdu_config.config_name))
                decline_save_alert.exec()

        buttons_widget = QWidget()
        button_layout = QHBoxLayout()
        buttons_widget.setLayout(button_layout)

        save_button = QPushButton(si(self, QStyle.SP_DriveFDIcon), tr("Save {}").format(vdu_config.config_name))
        save_button.clicked.connect(save_clicked)
        button_layout.addWidget(save_button, 0, Qt.AlignBottom | Qt.AlignLeft)

        save_all_button = QPushButton(si(self, QStyle.SP_DriveFDIcon),
                                      tr("Save All").format(vdu_config.config_name))
        save_all_button.clicked.connect(self.save_all_clicked)
        button_layout.addWidget(save_all_button, 0, Qt.AlignBottom | Qt.AlignLeft)

        quit_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr("Close"))
        quit_button.clicked.connect(parent.close)
        button_layout.addWidget(quit_button, 0, Qt.AlignBottom | Qt.AlignRight)

        editor_layout.addWidget(buttons_widget)

    def save(self, force: bool = False, all_changes: Dict[str, str] | None = None) -> int:
        if self.is_unsaved() or force:
            confirmation = MessageBox(QMessageBox.Question,
                                      buttons=QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Discard, default=QMessageBox.Save)
            message = tr('Update existing {}?') if self.config_path.exists() else tr("Create new {}?")
            message = message.format(self.config_path.as_posix())
            confirmation.setText(message)
            answer = confirmation.exec()
            if answer == QMessageBox.Save:
                self.ini_editable.save(self.config_path)
                copy = pickle.dumps(self.ini_editable)
                self.ini_before = pickle.loads(copy)
                # After file is closed...
                if all_changes is None:
                    self.change_callback(self.changed)
                else:
                    all_changes.update(self.changed)
                self.changed = {}
            elif answer == QMessageBox.Discard:
                copy = pickle.dumps(self.ini_before)
                self.ini_editable = pickle.loads(copy)
                self.reset()
            return answer
        return QMessageBox.Cancel

    def reset(self):
        for field in self.field_list:
            field.reset()

    def is_unsaved(self) -> bool:
        self.changed = {}
        for section in self.ini_before:
            for option in self.ini_before[section]:
                if self.ini_before[section][option] != self.ini_editable[section][option]:
                    self.changed[(section, option)] = (
                        self.ini_before[section][option], self.ini_editable[section][option])
        return len(self.changed) != 0


class SettingsEditorFieldBase(QWidget):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__()
        self.section_editor = section_editor
        self.section = section
        self.option = option
        self.has_error = False

    def translate_option(self):
        return translate_option(self.option)


class SettingsEditorBooleanWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        self.setLayout(QHBoxLayout())
        checkbox = QCheckBox(self.translate_option())
        checkbox.setChecked(section_editor.ini_editable.getboolean(section, option))

        def toggled(is_checked: bool) -> None:
            section_editor.ini_editable[section][option] = 'yes' if is_checked else 'no'

        checkbox.toggled.connect(toggled)
        self.layout().addWidget(checkbox)
        self.checkbox = checkbox

    def reset(self):
        self.checkbox.setChecked(self.section_editor.ini_before.getboolean(self.section, self.option))


class SettingsEditorLineBase(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)
        self.text_label = QLabel(self.translate_option())
        layout.addWidget(self.text_label)
        self.text_input = QLineEdit()
        self.validator: QValidator | None = None
        self.valid_palette = self.text_input.palette()
        self.error_palette = self.text_input.palette()
        self.error_palette.setColor(QPalette.Text, Qt.red)
        self.error_palette.setColor(QPalette.Window, Qt.red)
        self.text_input.inputRejected.connect(partial(self.set_error_indication, True))
        self.text_input.textEdited.connect(partial(self.set_error_indication, False))
        self.text_input.editingFinished.connect(self.editing_finished)
        layout.addWidget(self.text_input)

    def editing_finished(self) -> None:
        text = self.text_input.text()
        if self.validator is not None:
            self.has_error = self.validator.validate(text, 0)[0] != QValidator.Acceptable
            self.set_error_indication(self.has_error)
        if not self.has_error:
            internal_value = self.internalize_value(text)
            if not self.has_error:
                self.section_editor.ini_editable[self.section][self.option] = internal_value

    def internalize_value(self, text: str) -> str | None:
        return str(text)

    def set_error_indication(self, has_error: bool):
        self.has_error = has_error
        self.text_input.setPalette(self.error_palette if has_error else self.valid_palette)

    def reset(self):
        self.text_input.setText(self.section_editor.ini_before[self.section][self.option])


class SettingsEditorFloatWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        self.setLayout(QHBoxLayout())
        self.layout().setAlignment(Qt.AlignLeft)
        self.text_label = QLabel(self.translate_option())
        self.layout().addWidget(self.text_label)
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0.0, 4.0)   # TODO this should be looked up in the metadata
        self.spinbox.setSingleStep(0.1)
        self.spinbox.setValue(float(section_editor.ini_editable[section][option]))
        self.layout().addWidget(self.spinbox)

        def spinbox_value_changed() -> None:
            section_editor.ini_editable[section][option] = locale.delocalize(f"{self.spinbox.value():.2f}")

        self.spinbox.valueChanged.connect(spinbox_value_changed)

    def reset(self):
        self.spinbox.setValue(float(self.section_editor.ini_before.get(self.section, self.option)))


class SettingsEditorCsvWidget(SettingsEditorLineBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        self.text_input.setMaximumWidth(1000)
        self.text_input.setMaxLength(500)
        # TODO - should probably also allow spaces as well as commas, but the regexp is getting a bit tricky?
        # Validator matches CSV of two digit hex or the empty string.
        self.validator = QRegExpValidator(QRegExp(r"^([0-9a-fA-F]{2}([ \t]*,[ \t]*[0-9a-fA-F]{2})*)|$"))
        self.text_input.setText(section_editor.ini_editable[section][option])


class LatitudeLongitudeValidator(QRegExpValidator):

    def __init__(self):
        super().__init__(QRegExp(r"^([+-]*[0-9.,]+[,;][+-]*[0-9.,]+)([,;]\w+)?|$"))

    def validate(self, text: str, pos: int) -> Tuple[QValidator.State, str, int]:
        result = super().validate(text, pos)
        if result[0] == QValidator.Acceptable:
            if text != '':
                try:
                    lat, lon = [float(i) for i in text.split(',')[:2]]
                    if -90.0 <= lat <= 90.0:
                        if -180.0 <= lon <= 180.0:
                            return QValidator.Acceptable, text, pos
                    return QValidator.Invalid, text, pos
                except ValueError:
                    return QValidator.Intermediate, text, pos
        return result


class SettingsEditorLocationWidget(SettingsEditorLineBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        self.text_input.setFixedWidth(500)
        self.text_input.setMaximumWidth(500)
        self.text_input.setMaxLength(250)
        self.validator = LatitudeLongitudeValidator()
        self.text_input.setText(section_editor.ini_editable[section][option])
        self.text_input.setToolTip(tr("Latitude,Longitude for solar elevation calculations."))

        def detection_location():
            data_csv = self.location_dialog()
            if data_csv:
                self.text_input.setText(data_csv)
                self.editing_finished()

        detect_location_button = QPushButton(tr("Detect"))
        detect_location_button.clicked.connect(detection_location)
        detect_location_button.setToolTip(tr("Detect location by querying this desktop's external IP address."))
        self.layout().addWidget(detect_location_button)
        self.layout().addStretch(1)

    def retrieve_ipinfo(self) -> Mapping:
        """
        https://stackoverflow.com/a/55432323/609575
        """
        from urllib.request import urlopen
        from json import load
        with urlopen(IP_ADDRESS_INFO_URL) as res:
            return load(res)

    def location_dialog(self) -> str | None:
        ask_permission = MessageBox(QMessageBox.Question, buttons=QMessageBox.Yes | QMessageBox.No)
        ask_permission.setText(
            tr('Query {} to obtain information based on your IP-address?').format(IP_ADDRESS_INFO_URL))
        if ask_permission.exec() == QMessageBox.Yes:
            try:
                ipinfo = self.retrieve_ipinfo()
                info_text = f"{tr('Use the following info?')}\n" f"{ipinfo['loc']}\n" + \
                            ','.join([ipinfo[key] for key in ('city', 'region', 'country') if key in ipinfo])
                full_text = f"Queried {IP_ADDRESS_INFO_URL}\n" + \
                            '\n'.join([f"{name}: {value}" for name, value in ipinfo.items()])
                confirm = MessageBox(QMessageBox.Information, buttons=QMessageBox.Yes | QMessageBox.No)
                confirm.setText(info_text)
                confirm.setDetailedText(full_text)
                if confirm.exec() == QMessageBox.Yes:
                    data = ipinfo['loc']
                    # Get location name for weather lookups.
                    for key in ('city', 'region', 'country'):
                        if key in ipinfo:
                            data = data + ',' + ipinfo[key]
                            break
                    return data
            except (URLError, KeyError) as e:
                error_dialog = MessageBox(QMessageBox.Critical)
                error_dialog.setText(
                    tr("Failed to obtain info from {}: {}").format(IP_ADDRESS_INFO_URL, e))
                error_dialog.exec()
        return ''


class SettingsEditorTextEditorWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        layout = QVBoxLayout()
        self.setLayout(layout)
        text_label = QLabel(self.translate_option())
        layout.addWidget(text_label)
        text_editor = QPlainTextEdit(section_editor.ini_editable[section][option])

        def text_changed() -> None:
            section_editor.ini_editable[section][option] = text_editor.toPlainText().replace("%", "%%")

        text_editor.textChanged.connect(text_changed)
        layout.addWidget(text_editor)
        self.text_editor = text_editor

    def reset(self):
        self.text_editor.setPlainText(self.section_editor.ini_before[self.section][self.option])


def restart_application(reason: str) -> None:
    """
    Force a restart of the application.

    To be invoked when part of the GUI executes a VCP command that changes the number of connected monitors or
    when the GUI detects the number of monitors has changes.
    """
    alert = MessageBox(QMessageBox.Warning)
    alert.setText(reason)
    alert.setInformativeText(tr('When this message is dismissed, vdu_controls will restart.'))
    alert.exec()
    QCoreApplication.exit(EXIT_CODE_FOR_RESTART)


class VduException(Exception):

    def __init__(self, vdu_description=None, vcp_code=None, exception=None, operation=None) -> None:
        super().__init__()
        self.vdu_description = vdu_description
        self.attr_id = vcp_code
        self.cause = exception
        self.operation = operation

    def is_display_not_found_error(self):
        return self.cause is not None and isinstance(self.cause, DdcUtilDisplayNotFound)

    def __str__(self):
        return f"VduException: {self.vdu_description} op={self.operation} attr={self.attr_id} {self.cause}"


class VduControlBase(QWidget):
    """
    Base GUI control for a DDC attribute.
    """

    connected_vdus_changed = pyqtSignal()
    current_msgbox: MessageBox | None = None

    class VduUptodate(object):
        """Used in conjunction with a with-statement to wrap operations when the
        physical VDU and data are in sync, indicating there is no need to call ddcutil"""

        def __init__(self, ui_control: VduControlBase):
            self.ui_control = ui_control

        def __enter__(self):
            self.ui_control.is_physical_vdu_uptodate = True

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.ui_control.is_physical_vdu_uptodate = False

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__()
        self.controller = controller
        self.vcp_capability = vcp_capability
        self.is_physical_vdu_uptodate = False
        self.current_value: str | None = None

    def restore_vdu_attribute(self, new_value: str):
        # Used when restoring a Preset
        # The with VduControlBase.VduUptodate stops any resultant signal/slot propagation (within this control)
        # from causing further ddcutil requests. Any UI updates will just update the UI.
        with VduControlBase.VduUptodate(self):
            self.__change_vdu_attribute(new_value)
        self.current_value = new_value

    def ui_change_vdu_attribute(self, new_value):
        # Used when the user manipulates a control.
        # If the physical VDU is already uptodate, there is no need to issue any ddcutil commands
        # If the physical VDU is not uptodate, the user must be changing a slider/combo, we need to update the physical VDU
        if not self.is_physical_vdu_uptodate:
            # Update VDU with what ever the user has changed in the GUI - loop on error at the user's discretion.
            while True:
                try:
                    self.__change_vdu_attribute(new_value)
                    break
                except VduException as e:
                    if not self.controller.vdu_exception_handler(e, True):
                        # Assume that the configured VDU's have changed
                        self.connected_vdus_changed.emit()
                        break

    def __change_vdu_attribute(self, new_value):
        self.controller.set_attribute(self.vcp_capability.vcp_code, new_value)
        if self.vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].causes_config_change:
            self.connected_vdus_changed.emit()

    def refresh_view(self):
        pass


class VduControlSlider(VduControlBase):
    """
    GUI control for a DDC continuously variable attribute.

    A compound widget with icon, slider, and text-field.  This is a duck-typed GUI control widget (could inherit
    from an abstract type if we wanted to get formal about it).
    """

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__(controller, vcp_capability)
        self.max_value: str | None = None
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.svg_icon: QSvgWidget | None = None

        if vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                VDU_SUPPORTED_CONTROLS.by_code[vcp_capability.vcp_code].icon_source is not None:
            svg_icon = QSvgWidget()
            svg_icon.load(handle_theme(VDU_SUPPORTED_CONTROLS.by_code[vcp_capability.vcp_code].icon_source))
            svg_icon.setFixedSize(50, 50)
            svg_icon.setToolTip(tr(vcp_capability.name))
            self.svg_icon = svg_icon
            layout.addWidget(svg_icon)
        else:
            label = QLabel()
            label.setText(tr(vcp_capability.name))
            layout.addWidget(label)

        self.slider = slider = QSlider()
        slider.setMinimumWidth(200)
        self.range_restriction = vcp_capability.values
        if len(self.range_restriction) != 0:
            slider.setRange(int(self.range_restriction[1]), int(self.range_restriction[2]))

        self.slider = slider
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setOrientation(Qt.Horizontal)
        # Don't rewrite the ddc value too often - not sure of the implications
        slider.setTracking(False)
        layout.addWidget(slider)

        self.spinbox = QSpinBox()
        if len(self.range_restriction) != 0:
            self.spinbox.setRange(int(self.range_restriction[1]), int(self.range_restriction[2]))

        self.spinbox.setValue(slider.value())
        layout.addWidget(self.spinbox)

        def slider_changed(value: int) -> None:
            self.current_value = str(value)
            self.spinbox.setValue(value)
            self.ui_change_vdu_attribute(self.current_value)

        slider.valueChanged.connect(slider_changed)

        self.sliding = False  # Stop the controls from circular feedback and from triggering self.ui_change_vdu_attribute()

        def slider_moved(value: int) -> None:
            try:
                self.sliding = True
                self.spinbox.setValue(value)
            finally:
                self.sliding = False

        slider.sliderMoved.connect(slider_moved)

        def spinbox_value_changed() -> None:
            if not self.sliding:
                slider.setValue(self.spinbox.value())

        self.spinbox.valueChanged.connect(spinbox_value_changed)

    def refresh_data(self, value: Tuple[str, str] | None = None) -> None:
        """Query the VDU for a new data value and cache it (maybe called from a task thread, so no GUI op's here)."""
        new_value_str, max_value_str = None, None
        for _ in range(SLIDER_REFRESH_RETRIES):
            try:
                new_value_str, max_value_str = value if value is not None else self.controller.get_attribute(
                    self.vcp_capability.vcp_code)
                if self.max_value is None:
                    # Validate as integer
                    _, int_max = int(new_value_str), int(max_value_str)
                    self.current_value, self.max_value = new_value_str, max_value_str
                    if len(self.range_restriction) == 0:
                        self.spinbox.setRange(0, int_max)
                        self.slider.setRange(0, int_max)
                else:
                    int(new_value_str)
                    self.current_value = new_value_str
                return
            except ValueError:
                # Might be initializing at login - can cause transient errors due to X11 talking to
                # the monitor.
                log_warning(f"Non integer values for slider {self.controller.vdu_stable_id} "
                            f"{self.vcp_capability.name} = {new_value_str} (max={max_value_str})")
                log_warning("have to repeat vdu_model.get_attribute - maybe --sleep-multiplier is set too low?")
                sleep_secs = 3.0
                log_warning(f"will try again in {sleep_secs} seconds in case this a transient error due to session "
                            f"initialisation.")
                time.sleep(sleep_secs)
                continue
        # Something is wrong with ddcutils - pass the buck
        raise ValueError(f"Non integer values for slider {self.controller.vdu_stable_id} "
                         f"{self.vcp_capability.name} = {new_value_str} (max={max_value_str})")

    def refresh_view(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        if self.current_value is not None:
            with VduControlBase.VduUptodate(self):  # The with stops the set from causing us to do further unneeded ddcutil calls.
                self.slider.setValue(int(self.current_value))

    def event(self, event: QEvent) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            icon_source = VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].icon_source
            if icon_source is not None:
                self.svg_icon.load(handle_theme(icon_source))
        return super().event(event)


class VduControlComboBox(VduControlBase):
    """
    GUI control for a DDC non-continuously variable attribute, one that has a list of choices.

    This is a duck-typed GUI control widget (could inherit from an abstract type if we wanted to get formal about it).
    """

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the combobox control and initialize its values from the VDU."""
        super().__init__(controller, vcp_capability)
        layout = QHBoxLayout()
        self.setLayout(layout)
        label = QLabel()
        label.setText(self.translate_label(vcp_capability.name))
        layout.addWidget(label)
        self.combo_box = combo_box = QComboBox()
        layout.addWidget(combo_box)

        self.keys = []
        for value, desc in self.vcp_capability.values:
            self.keys.append(value)
            combo_box.addItem(self.translate_label(desc), value)

        def index_changed(index: int) -> None:
            self.current_value = self.combo_box.currentData()
            self.validate_value()
            self.ui_change_vdu_attribute(self.current_value)

        combo_box.currentIndexChanged.connect(index_changed)

    def translate_label(self, source: str):
        canonical = source.lower()
        maybe = tr(canonical)
        result = maybe if maybe != canonical else source
        # Default to capitalized version of each word
        return ' '.join(w[:1].upper() + w[1:] for w in result.split(' '))

    def refresh_data(self, value: Tuple[str, str] | None = None) -> None:
        """Query the VDU for a new data value and cache it (maybe called from a task thread, so no GUI op's here)."""
        self.current_value, _ = value if value is not None else self.controller.get_attribute(self.vcp_capability.vcp_code)

    def refresh_view(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        with VduControlBase.VduUptodate(self):  # The with stops the set from causing us to do further unneeded ddcutil calls.
            self.validate_value()
            self.combo_box.setCurrentIndex(self.keys.index(self.current_value))

    def validate_value(self):
        if self.current_value not in self.keys:
            self.keys.append(self.current_value)
            self.combo_box.addItem('UNKNOWN-' + str(self.current_value), self.current_value)
            self.combo_box.model().item(self.combo_box.count() - 1).setEnabled(False)
            alert = MessageBox(QMessageBox.Critical)
            alert.setText(
                tr("Display {vnum} {vdesc} feature {code} '({cdesc})' has an undefined value '{value}'. "
                   "Valid values are {valid}.").format(
                    vdesc=self.controller.get_vdu_description(),
                    vnum=self.controller.vdu_id,
                    code=self.vcp_capability.vcp_code,
                    cdesc=self.vcp_capability.name,
                    value=self.current_value,
                    valid=self.keys))
            alert.setInformativeText(
                tr('If you want to extend the set of permitted values, you can edit the metadata '
                   'for {} in the settings panel.  For more details see the man page concerning '
                   'VDU/VDU-model config files.').format(self.controller.get_vdu_description()))
            alert.exec()


class VduControlPanel(QWidget):
    """
    Widget that contains all the controls for a single VDU (monitor/display).

    The widget maintains a list of GUI "controls" that are duck-typed and will have refresh_data() and refresh_view()
    methods.
    """
    connected_vdus_changed = pyqtSignal()

    def __init__(self, controller: VduController, warnings: bool, vdu_exception_handler) -> None:
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        label.setText(tr('Monitor {}: {}').format(controller.vdu_id, controller.get_vdu_description()))
        layout.addWidget(label)
        self.controller = controller
        self.vcp_controls: List[VduControlBase] = []
        self.vdu_exception_handler = vdu_exception_handler

        for vcp_code in controller.enabled_vcp_codes:
            if vcp_code in controller.capabilities:
                control = None
                capability = controller.capabilities[vcp_code]
                if capability.vcp_type == CONTINUOUS_TYPE:
                    try:
                        control = VduControlSlider(controller, capability)
                    except ValueError as valueError:
                        alert = MessageBox(QMessageBox.Critical)
                        alert.setText(str(valueError))
                        alert.exec()
                elif capability.vcp_type == GUI_NON_CONTINUOUS_TYPE:
                    try:
                        control = VduControlComboBox(controller, capability)
                    except ValueError as valueError:
                        alert = MessageBox(QMessageBox.Critical)
                        alert.setText(valueError.args[0])
                        alert.setInformativeText(
                            tr('If you want to extend the set of permitted values, see the man page concerning '
                               'VDU/VDU-model config files .').format(capability.vcp_code, capability.name))
                        alert.exec()
                else:
                    raise TypeError(f'No GUI support for VCP type {capability.vcp_type} for vcp_code {vcp_code}')
                if control is not None:
                    control.connected_vdus_changed.connect(self.connected_vdus_changed)
                    layout.addWidget(control)
                    self.vcp_controls.append(control)
            elif warnings:
                missing_vcp = VDU_SUPPORTED_CONTROLS.by_code[
                    vcp_code].name if vcp_code in VDU_SUPPORTED_CONTROLS.by_code else vcp_code
                alert = MessageBox(QMessageBox.Warning)
                alert.setText(
                    tr('Monitor {} lacks a VCP control for {}.').format(
                        controller.get_vdu_description(), tr(missing_vcp)))
                alert.setInformativeText(tr('No read/write ability for vcp_code {}.').format(vcp_code))
                alert.exec()
        if len(self.vcp_controls) != 0:
            self.setLayout(layout)
        try:
            self.refresh_data()
            self.refresh_view()
        except VduException as e:
            self.vdu_exception_handler(e)

    def refresh_data(self) -> None:
        """Tell the control widgets to get fresh VDU data (maybe called from a task thread, so no GUI op's here)."""
        values = self.controller.get_attributes([control.vcp_capability.vcp_code for control in self.vcp_controls])
        if values is not None:
            for control, value in zip(self.vcp_controls, values):
                control.refresh_data(value=value)

    def refresh_view(self) -> None:
        """Tell the control widgets to refresh their views from their internally cached values."""
        for control in self.vcp_controls:
            control.refresh_view()

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)

    def copy_state(self, preset_ini: ConfigIni, update_only) -> None:
        vdu_section_name = self.controller.vdu_stable_id
        if not preset_ini.has_section(vdu_section_name):
            preset_ini.add_section(vdu_section_name)
        for control in self.vcp_controls:
            if not update_only or preset_ini.has_option(vdu_section_name, control.vcp_capability.property_name()):
                if control.current_value is not None:
                    preset_ini[vdu_section_name][control.vcp_capability.property_name()] = control.current_value

    def restore_vdu_state(self, preset_ini: ConfigIni) -> None:
        for control in self.vcp_controls:
            if control.vcp_capability.property_name() in preset_ini[self.controller.vdu_stable_id]:
                value = preset_ini[self.controller.vdu_stable_id][control.vcp_capability.property_name()]
                control.restore_vdu_attribute(value)

    def is_preset_active(self, preset_ini: ConfigIni) -> bool:
        vdu_section = self.controller.vdu_stable_id
        for control in self.vcp_controls:
            if control.vcp_capability.property_name() in preset_ini[vdu_section]:
                if control.current_value != preset_ini[vdu_section][control.vcp_capability.property_name()]:
                    return False
        return True


class Preset:
    """
    A config/ini file of user-created settings presets - such as Sunny, Cloudy, Night, etc.
    """

    def __init__(self, name):
        self.name = name
        self.path = get_config_path(proper_name('Preset', name))
        self.preset_ini = ConfigIni()
        self.timer: QTimer | None = None
        self.timer_action: Callable | None = None
        self.schedule_status = ScheduleStatus.UNSCHEDULED
        self.elevation_time_today: datetime | None = None

    def get_title_name(self):
        return self.name

    def get_icon_path(self) -> Path | None:
        if self.preset_ini.has_section("preset"):
            path_text = self.preset_ini.get("preset", "icon", fallback=None)
            return Path(path_text) if path_text else None
        return None

    def set_icon_path(self, icon_path: Path | None):
        if icon_path:
            if not self.preset_ini.has_section("preset"):
                self.preset_ini.add_section("preset")
            self.preset_ini.set("preset", "icon", icon_path.as_posix())

    def create_icon(self) -> QIcon:
        icon_path = self.get_icon_path()
        if icon_path and icon_path.exists():
            return create_icon_from_path(icon_path)
        else:
            # Only room for two letters at most - use first and last if more than one word.
            full_acronym = [word[0] for word in re.split(r"[ _-]", self.name) if word != '']
            abbreviation = full_acronym[0] if len(full_acronym) == 1 else full_acronym[0] + full_acronym[-1]
            return create_themed_icon_from_text(abbreviation)

    def load(self) -> ConfigIni:
        if self.path.exists():
            log_info(f"Reading preset file '{self.path.as_posix()}'")
            preset_text = Path(self.path).read_text()
            preset_ini = ConfigIni()
            preset_ini.read_string(preset_text)
        else:
            preset_ini = ConfigIni()
        self.preset_ini = preset_ini
        return self.preset_ini

    def clear_content(self):
        self.remove_elevation_trigger()
        self.preset_ini = ConfigIni()

    def save(self):
        self.preset_ini.save(self.path)

    def delete(self):
        log_info(f"Deleting preset file '{self.path.as_posix()}'")
        self.remove_elevation_trigger()
        if self.path.exists():
            os.remove(self.path.as_posix())

    def get_brightness(self, vdu_id: str) -> int:
        if vdu_id in self.preset_ini:
            return self.preset_ini.getint(vdu_id, 'brightness', fallback=-1)
        return -1

    def get_solar_elevation(self) -> SolarElevationKey | None:
        elevation_spec = self.preset_ini.get('preset', 'solar-elevation', fallback=None)
        if elevation_spec:
            solar_elevation = parse_solar_elevation_ini_text(elevation_spec)
            return solar_elevation
        return None

    def get_solar_elevation_abbreviation(self) -> str:
        elevation = self.get_solar_elevation()
        if elevation is None:
            return ''
        result = format_solar_elevation_abbreviation(elevation)
        if self.elevation_time_today:
            result += f" {TIME_CLOCK_SYMBOL} {self.elevation_time_today.strftime('%H:%M')}"
        else:
            # Not possible today - sun doesn't get that high
            result += ' ' + TOO_HIGH_SYMBOL
        if self.get_weather_restriction_filename() is not None:
            result += ' ' + WEATHER_RESTRICTION_SYMBOL
        result += ' ' + self.schedule_status.symbol()
        return result

    def get_solar_elevation_description(self) -> str:
        elevation = self.get_solar_elevation()
        if elevation is None:
            return ''
        basic_desc = format_solar_elevation_description(elevation)
        weather_fn = self.get_weather_restriction_filename()
        weather_suffix = tr(" (subject to {} weather)").format(
            Path(weather_fn).stem.replace('_', ' ')) if weather_fn is not None else ''
        # This might not work too well in translation - rethink?
        if self.elevation_time_today:
            if self.timer and self.timer.remainingTime() > 0:
                template = tr("{} later today at {}") + weather_suffix
            elif self.elevation_time_today < zoned_now():
                template = tr("{} earlier today at {}") + weather_suffix + f" ({self.schedule_status.description()})"
            else:
                template = tr("{} suspended for  {}")
            result = template.format(basic_desc, self.elevation_time_today.strftime("%H:%M"))
        else:
            result = basic_desc + ' ' + tr("the sun does not rise this high today")
        return result

    def get_transition_type(self) -> TransitionType:
        return parse_transaction_type(self.preset_ini.get('preset', 'transition-type', fallback="NONE"))

    def get_step_interval_seconds(self) -> int:
        return self.preset_ini.getint('preset', 'transition-step-interval-seconds', fallback=0)

    def start_timer(self, when_local: datetime, action: Callable):
        if self.timer:
            self.timer.stop()
        else:
            self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer_action = action
        self.timer.timeout.connect(partial(action, self))  # TODO the action may be running in an inappropriate thread
        millis = round((when_local - zoned_now()) / timedelta(milliseconds=1))
        self.timer.start(millis)
        self.schedule_status = ScheduleStatus.SCHEDULED
        log_info(f"Scheduled preset '{self.name}' for {when_local} in {round(millis / 1000 / 60)} minutes "
                 f"{self.get_solar_elevation()}")

    def remove_elevation_trigger(self):
        if self.timer:
            log_info(f"Preset timer and schedule status cleared for '{self.name}'")
            self.timer.stop()
            self.timer = None
        if self.elevation_time_today is not None:
            self.elevation_time_today = None
        self.schedule_status = ScheduleStatus.UNSCHEDULED

    def toggle_timer(self):
        if self.elevation_time_today and self.elevation_time_today > zoned_now():
            if self.timer.remainingTime() > 0:
                log_info(f"Preset scheduled timer cleared for '{self.name}'")
                self.timer.stop()
                self.schedule_status = ScheduleStatus.SUSPENDED
            else:
                log_info(f"Preset scheduled timer restored for '{self.name}'")
                self.start_timer(self.elevation_time_today, self.timer_action)
                self.schedule_status = ScheduleStatus.SCHEDULED

    def get_timer_status(self) -> str:
        if self.elevation_time_today:
            if self.elevation_time_today < zoned_now():
                return "past"
            if self.timer:
                if self.timer.remainingTime() > 0:
                    return "scheduled"
                elif self.timer.remainingTime == 0:
                    return "past"
                else:
                    return "suspended"
        return "unscheduled"

    def is_weather_dependent(self):
        return self.get_weather_restriction_filename() is not None

    def check_weather(self, weather: QueryWeather):
        weather_restriction_filename = self.get_weather_restriction_filename()
        if weather.weather_code is None or weather_restriction_filename is None:
            return True
        path = Path(weather_restriction_filename)
        if not path.exists():
            log_error(f"Preset {self.name} missing weather requirements file: {weather_restriction_filename}")
            return True
        with open(path, encoding="utf-8") as weather_file:
            code_list = weather_file.readlines()
            for code_line in code_list:
                parts = code_line.split()
                if parts and weather.weather_code.strip() == parts[0]:
                    log_info(f"Preset {self.name} met {path.name} requirements. Current weather is: "
                             f"{weather.area_name} {weather.weather_code} {weather.weather_desc}")
                    return True
        log_info(f"Preset {self.name} failed {path.name} requirements. Current weather is: "
                 f"{weather.area_name} {weather.weather_code} {weather.weather_desc}")
        return False

    def get_weather_restriction_filename(self):
        weather_restriction_filename = \
            self.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None)
        return weather_restriction_filename


class ContextMenu(QMenu):

    def __init__(self,
                 main_window,
                 main_window_action,
                 about_action, help_action, chart_action, lux_auto_action, lux_meter_action, settings_action,
                 presets_action, refresh_action, quit_action) -> None:
        super().__init__()
        self.main_window = main_window
        if main_window_action is not None:
            self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Control Panel'), main_window_action)
            self.addSeparator()
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Presets'), presets_action)
        self.presets_separator = self.addSeparator()
        self.busy_disable_prop = "busy_disable"
        self.preset_prop = "is_preset"
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Grey Scale'), chart_action)
        if lux_meter_action is not None:
            self.lux_auto_action = self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Auto/Manual'), lux_auto_action)
            self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Light-Meter'), lux_meter_action)
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Settings'), settings_action)
        self.addAction(si(self, QStyle.SP_BrowserReload), tr('Refresh'), refresh_action).setProperty(self.busy_disable_prop,
                                                                                                     QVariant(True))
        self.addAction(si(self, QStyle.SP_MessageBoxInformation), tr('About'), about_action)
        self.addAction(si(self, QStyle.SP_DialogHelpButton), tr('Help'), help_action)
        self.addSeparator()
        self.addAction(si(self, QStyle.SP_DialogCloseButton), tr('Quit'), quit_action)

    def insert_preset_menu_action(self, preset: Preset) -> None:
        # Have to add it first and then move it (otherwise it won't appear - weird).

        def restore_preset() -> None:
            self.main_window.restore_named_preset(self.sender().text())

        action = self.addAction(preset.create_icon(), preset.name, restore_preset)
        action.setProperty(self.busy_disable_prop, QVariant(True))
        action.setProperty(self.preset_prop, QVariant(True))
        self.insertAction(self.presets_separator, action)
        self.update()

    def remove_preset_menu_action(self, preset: Preset):
        action = self.get_preset_menu_action(preset.name)
        self.removeAction(action) if action is not None else None

    def refresh_preset_menu(self, palette_change: bool = False) -> None:
        for name, preset in self.main_window.preset_controller.find_presets().items():
            # Allow for presets with the same name as existing non-preset menu items
            if not self.has_preset_menu_action(name) or not self.get_preset_menu_action(name).property(self.preset_prop):
                self.insert_preset_menu_action(preset)
            elif palette_change:  # Must redraw icons in case desktop theme changed between light/dark.
                self.get_preset_menu_action(name).setIcon(preset.create_icon())

    def has_preset_menu_action(self, name: str) -> bool:
        for action in self.actions():
            if action == self.presets_separator:
                break
            if action.text() == name:
                return True
        return False

    def get_preset_menu_action(self, name: str) -> QAction | None:
        for action in self.actions():
            if action == self.presets_separator:
                break
            if action.text() == name:
                return action
        return None

    def indicate_busy(self, is_busy: bool = True):
        for action in self.actions():
            if action.property(self.busy_disable_prop):
                action.setDisabled(is_busy)

    def update_lux_auto_icon(self, icon: QIcon) -> None:
        if self.lux_auto_action.icon() != icon:
            self.lux_auto_action.setIcon(icon)
            self.update()


class ToolButton(QToolButton):

    def __init__(self, svg_source: bytes, tip: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        if tip is not None:
            self.setToolTip(tip)
        self.svg_source = svg_source
        self.refresh_icon()

    def refresh_icon(self, svg_source: bytes | None = None):  # may refresh the theme (coloring light/dark) of the icon
        if svg_source is not None:
            self.svg_source = svg_source
        self.setIcon(create_themed_icon_from_svg_bytes(self.svg_source))  # this may alter the SVG for light/dark theme


class VduPanelBottomToolBar(QToolBar):

    def __init__(self, tool_buttons: List[ToolButton], app_context_menu: ContextMenu, parent: VduControlsMainPanel):
        super().__init__(parent=parent)

        self.tool_buttons = tool_buttons
        for button in self.tool_buttons:
            self.addWidget(button)

        self.setIconSize(QSize(32, 32))

        self.progress_bar = QProgressBar(self)
        # Disable text percentage label on the spinner progress-bar
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setDisabled(True)
        self.addWidget(self.progress_bar)

        self.menu_button = ToolButton(MENU_ICON_SOURCE, tr("Context and Preset Menu"), self)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.preset_action = self.addAction(QIcon(), "")
        self.preset_action.setVisible(False)
        self.preset_action.triggered.connect(self.menu_button.click)

        self.addWidget(self.menu_button)

        self.installEventFilter(self)

    def eventFilter(self, target: QObject, event: QEvent) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            for button in self.tool_buttons:
                button.refresh_icon()
            self.menu_button.refresh_icon()
        return super().eventFilter(target, event)

    def indicate_busy(self, is_busy: bool = True):
        for button in self.tool_buttons:
            button.setDisabled(is_busy)
        self.preset_action.setDisabled(is_busy)
        self.progress_bar.setDisabled(not is_busy)
        # Setting range to 0,0 cause the progress bar to pulsate left/right - used as a busy spinner.
        self.progress_bar.setRange(0, 0 if is_busy else 1)

    def display_active_preset(self, preset: Preset | None):
        if preset is not None:
            self.preset_action.setToolTip(f"{preset.get_title_name()} preset")
            self.preset_action.setIcon(preset.create_icon())
            self.preset_action.setVisible(True)
        else:
            self.preset_action.setToolTip("")
            self.preset_action.setIcon(QIcon())
            self.preset_action.setVisible(False)
        self.layout().update()


class VduControlsMainPanel(QWidget):
    """GUI for detected VDU's, it will construct and contain a control panel for each VDU."""

    vdu_setting_changed = pyqtSignal()
    connected_vdus_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.vdu_controllers: List[VduController] = []
        self.bottom_toolbar: VduPanelBottomToolBar | None = None
        self.context_menu: ContextMenu | None = None
        self.refresh_data_task = None
        self.setObjectName("vdu_controls_main_panel")
        self.vdu_control_panels: List[VduControlPanel] = []
        self.alert: QMessageBox | None = None
        self.busy = False

    def initialise_control_panels(self, app_context_menu: ContextMenu, main_config: VduControlsConfig,
                                  vdu_controllers: List[VduController],
                                  tool_buttons: List[ToolButton],
                                  splash_message_signal: pyqtSignal):

        self.vdu_controllers = vdu_controllers

        if self.layout():
            # Already laid out, must be responding to a configuration change requiring re-layout.
            # Remove all existing widgets.
            for i in range(0, self.layout().count()):
                item = self.layout().itemAt(i)
                if isinstance(item, QWidget):
                    self.layout().removeWidget(item)
                    item.deleteLater()
                elif isinstance(item, QWidgetItem):
                    self.layout().removeItem(item)
                    item.widget().deleteLater()

        self.setLayout(QVBoxLayout())
        self.context_menu = app_context_menu
        app_context_menu.refresh_preset_menu()
        controllers_layout = self.layout()
        warnings_enabled = main_config.is_set(GlobalOption.WARNINGS_ENABLED)

        for controller in self.vdu_controllers:
            splash_message_signal.emit(f"DDC ID {controller.vdu_id}\n{controller.get_vdu_description()}")
            vdu_control_panel = VduControlPanel(controller, warnings_enabled, self.display_vdu_exception)
            vdu_control_panel.connected_vdus_changed.connect(self.connected_vdus_changed)
            controller.vdu_setting_changed.connect(self.vdu_setting_changed)
            if vdu_control_panel.number_of_controls() != 0:
                self.vdu_control_panels.append(vdu_control_panel)
                controllers_layout.addWidget(vdu_control_panel)
            elif warnings_enabled:
                warn_omitted = MessageBox(QMessageBox.Warning)
                warn_omitted.setText(
                    tr('Monitor {} {} lacks any accessible controls.').format(controller.vdu_id,
                                                                              controller.get_vdu_description()))
                warn_omitted.setInformativeText(tr('The monitor will be omitted from the control panel.'))
                warn_omitted.exec()
        if len(self.vdu_control_panels) == 0:
            no_vdu_widget = QWidget()
            no_vdu_layout = QHBoxLayout()
            no_vdu_widget.setLayout(no_vdu_layout)
            no_vdu_text = QLabel(tr('No controllable monitors found.\n'
                                    'Use the refresh button if any become available.\n'
                                    'Check that ddcutil and i2c are installed and configured.'))
            no_vdu_text.setAlignment(Qt.AlignLeft)
            no_vdu_image = QLabel()
            no_vdu_image.setPixmap(QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(QSize(64, 64)))
            no_vdu_image.setAlignment(Qt.AlignVCenter)
            no_vdu_layout.addSpacing(32)
            no_vdu_layout.addWidget(no_vdu_image)
            no_vdu_layout.addWidget(no_vdu_text)
            no_vdu_layout.addSpacing(32)
            controllers_layout.addWidget(no_vdu_widget)

        self.bottom_toolbar = VduPanelBottomToolBar(tool_buttons=tool_buttons, app_context_menu=app_context_menu, parent=self)
        self.layout().addWidget(self.bottom_toolbar)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        def open_context_menu(position: QPoint) -> None:
            self.context_menu.exec(self.mapToGlobal(position))

        self.customContextMenuRequested.connect(open_context_menu)

    def refresh_data(self, detected_vdu_list: List[Tuple[str, str, str, str]]):
        for control_panel in self.vdu_control_panels:
            if control_panel.controller.get_full_id() in detected_vdu_list:
                control_panel.refresh_data()

    def refresh_view(self):
        """Invoke when the GUI worker thread completes. Runs in the GUI thread and can refresh the GUI views."""
        for control_panel in self.vdu_control_panels:
            control_panel.refresh_view()

    def restore_preset_data(self, preset: Preset):
        # Called in a non-GUI thread, cannot do any GUI op's.
        for section in preset.preset_ini:
            for control_panel in self.vdu_control_panels:
                if section == control_panel.controller.vdu_stable_id:
                    log_info(f"Restoring preset '{preset.name}' monitor {control_panel.controller.vdu_stable_id}")
                    control_panel.restore_vdu_state(preset.preset_ini)

    def restore_preset_view(self, preset: Preset):
        # Called in a GUI thread, can do GUI op's.
        for section in preset.preset_ini:
            for control_panel in self.vdu_control_panels:
                if section == control_panel.controller.vdu_stable_id:
                    control_panel.refresh_view()

    def indicate_busy(self, is_busy: bool = True):
        self.busy = is_busy
        if self.bottom_toolbar is not None:
            self.bottom_toolbar.indicate_busy(is_busy)
        if self.context_menu is not None:
            self.context_menu.indicate_busy(is_busy)
        for control_panel in self.vdu_control_panels:
            control_panel.setDisabled(is_busy)

    def is_preset_active(self, preset: Preset) -> bool:
        for section in preset.preset_ini:
            if section != 'vdu_controls':
                for control_panel in self.vdu_control_panels:
                    if section == control_panel.controller.vdu_stable_id:
                        if not control_panel.is_preset_active(preset.preset_ini):
                            return False
        return True

    def display_active_preset(self, preset: Preset | None):
        if self.bottom_toolbar:
            self.bottom_toolbar.display_active_preset(preset)

    def display_vdu_exception(self, exception: VduException, can_retry: bool = False) -> bool:
        log_error(f"{exception.vdu_description} {exception.operation} {exception.attr_id} {exception.cause}")
        if self.alert is not None:  # Dismiss any existing alert
            self.alert.done(QMessageBox.Close)
        self.alert = MessageBox(QMessageBox.Critical,
                                buttons=QMessageBox.Close | QMessageBox.Retry if can_retry else QMessageBox.Close,
                                default=QMessageBox.Retry if can_retry else QMessageBox.Close)
        if exception.is_display_not_found_error():
            self.alert.setInformativeText(tr('Monitor appears to be switched off or disconnected.'))
        else:
            self.alert.setInformativeText(
                tr('Is the monitor switched off?)') + '<br>' + tr('Is the sleep-multiplier setting too low?'))
        self.alert.setText(tr("Set value: Failed to communicate with display {}").format(exception.vdu_description))
        self.alert.setAttribute(Qt.WA_DeleteOnClose)
        answer = self.alert.exec()
        self.alert = None
        return answer == QMessageBox.Retry


class WorkerThread(QThread):
    finished_work = pyqtSignal()

    def __init__(self, task_body: Callable, task_finished: Callable | None = None) -> None:
        """Init should always be called from the GUI thread - for easy access to the GUI thread"""
        super().__init__()
        log_debug(f"WorkerThread init in thread = {threading.get_ident()} {self.__class__.__name__}")
        # Background is always initiated from the GUI thread to grant the worker's __init__ easy access to the GUI thread.
        assert is_running_in_gui_thread()
        self.task_body = task_body
        self.task_finished = task_finished
        if self.task_finished is not None:
            self.finished_work.connect(task_finished)
        self.vdu_exception: VduException | None = None

    def run(self):
        """Long-running task, runs in a separate non-GUI thread"""
        try:
            log_debug(f"WorkerThread run in thread = {threading.get_ident()} {self.task_body}")
            self.task_body()
        except VduException as e:
            self.vdu_exception = e
        self.finished_work.emit()


class TransitionState(Enum):
    INITIALIZED = 0
    PARTIAL = 1
    FINISHED_STEPPING = 2
    FINISHED = 3
    INTERRUPTED = 4


class TransitionWorker(WorkerThread):
    progress_signal = pyqtSignal()
    _update_gui_signal = pyqtSignal(VduControlBase)

    def __init__(self, main_panel: VduControlsMainPanel, preset: Preset, progress_callable: Callable, finished_callable: Callable,
                 immediately: bool = False):
        super().__init__(self.task_body, finished_callable)
        log_info(f"TransitionWorker: transition {preset.name} immediately={immediately}")
        self.start_time = datetime.now()
        self.end_time: datetime | None = None
        self.last_step_time: float = 0.0
        self.last_progress_time = datetime.now()
        self.main_panel = main_panel
        self.preset = preset
        self.step_interval_seconds = self.preset.get_step_interval_seconds()
        self.preset_non_transitioning_controls: List[VduControlBase] = []  # specific to this preset
        self.preset_transitioning_controls: List[VduControlBase] = []  # specific to this preset
        self.final_values: Dict[VduControlBase, str] = {}
        self.expected_values: Dict[VduControlBase, str] = {}
        self.transition_immediately = immediately
        self.state = TransitionState.FINISHED_STEPPING if self.transition_immediately else TransitionState.INITIALIZED
        self.progress_callable = progress_callable

        def update_gui(target_widget: VduControlBase):
            target_widget.refresh_view()  # Cause the control to refresh and show the latest value.

        # Make sure these signals execute in the GUI thread by connecting them here (this __init__ runs in the GUI thread).
        self._update_gui_signal.connect(update_gui)
        self.progress_signal.connect(self.progress_callable)

        for control_panel in self.main_panel.vdu_control_panels:
            section = control_panel.controller.vdu_stable_id
            if section in self.preset.preset_ini:
                for control in control_panel.vcp_controls:
                    property_name = control.vcp_capability.property_name()
                    if property_name in self.preset.preset_ini[section]:
                        self.final_values[control] = self.preset.preset_ini[section][property_name]
                        if control.vcp_capability.can_transition and not self.transition_immediately:
                            self.preset_transitioning_controls.append(control)
                        else:
                            self.preset_non_transitioning_controls.append(control)

    def task_body(self):
        while self.state != TransitionState.FINISHED_STEPPING and self.values_are_as_expected():
            cycle_start = time.time()
            if cycle_start - self.last_step_time > self.step_interval_seconds:
                self.last_step_time = cycle_start
                self.step()
            if self.step_interval_seconds > 0:
                remainder = 1.0 - time.time() - cycle_start
                if remainder > 0.0:
                    time.sleep(remainder)
            self.progress_signal.emit()
        if self.state == TransitionState.FINISHED_STEPPING:
            for control in self.preset_non_transitioning_controls:  # Finish by doing the non-transitioning controls
                control.restore_vdu_attribute(self.final_values[control])
                self._update_gui_signal.emit(control)
            self.state = TransitionState.FINISHED
            self.end_time = datetime.now()
            log_info(f"Finished {self.preset.name} {round(self.total_elapsed_seconds(), ndigits=2)} seconds")

    def step(self):
        more_to_do = False
        for control in self.preset_transitioning_controls:  # Step each control by 1 or -1...
            int_val = int(self.expected_values[control])
            final_value = self.final_values[control]
            diff = int(final_value) - int_val
            if diff != 0:
                step_size = 5
                step = int(math.copysign(step_size, diff)) if abs(diff) > step_size else diff
                str_value = str(int_val + step)
                self.expected_values[control] = str_value  # revise to new value
                control.restore_vdu_attribute(str_value)
                self._update_gui_signal.emit(control)
                more_to_do = more_to_do or str_value != final_value
            now = datetime.now()
            if (now - self.last_progress_time).total_seconds() >= 1.0:
                self.last_progress_time = now
                self.progress_signal.emit()
        # Some transitioning controls are not at their final values, need to step again
        self.state = TransitionState.PARTIAL if more_to_do else TransitionState.FINISHED_STEPPING

    def values_are_as_expected(self) -> bool:
        for control_panel in self.main_panel.vdu_control_panels:  # Check that no one else is changing the controls
            control_panel.refresh_data()  # Update the values of all the controls
            for control in control_panel.vcp_controls:
                current_value = control.current_value  # play safe, get a constant copy now
                if control in self.expected_values:
                    if self.expected_values[control] != current_value:
                        log_warning(f"Interrupted transition to {self.preset.name}")
                        self.state = TransitionState.INTERRUPTED  # Something else is changing the controls - abandon the task
                else:
                    self.expected_values[control] = current_value  # must be first time through, initialize value
        return self.state != TransitionState.INTERRUPTED

    def total_elapsed_seconds(self) -> float:
        return ((self.end_time if self.end_time else datetime.now()) - self.start_time).total_seconds()


class TransitioningDummyPreset(Preset):  # A wrapper that creates titles and icons that indicate a transition is in progress.

    def __init__(self, wrapped: Preset):
        super().__init__(wrapped.name)
        self.count = 1
        # self.clocks = ('\u25F7','\u25F6', '\u25F5', '\u25F4') self.arrows_big = ('\u25B6', '\u25B7')
        self.arrows = ('\u25B8', '\u25B9')
        self.icons = (wrapped.create_icon(), create_themed_icon_from_svg_bytes(TRANSITION_ICON_SOURCE))

    def update_progress(self):
        self.count += 1

    def get_title_name(self):
        return self.arrows[self.count % 2] + self.name

    def create_icon(self) -> QIcon:
        return self.icons[self.count % 2]


class PresetController:
    def __init__(self):
        self.presets = {}
        pass

    def find_presets(self) -> Dict[str, Preset]:
        presets_still_present = []
        # Use a stable order for the files - alphabetical filename.
        for path_str in sorted(glob.glob(CONFIG_DIR_PATH.joinpath("Preset_*.conf").as_posix()), key=os.path.basename):
            preset_name = os.path.splitext(os.path.basename(path_str))[0].replace('Preset_', '').replace('_', ' ')
            if preset_name not in self.presets:
                preset = Preset(preset_name)
                preset.load()
                self.presets[preset_name] = preset
            presets_still_present.append(preset_name)
        for preset_name in list(self.presets.keys()):
            if preset_name not in presets_still_present:
                del self.presets[preset_name]
        # If Order_Presets.conf exists, reorder according to the CSV Preset names it holds.
        order_presets_path = CONFIG_DIR_PATH.joinpath("Order_Presets.conf")
        if order_presets_path.exists():
            ordering = order_presets_path.read_text().split(",")
            all_presets = list(self.presets.values())
            # Use the Preset-name's position in the Order_Presets.conf CSV as the key-value (or zero if not in the CSV)
            all_presets.sort(key=lambda obj: ordering.index(obj.name) if obj.name in ordering else 0)
            self.presets = {}
            for preset in all_presets:
                self.presets[preset.name] = preset
        return self.presets

    def save_order(self, ordering):
        order_presets_path = CONFIG_DIR_PATH.joinpath("Order_Presets.conf")
        order_presets_path.write_text(','.join(ordering))

    def save_preset(self, preset: Preset) -> None:
        preset.save()
        self.presets[preset.name] = preset

    def delete_preset(self, preset: Preset) -> None:
        preset.delete()
        del self.presets[preset.name]

    def get_preset(self, preset_number: int) -> Preset | None:
        presets = self.find_presets()
        if preset_number < len(presets):
            return list(presets.values())[preset_number]
        return None


class MessageBox(QMessageBox):
    def __init__(self, icon: QIcon, buttons: QMessageBox.StandardButtons = QMessageBox.NoButton,
                 default: QMessageBox.StandardButton | None = None) -> None:
        super().__init__(icon, APPNAME, '', buttons=buttons)
        if default is not None:
            self.setDefaultButton(default)


class PushButtonLeftJustified(QPushButton):
    def __init__(self, text: str = None, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.label = QLabel()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.layout().addWidget(self.label)
        # Not sure if this helps:
        self.setContentsMargins(0, 0, 0, 0)
        # Seems to fix top/bottom clipping on openbox and xfce:
        layout.setContentsMargins(0, 0, 0, 0)
        if text is not None:
            self.setText(text)

    def setText(self, text: str) -> None:
        self.label.setText(text)


class PresetWidget(QWidget):
    def __init__(self,
                 preset: Preset,
                 restore_action=Callable,
                 save_action=Callable,
                 delete_action=Callable,
                 edit_action=Callable,
                 up_action=Callable,
                 down_action=Callable):
        super().__init__()
        self.name = preset.name
        self.preset = preset
        line_layout = QHBoxLayout()
        line_layout.setSpacing(0)
        self.setLayout(line_layout)

        preset_name_button = PresetActivationButton(preset)

        line_layout.addWidget(preset_name_button)
        preset_name_button.clicked.connect(partial(restore_action, preset=preset))
        preset_name_button.setAutoDefault(False)
        line_layout.addSpacing(20)

        edit_button = QPushButton()
        edit_button.setIcon(si(self, QStyle.SP_FileIcon))
        edit_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        edit_button.setFlat(True)
        edit_button.setToolTip(tr('Edit the options for this preset.'))
        line_layout.addWidget(edit_button)
        edit_button.clicked.connect(partial(edit_action, preset=preset))
        edit_button.setAutoDefault(False)

        save_button = QPushButton()
        save_button.setIcon(si(self, QStyle.SP_DriveFDIcon))
        save_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        save_button.setFlat(True)
        save_button.setContentsMargins(0, 0, 0, 0)
        save_button.setToolTip(tr("Update this preset from the current VDU settings."))
        line_layout.addWidget(save_button)
        save_button.clicked.connect(partial(save_action, preset=preset))
        save_button.setAutoDefault(False)

        up_button = QPushButton()
        up_button.setIcon(si(self, QStyle.SP_ArrowUp))
        up_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        up_button.setFlat(True)
        up_button.setContentsMargins(0, 0, 0, 0)
        up_button.setToolTip(tr("Move up the menu order."))
        line_layout.addWidget(up_button)
        up_button.clicked.connect(partial(up_action, preset=preset, target_widget=self))
        up_button.setAutoDefault(False)

        down_button = QPushButton()
        down_button.setIcon(si(self, QStyle.SP_ArrowDown))
        down_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        down_button.setFlat(True)
        down_button.setContentsMargins(0, 0, 0, 0)
        down_button.setToolTip(tr("Move down the menu order."))
        line_layout.addWidget(down_button)
        down_button.clicked.connect(partial(down_action, preset=preset, target_widget=self))
        down_button.setAutoDefault(False)

        delete_button = QPushButton()
        delete_button.setIcon(si(self, QStyle.SP_DialogDiscardButton))
        delete_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        delete_button.setFlat(True)
        delete_button.setToolTip(tr('Delete this preset.'))
        line_layout.addWidget(delete_button)
        delete_button.clicked.connect(partial(delete_action, preset=preset, target_widget=self))
        delete_button.setAutoDefault(False)

        preset_transition_button = PushButtonLeftJustified()
        preset_transition_button.setText(
            f"{preset.get_transition_type().abbreviation()}"
            f"{str(preset.get_step_interval_seconds()) if preset.get_step_interval_seconds() > 0 else ''}")
        preset_transition_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        width = QFontMetrics(preset_transition_button.font()).horizontalAdvance(">____99")
        preset_transition_button.setMaximumWidth(width + 5)
        preset_transition_button.setFlat(True)
        if preset.get_step_interval_seconds() > 0:
            preset_transition_button.setToolTip(tr("Transition to {}, each step is {} seconds. {}").format(
                preset.get_title_name(), preset.get_step_interval_seconds(), preset.get_transition_type().description()))
        else:
            preset_transition_button.setToolTip(tr("Transition to {}. {}").format(
                preset.get_title_name(), preset.get_transition_type().description()))
        preset_transition_button.clicked.connect(partial(restore_action, preset=preset, immediately=False))
        preset_transition_button.setAutoDefault(False)
        if preset.get_transition_type() == TransitionType.NONE:
            preset_transition_button.setDisabled(True)
            preset_transition_button.setText('')
        line_layout.addWidget(preset_transition_button)

        line_layout.addSpacing(5)
        timer_control_button = PushButtonLeftJustified(parent=self)
        timer_control_button.setFlat(True)
        timer_control_button.setAutoDefault(False)

        if preset.get_solar_elevation() is not None:

            def format_description() -> str:
                if preset.schedule_status == ScheduleStatus.SCHEDULED:
                    action_desc = tr("Press to skip: ")
                elif preset.schedule_status == ScheduleStatus.SUSPENDED:
                    action_desc = tr("Press to re-enable: ")
                else:
                    action_desc = ''
                return f"{action_desc}{SUN_SYMBOL} {preset.get_solar_elevation_description()}"

            def toggle_timer(arg):
                preset.toggle_timer()
                timer_control_button.setText(preset.get_solar_elevation_abbreviation())
                timer_control_button.setToolTip(format_description())

            timer_control_button.setText(preset.get_solar_elevation_abbreviation())
            timer_control_button.setToolTip(format_description())
            timer_control_button.clicked.connect(toggle_timer)
        timer_control_button.setEnabled(preset.schedule_status in (ScheduleStatus.SCHEDULED, ScheduleStatus.SUSPENDED))
        line_layout.addWidget(timer_control_button)


class PresetActivationButton(QPushButton):
    def __init__(self, preset: Preset):
        super().__init__()
        self.preset = preset
        self.setIcon(preset.create_icon())
        self.setText(preset.get_title_name())
        self.setToolTip(tr("Restore {} (immediately)").format(preset.get_title_name()))

    def event(self, event: QEvent) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.setIcon(self.preset.create_icon())
        return super().event(event)


class PresetChooseIconButton(QPushButton):

    def __init__(self):
        super().__init__()
        self.setIcon(si(self, PresetsDialog.no_icon_icon_number))
        self.setToolTip(tr('Choose a preset icon.'))
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.setAutoDefault(False)
        self.last_selected_icon_path: Path | None = None
        self.last_icon_dir = Path("/usr/share/icons")
        if not self.last_icon_dir.exists():
            self.last_icon_dir = Path.home()
        self.preset = None
        self.clicked.connect(self.choose_preset_icon_action)

    def set_preset(self, preset: Preset | None):
        self.preset = preset
        if preset is not None:
            self.last_selected_icon_path = preset.get_icon_path()
        if self.last_selected_icon_path is not None:
            self.last_icon_dir = self.last_selected_icon_path.parent
        self.update_icon()

    def choose_preset_icon_action(self) -> None:
        icon_file = QFileDialog.getOpenFileName(self, tr('Icon SVG or PNG file'),
                                                self.last_icon_dir.as_posix(),
                                                tr('SVG or PNG (*.svg *.png)'))
        self.last_selected_icon_path = Path(icon_file[0]) if icon_file[0] != '' else None
        if self.last_selected_icon_path:
            self.last_icon_dir = self.last_selected_icon_path.parent
        self.update_icon()

    def update_icon(self):
        if self.last_selected_icon_path:
            self.setIcon(create_icon_from_path(self.last_selected_icon_path))
        elif self.preset:
            self.setIcon(self.preset.create_icon())
        else:
            self.setIcon(si(self, PresetsDialog.no_icon_icon_number))

    def event(self, event: QEvent) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.update_icon()
        return super().event(event)


class QueryWeather:

    def __init__(self, location: GeoLocation):
        self.location = location
        self.maximum_distance_km = int(os.getenv("VDU_CONTROLS_WEATHER_KM", default='200'))
        loc = locale.getlocale()
        lang = loc[0][:2] if loc is not None else 'C'
        self.url = f"{WEATHER_FORECAST_URL}/{location.place_name}?" + urllib.parse.urlencode({'lang': lang, 'format': 'j1'})
        self.weather_data = None
        self.proximity_km = 0
        self.proximity_ok = True
        self.longitude = self.latitude = self.country_name = self.area_name = None
        self.cloud_cover = self.visibility = self.weather_desc = self.weather_code = None
        self.when: datetime | None = None
        self.query_succeeded = False

    def run_query(self):
        location_name = self.location.place_name
        lang = locale.getlocale()[0][:2]
        if location_name is None or location_name.strip() == '':
            location_name = ''

        self.when = zoned_now()
        try:
            log_info(f"QueryWeather: {self.url}")
            with urllib.request.urlopen(self.url, timeout=15) as request:
                json_content = request.read()
                self.weather_data = json.loads(json_content)
                self.weather_code = self.weather_data['current_condition'][0]['weatherCode']
                lang_key = f"lang_{lang}"
                if lang_key in self.weather_data['current_condition'][0]:
                    self.weather_desc = self.weather_data['current_condition'][0][lang_key][0]['value']
                else:
                    self.weather_desc = self.weather_data['current_condition'][0]['weatherDesc'][0]['value']
                self.visibility = self.weather_data['current_condition'][0]['visibility']
                self.cloud_cover = self.weather_data['current_condition'][0]['cloudcover']
                self.area_name = self.weather_data['nearest_area'][0]['areaName'][0]['value']
                self.country_name = self.weather_data['nearest_area'][0]['country'][0]['value']
                self.latitude = self.weather_data['nearest_area'][0]['latitude']
                self.longitude = self.weather_data['nearest_area'][0]['longitude']
                self.proximity_km = spherical_kilometers(float(self.latitude), float(self.longitude),
                                                         self.location.latitude, self.location.longitude)
                self.proximity_ok = self.proximity_km <= self.maximum_distance_km
                self.query_succeeded = True
                log_info(f"QueryWeather result: {self}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(tr("Unknown location {}").format(location_name),
                                 tr("Please check Location in Settings"))
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(e))
        except Exception as ue:
            # Can't afford to fall over because of a problem with a remote site
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(ue))

    def __str__(self):
        if self.weather_data is None:
            return ""
        return f"{self.area_name}, {self.country_name}, {self.weather_desc} ({self.weather_code})," \
               f"cloud_cover {self.cloud_cover}, visibility {self.visibility}, " \
               f"location={self.latitude},{self.longitude}"


def weather_bad_location_dialog(weather):
    kilometres = weather.proximity_km
    use_km = QLocale.system().measurementSystem() == QLocale.MetricSystem
    msg = MessageBox(QMessageBox.Warning)
    msg.setText(
        tr("The site {} reports your location as {}, {}, {},{} "
           "which is about {} {} from the latitude and longitude specified in Settings."
           ).format(WEATHER_FORECAST_URL, weather.area_name, weather.country_name, weather.latitude, weather.longitude,
                    round(kilometres if use_km else kilometres * 0.621371), 'km' if use_km else 'miles'))
    msg.setInformativeText(tr("Please check the location specified in Settings."))
    msg.setDetailedText(f"{weather}")
    msg.exec()


class PresetChooseWeatherWidget(QWidget):

    def __init__(self, location: GeoLocation):
        super().__init__()
        self.location = location
        self.init_weather()
        self.required_weather_filepath: Path | None = None
        self.setLayout(QVBoxLayout())
        self.label = QLabel(tr("Additional weather requirements"))
        self.label.setToolTip(
            tr("Weather conditions will be retrieved from {}").format(WEATHER_FORECAST_URL))
        self.layout().addWidget(self.label)
        self.chooser = QComboBox()
        self.warned: GeoLocation | None = None

        def select_action(index: int):
            self.required_weather_filepath = self.chooser.itemData(index)
            if self.chooser.itemData(index) is None:
                self.info_label.setText('')
            else:
                self.verify_weather_location(self.location)
                path = self.chooser.itemData(index)
                if path.exists():
                    with open(path, encoding="utf-8") as weather_file:
                        code_list = weather_file.read()
                        self.info_label.setText(code_list)
                else:
                    self.chooser.removeItem(index)
                    self.chooser.setCurrentIndex(0)
            self.populate()

        self.chooser.currentIndexChanged.connect(select_action)
        self.chooser.setToolTip(self.label.toolTip())
        self.layout().addWidget(self.chooser)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignTop)
        self.populate()
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.info_label)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setWidgetResizable(True)
        self.layout().addWidget(scroll_area)

    def init_weather(self):
        if len(list(CONFIG_DIR_PATH.glob("*.weather"))) == 0:
            log_info(f"Making good, bad and all weather in {CONFIG_DIR_PATH}")
            with open(CONFIG_DIR_PATH.joinpath('good.weather'), 'w', encoding="utf-8") as weather_file:
                weather_file.write("113 Sunny\n116 Partly Cloudy\n119 Cloudy\n")
            with open(CONFIG_DIR_PATH.joinpath('bad.weather'), 'w', encoding="utf-8") as weather_file:
                weather_file.write(
                    "143 Fog\n179 Light Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 "
                    "Light Snow\n230 Heavy Snow\n248 Fog\n260 Fog\n266 Light Rain\n281 Light Sleet\n284 Light "
                    "Sleet\n293 Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 "
                    "Heavy Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
                    "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
                    "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
                    "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
                    "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
                    "Thundery Snow Showers\n395 HeavySnowShowers\n"
                )
            with open(CONFIG_DIR_PATH.joinpath('all.weather'), 'w', encoding="utf-8") as weather_file:
                weather_file.write(
                    "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n122 Very Cloudy\n143 Fog\n176 Light Showers\n179 Light "
                    "Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 Light Snow\n230 Heavy "
                    "Snow\n248 Fog\n260 Fog\n263 Light Showers\n266 Light Rain\n281 Light Sleet\n284 Light Sleet\n293 "
                    "Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 Heavy "
                    "Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
                    "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
                    "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
                    "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
                    "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
                    "Thundery Snow Showers\n395 Heavy Snow Showers\n")

    def verify_weather_location(self, location: GeoLocation):
        place_name = location.place_name if location.place_name is not None else 'IP-address'
        # Only do this check if the location has changed.
        vf_file_path = CONFIG_DIR_PATH.joinpath('verified_weather_location.txt')
        if vf_file_path.exists():
            with open(vf_file_path, encoding="utf-8") as vf:
                if vf.read() == place_name:
                    return
        try:
            log_info(f"Verifying weather location by querying {WEATHER_FORECAST_URL}.")
            weather = QueryWeather(location)
            weather.run_query()
            if weather.proximity_ok:
                msg = MessageBox(QMessageBox.Information)
                msg.setText(tr("Weather for {} will be retrieved from {}").format(place_name, WEATHER_FORECAST_URL))
                msg.exec()
                with open(vf_file_path, 'w', encoding="utf-8") as vf:
                    vf.write(place_name)
            else:
                weather_bad_location_dialog(weather)
        except ValueError as e:
            log_error(f"Failed to validate location: {e}")
            msg = MessageBox(QMessageBox.Critical)
            msg.setText(tr("Failed to validate weather location: {}").format(e.args[0]))
            msg.setInformativeText(e.args[1])
            msg.exec()

    def populate(self):
        if self.chooser.count() == 0:
            self.chooser.addItem("None", None)
        existing_paths = [self.chooser.itemData(i) for i in range(1, self.chooser.count())]
        for path in sorted(CONFIG_DIR_PATH.glob("*.weather")):
            if path not in existing_paths:
                weather_name = path.stem.replace('_', ' ')
                self.chooser.addItem(weather_name, path)

    def get_required_weather_filepath(self) -> Path | None:
        return self.required_weather_filepath if self.required_weather_filepath is not None else None

    def set_required_weather_filepath(self, weather_filename: str | None):
        if weather_filename is None:
            self.required_weather_filepath = None
            self.chooser.setCurrentIndex(0)
            self.info_label.setText('')
            return
        self.required_weather_filepath = Path(weather_filename)
        for i in range(1, self.chooser.count()):
            if self.chooser.itemData(i).as_posix() == self.required_weather_filepath.as_posix():
                self.chooser.setCurrentIndex(i)
                return

    def update_location(self, location: GeoLocation):
        self.location = location
        self.verify_weather_location(self.location)


class PresetChooseTransitionWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(tr("Transition smoothly")), alignment=Qt.AlignLeft)
        self.transition_type_widget = QPushButton("None")
        self.button_menu = QMenu()
        self.transition_type = TransitionType.NONE
        self.is_setting = False

        for transition_type in TransitionType.ALWAYS.component_values():
            action = QAction(transition_type.description(), self.button_menu)
            action.setData(transition_type)
            action.setCheckable(True)
            action.toggled.connect(self.update_value)
            self.button_menu.addAction(action)

        self.transition_type_widget.setMenu(self.button_menu)
        layout.addWidget(self.transition_type_widget, alignment=Qt.AlignLeft)
        layout.addStretch(20)
        layout.addWidget(QLabel(tr("Transition step")), alignment=Qt.AlignRight)
        self.step_seconds_widget = QSpinBox()
        self.step_seconds_widget.setRange(0, 60)
        layout.addWidget(self.step_seconds_widget, alignment=Qt.AlignRight)
        layout.addWidget(QLabel(tr("sec.")), alignment=Qt.AlignRight)

    def update_value(self):
        if self.is_setting:
            return
        for act in self.button_menu.actions():
            if act.isChecked():
                self.transition_type |= act.data()
            elif act.data() in self.transition_type:
                self.transition_type ^= act.data()
        self.transition_type_widget.setText(str(self.transition_type.description()))

    def set_transition_type(self, transition_type: TransitionType):
        try:
            self.is_setting = True
            self.transition_type = transition_type
            for act in self.button_menu.actions():
                act.setChecked(self.transition_type & act.data())
            self.transition_type_widget.setText(str(self.transition_type.description()))
        finally:
            self.is_setting = False

    def set_step_seconds(self, seconds: int):
        self.step_seconds_widget.setValue(seconds)

    def get_transition_type(self) -> TransitionType:
        return self.transition_type

    def get_step_seconds(self) -> int:
        return self.step_seconds_widget.value()


class PresetChooseElevationChart(QLabel):

    selected_elevation_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(150)
        self.setMinimumWidth(200)
        self.sun_image: QImage | None = None
        self.setMouseTracking(True)
        self.in_drag = False
        self.current_pos = None
        self.elevation_time_map: Dict[SolarElevationKey, SolarElevationData] | None = None
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation | None = None
        self.elevation_steps: List[SolarElevationKey] = []
        for i in range(-19, 90):
            self.elevation_steps.append(SolarElevationKey(EASTERN_SKY, i))
        for i in range(90, -20, -1):
            self.elevation_steps.append(SolarElevationKey(WESTERN_SKY, i))
        self.noon_x: int = 100
        self.noon_y: int = 25
        self.horizon_y: int = 75
        self.radius_of_deletion = self.minimumWidth() // 10

    def has_elevation_key(self, key: SolarElevationKey):
        return key in self.elevation_steps

    def get_elevation_data(self, elevation_key: SolarElevationKey):
        return self.elevation_time_map[elevation_key] if elevation_key in self.elevation_time_map else None

    def set_elevation_key(self, elevation_key: SolarElevationKey | None):
        self.elevation_key = elevation_key
        self.create_plot()

    def configure_for_location(self, location: GeoLocation | None):
        self.location = location
        self.elevation_time_map = create_todays_elevation_time_map(latitude=location.latitude,
                                                                   longitude=location.longitude)
        self.elevation_key = None
        self.create_plot()

    def create_plot(self):
        ev_key = self.elevation_key
        width, height = self.width(), self.height()
        origin_iy, range_iy = round(height / 2), round(self.height() / 2.5)
        self.horizon_y = origin_iy
        self.radius_of_deletion = round(width / 10)
        std_line_width = 4

        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)

        def reverse_x(x_val: int) -> int:  # makes thinking right-to-left a bit easier. MAYBE
            return width - x_val

        painter.fillRect(0, 0, width, origin_iy, QColor(0x5b93c5))
        painter.fillRect(0, origin_iy, width, height, QColor(0x7d5233))
        painter.setPen(QPen(Qt.white, std_line_width))  # Horizon
        painter.drawLine(0, origin_iy, width, origin_iy)

        # Perform computations for today's curve and maxima.
        today = zoned_now().replace(hour=0, minute=0)
        sun_plot_x, sun_plot_y, sun_plot_time = None, None, None
        max_sun_height = -90.0
        solar_noon_x, solar_noon_y = 0, 0  # Solar noon
        t = today
        curve_points = []
        while t.day == today.day:
            second_of_day = (t - today).total_seconds()
            x = round(width * second_of_day / (60.0 * 60.0 * 24.0))
            a, z = calc_solar_azimuth_zenith(t, self.location.latitude, self.location.longitude)
            sun_height = math.sin(math.radians(90.0 - z)) * range_iy
            y = origin_iy - round(sun_height)
            curve_points.append(QPoint(reverse_x(x), y))  # Save the plot points to a list
            if sun_height > max_sun_height:
                max_sun_height = sun_height
                solar_noon_x, solar_noon_y = x, y
            if sun_plot_time is None and ev_key and round(90.0 - z) == ev_key.elevation:
                if (ev_key.direction == EASTERN_SKY and round(a) <= 180) or (
                        ev_key.direction == WESTERN_SKY and round(a) >= 180):
                    sun_plot_x, sun_plot_y = x, y
                    sun_plot_time = t
            t += timedelta(minutes=1)
        if sun_plot_x is None:  # ev_key is for an elevation that does not occur today - draw sun at noon elev.
            sun_plot_x, sun_plot_y = solar_noon_x, solar_noon_y
        self.noon_x = reverse_x(solar_noon_x)
        self.noon_y = solar_noon_y

        # Draw elevation curve for today from the accumulated plot points:
        painter.setPen(QPen(QColor(0xff965b), std_line_width))
        painter.drawPoints(curve_points)

        # Draw various annotations such the horizon-line, noon-line, E & W, and the current degrees:
        painter.setPen(QPen(Qt.white, std_line_width))
        painter.drawLine(reverse_x(0), origin_iy, reverse_x(width), origin_iy)
        painter.drawLine(reverse_x(solar_noon_x), origin_iy, reverse_x(solar_noon_x), 0)
        painter.setPen(QPen(Qt.white, std_line_width))
        painter.setFont(QFont(QApplication.font().family(), width // 20, QFont.Weight.Bold))
        painter.drawText(QPoint(reverse_x(70), origin_iy - 32), tr("E"))
        painter.drawText(QPoint(reverse_x(width - 25), origin_iy - 32), tr("W"))
        time_text = sun_plot_time.strftime("%H:%M") if sun_plot_time else "____"
        painter.drawText(reverse_x(solar_noon_x + width // 4), origin_iy + int(height / 2.75),
                         f"{ev_key.elevation if ev_key else 0:3d}{DEGREE_SYMBOL} {time_text}")

        # Draw pie/compas angle
        if ev_key:
            angle_above_horz = ev_key.elevation if ev_key.direction == EASTERN_SKY else (180 - ev_key.elevation)  # anticlockwise from 0
        else:
            angle_above_horz = 180 + 19
        _, radius = self.calc_angle_radius(self.current_pos) if self.current_pos else (0, 21)
        painter.setPen(QPen(QColor(0xffffff if self.current_pos is None or self.in_drag or radius > self.radius_of_deletion else 0xff0000), 2))
        painter.setBrush(QColor(255, 255, 255, 64))
        span_angle = -(angle_above_horz + 19)  # From start angle spanning counterclockwise back toward the right to -19.
        pie_width = pie_height = range_iy * 2
        painter.drawPie(reverse_x(solar_noon_x) - pie_width // 2, origin_iy - pie_height // 2, pie_width, pie_height,
                        angle_above_horz * 16, span_angle * 16)

        # Draw drag-dot
        painter.setFont(QFont(QApplication.font().family(), 8, QFont.Weight.Normal))
        if self.current_pos is not None or self.in_drag or radius >= self.radius_of_deletion:
            painter.setPen(QPen(Qt.red, 6))
            painter.setBrush(Qt.white)
            ddot_radians = math.radians(angle_above_horz if ev_key else -19)
            ddot_x = round(range_iy * math.cos(ddot_radians)) - 8
            ddot_y = round(range_iy * math.sin(ddot_radians)) + 8
            painter.drawEllipse(reverse_x(solar_noon_x - ddot_x), origin_iy - ddot_y, 16, 16)
            if not self.in_drag:
                painter.setPen(QPen(Qt.black, 1))
                painter.drawText(QPoint(reverse_x(solar_noon_x - ddot_x) + 10, origin_iy - ddot_y - 5), tr("Drag to change."))

        # Draw origin-dot
        painter.setPen(QPen(QColor(0xff965b), 2))
        if self.current_pos is not None and not self.in_drag:
            if radius < self.radius_of_deletion:
                painter.setPen(QPen(Qt.black, 1))
                painter.drawText(QPoint(reverse_x(solar_noon_x + 8) + 10, origin_iy - 8 - 5), tr("Click to delete."))
                painter.setPen(QPen(Qt.red, 2))
        painter.setBrush(painter.pen().color())
        painter.drawEllipse(reverse_x(solar_noon_x + 8), origin_iy - 8, 16, 16)

        if ev_key:
            # Draw a line representing the slider degrees and rise/set indicator - may be higher than sun for today:
            sky_line_y = origin_iy - round(math.sin(math.radians(ev_key.elevation)) * range_iy)
            if sky_line_y >= solar_noon_y:
                sky_line_pen = QPen(Qt.white, 2)
            else:
                sky_line_pen = QPen(QColor(0xcccccc), 2)
                sky_line_pen.setStyle(Qt.DotLine)
            painter.setPen(sky_line_pen)
            painter.setBrush(painter.pen().color())
            if ev_key.direction == EASTERN_SKY:
                painter.drawLine(reverse_x(0), sky_line_y, reverse_x(solar_noon_x), sky_line_y)
                painter.setPen(QPen(painter.pen().color(), 1))
                painter.drawPolygon([QPoint(reverse_x(0) - 20 + tx, sky_line_y - 10 + ty) for tx, ty in [(-8, 0), (0, -16), (8, 0)]])
            else:
                painter.drawLine(reverse_x(solar_noon_x), sky_line_y, reverse_x(width), sky_line_y)
                painter.setPen(QPen(painter.pen().color(), 1))
                painter.drawPolygon([QPoint(reverse_x(width - 18) + tx, sky_line_y + 10 + ty) for tx, ty in [(-8, 0), (0, 16), (8, 0)]])

            # Draw the sun
            painter.setPen(QPen(QColor(0xff4a23), std_line_width))
            if self.sun_image is None:
                self.sun_image = create_themed_image_from_svg_bytes(BRIGHTNESS_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#ffdd30"))
            painter.drawImage(QPoint(reverse_x(sun_plot_x) - self.sun_image.width() // 2,
                                     sun_plot_y - self.sun_image.height() // 2), self.sun_image)

        painter.end()
        self.setPixmap(pixmap)

    def calc_angle_radius(self, pos: QPoint):
        x, y = pos.x(), pos.y()
        adjacent = x - self.noon_x
        opposite = self.horizon_y - y
        angle = 90 if adjacent == 0 else round(math.degrees(math.atan(opposite / adjacent)))
        radius = round(math.sqrt(adjacent ** 2 + opposite ** 2))
        return angle, radius

    def update_current_pos(self, global_pos: QPoint):
        local_pos = self.mapFromGlobal(global_pos)
        self.current_pos = local_pos if (0 < local_pos.x() < self.width() and 0 <= local_pos.y() < self.height()) else None
        return self.current_pos

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = self.update_current_pos(event.globalPos())
        angle, radius = self.calc_angle_radius(pos)
        if radius <= self.radius_of_deletion:
            self.set_elevation_key(None)
            self.selected_elevation_signal.emit(None)
        else:
            self.in_drag = True
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.update_current_pos(event.globalPos())
        self.in_drag = False
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = self.update_current_pos(event.globalPos())
        if pos is not None and 0 <= pos.x() < self.width() and 0 <= pos.y() < self.height():
            angle, radius = self.calc_angle_radius(pos)
            if self.in_drag:
                self.current_pos = pos
                angle = -angle if pos.x() < self.noon_x else angle
                key = SolarElevationKey(EASTERN_SKY if pos.x() >= self.noon_x else WESTERN_SKY, angle)
                if key in self.elevation_steps:
                    self.set_elevation_key(key)
                    self.selected_elevation_signal.emit(key)
                    return
        self.create_plot()
        event.accept()

    def leaveEvent(self, event: QEvent) -> None:
        self.current_pos = None
        self.create_plot()
        super().leaveEvent(event)


class PresetChooseElevationWidget(QWidget):

    _slider_select_elevation = pyqtSignal(object)

    def __init__(self, location: GeoLocation):
        super().__init__()
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation = location

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.title_prefix = tr("Solar elevation trigger: ")
        self.title_label = QLabel(self.title_prefix)
        layout.addWidget(self.title_label)
        layout.addSpacing(8)

        self.elevation_chart = PresetChooseElevationChart()
        self.elevation_chart.selected_elevation_signal.connect(self.set_elevation_key)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTracking(True)
        self.slider.setMinimum(-1)
        self.slider.setValue(-1)
        self.slider.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.slider.setTickInterval(5)
        self.slider.setTickPosition(QSlider.TicksAbove)
        self._slider_select_elevation.connect(self.set_elevation_key)

        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)

        chart_slider_layout = QVBoxLayout()
        chart_slider_layout.addWidget(self.elevation_chart, 1)
        chart_slider_layout.addWidget(self.slider)
        bottom_layout.addLayout(chart_slider_layout, 1)

        self.weather_widget = PresetChooseWeatherWidget(location)
        bottom_layout.addWidget(self.weather_widget, 0)
        self.configure_for_location(location)
        self.slider.valueChanged.connect(self.sliding)

        self.setMinimumWidth(400)
        self.sun_image: QImage | None = None

    def sliding(self):
        value = self.slider.value()
        if value == -1:
            self._slider_select_elevation.emit(None)
            return
        chart = self.elevation_chart
        self._slider_select_elevation.emit(chart.elevation_steps[value] if 0 <= value < len(chart.elevation_steps) else None)

    def display_elevation_description(self):
        if self.elevation_key is None:
            self.title_label.setText(self.title_prefix)
            return
        elevation_data = self.elevation_chart.get_elevation_data(self.elevation_key)
        occurs_at = elevation_data.when if elevation_data is not None else None  # No elev data => sun doesn't rise this high today
        if occurs_at:
            when_text = tr("today at {}").format(occurs_at.strftime('%H:%M'))
        else:
            when_text = tr("the sun does not rise this high today")
        # https://en.wikipedia.org/wiki/Twilight
        if self.elevation_key.elevation < 1:
            if self.elevation_key.elevation >= -6:
                when_text += " " + (tr("dawn") if self.elevation_key.direction == EASTERN_SKY else tr("dusk"))
            elif self.elevation_key.elevation >= -18:
                # Astronomical twilight
                when_text += " " + tr("twilight")
            else:
                when_text += " " + tr("nighttime")
        display_text = "{} {} ({}, {})".format(
            self.title_prefix,
            format_solar_elevation_abbreviation(self.elevation_key), tr(self.elevation_key.direction), when_text)
        if display_text != self.title_label.text():
            self.title_label.setText(display_text)

    def configure_for_location(self, location: GeoLocation | None):
        self.elevation_chart.configure_for_location(location)
        self.location = location
        if location is None:
            self.title_label.setText(self.title_prefix + tr("location undefined (see settings)"))
            self.slider.setDisabled(True)
            return
        self.slider.setEnabled(True)
        self.slider.setMaximum(len(self.elevation_chart.elevation_steps) - 1)
        self.slider.setValue(-1)
        self.sliding()
        self.weather_widget.update_location(location)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.elevation_chart.set_elevation_key(self.elevation_key)

    def set_elevation_from_text(self, elevation_text: str):
        if elevation_text and len(self.elevation_chart.elevation_steps) != 0:
            elevation_key = parse_solar_elevation_ini_text(elevation_text)
            if self.elevation_chart.has_elevation_key(elevation_key):
                self.set_elevation_key(elevation_key)
                return
        self.set_elevation_key(None)

    def set_elevation_key(self, elevation_key: SolarElevationKey | None):
        if self.elevation_chart.has_elevation_key(elevation_key):
            self.elevation_key = elevation_key
            self.slider.setValue(self.elevation_chart.elevation_steps.index(self.elevation_key))
            self.slider.setToolTip(f"{self.elevation_key.elevation}{DEGREE_SYMBOL}")
            self.elevation_chart.set_elevation_key(self.elevation_key)
            self.weather_widget.setEnabled(True)
            self.display_elevation_description()
            return
        self.elevation_key = None
        self.slider.setValue(-1)
        self.elevation_chart.set_elevation_key(None)
        self.weather_widget.setEnabled(False)
        self.weather_widget.chooser.setCurrentIndex(0)
        self.display_elevation_description()

    def get_required_weather_filename(self) -> str | None:
        path = self.weather_widget.get_required_weather_filepath()
        return path.as_posix() if path else None

    def set_required_weather_filename(self, weather_filename: str | None):
        self.weather_widget.set_required_weather_filepath(weather_filename)


class PresetsDialog(QDialog, DialogSingletonMixin):
    """A dialog for creating/updating/removing presets."""
    # TODO has become rather complex - break into parts?

    no_icon_icon_number = QStyle.SP_ComputerIcon

    edit_save_needed = pyqtSignal()

    @staticmethod
    def invoke(main_window: 'VduAppWindow', main_config: VduControlsConfig) -> None:
        PresetsDialog.show_existing_dialog() if PresetsDialog.exists() else PresetsDialog(main_window, main_config)
        presets_dialog_update_view('', refresh_view=False)

    def __init__(self, main_window: 'VduAppWindow', main_config: VduControlsConfig) -> None:
        super().__init__()
        self.setWindowTitle(tr('Presets'))
        self.main_window = main_window
        self.main_config = main_config
        self.content_controls: Dict[Tuple[str, str], QWidget] = {}
        self.resize(1600, 850)
        self.setMinimumWidth(1350)
        self.setMinimumHeight(600)
        layout = QVBoxLayout()
        self.setLayout(layout)

        presets_dialog_splitter = QSplitter()
        presets_dialog_splitter.setOrientation(Qt.Horizontal)
        presets_dialog_splitter.setHandleWidth(10)
        layout.addWidget(presets_dialog_splitter)

        presets_panel = QGroupBox()
        presets_panel.setMinimumWidth(700)
        presets_panel.setFlat(True)
        presets_panel_layout = QVBoxLayout()
        presets_panel.setLayout(presets_panel_layout)
        presets_panel_title = QLabel(tr("Presets"))
        presets_panel_title.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        presets_panel_layout.addWidget(presets_panel_title)
        self.preset_widgets_scrollarea = QScrollArea(parent=self)
        preset_widgets_content = QWidget()
        self.preset_widgets_layout = QVBoxLayout()
        preset_widgets_content.setLayout(self.preset_widgets_layout)
        self.preset_widgets_scrollarea.setWidget(preset_widgets_content)
        self.preset_widgets_scrollarea.setWidgetResizable(True)
        presets_panel_layout.addWidget(self.preset_widgets_scrollarea)
        presets_dialog_splitter.addWidget(presets_panel)

        button_box = QWidget()
        button_layout = QHBoxLayout()
        button_box.setLayout(button_layout)
        button_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_window.app_context_menu.refresh_preset_menu()
        # Create a temporary holder of preset values
        self.base_ini = ConfigIni()
        main_window.copy_to_preset_ini(self.base_ini)

        self.populate_presets_layout()

        self.edit_preset_widget = QWidget(parent=self)
        self.edit_preset_layout = QHBoxLayout()
        self.edit_preset_widget.setLayout(self.edit_preset_layout)
        self.edit_preset_widget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.edit_choose_icon_button = PresetChooseIconButton()
        self.edit_preset_layout.addWidget(self.edit_choose_icon_button)

        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setToolTip(tr('Enter a new preset name.'))
        self.preset_name_edit.setClearButtonEnabled(True)

        self.preset_name_edit.textChanged.connect(self.change_edit_group_title)
        self.preset_name_edit.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9][A-Za-z0-9_ .-]{0,60}")))

        self.edit_preset_layout.addWidget(self.preset_name_edit)

        self.edit_save_button = QPushButton()
        self.edit_save_button.setIcon(si(self, QStyle.SP_DriveFDIcon))
        self.edit_save_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.edit_save_button.setFlat(True)
        self.edit_save_button.setToolTip(tr('Save current VDU settings to a new preset.'))
        self.edit_preset_layout.addWidget(self.edit_save_button)

        self.edit_save_button.clicked.connect(self.save_edited_preset)
        self.edit_save_needed.connect(self.save_edited_preset)

        self.editor_groupbox = QGroupBox()
        self.editor_groupbox.setFlat(True)
        self.editor_groupbox.setMinimumHeight(768)
        self.editor_groupbox.setMinimumWidth(550)
        self.editor_layout = QVBoxLayout()
        self.editor_title = QLabel(tr("New Preset:"))
        self.editor_title.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.editor_layout.addWidget(self.editor_title)
        self.editor_groupbox.setLayout(self.editor_layout)

        self.editor_controls_widget = self.create_preset_content_controls()
        self.editor_layout.addWidget(self.edit_preset_widget)

        self.controls_title_widget = self.editor_controls_prompt = QLabel(tr("Controls to include:"))
        self.controls_title_widget.setDisabled(True)
        self.editor_layout.addWidget(self.controls_title_widget)
        self.editor_layout.addWidget(self.editor_controls_widget)

        self.editor_transitions_widget = PresetChooseTransitionWidget()
        self.editor_layout.addWidget(self.editor_transitions_widget)

        self.editor_trigger_widget = PresetChooseElevationWidget(self.main_config.get_location())
        self.editor_layout.addWidget(self.editor_trigger_widget)

        presets_dialog_splitter.addWidget(self.editor_groupbox)

        self.bottom_bar_message = QLabel()  # TODO replace with a status bar
        self.close_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr('close'))
        self.close_button.clicked.connect(self.close)
        button_layout.addSpacing(5)
        button_layout.addWidget(self.bottom_bar_message)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.close_button, 0, Qt.AlignRight | Qt.AlignBottom)

        self.edit_choose_icon_button.set_preset(None)
        self.editor_controls_widget.setDisabled(True)
        self.editor_transitions_widget.setDisabled(True)
        self.editor_trigger_widget.setDisabled(True)
        self.edit_save_button.setDisabled(True)
        layout.addWidget(button_box)
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(1200, 768)

    def populate_presets_layout(self):
        for preset_def in self.main_window.preset_controller.find_presets().values():
            preset_widget = self.create_preset_widget(preset_def)
            self.preset_widgets_layout.addWidget(preset_widget)
        self.preset_widgets_layout.addStretch(1)

    def reload_data(self):
        for i in range(self.preset_widgets_layout.count() - 1, -1, -1):
            w = self.preset_widgets_layout.itemAt(i).widget()
            if isinstance(w, PresetWidget):
                self.preset_widgets_layout.removeWidget(w)
                w.deleteLater()
            else:
                self.preset_widgets_layout.removeItem(self.preset_widgets_layout.itemAt(i))
        self.populate_presets_layout()
        self.preset_name_edit.setText('')
        self.editor_trigger_widget.configure_for_location(self.main_config.get_location())

    def refresh_view(self):
        # A bit extreme, but it works
        # TODO Update preset status display - a bit of an extreme way to do it - consider something better?
        self.reload_data()

    def set_status_message(self, message: str):
        self.bottom_bar_message.setText(message)

    def find_preset_widget(self, name) -> PresetWidget | None:
        for i in range(self.preset_widgets_layout.count()):
            w = self.preset_widgets_layout.itemAt(i).widget()
            if isinstance(w, PresetWidget):
                if w.name == name:
                    return w
        return None

    def create_preset_content_controls(self) -> QWidget:
        container = QScrollArea(parent=self)
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        for count, section in enumerate(self.base_ini.data_sections()):
            if count > 1:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                layout.addWidget(line)
            group_box = QGroupBox(section)
            group_box.setFlat(True)
            group_box.setToolTip(tr("Choose which settings to save for {}").format(section))
            group_layout = QHBoxLayout()
            group_box.setLayout(group_layout)
            for option in self.base_ini[section]:
                option_control = QCheckBox(translate_option(option))
                group_layout.addWidget(option_control)
                self.content_controls[(section, option)] = option_control
                option_control.setChecked(True)
            layout.addWidget(group_box)
        container.setWidget(widget)
        widget.show()
        return container

    def initialise_preset_from_controls(self, preset: Preset):
        preset_ini = preset.preset_ini
        for key, checkbox in self.content_controls.items():
            if checkbox.isChecked():
                section, option = key
                if not preset_ini.has_option(section, option):
                    # Can use a dummy value - it wil update when saved.
                    value = self.base_ini.get(section, option, fallback="%should not happen%")
                    if not preset_ini.has_section(section):
                        preset_ini.add_section(section)
                    preset_ini.set(section, option, value)
        preset.set_icon_path(self.edit_choose_icon_button.last_selected_icon_path)
        elevation_ini_text = format_solar_elevation_ini_text(self.editor_trigger_widget.elevation_key)
        if elevation_ini_text is not None:
            if not preset_ini.has_section('preset'):
                preset_ini.add_section('preset')
            preset_ini.set('preset', 'solar-elevation', elevation_ini_text)
            weather_filename = self.editor_trigger_widget.get_required_weather_filename()
            if weather_filename is not None:
                preset_ini.set('preset', 'solar-elevation-weather-restriction', weather_filename)
        preset_ini.set('preset', 'transition-type', str(self.editor_transitions_widget.get_transition_type()))
        preset_ini.set('preset', 'transition-step-interval-seconds', str(self.editor_transitions_widget.get_step_seconds()))

    def get_presets(self):
        return [self.preset_widgets_layout.itemAt(i).widget()
                for i in range(0, self.preset_widgets_layout.count() - 1)
                if isinstance(self.preset_widgets_layout.itemAt(i).widget(), PresetWidget)
                ]

    def get_presets_name_order(self):
        return [w.name for w in self.get_presets()]

    def add_preset_widget(self, preset_widget: PresetWidget):
        # Insert before trailing stretch item
        self.preset_widgets_layout.insertWidget(self.preset_widgets_layout.count() - 1, preset_widget)

    def up_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index > 0:
            self.preset_widgets_layout.removeWidget(target_widget)
            new_preset_widget = self.create_preset_widget(preset)
            self.preset_widgets_layout.insertWidget(index - 1, new_preset_widget)
            target_widget.deleteLater()
            self.main_window.preset_controller.save_order(self.get_presets_name_order())
            self.preset_widgets_scrollarea.updateGeometry()
        self.set_status_message('')

    def down_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index < self.preset_widgets_layout.count() - 2:
            self.preset_widgets_layout.removeWidget(target_widget)
            new_preset_widget = self.create_preset_widget(preset)
            self.preset_widgets_layout.insertWidget(index + 1, new_preset_widget)
            target_widget.deleteLater()
            self.main_window.preset_controller.save_order(self.get_presets_name_order())
            self.preset_widgets_scrollarea.updateGeometry()
        self.set_status_message('')

    def restore_preset(self, preset: Preset, immediately: bool = True) -> None:
        self.main_window.restore_preset(preset, immediately=immediately)
        self.preset_name_edit.setText('')

    def save_preset(self, preset: Preset) -> None:
        preset_path = get_config_path(proper_name('Preset', preset.name))
        if preset_path.exists():
            confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | QMessageBox.Cancel, default=QMessageBox.Save)
            message = tr('Update existing {} preset with current monitor settings?').format(preset.name)
            confirmation.setText(message)
            if confirmation.exec() == QMessageBox.Cancel:
                self.set_status_message('')
                return
        self.preset_name_edit.setText('')
        self.main_window.save_preset(preset)
        self.set_status_message(tr("Saved {}").format(preset.name))

    def delete_preset(self, preset: Preset, target_widget: QWidget) -> None:
        confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Ok | QMessageBox.Cancel, default=QMessageBox.Cancel)
        confirmation.setText(tr('Delete {}?').format(preset.name))
        rc = confirmation.exec()
        if rc == QMessageBox.Cancel:
            self.set_status_message('')
            return
        self.main_window.delete_preset(preset)
        self.preset_widgets_layout.removeWidget(target_widget)
        target_widget.deleteLater()
        self.main_window.preset_controller.save_order(self.get_presets_name_order())
        self.preset_name_edit.setText('')
        self.preset_widgets_scrollarea.updateGeometry()
        self.set_status_message(tr("Deleted {}").format(preset.name))

    def change_edit_group_title(self):
        changed_text = self.preset_name_edit.text()
        if changed_text.strip() == "":
            self.editor_controls_widget.setDisabled(True)
            self.editor_transitions_widget.setDisabled(True)
            self.editor_trigger_widget.setDisabled(True)
            self.edit_save_button.setDisabled(True)
            self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include:"))
            self.controls_title_widget.setDisabled(True)
            self.editor_transitions_widget.setDisabled(True)
        else:
            already_exists = self.find_preset_widget(changed_text)
            if already_exists:
                self.editor_title.setText(tr("Edit {}:").format(changed_text))
            else:
                self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include in {}:").format(changed_text))
            self.editor_controls_widget.setDisabled(False)
            self.editor_transitions_widget.setDisabled(False)
            self.editor_trigger_widget.setDisabled(False)
            self.controls_title_widget.setDisabled(False)
            self.editor_transitions_widget.setDisabled(False)
            self.edit_save_button.setDisabled(False)

    def edit_preset(self, preset: Preset) -> None:
        def begin_editing(succeeded: bool):
            self.preset_name_edit.setText(preset.name)
            self.edit_choose_icon_button.set_preset(preset)
            for key, item in self.content_controls.items():
                item.setChecked(preset.preset_ini.has_option(key[0], key[1]))
            if preset.preset_ini.has_section('preset'):
                self.editor_trigger_widget.set_elevation_from_text(
                    preset.preset_ini.get('preset', 'solar-elevation', fallback=None))
                self.editor_trigger_widget.set_required_weather_filename(
                    preset.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None))
                self.editor_transitions_widget.set_transition_type(preset.get_transition_type())
                self.editor_transitions_widget.set_step_seconds(preset.get_step_interval_seconds())

        self.main_window.restore_preset(preset, restore_finished=begin_editing, immediately=True)
        self.set_status_message('')  # Will be shortly followed by a restore message

    def save_edited_preset(self) -> None:
        preset_name = self.preset_name_edit.text().strip()
        if preset_name == '':
            return
        existing_preset_widget: PresetWidget | None = self.find_preset_widget(preset_name)
        if existing_preset_widget:
            confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | QMessageBox.Cancel, default=QMessageBox.Save)
            confirmation.setText(tr("Replace existing '{}' preset?").format(preset_name))
            if confirmation.exec() == QMessageBox.Cancel:
                self.set_status_message('')
                return
            preset = existing_preset_widget.preset
            preset.clear_content()
        else:
            preset = Preset(preset_name)
        self.initialise_preset_from_controls(preset)
        self.main_window.save_preset(preset)
        # Create a new widget - an easy way to update the icon.
        new_preset_widget = self.create_preset_widget(preset)
        if existing_preset_widget:
            self.preset_widgets_layout.replaceWidget(existing_preset_widget, new_preset_widget)
            # The deleteLater removes the widget from the tree so that it is no longer findable and can be freed.
            existing_preset_widget.deleteLater()
            self.make_visible()
        else:
            self.add_preset_widget(new_preset_widget)
            self.main_window.preset_controller.save_order(self.get_presets_name_order())

            def scroll_to_bottom():
                # TODO figure out why this does not work
                self.preset_widgets_scrollarea.updateGeometry()
                self.preset_widgets_scrollarea.verticalScrollBar().setValue(
                    self.preset_widgets_scrollarea.verticalScrollBar().maximum())
                self.preset_widgets_scrollarea.ensureWidgetVisible(new_preset_widget)

            self.preset_widgets_scrollarea.updateGeometry()
            QTimer.singleShot(0, scroll_to_bottom)
        self.preset_name_edit.setText('')
        self.set_status_message(tr("Saved {}").format(preset.name))

    def create_preset_widget(self, preset):
        return PresetWidget(
            preset,
            restore_action=self.restore_preset,
            save_action=self.save_preset,
            delete_action=self.delete_preset,
            edit_action=self.edit_preset,
            up_action=self.up_action,
            down_action=self.down_action)

    def event(self, event: QEvent) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.repaint()
        return super().event(event)

    def closeEvent(self, event) -> None:
        if self.preset_name_edit.text().strip() != '':
            alert = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                               default=QMessageBox.Save)
            alert.setText("Save current edit?")
            answer = alert.exec()
            if answer == QMessageBox.Cancel:
                event.ignore()
                return
            elif answer == QMessageBox.Save:
                self.edit_save_needed.emit()
            else:
                self.preset_name_edit.setText('')
        self.set_status_message('')
        super().closeEvent(event)


def presets_dialog_update_view(message: str, refresh_view: bool = True):
    presets_dialog = PresetsDialog.get_instance()
    if presets_dialog:
        presets_dialog.set_status_message(message)
        if refresh_view:
            presets_dialog.refresh_view()


def exception_handler(e_type, e_value, e_traceback):
    """Overarching error handler in case something unexpected happens."""
    log_error("\n" + ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    alert = MessageBox(QMessageBox.Critical)
    alert.setText(tr('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))))
    alert.setInformativeText(tr('Is --sleep-multiplier set too low?') +
                             '<br>_______________________________________________________<br>')
    alert.setDetailedText(
        tr('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback))))
    alert.exec()
    QApplication.quit()


def handle_theme(svg_str: bytes) -> bytes:
    if is_dark_theme():
        svg_str = svg_str.replace(SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR)
    return svg_str


def create_themed_pixmap_from_svg_bytes(svg_bytes: bytes):
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    image = create_themed_image_from_svg_bytes(svg_bytes)
    return QPixmap.fromImage(image)


def create_themed_image_from_svg_bytes(svg_bytes) -> QImage:
    renderer = QSvgRenderer(handle_theme(svg_bytes))
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def create_themed_icon_from_svg_bytes(svg_bytes: bytes) -> QIcon:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    return QIcon(create_themed_pixmap_from_svg_bytes(svg_bytes))


def create_icon_from_path(path: Path) -> QIcon:
    if path.exists():
        if path.suffix == '.svg':
            with open(path, 'rb') as icon_file:
                icon_bytes = icon_file.read()
                return create_themed_icon_from_svg_bytes(icon_bytes)
        if path.suffix == '.png':
            return QIcon(path.as_posix())
    # Copes with the case where the path has been deleted.
    return QApplication.style().standardIcon(QStyle.SP_MessageBoxQuestion)


def create_themed_icon_from_text(text: str) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setFont(QApplication.font())
    painter.setOpacity(1.0)
    painter.setPen(QColor((SVG_DARK_THEME_COLOR if is_dark_theme() else SVG_LIGHT_THEME_COLOR).decode("utf-8")))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)


def create_merged_icon(base_icon: QIcon, overlay_icon: QIcon) -> QIcon:
    """Non-destructively overlay overlay_icon in the middle of base_icon."""
    base_pixmap = base_icon.pixmap(QSize(64, 64), QIcon.Mode.Normal, QIcon.State.On)
    base_size = base_pixmap.size()
    combined_pixmap = QPixmap(base_pixmap)
    overlay_pixmap = overlay_icon.pixmap(base_size, QIcon.Mode.Normal, QIcon.State.On)
    painter = QPainter(combined_pixmap)
    painter.drawPixmap(0, 0, base_pixmap)
    painter.drawPixmap(base_size.width() // 4, base_size.height() // 8, base_size.width() // 2, base_size.height() // 2,
                       overlay_pixmap)
    painter.end()
    overlay_icon = QIcon()
    overlay_icon.addPixmap(combined_pixmap)
    return overlay_icon


def install_as_desktop_application(uninstall: bool = False):
    """Self install this script in the current Linux user's bin directory and desktop applications->settings menu."""
    desktop_dir = Path.home().joinpath('.local', 'share', 'applications')
    icon_dir = Path.home().joinpath('.local', 'share', 'icons')

    if not desktop_dir.exists():
        log_error(f"No desktop directory is present:{desktop_dir.as_posix()}"
                  " Cannot proceed - is this a non-standard desktop?")
        return

    bin_dir = Path.home().joinpath('bin')
    if not bin_dir.is_dir():
        log_warning(f"creating:{bin_dir.as_posix()}")
        os.mkdir(bin_dir)

    if not icon_dir.is_dir():
        log_warning("creating:{icon_dir.as_posix()}")
        os.mkdir(icon_dir)

    installed_script_path = bin_dir.joinpath("vdu_controls")
    desktop_definition_path = desktop_dir.joinpath("vdu_controls.desktop")
    icon_path = icon_dir.joinpath("vdu_controls.png")

    if uninstall:
        os.remove(installed_script_path)
        log_info(f"Removed {installed_script_path.as_posix()}")
        os.remove(desktop_definition_path)
        log_info(f"Removed {desktop_definition_path.as_posix()}")
        os.remove(icon_path)
        log_info(f"Removed {icon_path.as_posix()}")
        return

    if installed_script_path.exists():
        log_warning(f"skipping installation of {installed_script_path.as_posix()}, it is already present.")
    else:
        source = open(__file__).read()
        source = source.replace("#!/usr/bin/python3", '#!' + sys.executable)
        log_info(f"Creating {installed_script_path.as_posix()}")
        open(installed_script_path, 'w').write(source)
        log_info(f"chmod u+rwx {installed_script_path.as_posix()}")
        os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        log_warning(f"Skipping installation of {desktop_definition_path.as_posix()}, it is already present.")
    else:
        log_info(f"Creating {desktop_definition_path.as_posix()}")
        desktop_definition = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            Exec={installed_script_path.as_posix()}
            Name=VDU Controls
            GenericName=DDC control panel for monitors
            Comment=Virtual Control Panel for externally connected VDU's
            Icon={icon_path.as_posix()}
            Categories=Qt;Settings;
            """)
        open(desktop_definition_path, 'w').write(desktop_definition)

    if icon_path.exists():
        log_warning(f"skipping installation of {icon_path.as_posix()}, it is already present.")
    else:
        log_info(f"Creating {icon_path.as_posix()}")
        get_splash_image().save(icon_path.as_posix())

    log_info('Installation complete. Your desktop->applications->settings should now contain VDU Controls')


class LuxConfigChart(QLabel):

    def __init__(self, lux_dialog: LuxDialog):
        super().__init__(parent=lux_dialog)
        self.lux_dialog = lux_dialog
        self.chart_changed_callback = lux_dialog.chart_changed_callback
        self.profile_data = lux_dialog.profile_data
        self.preset_points = lux_dialog.preset_points
        self.main_app = lux_dialog.main_app
        self.vdu_chart_colors = self.lux_dialog.vdu_chart_color
        self.range_restrictions = lux_dialog.range_restrictions
        self.current_lux = None
        self.snap_to_margin = 4
        self.current_vdu_id = None if len(lux_dialog.profile_data) == 0 else list(lux_dialog.profile_data.keys())[0]
        self.pixmap_width = 600
        self.pixmap_height = 550
        self.plot_width, self.plot_height = self.pixmap_width - 200, self.pixmap_height - 150
        self.x_origin, self.y_origin = 120, self.plot_height + 50
        self.setMouseTracking(True)  # Enable mouse move events so we can draw cross-hairs
        self.setMinimumWidth(self.pixmap_width)
        self.setMinimumHeight(self.pixmap_height)
        self.possible_colors = []

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.plot_width, self.plot_height = event.size().width() - 200, event.size().height() - 150
        self.x_origin, self.y_origin = 120, self.plot_height + 50
        self.pixmap_width, self.pixmap_height = event.size().width(), event.size().height()
        self.create_plot()

    def create_plot(self):
        std_line_width = 4
        preset_color = 0xebfff9
        triangle = [(-8, 0), (0, -16), (8, 0)]
        pixmap = QPixmap(self.pixmap_width, self.pixmap_height)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, self.pixmap_width, self.pixmap_height, QColor(0x5b93c5))
        painter.setPen(QPen(Qt.white, std_line_width))
        painter.drawText(self.pixmap_width // 3, 30, tr("Lux Brightness Response Profiles"))

        painter.drawLine(self.x_origin, self.y_origin, self.x_origin + self.plot_width + 25, self.y_origin)  # Draw x-axis
        for lux in [0, 10, 100, 1_000, 10_000, 100_000]:  # Draw x-axis ticks
            x = self.x_from_lux(lux)
            painter.drawLine(self.x_origin + x, self.y_origin + 5, self.x_origin + x, self.y_origin - 5)
            painter.drawText(self.x_origin + x - 8 * len(str(lux)), self.y_origin + 40, str(lux))
        painter.drawText(self.x_origin + self.plot_width // 2 - len(str("Lux")), self.y_origin + 70, str("Lux"))

        painter.drawLine(self.x_origin, self.y_origin, self.x_origin, self.y_origin - self.plot_height)   # Draw y-axis
        for brightness in range(0, 101, 10):  # Draw y-axis ticks
            y = self.y_from_percent(brightness)
            painter.drawLine(self.x_origin - 5, self.y_origin - y, self.x_origin + 5, self.y_origin - y)
            painter.drawText(self.x_origin - 50, self.y_origin - y + 5, str(brightness))
        painter.save()
        painter.translate(self.x_origin - 70, self.y_origin - self.plot_height // 2 + 6 * len(tr("Brightness %")))
        painter.rotate(-90)
        painter.drawText(0, 0, tr("Brightness %"))
        painter.restore()

        if self.current_vdu_id is None:  # Nothing to draw
            painter.end()
            self.setPixmap(pixmap)
            return

        min_v, max_v = self.range_restrictions[self.current_vdu_id]   # Draw range restrictions (if not 0..100)
        if min_v > 0:
            painter.setPen(QPen(Qt.red, std_line_width // 2, Qt.DashLine))
            cutoff = self.y_origin - self.y_from_percent(min_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + 25, cutoff)
        if max_v < 100:
            painter.setPen(QPen(Qt.red, std_line_width // 2, Qt.DashLine))
            cutoff = self.y_origin - self.y_from_percent(max_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + 25, cutoff)

        point_markers = []  # Draw profile lines/histogram per vdu, current_profile last/on-top, collect point marker locations
        for vdu_id, vdu_data in [(vid, data) for vid, data in self.profile_data.items() if vid != self.current_vdu_id] + \
                                [(self.current_vdu_id, self.profile_data[self.current_vdu_id])]:
            last_x, last_y = 0, 0
            for point_data in vdu_data:
                lux = point_data.lux
                if point_data.preset_name is None:
                    brightness = point_data.brightness
                else:
                    preset = self.main_app.find_preset_by_name(point_data.preset_name)
                    brightness = preset.get_brightness(vdu_id) if preset is not None else -1
                if brightness >= 0:
                    vdu_line_color = QColor(self.vdu_chart_colors[vdu_id])
                    x = self.x_origin + self.x_from_lux(lux)
                    y = self.y_origin - self.y_from_percent(brightness)
                    if last_x and last_y:  # Join the previous and current point with a line
                        painter.setPen(QPen(vdu_line_color, std_line_width))
                        painter.drawLine(last_x, last_y, x, y)
                    if self.current_vdu_id == vdu_id:  # Special handling for the current/selected VDU
                        point_markers.append((point_data, x, y, lux, brightness))  # Save data for drawing markers later
                        if last_x and last_y:  # draw histogram rectangle
                            vdu_line_color.setAlpha(50)
                            painter.fillRect(last_x, last_y, x - last_x, self.y_origin - last_y, vdu_line_color)
                    last_x, last_y = x, y
            if self.current_vdu_id == vdu_id and last_x and last_y:   # Fill steps under the points
                painter.fillRect(last_x, last_y, 25, self.y_origin - last_y, vdu_line_color)

        for point_data, x, y, lux, brightness in point_markers:  # draw point markers on top of lines and histograms
            if point_data.preset_name is None:  # Normal point
                marker_diameter = std_line_width * 4
                painter.setPen(QPen(QColor(self.vdu_chart_colors[vdu_id]), std_line_width))
            else:  # Preset Point - fixed/non-deletable brightness level from Preset
                marker_diameter = std_line_width * 2
                painter.setPen(QPen(QColor(preset_color), std_line_width))
            painter.drawEllipse(x - marker_diameter // 2, y - marker_diameter // 2, marker_diameter, marker_diameter)

        for preset_point in self.preset_points:  # draw preset vertical lines and white triangle below axis
            painter.setPen(QPen(Qt.white, std_line_width // 2, Qt.DashLine))
            painter.setBrush(Qt.white)
            x = self.x_origin + self.x_from_lux(preset_point.lux)
            painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height)
            painter.drawPolygon([QPoint(x + tx//2, self.y_origin + 16 + ty//2) for tx, ty in triangle])

        if self.current_lux is not None:  # Draw vertical line at current lux
            painter.setPen(QPen(QColor(0xfec053), 2))  # fbc21b 0xffdd30 #fec053
            x = self.x_origin + self.x_from_lux(self.current_lux)
            painter.drawLine(x, self.y_origin + 10, x, self.y_origin - self.plot_height - 10)

        marker_diameter = std_line_width * 4
        mouse_pos = self.mapFromGlobal(self.cursor().pos())  # Draw cross-hairs at mouse pos
        mouse_x, mouse_y, margin = mouse_pos.x(), mouse_pos.y(), self.snap_to_margin
        if margin <= mouse_x <= self.width() - margin and margin <= mouse_y <= self.height() - margin:
            x = clamp(mouse_x, self.x_origin, self.x_origin + self.plot_width)
            y = clamp(mouse_y, self.y_origin - self.plot_height, self.y_origin)
            match = self.find_close_to(x - self.x_origin, self.y_origin - y, self.current_vdu_id)
            if match[0] is not None:  # Existing Point: snap to position for deleting the point under the mouse.
                x, y, lux, brightness, point_data = match[0] + self.x_origin, self.y_origin - match[1], match[2], match[3], match[4]
                point_preset_name = point_data.preset_name if point_data.preset_name is not None else ''
                if not point_preset_name:  # Existing normal point: cross-hairs, white for add, red for delete
                    painter.setPen(QPen(Qt.red if match[0] is not None else Qt.white, 2))
                    if match[0]:  # deletable: add a red circle
                        painter.setBrush(Qt.white)
                        painter.drawEllipse(x - marker_diameter // 2, y - marker_diameter // 2, marker_diameter, marker_diameter)
                    painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + 5, y)
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - 5)
                else:  # Existing Preset point: vertical line; plus removal hint, a red triangle below axis
                    painter.setPen(QPen(Qt.red if mouse_y > self.y_origin else Qt.white, 2))
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - 5)
                    painter.setPen(QPen(Qt.red, 2))
                    painter.setBrush(Qt.white)
                    painter.drawPolygon([QPoint(x + tx, self.y_origin + 18 + ty) for tx, ty in triangle])
                    if mouse_y > self.y_origin:  # Preset remove hint
                        painter.setPen(QPen(Qt.black, 1))
                        painter.drawText(x + 10, self.y_origin - 35, tr("Click remove preset at {} lux").format(lux))
            else:  # Potential new Point - show precise position for adding a new point
                lux, brightness = self.lux_from_x(x - self.x_origin), self.percent_from_y(y - self.y_origin)
                point_preset_name = ''
                painter.setPen(QPen(Qt.white, 1))
                painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + 5, y)
                painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - 5)
                if mouse_y > self.y_origin:  # Below axis, show hint for adding a Preset point: draw a red triangle below axis
                    painter.setPen(QPen(Qt.red, 2))
                    painter.setBrush(Qt.white)
                    painter.drawPolygon([QPoint(x + tx, self.y_origin + 18 + ty) for tx, ty in triangle])
                    painter.setPen(QPen(Qt.black, 1))
                    painter.drawText(x + 10, self.y_origin - 35, tr("Click to add preset at {} lux").format(lux))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawText(x + 10, y - 10, f"{lux} lux, {brightness}% {point_preset_name}")  # Tooltip lux and percent

        painter.end()
        self.setPixmap(pixmap)

    def set_current_profile(self, name: str):
        self.current_vdu_id = name
        self.create_plot()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        changed = False
        local_pos = self.mapFromGlobal(event.globalPos())
        x = local_pos.x() - self.x_origin
        y = self.y_origin - local_pos.y()
        if event.button() == Qt.LeftButton:
            if y >= 0:
                changed = self.lux_point_edit(x, y)
            else:
                changed = self.lux_preset_edit(x)
        if changed:
            self.show_changes()
        event.accept()

    def lux_point_edit(self, x, y) -> bool:
        vdu_data = self.profile_data[self.current_vdu_id]
        _, _, existing_lux, existing_percent, existing_point = self.find_close_to(x, y, self.current_vdu_id)
        if existing_lux is not None:  # Remove
            if existing_point.preset_name is None:
                vdu_data.remove(existing_point)
        else:  # Add
            percent = self.percent_from_y(y)
            lux = self.lux_from_x(x)
            vdu_data.append(LuxPoint(lux, percent))
            vdu_data.sort()
        return True

    def lux_preset_edit(self, x) -> bool:
        point = self.find_preset_point_close_to(x)
        if point is not None:  # Delete
            self.preset_points.remove(point)
            for vdu_id, profile in self.profile_data.items():
                for profile_point in profile:
                    if profile_point == point:  # Note: these will not be the same object
                        preset = self.main_app.find_preset_by_name(point.preset)
                        preset_brightness = preset.get_brightness(vdu_id) if preset is not None else -1
                        if preset_brightness >= 0: # Convert to normal point - as a convenience for the user
                            profile_point.preset_name = None
                            profile_point.brightness = preset_brightness
                        else:  # A Preset without a brightness value for this VDU - remove the point
                            profile.remove(profile_point)
                        break
            return True
        ask_preset = QInputDialog()
        presets = self.main_app.get_presets()
        ask_preset.setComboBoxItems(list(presets.keys()))
        ask_preset.setOption(QInputDialog.UseListViewForComboBoxItems)
        rc = ask_preset.exec()
        if rc == QDialog.Accepted:
            preset_name = ask_preset.textValue()
            point = LuxPoint(self.lux_from_x(x), -1, preset_name)
            self.preset_points.append(point)
            self.preset_points.sort()
            for profile in self.profile_data.values():
                profile.append(point)
                profile.sort()
            return True
        return False

    def show_changes(self):
        self.create_plot()
        self.update()
        self.chart_changed_callback()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.create_plot()
        self.update()

    def find_close_to(self, x: int, y: int, vdu_id: str) -> Tuple:
        r = self.snap_to_margin
        for point_data in self.profile_data[vdu_id]:
            existing_lux = point_data.lux
            if point_data.preset_name is None:
                existing_percent = point_data.brightness
            else:
                preset = self.main_app.find_preset_by_name(point_data.preset_name)
                if preset is not None:
                    existing_percent = preset.get_brightness(vdu_id)
                else:
                    continue  # Must have been deleted
            existing_x = self.x_from_lux(existing_lux)
            existing_y = self.y_from_percent(existing_percent)
            if existing_x - r <= x <= existing_x + r and (existing_y - r <= y <= existing_y + r or point_data.preset_name is not None):
                return existing_x, existing_y, existing_lux, existing_percent, point_data
        return None, None, None, None, None

    def find_preset_point_close_to(self, x: int):
        for point in self.preset_points:
            point_x = self.x_from_lux(point.lux)
            if abs(point_x - x) <= self.snap_to_margin:
                return point
        return None

    def percent_from_y(self, y):
        percent = round(100.0 * abs(y) / self.plot_height)
        min_v, max_v = self.range_restrictions[self.current_vdu_id]
        if percent > max_v:
            return max_v
        if percent < min_v:
            return min_v
        return percent

    def y_from_percent(self, percent):
        return round(self.plot_height * percent / 100)

    def lux_from_x(self, x):
        lux = 0 if x <= 0 else round(10.0 ** (math.log10(1) + (x / self.plot_width) * (math.log10(100_000) - math.log10(1))))
        if lux > 100_000:
            return 100_000
        return lux

    def x_from_lux(self, lux: int) -> int:
        return round((math.log10(lux) - math.log10(1)) / ((math.log10(100000) - math.log10(1)) / self.plot_width)) if lux > 0 else 0


class LuxMeterWidget(QWidget):

    def __init__(self, lux_changed_callback: Callable, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.current_lux_display = QLabel()
        self.lux_changed_callback = lux_changed_callback
        big_font = self.current_lux_display.font()
        big_font.setPointSize(big_font.pointSize() + 8)
        self.current_lux_display.setFont(big_font)
        self.layout().addWidget(self.current_lux_display)
        self.history = [0] * 50
        self.lux_plot = QLabel()
        self.lux_plot.setFixedWidth(200)
        self.lux_plot.setFixedHeight(100)
        self.layout().addWidget(self.lux_plot)
        self.lux_meter_worker: LuxMeterWidgetThread | None = None

    def display_lux(self, lux: int):
        self.current_lux_display.setText(tr("Lux: {}".format(lux)))
        self.history = self.history[-100:]
        self.history.append(lux)
        pixmap = QPixmap(self.lux_plot.width(), self.lux_plot.height())
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, self.lux_plot.width(), self.lux_plot.height(), QColor(0x6baee8))  # 0x5b93c5))
        painter.setPen(QPen(QColor(0xfec053), 1))  # fbc21b 0xffdd30 #fec053
        for i in range(len(self.history)):
            painter.drawLine(i, self.lux_plot.height(), i, self.lux_plot.height() - self.y_from_lux(self.history[i]))
        painter.end()
        self.lux_plot.setPixmap(pixmap)
        self.lux_changed_callback(lux)

    def interrupt_history(self):
        if len(self.history) > 1:
            self.history = (self.history + [0] * 10)[-100:]

    def start_metering(self, lux_meter):
        self.stop_metering()
        self.lux_meter_worker = LuxMeterWidgetThread(lux_meter)
        self.lux_meter_worker.new_lux_value.connect(self.display_lux)
        self.lux_meter_worker.start()

    def stop_metering(self):
        if self.lux_meter_worker is not None:
            self.lux_meter_worker.stop_requested = True
            self.lux_meter_worker.new_lux_value.disconnect(self.display_lux)
            self.interrupt_history()
            self.lux_meter_worker = None

    def y_from_lux(self, lux: int) -> int:
        return round(
            (math.log10(lux) - math.log10(1)) / ((math.log10(100000) - math.log10(1)) / self.lux_plot.height())) if lux > 0 else 0


class LuxMeterWidgetThread(WorkerThread):
    new_lux_value = pyqtSignal(int)

    def __init__(self, lux_meter: LuxMeterSerialDevice):
        super().__init__(task_body=self.read_meter)
        self.lux_meter = lux_meter
        self.stop_requested = False

    def read_meter(self):
        while not self.stop_requested:
            if self.lux_meter is None:
                return
            self.new_lux_value.emit(round(self.lux_meter.get_cached_value(5.0)))
            time.sleep(5.0)


def lux_create_device(device_name: str):
    if not pathlib.Path(device_name).exists():
        raise LuxDeviceException(tr("Failed to setup {} - path does not exist.").format(device_name))
    if not os.access(device_name, os.R_OK):
        raise LuxDeviceException(tr("Failed to setup {} - no read access to device.").format({device_name}))
    if pathlib.Path(device_name).is_char_device():
        return LuxMeterSerialDevice(device_name)
    elif pathlib.Path(device_name).is_fifo():
        return LuxMeterFifoDevice(device_name)
    elif pathlib.Path(device_name).exists() and os.access(device_name, os.X_OK):
        return LuxMeterRunnableDevice(device_name)
    raise LuxDeviceException(tr("Failed to setup {} - not an recognised kind of device or not executable.").format(device_name))


class LuxMeterFifoDevice:

    def __init__(self, device_name: str, thread: QThread = None):
        super().__init__()
        self.device_name = device_name
        self.fifo = None
        self.lock = Lock()
        self.cached_value = None
        self.cached_time = time.time()
        self.thread = thread

    def get_cached_value(self, age_seconds: float) -> float:
        if self.cached_value is not None and time.time() - self.cached_time <= age_seconds:
            return self.cached_value
        self.cached_value = self.get_value()
        self.cached_time = time.time()
        return self.cached_value

    def get_value(self) -> float:
        with self.lock:
            while True:
                try:
                    if self.fifo is None:
                        log_info(f"Initialising fifo {self.device_name} - waiting on fifo data.")
                        self.fifo = open(self.device_name)
                    if len(select.select([self.fifo], [], [], 5.0)[0]) == 1:
                        buffer = self.fifo.readline()
                        if len(select.select([self.fifo], [], [], 0.0)[0]) == 0 and buffer is not None:  # Buffer has been flushed
                            return float(buffer.replace('\n', ''))
                except (OSError, ValueError) as se:
                    log_warning(f"Retry read of {self.device_name}, will retry feed in 10 seconds", se)
                    time.sleep(10)

    def close(self):
        with self.lock:
            if self.fifo is not None:
                os.close(self.fifo)


class LuxMeterRunnableDevice:

    def __init__(self, device_name: str, thread: QThread = None):
        super().__init__()
        self.runnable = device_name
        self.lock = Lock()
        self.cached_value = None
        self.cached_time = time.time()
        self.thread = thread

    def get_cached_value(self, age_seconds: float) -> float:
        if self.cached_value is not None and time.time() - self.cached_time <= age_seconds:
            return self.cached_value
        self.cached_value = self.get_value()
        self.cached_time = time.time()
        return self.cached_value

    def get_value(self) -> float:
        with self.lock:
            while True:
                try:
                    result = subprocess.run([self.runnable], stdout=subprocess.PIPE, check=True)
                    return float(result.stdout)
                except (OSError, ValueError, subprocess.CalledProcessError) as se:
                    log_warning(f"Error running {self.runnable}, will retry in 10 seconds", se)
                    time.sleep(10)

    def close(self):
        pass


class LuxMeterSerialDevice:

    def __init__(self, device_name: str):
        super().__init__()
        self.device_name = device_name
        self.serial_device = None
        self.lock = Lock()
        self.cached_value = None
        self.cached_time = time.time()
        try:
            self.serial_module = import_module('serial')
        except ModuleNotFoundError as mnf:
            raise LuxDeviceException(tr("The required pyserial serial-port module is not installed on this system."))

    def get_cached_value(self, age_seconds: float) -> float:  # Used for metering where an up-to-date value is less important
        if self.cached_value is not None and time.time() - self.cached_time <= age_seconds:
            return self.cached_value
        self.cached_value = self.get_value()
        self.cached_time = time.time()
        return self.cached_value

    def get_value(self) -> float:  # an un-smoothed raw value
        with self.lock:
            backoff_secs = 10
            while True:
                try:
                    if self.serial_device is None:
                        log_info(f"Initialising character device {self.device_name} - waiting on data.")
                        self.serial_device = self.serial_module.Serial(self.device_name)
                    self.serial_device.flushInput()
                    time.sleep(0.1)
                    buffer = self.serial_device.readline()
                    value = float(buffer.decode('utf-8').replace("\r\n", ''))
                    return value
                except (self.serial_module.SerialException, termios.error, FileNotFoundError, ValueError) as se:
                    log_warning(f"Retry read of {self.device_name}, will reopen feed in {backoff_secs} seconds", se)
                    time.sleep(backoff_secs)
                    backoff_secs = backoff_secs * 2 if backoff_secs < 300 else 300
                    if self.serial_device is not None:
                        self.serial_device.close()
                    self.serial_device = None

    def close(self):
        with self.lock:
            if self.serial_device is not None:
                self.serial_device.close()


class LuxSmooth:
    def __init__(self, n, alpha=0.5):
        self.length = n
        self.input = []
        self.output = []
        self.alpha = alpha

    def smooth(self, v):  # A low pass filter
        # The smaller the alpha, the more each previous value affects the following value. Smaller alpha results => more smoothing.
        # https://stackoverflow.com/questions/4611599/smoothing-data-from-a-sensor
        # https://en.wikipedia.org/wiki/Low-pass_filter#Simple_infinite_impulse_response_filter
        if len(self.input) == self.length:
            self.input.pop(0)
            self.output.pop(0)
        self.input.append(v)
        self.output.append(v)  # extend to same length - value will be overwritten if there is more than one sample.
        for i in range(1, len(self.input)):
            self.output[i] = self.output[i-1] + self.alpha * (self.input[i] - self.output[i-1])
        return self.output[-1]


class LuxAutoWorker(WorkerThread):
    working = pyqtSignal()
    _refresh_gui_view = pyqtSignal(VduControlBase)
    _message = pyqtSignal(str)

    def __init__(self, auto_controller: LuxAutoController):
        super().__init__(task_body=self.adjust_for_lux, task_finished=self.finished_callable)
        self.auto_controller = auto_controller
        self.main_app = auto_controller.main_app
        self.last_value = None
        self.stop_requested = False
        self.consecutive_errors = 0
        self.target_brightness: Dict[str, int] = {}
        self.previous_metered_lux = 0
        self.smoother = LuxSmooth(auto_controller.lux_config.getint('lux-meter', 'smoother-n', fallback=5),
                                  alpha=auto_controller.lux_config.getfloat('lux-meter', 'smoother-alpha', fallback=0.5))
        log_info(f"LuxAutoWorker: smoother n={self.smoother.length} alpha={self.smoother.alpha}" )

        def refresh_control(control: VduControlBase):
            control.refresh_view()

        self._refresh_gui_view.connect(refresh_control)  # Make sure GUI refreshes occur in the GUI thread (this thread).

        def lux_message(message: str):
            if LuxDialog.exists():
                dialog = LuxDialog.get_instance()
                dialog.display_message(message)

        self._message.connect(lux_message)

    def adjust_for_lux(self):
        time.sleep(2.0)  # Give any previous thread a chance to exit
        log_info(f"LuxAutoWorker monitoring commences (Thread={threading.get_ident()})")
        self._message.emit(tr("Brightness auto adjustment monitoring commences."))
        try:
            step_count = 0  # No zero if work is in progress, zero if there is nothing to do
            while not self.stop_requested:
                self.working.emit()
                lux_auto_controller = self.main_app.lux_auto_controller
                if lux_auto_controller.lux_meter is None:  # In app config change
                    log_error("Exiting, no lux meter available.")
                    break
                lux_config = lux_auto_controller.lux_config.load()  # Refresh
                metered_lux = lux_auto_controller.lux_meter.get_value()
                smoothed_lux = round(self.get_smoothed_value(metered_lux))  # Get new smoothed lux value
                if self.perform_one_step(lux_config, metered_lux, smoothed_lux, step_count):  # if some work was done
                    step_count += 1
                else:   # No work done this cycle, sleep longer
                    step_count = 0
                    sleep_end_time = time.time() + lux_auto_controller.lux_config.get_interval_minutes() * 60.0 - 0.5
                    while not self.stop_requested and time.time() < sleep_end_time:
                        time.sleep(1.0)  # Sleep for the lux-check-interval - but check for stop requests.
        finally:
            log_info(f"LuxAutoWorker exiting (stop_requested={self.stop_requested}) (Thread={threading.get_ident()})")

    def perform_one_step(self, lux_config: LuxConfig, metered_lux: int, smoothed_lux: int, step_count: int) -> bool:
        profile_preset_name = None  # should be at most one for a given lux value.
        made_brightness_changes = False
        for control_panel in self.main_app.main_panel.vdu_control_panels:  # For each VDU, find its profile and apply it
            if self.stop_requested:
                break
            controller = control_panel.controller
            profile_brightness = -1  # Just in case we don't get a match
            vdu_id = controller.vdu_stable_id
            for lux_point in lux_config.get_vdu_profile(controller, self.main_app):  # find the appropriate point in the profile
                if smoothed_lux >= lux_point.lux:
                    if lux_point.preset_name is None:  # Normal Point
                        profile_brightness = lux_point.brightness
                    else:  # Point with a Preset attached at this lux value, might only be this point and not others.
                        # profile_brightness will be -1 if the Preset doesn't specify a brightness value.
                        preset = self.main_app.find_preset_by_name(lux_point.preset_name)
                        if preset:
                            profile_brightness = preset.get_brightness(vdu_id)
                            profile_preset_name = lux_point.preset_name
            brightness_control = next((c for c in control_panel.vcp_controls if c.vcp_capability.vcp_code == '10'), None)
            if profile_brightness >= 0 and brightness_control is not None:  # can only adjust brightness controls
                try:
                    current_brightness = int(controller.get_attribute('10')[0])
                    if not self.stop_requested and current_brightness != profile_brightness:
                        made_brightness_changes = True
                        if vdu_id not in self.target_brightness or self.target_brightness[vdu_id] != profile_brightness:
                            self.target_brightness[vdu_id] = profile_brightness
                            if step_count == 0:
                                log_info(f"LuxAutoWorker: stepping commences vdu={vdu_id} current={current_brightness}%"
                                         f" target={profile_brightness}% lux={metered_lux} smoothed-lux=={smoothed_lux} step=1")
                            else:  # lux level must have changed, so target brightness has changed
                                log_info(f"LuxAutoWorker: target changed vdu={vdu_id} current={current_brightness}%" 
                                         f" target={profile_brightness}% lux={metered_lux} smoothed-lux={smoothed_lux} step={step_count}")
                        diff = profile_brightness - current_brightness
                        step_size = max(1, abs(diff) // 3)  # 4 if abs(diff) < 8 else 8  # TODO find a good heuristic
                        step = int(math.copysign(step_size, diff)) if abs(diff) > step_size else diff
                        self._message.emit(tr("Adjusting {} by {}").format(vdu_id, step_size))
                        if step_count != 0 and log_debug_enabled:
                            log_debug(f"LuxAutoWorker: vdu={vdu_id} current={current_brightness}% target={profile_brightness}%"
                                      f" lux={metered_lux} smoothed-lux={smoothed_lux} step={step_count}")
                        brightness_control.restore_vdu_attribute(str(current_brightness + step))
                        raise VduException("test")
                        self._refresh_gui_view.emit(brightness_control)
                        raise VduException("test")
                        self.consecutive_errors = 0
                except VduException as ve:
                    self.consecutive_errors += 1
                    if self.consecutive_errors == 1:
                        self._message.emit(tr("Failed to adjust {}, will try again").format(vdu_id))
                        log_warning(f"LuxAutoWorker: Brightness error on {vdu_id}, will sleep and try again: {ve}")
                    elif self.consecutive_errors > 1:
                        self._message.emit(
                            tr("Failed to adjust {}, {} errors so far. Sleeping {} minutes.").format(
                                vdu_id, self.consecutive_errors, self.auto_controller.lux_config.get_interval_minutes()))
                        if self.consecutive_errors == 2 or log_debug_enabled:
                            log_info(f"LuxAutoWorker: multiple errors count={self.consecutive_errors}, sleeping and retrying.")
                        return False  # force a full sleep cycle.
        if not made_brightness_changes:
            if step_count != 0:   # Have now finished past work, if a point had a Preset attached, activate it now
                log_info(f"LuxAutoWorker: stepping completed step={step_count}")  # Only if work was done
                self._message.emit(tr("Stepping completed"))
                if profile_preset_name is not None:
                    # Finish by restoring the Preset's non-brightness controls, do it now, while this lux thread is not active.
                    log_info(f"LuxAutoWorker: triggering Preset {profile_preset_name}")
                    self._message.emit(tr("Restoring preset {}").format(profile_preset_name))
                    preset = self.main_app.find_preset_by_name(profile_preset_name)
                    if preset is not None:
                        self.main_app.restore_preset_in_gui_thread(preset)
        else:
            time.sleep(0.5)  # Let i2c settle down, then continue stepping
        return made_brightness_changes

    def get_smoothed_value(self, metered_value: float) -> float:  # A smoothed value
        smoothed = self.smoother.smooth(metered_value)
        return smoothed

    def finished_callable(self):
        if self.vdu_exception:
            log_error(f"LuxAutoWorker exited with exception={self.vdu_exception}")


class LuxPoint:

    def __init__(self, lux: int, brightness: int, preset_name: str | None = None):
        self.lux = lux
        self.brightness = brightness
        self.preset_name = preset_name

    def __lt__(self, other):
        return self.lux < other.lux

    def __eq__(self, other):
        return self.lux == other.lux and self.preset_name == other.preset_name


class LuxConfig(ConfigIni):

    def __init__(self):
        super().__init__()
        self.path = get_config_path('AutoLux')
        self.last_modified_time = 0.0

    def get_device_name(self):
        return self.get("lux-meter", "lux-device", fallback=None)

    def set_device_name(self, device_name: str):
        self.set("lux-meter", "lux-device", device_name)

    def get_vdu_profile(self, vdu: VduController, main_app: VduAppWindow) -> List[LuxPoint]:
        if self.has_option('lux-profile', vdu.vdu_stable_id):
            lux_points = [LuxPoint(v[0], v[1]) for v in literal_eval(self.get('lux-profile', vdu.vdu_stable_id))]
        else:  # Use a default profile:
            range_restriction = vdu.capabilities['10'].values
            min_v, max_v = (0, 100) if len(range_restriction) == 0 else (int(range_restriction[1]), int(range_restriction[2]))
            lux_values = [0, 10, 100, 1_000, 10_000, 100_000]
            brightness_values = [15, 15, 70, 90, 95, 100]
            brightness_values = [v if v >= min_v else min_v for v in brightness_values]
            brightness_values = [v if v <= max_v else max_v for v in brightness_values]
            lux_points = [LuxPoint(lux, brightness) for lux, brightness in  zip(lux_values, brightness_values)]
        if self.has_option('lux-presets', 'lux-preset-points'):
            preset_points = [LuxPoint(lux, -1, name) for lux, name in literal_eval(self.get('lux-presets', 'lux-preset-points'))]
            lux_points = lux_points + preset_points
            lux_points.sort()
        return lux_points

    def get_preset_points(self):
        lux_preset_points = []
        if self.has_option('lux-presets', 'lux-preset-points'):
            for value in literal_eval(self.get('lux-presets', 'lux-preset-points')):
                lux_preset_points.append(LuxPoint(value[0], -1, value[1]))
        return lux_preset_points

    def get_interval_minutes(self) -> int:
        return self.getint('lux-meter', 'interval-minutes', fallback=1)

    def is_auto_enabled(self):
        return self.getboolean("lux-meter", "automatic-brightness", fallback=False)

    def load(self, force: bool = False) -> LuxConfig:
        if self.path.exists():
            if Path.stat(self.path).st_mtime > self.last_modified_time or force:
                log_info(f"Reading autolux file '{self.path.as_posix()}'")
                text = Path(self.path).read_text()
                self.read_string(text)
                self.last_modified_time = Path.stat(self.path).st_mtime
        for section_name in ['lux-meter', 'lux-profile', 'lux-ui', 'lux-presets']:
            if not self.has_section(section_name):
                self.add_section(section_name)
        return self


class LuxDialog(QDialog, DialogSingletonMixin):

    @staticmethod
    def invoke(main_app: VduAppWindow) -> None:
        LuxDialog.show_existing_dialog() if LuxDialog.exists() else LuxDialog(main_app)

    def __init__(self, main_app: VduAppWindow):
        super().__init__()
        self.setWindowTitle(tr('Light-Meter'))
        self.main_app = main_app
        self.profile_data = {}
        self.range_restrictions = {}
        self.preset_points = []
        self.vdu_chart_color = {}
        self.has_profile_changes = False
        self.setMinimumWidth(800)

        self.path = get_config_path('AutoLux')

        self.device_name = ''
        self.config: LuxConfig | None = None

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        top_box = QWidget()
        main_layout.addWidget(top_box)
        grid_layout = QGridLayout()
        top_box.setLayout(grid_layout)

        self.profile_plot: LuxConfigChart | None = None

        def lux_changed(lux: int):
            if self.profile_plot:
                self.profile_plot.current_lux = lux
                self.profile_plot.create_plot()

        self.lux_meter_widget = LuxMeterWidget(lux_changed, parent=self)
        self.lux_meter_widget.display_lux(0)
        grid_layout.addWidget(self.lux_meter_widget, 0, 0, 3, 3, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.meter_device_selector = PushButtonLeftJustified()
        self.meter_device_selector.setText(tr("No metering source selected"))
        grid_layout.addWidget(self.meter_device_selector, 0, 2, 1, 3)

        self.enabled_checkbox = QCheckBox(tr("Enable automatic brightness adjustment"))
        grid_layout.addWidget(self.enabled_checkbox, 1, 2, 1, 3)

        self.interval_label = QLabel(tr("Adjustment interval minutes"))
        grid_layout.addWidget(self.interval_label, 2, 2, 1, 2)

        self.interval_selector = QSpinBox()
        self.interval_selector.setMinimum(1)
        self.interval_selector.setMaximum(120)
        grid_layout.addWidget(self.interval_selector, 2, 4, 1, 1)

        self.profile_selector = QComboBox()
        main_layout.addWidget(self.profile_selector)

        self.profile_plot = LuxConfigChart(self)
        main_layout.addWidget(self.profile_plot, 1)

        buttons_widget = QWidget()
        button_layout = QHBoxLayout()
        buttons_widget.setLayout(button_layout)

        save_button = QPushButton(si(self, QStyle.SP_DriveFDIcon), tr("Apply"))
        save_button.setToolTip(tr("Save and apply charted VDU profiles."))
        save_button.clicked.connect(partial(self.save_profiles))
        button_layout.addWidget(save_button, 0, Qt.AlignBottom | Qt.AlignLeft)

        revert_button = QPushButton(si(self, QStyle.SP_DriveFDIcon), tr("Revert"))
        revert_button.setToolTip(tr("Revert charted VDU profiles to those last saved."))
        revert_button.clicked.connect(self.reinitialise)
        button_layout.addWidget(revert_button, 0, Qt.AlignBottom | Qt.AlignLeft)

        button_layout.addSpacing(30)
        self.message_area = QLabel("Lux Meter")
        button_layout.addWidget(self.message_area)
        button_layout.addStretch(0)

        quit_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr("Close"))
        quit_button.clicked.connect(self.close)
        button_layout.addWidget(quit_button, 0, Qt.AlignBottom | Qt.AlignRight)

        main_layout.addWidget(buttons_widget)  # TODO Replace with a QStatusBar?

        def choose_device():
            device_name = QFileDialog.getOpenFileName(self, tr("Select a tty device or fifo"), "/dev/ttyUSB0")[0]
            if device_name != '':
                device_name = self.validate_device(device_name)
                if device_name is not None:
                    if device_name != self.config.get('lux-meter', 'lux-device', fallback=None):
                        self.config.set('lux-meter', "lux-device", device_name)
                        self.save_settings()

        self.meter_device_selector.pressed.connect(choose_device)

        def set_auto_monitoring(checked: int):
            if (checked == Qt.Checked) != self.config.is_auto_enabled():
                self.config.set('lux-meter', 'automatic-brightness', 'yes' if checked == Qt.Checked else 'no')
                self.save_settings()

        self.enabled_checkbox.stateChanged.connect(set_auto_monitoring)

        def interval_selector_changed() -> None:
            self.config.set('lux-meter', 'interval-minutes', str(self.interval_selector.value()))
            self.save_settings(requires_auto_brightness_restart=False)

        self.interval_selector.valueChanged.connect(interval_selector_changed)

        def select_profile(index: int):
            if self.profile_plot is not None:
                self.profile_plot.set_current_profile(list(self.profile_data.keys())[index])
            if self.config.get('lux-ui', 'selected-profile', fallback=None) != self.profile_selector.itemData(index):
                self.config.set('lux-ui', 'selected-profile', self.profile_selector.itemData(index))
                self.save_settings()

        self.profile_selector.currentIndexChanged.connect(select_profile)
        self.make_visible()
        self.in_constructor = False

    def chart_changed_callback(self):
        self.has_profile_changes = True

    def reinitialise(self):

        self.config: LuxConfig = self.main_app.lux_auto_controller.lux_config.duplicate(LuxConfig())
        self.device_name = self.config.get("lux-meter", "lux-device", fallback=None)
        self.enabled_checkbox.setChecked(self.config.is_auto_enabled())
        self.has_profile_changes = False

        new_id_list = []   # List of all currently connected VDU's
        for index, vdu in enumerate(self.main_app.vdu_controllers):
            range_restriction = vdu.capabilities['10'].values
            min_v, max_v = (0, 100) if len(range_restriction) == 0 else (int(range_restriction[1]), int(range_restriction[2]))
            self.range_restrictions[vdu.vdu_stable_id] = min_v, max_v
            self.profile_data[vdu.vdu_stable_id] = self.config.get_vdu_profile(vdu, self.main_app)
            new_id_list.append(vdu.vdu_stable_id)
        self.preset_points.clear()
        for preset_point in self.config.get_preset_points():  # Edit out deleted presets.
            if self.main_app.find_preset_by_name(preset_point.preset_name):
                self.preset_points.append(preset_point)

        self.validate_device(self.device_name)
        self.interval_selector.setValue(self.config.get_interval_minutes())

        existing_id_list = [self.profile_selector.itemData(index) for index in range(0, self.profile_selector.count())]
        existing_selected_id = self.config.get('lux-ui', 'selected-profile', fallback=new_id_list[0] if new_id_list else None)
        self.profile_selector.blockSignals(True)  # Stop initialization from causing signally until all data is aligned.
        if new_id_list != existing_id_list:  # List of connected VDU's has changed
            self.profile_selector.clear()
            random.seed(0x543fff)
            self.vdu_chart_color.clear()
            for index, vdu in enumerate(self.main_app.vdu_controllers):
                color = QColor.fromHsl(int(index * 137.508) % 255, random.randint(64, 128), random.randint(192, 200))
                self.vdu_chart_color[vdu.vdu_stable_id] = color
                color_icon = create_themed_icon_from_svg_bytes(SWATCH_ICON_SOURCE.replace(b"#ffffff", bytes(color.name(), 'utf-8')))
                self.profile_selector.addItem(color_icon, vdu.get_vdu_description(), userData=vdu.vdu_stable_id)
                if vdu.vdu_stable_id == existing_selected_id:
                    self.profile_selector.setCurrentIndex(index)
                    self.profile_plot.current_vdu_id = existing_selected_id
        self.profile_selector.blockSignals(False)
        self.lux_meter_widget.start_metering(self.main_app.lux_auto_controller.lux_meter)

    def make_visible(self):
        super().make_visible()
        self.display_message("")
        self.reinitialise()

    def validate_device(self, device):
        if device is None or device.strip() == '':
            return None
        path = pathlib.Path(device)
        if path.is_char_device():
            self.meter_device_selector.setText(tr(" Device {}").format(device))
        elif path.is_fifo():
            self.meter_device_selector.setText(tr(" Fifo {}").format(device))
        elif path.exists() and os.access(device, os.X_OK):
            self.meter_device_selector.setText(tr(" Run {}").format(device))
        else:
            self.meter_device_selector.setText(tr(" Not available {}").format(device))
            return None
        if not os.access(device, os.R_OK):
            alert = MessageBox(QMessageBox.Critical)
            alert.setText(tr("No read access to {}").format(device))
            if path.is_char_device() and path.group() != "root":
                alert.setInformativeText(tr("You might need to be a member of the {} group.").format(path.group()))
            alert.exec()
        return device

    def display_message(self, message):
        self.message_area.setText(message)

    def save_settings(self, requires_auto_brightness_restart: bool = True):
        self.has_profile_changes = False
        self.config.save(self.path)
        if requires_auto_brightness_restart:
            self.main_app.lux_auto_controller.refresh_from_config()
            self.lux_meter_widget.stop_metering()
            self.lux_meter_widget.start_metering(self.main_app.lux_auto_controller.lux_meter)

    def save_profiles(self):
        for vdu_id, profile in self.profile_plot.profile_data.items():
            data = [(lux_point.lux, lux_point.brightness) for lux_point in profile if lux_point.preset_name is None]
            self.config.set('lux-profile', vdu_id, repr(data))
        data = [(lux_point.lux, lux_point.preset_name) for lux_point in self.profile_plot.preset_points]
        self.config.set('lux-presets', 'lux-preset-points', repr(data))
        self.save_settings(True)

    def closeEvent(self, event) -> None:
        if self.has_profile_changes:
            alert = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                               default=QMessageBox.Cancel)
            alert.setText(tr("There are unsaved profile changes?"))
            answer = alert.exec()
            if answer == QMessageBox.Save:
                self.save_profiles()
            elif answer == QMessageBox.Cancel:
                event.ignore()
                return
        self.lux_meter_widget.stop_metering()
        super().closeEvent(event)


class LuxDeviceException(Exception):
    pass


class LuxAutoController:

    def __init__(self, main_app: VduAppWindow) -> None:
        super().__init__()
        self.main_app = main_app
        self.lux_config: LuxConfig | None = None
        self.lux_meter: LuxMeterSerialDevice | None = None
        self.lux_auto_brightness_worker: LuxAutoWorker | None = None
        self.lux_button: ToolButton | None = None
        self.create_tool_button()

    def create_tool_button(self) -> ToolButton:
        self.lux_button = ToolButton(AUTO_LUX_ON_SVG, tr("Toggle automatic brightness control"))
        self.lux_button.pressed.connect(self.toggle_auto)
        return self.lux_button

    def refresh_from_config(self):
        assert(is_running_in_gui_thread())
        self.lux_config = LuxConfig().load()
        try:
            if self.lux_config.get_device_name() is not None and  self.lux_config.get_device_name().strip() != '':
                self.lux_meter = lux_create_device(self.lux_config.get_device_name())
            if self.lux_config.is_auto_enabled():
                log_info("Lux auto-brightness settings refresh - restart monitoring.")
                if self.lux_meter is not None:
                    if self.lux_auto_brightness_worker is not None:
                        self.lux_auto_brightness_worker.stop_requested = True
                        self.lux_auto_brightness_worker.working.disconnect(self.main_app.display_lux_auto_indicators)
                    self.lux_auto_brightness_worker = LuxAutoWorker(self)
                    self.lux_auto_brightness_worker.working.connect(self.main_app.display_lux_auto_indicators)
                    self.lux_auto_brightness_worker.start()
                self.main_app.display_lux_auto_indicators()  # Refresh indicators immediately
            else:
                log_info("Lux auto-brightness settings refresh - monitoring is off.")  # TODO handle exception
                if self.lux_auto_brightness_worker is not None:
                    self.lux_auto_brightness_worker.stop_requested = True
                    self.lux_auto_brightness_worker.working.disconnect(self.main_app.display_lux_auto_indicators)
                    self.lux_auto_brightness_worker = None
                    self.main_app.display_lux_auto_indicators()

        except LuxDeviceException as lde:
            log_error(f"Error setting up lux meter {lde}")
            alert = MessageBox(QMessageBox.Critical)
            alert.setText(tr("Error setting up lux meter: {}").format(self.lux_config.get_device_name()))
            alert.setInformativeText(str(lde))
            alert.exec()
        self.lux_button.refresh_icon(self.current_auto_svg())  # Refresh indicators immediately

    def is_auto_enabled(self):
        return self.lux_config is not None and self.lux_config.is_auto_enabled()

    def current_auto_svg(self):
        return AUTO_LUX_ON_SVG if self.is_auto_enabled() else AUTO_LUX_OFF_SVG

    def toggle_auto(self):
        enabled = self.is_auto_enabled()
        self.lux_config.set('lux-meter', 'automatic-brightness', 'no' if enabled else 'yes')
        self.lux_config.save(get_config_path('AutoLux'))
        self.refresh_from_config()
        lux_dialog = LuxDialog.get_instance()
        if lux_dialog is not None:
            lux_dialog.reinitialise()
        return enabled


class GreyScaleDialog(QDialog):
    """Creates a dialog with a grey scale VDU calibration image.  Non-model. Have as many as you like - one per VDU."""

    # This stops garbage collection of independent instances of this dialog until the user closes them.
    # If you don't do this the dialog will disappear before it becomes visible.  Could also pass a parent
    # which would achieve the same thing - but would alter where the dialog appears.
    _active_list: List[QDialog] = []

    def __init__(self):
        super().__init__()
        GreyScaleDialog._active_list.append(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle(tr('Grey Scale Reference'))
        self.setModal(False)
        svg_widget = QSvgWidget()
        svg_widget.renderer().load(GREY_SCALE_SVG)
        svg_widget.setMinimumWidth(600)
        svg_widget.setMinimumHeight(400)
        svg_widget.setToolTip(tr(
            'Grey Scale Reference for VDU adjustment.\n\n'
            'Set contrast toward the maximum (for HDR monitors\n'
            'try something lower such as 70%) and adjust brightness\n'
            'until as many rectangles as possible can be perceived.\n\n'
            'Use the content-menu to create additional charts and\n'
            'drag them onto each display.\n\nThis chart is resizable. '))
        layout.addWidget(svg_widget)
        close_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr("Close"))
        close_button.clicked.connect(self.hide)
        layout.addWidget(close_button, 0, Qt.AlignRight)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        GreyScaleDialog._active_list.remove(self)
        event.accept()


class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def invoke():
        AboutDialog.show_existing_dialog() if AboutDialog.exists() else AboutDialog()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('About'))
        self.setTextFormat(Qt.AutoText)
        self.setText(tr('About vdu_controls'))
        path = find_locale_specific_file("about_{}.txt")
        if path:
            with open(path, encoding='utf-8') as about_for_locale:
                about_text = about_for_locale.read().format(
                    VDU_CONTROLS_VERSION=VDU_CONTROLS_VERSION,
                    IP_ADDRESS_INFO_URL=IP_ADDRESS_INFO_URL,
                    WEATHER_FORECAST_URL=WEATHER_FORECAST_URL)
        else:
            about_text = ABOUT_TEXT
        self.setInformativeText(about_text)
        self.setIcon(QMessageBox.Information)
        self.setModal(False)
        self.show()
        self.raise_()
        self.activateWindow()


class HelpDialog(QDialog, DialogSingletonMixin):

    @staticmethod
    def invoke():
        HelpDialog.show_existing_dialog() if HelpDialog.exists() else HelpDialog()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('Help'))
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setMarkdown(__doc__)
        layout.addWidget(markdown_view)
        close_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr("Close"))
        close_button.clicked.connect(self.hide)
        layout.addWidget(close_button, 0, Qt.AlignRight)
        self.setLayout(layout)
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(1200, 768)


class ScheduleStatus(Enum):
    UNSCHEDULED = 0, ' ', QT_TR_NOOP('unscheduled')
    # This hourglass character is too tall - it causes a jump when rendered - but nothing else is quite as appropriate.
    SCHEDULED = 1, TIMER_RUNNING_SYMBOL, QT_TR_NOOP('scheduled')
    SUSPENDED = 2, ' ', QT_TR_NOOP('suspended')
    SUCCEEDED = 3, SUCCESS_SYMBOL, QT_TR_NOOP('succeeded')
    SKIPPED_SUPERSEDED = 4, SKIPPED_SYMBOL, QT_TR_NOOP('skipped, superseded')
    WEATHER_CANCELLATION = 5, WEATHER_CANCELLATION_SYMBOL, QT_TR_NOOP('weather cancellation')

    def symbol(self) -> str:
        return self.value[1]

    def description(self):
        return self.value[2]

    def __str__(self):
        return self.value[0]


class TransitionType(IntFlag):
    _ignore_ = ['abbreviations', 'descriptions']  # Seems very hacky

    NONE = 0
    SCHEDULED = 1
    MENU = 2
    SIGNAL = 4
    ALWAYS = 7

    abbreviations = {NONE: '',
                     SCHEDULED: TIME_CLOCK_SYMBOL,
                     MENU: MENU_SYMBOL,
                     SIGNAL: SIGNAL_SYMBOL,
                     ALWAYS: TRANSITION_ALWAYS_SYMBOL}

    descriptions = {
        NONE: QT_TR_NOOP('Never'),
        SCHEDULED: QT_TR_NOOP('On schedule'),
        MENU: QT_TR_NOOP('On menu'),
        SIGNAL: QT_TR_NOOP('On signal'),
        ALWAYS: QT_TR_NOOP('Always')}

    def abbreviation(self, abbreviations=abbreviations) -> str:  # Even more hacky
        if self.value in (TransitionType.NONE, TransitionType.ALWAYS):
            return abbreviations[self]
        return TRANSITION_SYMBOL + ''.join([abbreviations[component] for component in self.component_values()])

    def description(self, descriptions=descriptions):  # Yuck
        if self.value in (TransitionType.NONE, TransitionType.ALWAYS):
            return descriptions[self]
        return ','.join([descriptions[component] for component in self.component_values()])

    def component_values(self) -> List[TransitionType]:
        # similar to Python 3.11 enum.show_flag_values(self) - list of power of two components for self
        return [option for option in TransitionType if (option & (option - 1) == 0) and option != 0 and option in self]

    def __str__(self):
        if self.value == TransitionType.NONE:
            return self.name.lower()
        return ','.join([component.name.lower() for component in self.component_values()])


def parse_transaction_type(string_value: str):
    transaction_type = TransitionType.NONE
    string_value = string_value.replace('schedule_or_signal', 'scheduled,signal')  # Backward compatible for unreleased 1.9.2
    for component_value in string_value.split(','):
        for option in TransitionType:
            if component_value.lower() == option.name.lower():
                transaction_type |= option
    return transaction_type


class VduAppWindow(QMainWindow):
    splash_message_signal = pyqtSignal(str)
    _restore_preset_in_gui_thread = pyqtSignal(Preset, object, bool)

    def __init__(self, main_config: VduControlsConfig, app: QApplication):
        super().__init__()
        global gui_thread
        gui_thread = app.thread()
        self.app = app
        self.displayed_preset_name = None
        self.setObjectName('main_window')
        self.geometry_key = self.objectName() + "_geometry"
        self.state_key = self.objectName() + "_window_state"
        self.settings = QSettings('vdu_controls.qt.state', 'vdu_controls')
        self.main_panel: VduControlsMainPanel | None = None
        self.main_config = main_config
        self.weather_query: QueryWeather | None = None
        self.daily_schedule_next_update = datetime.today()
        self.refresh_data_task: WorkerThread | None = None
        self.restore_preset_thread: WorkerThread | None = None
        self.detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.vdu_controllers: List[VduController] = []
        self.previously_detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.transitioning_dummy_preset: TransitioningDummyPreset | None = None
        self.ddcutil: DdcUtil | None = None
        self.lux_auto_controller = LuxAutoController(self) if self.main_config.is_set(GlobalOption.LUX_OPTIONS_ENABLED) else None
        gnome_tray_behaviour = main_config.is_set(GlobalOption.SYSTEM_TRAY_ENABLED) and 'gnome' in os.environ.get(
            'XDG_CURRENT_DESKTOP', default='unknown').lower()

        self._restore_preset_in_gui_thread.connect(self.restore_preset)

        main_window_action: Callable | None = None

        if gnome_tray_behaviour:
            # Gnome tray doesn't normally provide a way to bring up the main app.
            def main_window_action_implemenation() -> None:
                self.show()
                self.raise_()
                self.activateWindow()

            main_window_action = main_window_action_implemenation

        def settings_changed(changed_settings: List):
            for setting in GlobalOption:
                if ('vdu-controls-globals', setting.name()) in changed_settings and setting.requires_restart():
                    restart_application(tr("The change to the {} option requires "
                                           "vdu_controls to restart.").format(setting))
                    return
            main_config.reload()
            self.ddcutil.change_settings(debug=main_config.is_set(GlobalOption.DEBUG_ENABLED),
                                         default_sleep_multiplier=main_config.get_sleep_multiplier())
            self.create_main_control_panel()
            self.schedule_presets(reset=True)
            presets_dialog = PresetsDialog.get_instance()
            if presets_dialog:
                presets_dialog.reload_data()

        def edit_config() -> None:
            SettingsEditor.invoke(main_config, [vdu.config for vdu in self.main_panel.vdu_controllers], settings_changed)

        def refresh_from_vdus() -> None:
            self.start_refresh()

        def lux_auto_action() -> bool:
            self.lux_auto_controller.toggle_auto()
            self.display_lux_auto_indicators()
            return self.lux_auto_controller.is_auto_enabled()

        def lux_meter_action() -> None:
            LuxDialog.invoke(self)

        def grey_scale() -> None:
            GreyScaleDialog()

        def edit_presets() -> None:
            PresetsDialog.invoke(self, main_config)

        def quit_app() -> None:
            self.app_save_state()
            app.quit()

        if log_debug_enabled:
            for screen in app.screens():
                log_info("Screen", screen.name())

        self.preset_controller = PresetController()

        self.app_context_menu = ContextMenu(main_window=self,
                                            main_window_action=main_window_action,
                                            about_action=AboutDialog.invoke,
                                            help_action=HelpDialog.invoke,
                                            chart_action=grey_scale,
                                            lux_auto_action=lux_auto_action if main_config.is_set(
                                                GlobalOption.LUX_OPTIONS_ENABLED) else None,
                                            lux_meter_action=lux_meter_action if main_config.is_set(
                                                GlobalOption.LUX_OPTIONS_ENABLED) else None,
                                            settings_action=edit_config,
                                            presets_action=edit_presets,
                                            refresh_action=refresh_from_vdus,
                                            quit_action=quit_app)

        splash_pixmap = get_splash_image()
        splash = QSplashScreen(splash_pixmap.scaledToWidth(800).scaledToHeight(400),
                               Qt.WindowStaysOnTopHint) if main_config.is_set(GlobalOption.SPLASH_SCREEN_ENABLED) else None

        if splash is not None:
            splash.show()
            # Attempt to force it to the top with raise and activate
            splash.raise_()
            splash.activateWindow()
        self.app_icon = QIcon()
        self.app_icon.addPixmap(splash_pixmap)

        self.tray = None
        if main_config.is_set(GlobalOption.SYSTEM_TRAY_ENABLED):
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log_warning("no system tray, waiting to see if one becomes available.")
                for _ in range(0, SYSTEM_TRAY_WAIT_SECONDS):
                    if QSystemTrayIcon.isSystemTrayAvailable():
                        break
                    time.sleep(0.25)  # TODO - at least use a constant
            if QSystemTrayIcon.isSystemTrayAvailable():
                log_info("Using system tray.")
                # This next call appears to be automatic on KDE, but not on gnome.
                app.setQuitOnLastWindowClosed(False)
                self.tray = QSystemTrayIcon(parent=self)
                self.tray.setContextMenu(self.app_context_menu)
            else:
                log_error("no system tray - cannot run in system tray.")

        self.app_name = "VDU Controls"
        self.set_app_icon_and_title()
        app.setApplicationDisplayName(self.app_name)
        # Make sure all icons use HiDPI - toolbars don't by default, so force it.
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)

        if splash is not None:
            splash.showMessage(tr('\n\nVDU Controls\nLooking for DDC monitors...\n'),
                               Qt.AlignTop | Qt.AlignHCenter)

        def splash_message_action(message) -> None:
            if splash is not None:
                log_info(f"Splash {message}")
                splash.showMessage(
                    f"\n\nVDU Controls {VDU_CONTROLS_VERSION}\n{message}",
                    Qt.AlignTop | Qt.AlignHCenter)

        def respond_to_unix_signal(signal_number: int):
            if signal_number == signal.SIGHUP:
                self.start_refresh()
            elif PRESET_SIGNAL_MIN <= signal_number <= PRESET_SIGNAL_MAX:
                preset = self.preset_controller.get_preset(signal_number - PRESET_SIGNAL_MIN)
                log_info(f"Signaled for preset {preset.name} transition-type={preset.get_transition_type()}")
                if preset is not None:
                    # Signals occur outside the GUI thread - initiate the restore in the GUI thread
                    immediately = TransitionType.SIGNAL not in preset.get_transition_type()
                    log_info("initiate_restore_preset", threading.get_ident())  # This method is for use by non-GUI threads.
                    self._restore_preset_in_gui_thread.emit(preset, None, immediately)
                else:
                    # Cannot raise a Qt alert inside the signal handler in case another signal comes in.
                    log_warning(f"ignoring signal {signal_number}, no preset associated with that signal number.")

        global signal_wakeup_handler
        signal_wakeup_handler.signalReceived.connect(respond_to_unix_signal)

        self.splash_message_signal.connect(splash_message_action)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.create_main_control_panel()
        self.app_restore_state()

        if self.main_config.is_set(GlobalOption.LUX_OPTIONS_ENABLED) and self.lux_auto_controller is not None:
            self.lux_auto_controller.refresh_from_config()

        if self.tray is not None:
            def show_window():
                if self.isVisible():
                    self.hide()
                else:
                    if len(self.settings.allKeys()) == 0:
                        # No previous state - guess a position near the tray. Use the mouse pos as a guess to where the
                        # system tray is.  The Linux Qt x,y geometry returned by the tray icon is 0,0, so we can't use that.
                        p = QCursor.pos()
                        wg = self.geometry()
                        # Also try to cope with the tray not being at the bottom right of the screen.
                        x = p.x() - wg.width() if p.x() > wg.width() else p.x()
                        y = p.y() - wg.height() if p.y() > wg.height() else p.y()
                        self.setGeometry(x, y, wg.width(), wg.height())
                    self.show()
                    # Attempt to force it to the top with raise and activate
                    self.raise_()
                    self.activateWindow()

            self.hide()
            self.tray.activated.connect(show_window)
            self.tray.setVisible(True)
        else:
            self.show()

        overdue = self.schedule_presets()
        if overdue:
            # Start of run - this preset is the one that should be running now
            log_info(f"Restoring preset '{overdue.name}' "
                     f"because its scheduled to be active at this time ({zoned_now()}).")
            self.splash_message_signal.emit(tr("Restoring Preset\n{}").format(overdue.name))
            # Weather check will have succeeded inside schedule_presets() above, don't do it again.
            self.activate_scheduled_preset(overdue, check_weather=False, immediately=True)

        if splash is not None:
            splash.finish(self)

        if main_config.file_path is None or (not main_config.ini_content.is_version_ge() and VDU_CONTROLS_VERSION.endswith('.0')):
            # User is new to this major version - point them to the release notes.
            release_alert = MessageBox(QMessageBox.Information, buttons=QMessageBox.Close)
            welcome = tr("Welcome to vdu_controls version {}").format(VDU_CONTROLS_VERSION)
            note = tr("Please read the online release notes:")
            release_alert.setText(RELEASE_ANNOUNCEMENT.format(WELCOME=welcome, NOTE=note, VERSION=VDU_CONTROLS_VERSION))
            release_alert.setTextFormat(Qt.RichText)
            release_alert.exec()
            # Stops the release notes from being repeated.
            main_config.write_file(get_config_path('vdu_controls'), overwrite=True)

    def set_app_icon_and_title(self, icon: QIcon | None = None, title_prefix: str | None = None):
        assert(is_running_in_gui_thread())
        title = f"{title_prefix} {PRESET_APP_SEPARATOR_SYMBOL} {self.app_name}" if title_prefix else self.app_name
        if self.windowTitle() != title:
            self.setWindowTitle(title)
        icon = create_merged_icon(self.app_icon, icon) if icon else self.app_icon
        self.app.setWindowIcon(icon)
        if self.tray:
            self.tray.setToolTip(title)
            self.tray.setIcon(icon)

    def create_controllers(self) -> None:
        ddcutil_problem = None
        try:
            ddcutil_common_args = ['--force', ] if self.is_non_standard_enabled() else []
            self.ddcutil = DdcUtil(debug=self.main_config.is_set(GlobalOption.DEBUG_ENABLED), common_args=ddcutil_common_args,
                                   default_sleep_multiplier=self.main_config.get_sleep_multiplier())
            self.detected_vdu_list = []
            log_debug("Detecting connected monitors, looping detection until it stabilises.")
            # Loop in case the session is initialising/restoring which can make detection unreliable.
            # Limit to a reasonable number of iterations.
            for i in range(1, 11):
                prev_num = len(self.detected_vdu_list)
                self.detected_vdu_list = self.ddcutil.detect_monitors()
                if prev_num == len(self.detected_vdu_list):
                    log_info(f"Number of detected monitors is stable at {len(self.detected_vdu_list)} (loop={i})")
                    break
                elif prev_num > 0:
                    log_info(f"Number of detected monitors changed from {prev_num} to {len(self.detected_vdu_list)} (loop={i})")
                time.sleep(1.5)
        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
            log_error(e)
            ddcutil_problem = e
        self.previously_detected_vdu_list = self.detected_vdu_list
        self.vdu_controllers = []

        for vdu_id, manufacturer, vdu_model_name, vdu_serial in self.detected_vdu_list:
            controller = None
            while True:
                try:
                    controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, self.main_panel.display_vdu_exception)
                except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:  # TODO figure out all possible Exceptions:
                    # Catch any kind of parse related error
                    log_error(f"Problem creating controller for {vdu_id} {vdu_model_name} {vdu_serial} exception={e}")
                    no_auto = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Ignore | QMessageBox.Apply | QMessageBox.Retry)
                    no_auto.setText(
                        tr('Failed to obtain capabilities for monitor {} {} {}.').format(vdu_id, vdu_model_name, vdu_serial))
                    no_auto.setInformativeText(tr(
                        'Cannot automatically configure this monitor.'
                        '\n You can choose to:'
                        '\n 1: Retry obtaining the capabilities.'
                        '\n 2: Ignore this monitor.'
                        '\n 3: Apply standard brightness and contrast controls.'))
                    choice = no_auto.exec()
                    if choice == QMessageBox.Ignore:
                        controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, self.main_config,
                                                   self.ddcutil, self.main_panel.display_vdu_exception, ignore_monitor=True)
                        controller.write_template_config_files()
                        warn = MessageBox(QMessageBox.Information)
                        warn.setText(tr('Ignoring {} monitor.').format(vdu_model_name))
                        warn.setInformativeText(
                            tr('Wrote {} config files to {}.').format(vdu_model_name, CONFIG_DIR_PATH))
                        warn.exec()
                    if choice == QMessageBox.Apply:
                        controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, self.main_config,
                                                   self.ddcutil, self.main_panel.display_vdu_exception,
                                                   assume_standard_controls=True)
                        controller.write_template_config_files()
                        warn = MessageBox(QMessageBox.Information)
                        warn.setText(tr('Assuming {} has brightness and contrast controls.').format(vdu_model_name))
                        warn.setInformativeText(tr('Wrote {} config files to {}.').format(vdu_model_name, CONFIG_DIR_PATH) +
                                                tr('\nPlease check these files and edit or remove them if they '
                                                   'cause further issues.'))
                        warn.exec()
                    if choice == QMessageBox.Retry:
                        continue
                break
            if controller is not None:
                self.vdu_controllers.append(controller)
        if len(self.vdu_controllers) == 0:
            if self.main_config.is_set(GlobalOption.WARNINGS_ENABLED):
                error_no_monitors = MessageBox(QMessageBox.Critical)
                error_no_monitors.setText(tr('No controllable monitors found.'))
                extra_text = tr("(Most recent ddcutil error: {})").format(str(ddcutil_problem)) if ddcutil_problem else ''
                error_no_monitors.setInformativeText(
                    tr("Is ddcutil installed?  Is i2c installed and configured?\n\n"
                       "Run vdu_controls --debug in a console and check for "
                       "additional messages.\n\n{}").format(extra_text))
                error_no_monitors.exec()

    def create_main_control_panel(self) -> None:
        # Call on initialisation and whenever the number of connected VDU's changes.
        try:
            global log_to_syslog
            log_to_syslog = self.main_config.is_set(GlobalOption.SYSLOG_ENABLED)
            existing_width = 0
            if self.main_panel is not None:
                self.main_panel.indicate_busy(True)
                # Remove any existing control panel - which may now be incorrect for the config.
                self.main_panel.width()
                self.main_panel.vdu_setting_changed.disconnect(self.display_active_preset)
                self.main_panel.connected_vdus_changed.disconnect(self.create_main_control_panel)
                self.main_panel.deleteLater()
                self.main_panel = None
            self.main_panel = VduControlsMainPanel()
            # Write up the signal/slots first

            self.main_panel.vdu_setting_changed.connect(self.display_active_preset)
            self.main_panel.connected_vdus_changed.connect(self.create_main_control_panel)
            # Then initialise the control panel display
            self.create_controllers()
            refresh_button = ToolButton(REFRESH_ICON_SOURCE, tr("Refresh settings from monitors"))
            refresh_button.pressed.connect(self.start_refresh)
            tool_buttons = [refresh_button]
            if self.main_config.is_set(GlobalOption.LUX_OPTIONS_ENABLED) and self.lux_auto_controller is not None:
                tool_buttons.append(self.lux_auto_controller.create_tool_button())
            self.main_panel.initialise_control_panels(self.app_context_menu, self.main_config, self.vdu_controllers,
                                                      tool_buttons, self.splash_message_signal)
            self.main_panel.indicate_busy(True)
            self.setCentralWidget(self.main_panel)
            self.setMinimumWidth(existing_width)
            self.splash_message_signal.emit(
                "Reticulating Splines" if self.main_config.is_set(GlobalOption.DEBUG_ENABLED) else tr("Checking Presets"))
            self.display_active_preset()
        finally:
            self.main_panel.indicate_busy(False)

    def start_refresh(self) -> None:
        assert is_running_in_gui_thread()
        self.main_panel.indicate_busy()

        def refresh_data():
            # Called in a non-GUI thread, cannot do any GUI op's.
            self.detected_vdu_list = self.ddcutil.detect_monitors()
            self.main_panel.refresh_data(self.detected_vdu_list)

        def refresh_view():
            """Invoke when the GUI worker thread completes. Runs in the GUI thread and can refresh the GUI views."""
            if self.refresh_data_task.vdu_exception is not None:
                self.main_panel.display_vdu_exception(self.refresh_data_task.vdu_exception, can_retry=False)
            if self.detected_vdu_list != self.previously_detected_vdu_list:
                self.create_main_control_panel()
                self.previously_detected_vdu_list = self.detected_vdu_list
            self.main_panel.refresh_view()
            self.main_panel.indicate_busy(False)
            if self.main_config.is_set(GlobalOption.LUX_OPTIONS_ENABLED) and LuxDialog.exists():
                LuxDialog.get_instance().reinitialise()  # in case the number of connected monitors have changed.
            self.display_active_preset()

        self.refresh_data_task = WorkerThread(task_body=refresh_data, task_finished=refresh_view)
        self.refresh_data_task.start()

    def restore_preset_in_gui_thread(self, preset: Preset, immediately: bool = False):
        self._restore_preset_in_gui_thread.emit(preset, None, immediately)

    def restore_preset(self, preset: Preset, restore_finished: Callable | None = None, immediately: bool = False) -> None:
        # Starts the restore, but it will complete in the worker thread
        assert is_running_in_gui_thread()    # Boilerplate in case this is called from the wrong thread.
        self.transitioning_dummy_preset: TransitioningDummyPreset | None = None

        if not immediately:
            self.transitioning_dummy_preset = TransitioningDummyPreset(preset)
            presets_dialog_update_view(tr("Transitioning to preset {}").format(preset.name))
            self.display_active_preset(self.transitioning_dummy_preset)
        self.main_panel.indicate_busy()
        preset.load()

        def update_progress():
            nonlocal worker_thread
            if self.main_panel.busy:
                self.main_panel.indicate_busy(False)
                if self.tray is not None:
                    self.refresh_tray_menu()
            presets_dialog_update_view(
                tr("Transitioning to preset {} (elapsed time {} seconds)...").format(
                    preset.name, round(worker_thread.total_elapsed_seconds(), ndigits=1)))
            self.transitioning_dummy_preset.update_progress() if self.transitioning_dummy_preset else None
            self.display_active_preset(self.transitioning_dummy_preset)

        def finished():
            nonlocal worker_thread
            self.transitioning_dummy_preset = None
            if worker_thread.vdu_exception is not None:
                if self.main_panel.display_vdu_exception(worker_thread.vdu_exception, can_retry=True):
                    # Try again (recursion) in new thread
                    self.restore_preset(preset, restore_finished=restore_finished, immediately=immediately)
                    return  # Don't do anything more the semi-recursive call above will take over from here
            self.main_panel.refresh_view()
            self.main_panel.indicate_busy(False)
            if self.tray is not None:
                self.refresh_tray_menu()
            if worker_thread.state == TransitionState.FINISHED:
                with open(PRESET_NAME_FILE, 'w', encoding="utf-8") as cps_file:
                    cps_file.write(preset.name)
                self.display_active_preset(preset)
                presets_dialog_update_view(tr("Restored {} (elapsed time {} seconds)").format(
                    preset.name, round(worker_thread.total_elapsed_seconds(), ndigits=1)))
                if restore_finished is not None:
                    restore_finished(True)
            else:  # Interrupted or exception:
                self.display_active_preset()
                presets_dialog_update_view(tr("Interrupted restoration of {}").format(preset.name))
                if restore_finished is not None:
                    restore_finished(False)

        worker_thread = TransitionWorker(self.main_panel, preset, update_progress, finished, immediately)
        worker_thread.start()

    def find_preset_by_name(self, preset_name: str) -> Preset | None:
        presets = self.preset_controller.find_presets()
        if preset_name in presets:
            return presets[preset_name]
        return None

    def restore_named_preset(self, preset_name: str) -> None:
        preset = self.find_preset_by_name(preset_name)
        if preset is not None:
            # Transition immediately unless the Preset is required to ALWAYS transition.
            self.restore_preset(preset, immediately=TransitionType.MENU not in preset.get_transition_type())

    def save_preset(self, preset: Preset) -> None:
        self.copy_to_preset_ini(preset.preset_ini, update_only=True)
        self.preset_controller.save_preset(preset)
        if not self.app_context_menu.has_preset_menu_action(preset.name):
            self.app_context_menu.insert_preset_menu_action(preset)
        self.display_active_preset()
        preset.remove_elevation_trigger()
        self.schedule_presets()

    def copy_to_preset_ini(self, preset_ini: ConfigIni, update_only: bool = False) -> None:
        for control_panel in self.main_panel.vdu_control_panels:
            control_panel.copy_state(preset_ini, update_only)

    def delete_preset(self, preset: Preset) -> None:
        self.preset_controller.delete_preset(preset)
        if self.app_context_menu.has_preset_menu_action(preset.name):
            self.app_context_menu.remove_preset_menu_action(preset)
        self.display_active_preset()

    def which_preset_is_active(self) -> Preset | None:
        # See if we have a record of which was last active, and see if it still is active
        if PRESET_NAME_FILE.exists():
            with open(PRESET_NAME_FILE, encoding="utf-8") as cps_file:
                preset_name = cps_file.read()
                if preset_name.strip() != '':
                    preset = self.preset_controller.presets.get(preset_name)  # will be None if it has been deleted
                    if preset is not None and self.main_panel.is_preset_active(preset):
                        return preset
        # Guess by testing each possible preset against the current VDU settings
        for preset in self.preset_controller.find_presets().values():
            if self.main_panel.is_preset_active(preset):
                return preset
        return None

    def get_presets(self):
        return self.preset_controller.find_presets()

    def display_lux_auto_indicators(self):
        assert is_running_in_gui_thread()  # Boilerplate in case this is called from the wrong thread.
        if self.main_config.is_set(GlobalOption.LUX_OPTIONS_ENABLED) \
                and self.lux_auto_controller is not None and self.lux_auto_controller.lux_meter is not None:
            icon = create_themed_icon_from_svg_bytes(self.lux_auto_controller.current_auto_svg())
            self.app_context_menu.update_lux_auto_icon(icon)
            self.refresh_tray_menu()
            if self.lux_auto_controller.is_auto_enabled():
                self.set_app_icon_and_title(icon, tr('Auto'))
            else:
                self.set_app_icon_and_title()

    def display_active_preset(self, preset=None) -> None:
        assert is_running_in_gui_thread()  # Boilerplate in case this is called from the wrong thread.
        if preset is None and self.transitioning_dummy_preset is not None:
            preset = self.transitioning_dummy_preset
        if preset is None:
            preset = self.which_preset_is_active()
        if preset is None:
            self.main_panel.display_active_preset(None)
            self.set_app_icon_and_title()
            self.display_lux_auto_indicators()  # Check in case both schedule and lux auto are active
        else:
            self.main_panel.display_active_preset(preset)
            self.set_app_icon_and_title(preset.create_icon(), preset.get_title_name())
        self.app_context_menu.refresh_preset_menu()

    def refresh_tray_menu(self):
        assert is_running_in_gui_thread()
        self.app_context_menu.update()
        #self.tray.setContextMenu(self.app_context_menu)  # Force refresh

    def closeEvent(self, event):
        self.app_save_state()
        # Despite what you find on Google, the following seems unnecessary, and causes vdu_controls to veto logout/shutdown
        # if it's window is present on the desktop.  Leaving the code here for one more version.
        if os.getenv("VDU_CONTROLS_OLD_CLOSE_BEHAVIOR") is not None:
            if self.tray is not None:
                self.hide()
                event.ignore()  # hide the window
            else:
                event.accept()  # let the window close

    def create_config_files(self):
        for vdu_model in self.main_panel.vdu_controllers:
            vdu_model.write_template_config_files()

    def app_save_state(self):
        self.settings.setValue(self.geometry_key, self.saveGeometry())
        self.settings.setValue(self.state_key, self.saveState())

    def app_restore_state(self):
        geometry = self.settings.value(self.geometry_key, None)
        if geometry is not None:
            self.restoreGeometry(geometry)
            window_state = self.settings.value(self.state_key, None)
            self.restoreState(window_state)

    def event(self, event: QEvent) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.display_active_preset()
            self.app_context_menu.refresh_preset_menu(palette_change=True)
        return super().event(event)

    def schedule_presets(self, reset: bool = False) -> Preset | None:
        # As well as scheduling, this method finds and returns the preset that should be applied at this time.
        assert is_running_in_gui_thread()  # Needs to be run in the GUI thread so the timers also run in the GUI thread
        if not self.main_config.is_set(GlobalOption.SCHEDULE_ENABLED):
            log_info("Scheduling is disabled")
            return
        location = self.main_config.get_location()
        if location is None:
            return None
        log_info(f"Scheduling presets reset={reset}")
        time_map = create_todays_elevation_time_map(latitude=location.latitude, longitude=location.longitude)
        most_recent_overdue = None
        local_now = zoned_now()
        latest_due = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        for preset in self.preset_controller.find_presets().values():
            if reset:
                preset.remove_elevation_trigger()
            elevation_key = preset.get_solar_elevation()
            if elevation_key is not None and preset.schedule_status == ScheduleStatus.UNSCHEDULED:
                if elevation_key in time_map:
                    when_today = time_map[elevation_key].when
                    preset.elevation_time_today = when_today
                    if when_today > local_now:
                        preset.start_timer(when_today, self.activate_scheduled_preset)
                    else:
                        preset.schedule_status = ScheduleStatus.SKIPPED_SUPERSEDED
                        if when_today > latest_due:
                            # This may be the preset that should be applicable now, check if weather prevents it.
                            # Reuse the weather, don't do multiple weather queries while scheduling.
                            if self.is_weather_satisfactory(preset, use_cache=True):
                                most_recent_overdue = preset
                                latest_due = when_today
                else:
                    log_info(f"Solar activation skipping preset {preset.name} {elevation_key} degrees"
                             " - the sun does not reach that elevation today.")
        # set a timer to rerun this at the beginning of the next day.
        tomorrow = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        if self.daily_schedule_next_update != tomorrow:
            millis = (tomorrow - zoned_now()) / timedelta(milliseconds=1)
            log_info(f"Will update solar elevation activations tomorrow at "
                     f" {tomorrow} (in {round(millis / 1000 / 60)} minutes)")
            QTimer.singleShot(int(millis), partial(self.schedule_presets, True))
            # Testing: QTimer.singleShot(int(1000*30), partial(self.schedule_presets, True))
            self.daily_schedule_next_update = tomorrow
        if reset:
            presets_dialog = PresetsDialog.get_instance()
            if presets_dialog:
                presets_dialog.refresh_view()
        return most_recent_overdue

    def activate_scheduled_preset(self, preset: Preset, check_weather: bool = True, immediately: bool = False):
        assert is_running_in_gui_thread()
        if not self.main_config.is_set(GlobalOption.SCHEDULE_ENABLED):
            log_info(f"Schedule is disabled - not activating preset {preset.name}")
            return
        now = zoned_now()
        weather_text = ''
        proceed = True
        if preset.is_weather_dependent() and check_weather:
            proceed = self.is_weather_satisfactory(preset)
            if not proceed:
                preset.schedule_status = ScheduleStatus.WEATHER_CANCELLATION
                message = tr("Preset {} activation was cancelled due to weather at {}").format(
                    preset.name, now.isoformat(' ', 'seconds'))
                weather_text = f"({self.weather_query.weather_desc if self.weather_query is not None else ''})"
        if proceed:
            status_text = tr("Preset {} activating at {}").format(preset.name, now.isoformat(' ', 'seconds'))
            message = f"{TIME_CLOCK_SYMBOL} {status_text} {preset.schedule_status.symbol()} {weather_text}"

            def finished(succeeded: bool):
                preset.schedule_status = ScheduleStatus.SUCCEEDED if succeeded else ScheduleStatus.SKIPPED_SUPERSEDED
                self.display_active_preset()
                presets_dialog_update_view(message + ' - ' + tr("Restored {}").format(preset.name))

            log_info(f"Activating scheduled preset {preset.name}")
            # Happens asynchronously in a thread
            self.restore_preset(
                preset,
                restore_finished=finished,
                immediately=immediately or TransitionType.SCHEDULED not in preset.get_transition_type())
        presets_dialog_update_view(message)

    def is_weather_satisfactory(self, preset, use_cache: bool = False) -> bool:
        try:
            if preset.is_weather_dependent() and self.main_config.is_set(GlobalOption.WEATHER_ENABLED):
                if not use_cache or self.weather_query is None:
                    location = self.main_config.get_location()
                    if location is not None:
                        self.weather_query = QueryWeather(location)
                        self.weather_query.run_query()
                        if not self.weather_query.proximity_ok:
                            log_error(f"Preset {preset.name} weather location is {self.weather_query.proximity_km} km from "
                                      f"Settings Location, check settings.")
                            weather_bad_location_dialog(self.weather_query)
                if not preset.check_weather(self.weather_query):
                    preset.schedule_status = ScheduleStatus.WEATHER_CANCELLATION
                    return False
        except ValueError as e:
            msg = MessageBox(QMessageBox.Warning)
            msg.setText(
                tr("Ignoring weather requirements, unable to query local weather: {}").format(str(e.args[0])))
            msg.setInformativeText(e.args[1])
            msg.exec()
        return True

    def is_non_standard_enabled(self) -> bool:
        path = get_config_path("danger")
        if path.exists():
            with open(path, encoding="utf-8") as f:
                text = f.read()
                if text.strip() == DANGER_AGREEMENT_NON_STANDARD_VCP_CODES.strip():
                    log_warning(f"\n"
                                f"Non standard features may be enabled for write.\n"
                                f"ENABLING NON_STANDARD FEATURES COULD DAMAGE YOUR HARDWARE.\n"
                                f"To disable non-standard features delete the file {path}.\n"
                                f"{DANGER_AGREEMENT_NON_STANDARD_VCP_CODES}")
                    return True
        return False


class SignalWakeupHandler(QtNetwork.QAbstractSocket):
    # https://stackoverflow.com/a/37229299/609575
    # '''
    # Quoted here: The Qt event loop is implemented in C(++). That means, that while it runs and no Python code is
    # called (e.g. by a Qt signal connected to a Python slot), the signals are noted, but the Python signal handlers
    # aren't called.
    #
    # But, since Python 2.6 and in Python 3 you can cause Qt to run a Python function when a signal with a handler is
    # received using signal.set_wakeup_fd().
    #
    # This is possible, because, contrary to the documentation, the low-level signal handler doesn't only set a flag
    # for the virtual machine, but it may also write a byte into the file descriptor set by set_wakeup_fd(). Python 2
    # writes a NUL byte, Python 3 writes the signal number.
    #
    # So by subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g.
    # QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler) is received
    # causing the signal handler to execute nearly instantaneous without need for timers:
    # '''

    signalReceived = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(QtNetwork.QAbstractSocket.UdpSocket, parent)
        self.old_fd = None
        # Create a socket pair
        self.wsock, self.rsock = socket.socketpair(type=socket.SOCK_DGRAM)
        # Let Qt listen on the one end
        self.setSocketDescriptor(self.rsock.fileno())
        # And let Python write on the other end
        self.wsock.setblocking(False)
        self.old_fd = signal.set_wakeup_fd(self.wsock.fileno())
        # First Python code executed gets any exception from
        # the signal handler, so add a dummy handler first
        self.readyRead.connect(lambda: None)
        # Second handler does the real handling
        self.readyRead.connect(self._readSignal)

    def __del__(self):
        # Restore any old handler on deletion
        if self.old_fd is not None and signal and signal.set_wakeup_fd:
            signal.set_wakeup_fd(self.old_fd)

    def _readSignal(self):
        # Read the written byte.
        # Note: readyRead is blocked from occurring again until readData()
        # was called, so call it, even if you don't need the value.
        data = self.readData(1)
        # Emit a Qt signal for convenience
        signal_number = int(data[0])
        log_info("SignalWakeupHandler", signal_number)
        self.signalReceived.emit(signal_number)


#
# FUNCTION TO COMPUTE SOLAR AZIMUTH AND ZENITH ANGLE
# Extracted from a larger gist by Antti Lipponen
# https://gist.github.com/anttilipp/1c482c8cc529918b7b973339f8c28895
# which was translated to Python from http://www.psa.es/sdg/sunpos.htm
#
# Converted to only using the python math library (instead of numpy).
# Coding style altered for use with vdu_controls.
#
def calc_solar_azimuth_zenith(localised_time: datetime, latitude: float, longitude: float) -> Tuple[float, float]:
    """
    Return azimuth degrees clockwise from true north and zenith in degrees from vertical direction.
    """
    utc_date_time = localised_time if localised_time.tzinfo is None else localised_time.astimezone(timezone.utc)
    # UTC from now on...
    hours, minutes, seconds = utc_date_time.hour, utc_date_time.minute, utc_date_time.second
    year, month, day = utc_date_time.year, utc_date_time.month, utc_date_time.day

    earth_mean_radius = 6371.01
    astronomical_unit = 149597890

    # Calculate difference in days between the current Julian Day
    # and JD 2451545.0, which is noon 1 January 2000 Universal Time

    # Calculate time of the day in UT decimal hours
    decimal_hours = hours + (minutes + seconds / 60.) / 60.
    # Calculate current Julian Day
    aux1 = int((month - 14.) / 12.)
    aux2 = int((1461. * (year + 4800. + aux1)) / 4.) + int((367. * (month - 2. - 12. * aux1)) / 12.) - int(
        (3. * int((year + 4900. + aux1) / 100.)) / 4.) + day - 32075.
    julian_date = aux2 - 0.5 + decimal_hours / 24.
    # Calculate difference between current Julian Day and JD 2451545.0
    elapsed_julian_days = julian_date - 2451545.0

    # Calculate ecliptic coordinates (ecliptic longitude and obliquity of the
    # ecliptic in radians but without limiting the angle to be less than 2*Pi
    # (i.e., the result may be greater than 2*Pi)
    omega = 2.1429 - 0.0010394594 * elapsed_julian_days
    mean_longitude = 4.8950630 + 0.017202791698 * elapsed_julian_days  # Radians
    mean_anomaly = 6.2400600 + 0.0172019699 * elapsed_julian_days
    ecliptic_longitude = mean_longitude + 0.03341607 * math.sin(mean_anomaly) + 0.00034894 * math.sin(
        2. * mean_anomaly) - 0.0001134 - 0.0000203 * math.sin(omega)
    ecliptic_obliquity = 0.4090928 - 6.2140e-9 * elapsed_julian_days + 0.0000396 * math.cos(omega)

    # Calculate celestial coordinates ( right ascension and declination ) in radians
    # but without limiting the angle to be less than 2*Pi (i.e., the result may be
    # greater than 2*Pi)
    sin_ecliptic_longitude = math.sin(ecliptic_longitude)
    dy = math.cos(ecliptic_obliquity) * sin_ecliptic_longitude
    dx = math.cos(ecliptic_longitude)
    right_ascension = math.atan2(dy, dx)
    if right_ascension < 0.0:
        right_ascension = right_ascension + 2.0 * math.pi
    declination = math.asin(math.sin(ecliptic_obliquity) * sin_ecliptic_longitude)

    # Calculate local coordinates ( azimuth and zenith angle ) in degrees
    greenwich_mean_sidereal_time = 6.6974243242 + 0.0657098283 * elapsed_julian_days + decimal_hours
    local_mean_sidereal_time = (greenwich_mean_sidereal_time * 15. + longitude) * (math.pi / 180.)
    hour_angle = local_mean_sidereal_time - right_ascension
    latitude_in_radians = latitude * (math.pi / 180.)
    cos_latitude = math.cos(latitude_in_radians)
    sin_latitude = math.sin(latitude_in_radians)
    cos_hour_angle = math.cos(hour_angle)
    zenith_angle = (
        math.acos(cos_latitude * cos_hour_angle * math.cos(declination) + math.sin(declination) * sin_latitude))
    dy = -math.sin(hour_angle)
    dx = math.tan(declination) * cos_latitude - sin_latitude * cos_hour_angle
    azimuth = math.atan2(dy, dx)
    if azimuth < 0.0:
        azimuth += 2 * math.pi
    azimuth = azimuth / (math.pi / 180.)
    # Parallax Correction
    parallax = (earth_mean_radius / astronomical_unit) * math.sin(zenith_angle)
    zenith_angle = (zenith_angle + parallax) / (math.pi / 180.)
    # Return azimuth as clockwise angle from true north
    return azimuth, zenith_angle


# Spherical distance from
# https://stackoverflow.com/a/21623206/609575
def spherical_kilometers(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (
            1 - math.cos((lon2 - lon1) * p)) / 2
    return 12742 * math.asin(math.sqrt(a))


def create_todays_elevation_time_map(latitude: float, longitude: float) -> Dict[SolarElevationKey, SolarElevationData]:
    """
    Create a minute-by-minute map of today's SolarElevations,
    so for a given dict[SolarElevation], return the first minute it occurs.
    """
    elevation_time_map = {}
    local_now = zoned_now()
    local_when = local_now.replace(hour=0, minute=0)
    while local_when.day == local_now.day:
        a, z = calc_solar_azimuth_zenith(local_when, latitude, longitude)
        e = round(90.0 - z)
        direction = EASTERN_SKY if a < 180 else WESTERN_SKY
        key = SolarElevationKey(elevation=round(e), direction=direction)
        if key not in elevation_time_map:
            elevation_time_map[key] = SolarElevationData(azimuth=a, zenith=z, when=local_when)
        local_when += timedelta(minutes=1)
    return elevation_time_map


def find_locale_specific_file(filename_template: str) -> Path | None:
    locale_name = QLocale.system().name()
    filename = filename_template.format(locale_name)
    for path in LOCALE_TRANSLATIONS_PATHS:
        full_path = path.joinpath(filename)
        log_debug(f"Checking for {locale_name} translation: {full_path}") if log_debug_enabled else None
        if full_path.exists():
            log_info(f"Found {locale_name} translation: {full_path}")
            return full_path
    return None


translator: QTranslator | None = None
ts_translations: Dict[str, str] = {}


def initialise_locale_translations(app: QApplication):
    # Has to be put somewhere it won't be garbage collected when this function goes out of scope.
    global translator
    translator = QTranslator()
    log_info("Qt locale", QLocale.system().name())
    locale_name = QLocale.system().name()
    ts_path = find_locale_specific_file("{}.ts")
    qm_path = find_locale_specific_file("{}.qm")

    # If there is a .ts XML file in the path newer than the associated .qm binary file, load the messages
    # from the XML into a map and use them directly.  This is useful while developing and possibly useful
    # for users that want to do their own localisation.
    if ts_path is not None and (qm_path is None or os.path.getmtime(ts_path) > os.path.getmtime(qm_path)):
        log_info(tr("Using newer .ts file {} translations from {}").format(locale_name, ts_path.as_posix()))
        import xml.etree.ElementTree as XmlElementTree
        global ts_translations
        context = XmlElementTree.parse(ts_path).find('context')
        if context is not None:
            for message in context.findall('message'):
                translation = message.find('translation')
                source = message.find('source')
                if translation is not None and source is not None and translation.text is not None and source.text is not None:
                    ts_translations[source.text] = translation.text
        log_info(tr("Loaded {} translations from {}").format(locale_name, ts_path.as_posix()))
        return

    if qm_path is not None:
        log_info(tr("Loading {} translations from {}").format(locale_name, qm_path.as_posix()))
        if translator.load(qm_path.name, qm_path.parent.as_posix()):
            app.installTranslator(translator)
            log_info(tr("Using {} translations from {}").format(locale_name, qm_path.as_posix()))


def main():
    """vdu_controls application main."""
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    def signal_handler(x, y):
        log_info("Signal received", x, y)

    signal.signal(signal.SIGHUP, signal_handler)
    for i in range(PRESET_SIGNAL_MIN, PRESET_SIGNAL_MAX):
        signal.signal(i, signal_handler)

    sys.excepthook = exception_handler

    # This is supposed to set the locale for all categories to the user’s default setting.
    # This can error on some distros when the required language isn't installed, or if LANG
    # is set without also specifying the UTF-8 encoding, so LANG=da_DK might fail,
    # but LANG=da_DK.UTF-8 should work. For our purposes failure is not important.
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        log_warning("Could not set the default locale - may not be an issue...")
    log_info("Python locale", locale.getlocale())

    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)

    # Wayland needs this set in order to find/use the app's desktop icon.
    QGuiApplication.setDesktopFileName("vdu_controls")

    global signal_wakeup_handler
    signal_wakeup_handler = SignalWakeupHandler(app)

    main_config = VduControlsConfig('vdu_controls', include_globals=True)
    default_config_path = get_config_path('vdu_controls')
    log_info("Looking for config file '" + default_config_path.as_posix() + "'")
    if Path.is_file(default_config_path) and os.access(default_config_path, os.R_OK):
        main_config.parse_file(default_config_path)

    args = main_config.parse_global_args()
    global log_debug_enabled
    global log_to_syslog
    log_to_syslog = main_config.is_set(GlobalOption.SYSLOG_ENABLED)
    log_debug_enabled = main_config.is_set(GlobalOption.DEBUG_ENABLED)
    if args.syslog:
        log_to_syslog = True
    if args.debug:
        main_config.debug_dump()
    if args.create_config_files:
        main_config.write_file(default_config_path)
    if args.install:
        install_as_desktop_application()
        sys.exit()
    if args.uninstall:
        install_as_desktop_application(uninstall=True)
        sys.exit()
    if args.detailed_help:
        print(__doc__)
        sys.exit()

    log_debug(f"application style is {app.style().objectName()}") if log_debug_enabled else None

    # Assign to variable to stop it being reclaimed as garbage
    if main_config.is_set(GlobalOption.TRANSLATIONS_ENABLED):
        initialise_locale_translations(app)

    if args.about:
        AboutDialog.invoke()

    main_window = VduAppWindow(main_config, app)

    if args.create_config_files:
        main_window.create_config_files()

    rc = app.exec_()
    log_info(f"App exit rc={rc} {'EXIT_CODE_FOR_RESTART' if rc == EXIT_CODE_FOR_RESTART else ''}")
    if rc == EXIT_CODE_FOR_RESTART:
        log_info(f"Trying to restart - this only works if {app.arguments()[0]} is executable and on your PATH): ", )
        restart_status = QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
        if not restart_status:
            dialog = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Close)
            dialog.setText(tr("Restart of {} failed.  Please restart manually.").format(app.arguments()[0]))
            dialog.setInformativeText(tr("This is probably because {} is not"
                                         " executable or is not on your PATH.").format(app.arguments()[0]))
            dialog.exec()
    sys.exit(rc)


# A fallback in case the hard coded splash screen PNG doesn't exist (which probably means KDE is not installed).
FALLBACK_SPLASH_PNG_BASE64 = b"""
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
"""

if __name__ == '__main__':
    main()
