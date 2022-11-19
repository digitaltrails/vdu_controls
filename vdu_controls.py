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
                     [--location latitude,longitude] [--translations-enabled]
                     [--no-splash] [--sleep-multiplier multiplier]
                     [--create-config-files]
                     [--install] [--uninstall]

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
      --translations-enabled
                            enable language translations
      --debug               enable debug output to stdout
      --warnings            popup a warning when a VDU lacks an enabled control
      --syslog              repeat diagnostic output to the syslog (journald)
      --no-splash           don't show the splash screen
      --sleep-multiplier multiplier
                            protocol reliability multiplier for ddcutil (typically 0.1 .. 2.0, default is 0.5)
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

Named ``Preset`` configurations can be saved for later recalled. For example, a user could create
presets for night, day, photography, movies, and so forth.

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

Any small SVG or PNG can be selected as a preset's icon.  Monochrome SVG icons that conform to the Plasma color
conventions will be automatically inverted if the desktop them is changed from dark to light.

Each preset is stored in the application config directory as ``$HOME/.config/vdu_controls/Preset_<preset_name>.conf``.
Preset files are saved in INI-file format for ease of editing.  Each preset file contains a section for each connected
VDU, for example::

    [preset]
    icon = /usr/share/icons/breeze/status/16/cloudstatus.svg
    solar-elevation = eastern-sky 40

    [HP_ZR24w_CNT008]
    brightness = 50
    osd-language = 02

    [LG_HDR_4K_89765]
    brightness = 13
    audio-speaker-volume = 16
    input-source = 0f

When the GUI is used to create a preset file, you can select which controls to save.  For example, you
might create a preset that includes only the brightness, but not the contrast or audio volume.


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

A solar elevation trigger can have a weather requirement which will be checked
against the weather reported by https://wttr.in.  By default, there are three
possible weather requirements: ``good``, ``bad``, and ``all weather``. Each possible
requirement is defined by a file containing a list of WWO
(https://www.worldweatheronline.com) weather codes, one code per line.  The
three default possibilities are contained in the files
``$HOME/.config/vdu_controls/{good,bad,all}.weather``.  Additional weather
requirements can be created by using a text editor to create further files.
The ``all.weather`` file exists primarily as a convenient resource that lists
all possible codes.  Because weather is unpredictable and forecasts are
often unreliable or out of date, it's best to use weather requirements as a
coarse measure. Going beyond good and bad may not be very practical.

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

Responsiveness
--------------

If your VDU's are modern, you may find a smaller sleep-multiplier will speed up the ``ddcutil``/VDU protocol
exchanges making both ``ddcutil`` and ``vdu_controls`` much more responsive.  In a multi-VDU setup where the VDU's
are quite different, VDU config files can be used to specify individual multipliers (see previous section).

Startup speed may be increased by creating VDU config files with ``capabilities-override`` preset. Using an
override eliminates the need to run ``ddcutil`` to retrieve VDU capabilities.  The ``--create-config-files``
of context-menu settings-editor will pre-populate ``capabilities-override`` for each connected VDU.

Reducing the number of enabled controls can speed up the initialisation and reduce the time taken when the
refresh button is pressed.

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

    vdu_controls --sleep-multiplier 0.1
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


vdu_controls Copyright (C) 2021 Michael Hamilton
================================================

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

**Contact:**  m i c h a e l   @   a c t r i x   .   g e n   .   n z

----------

"""
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
import pickle
import re
import signal
import socket
import stat
import subprocess
import sys
import syslog
import textwrap
import time
import traceback
import urllib.request
from collections import namedtuple
from datetime import datetime, timedelta, date, timezone
from functools import partial
from pathlib import Path
from typing import List, Tuple, Mapping, Type, Dict, Callable
from urllib.error import URLError

from PyQt5 import QtNetwork
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QRegExp, QPoint, QObject, QEvent, \
    QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon, QCursor, QImage, QPainter, QDoubleValidator, QRegExpValidator, \
    QPalette, QGuiApplication, QColor, QValidator, QPen, QFont
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
    QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction, QMainWindow, QToolBar, QToolButton, QFileDialog, \
    QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter

APPNAME = "VDU Controls"
VDU_CONTROLS_VERSION = '1.8.2'

RELEASE_ANNOUNCEMENT = f"""
<h3>Welcome to vdu_controls version {VDU_CONTROLS_VERSION}</h3>

Please read the online release notes:<br>
<a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VDU_CONTROLS_VERSION}">
https://github.com/digitaltrails/vdu_controls/releases/tag/v{VDU_CONTROLS_VERSION}</a>
<hr>
"""

WESTERN_SKY = 'western-sky'
EASTERN_SKY = 'eastern-sky'

SolarElevationKey = namedtuple('SolarElevationKey', ['direction', 'elevation'])
SolarElevationData = namedtuple('SolarElevationData', ['azimuth', 'zenith', 'when'])

current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')


def zoned_now() -> datetime:
    return datetime.now().astimezone()


def format_solar_elevation_abbreviation(elevation: SolarElevationKey) -> str:
    direction_char = '\u29A8' if elevation.direction == EASTERN_SKY else '\u29A9'
    return f"\u2600 {direction_char} {elevation.elevation}\u00B0"


def format_solar_elevation_description(elevation: SolarElevationKey) -> str | None:
    # Note - repeating the constants here to force them to be included by pylupdate5 internationalisation
    direction_text = tr('eastern-sky') if elevation.direction == EASTERN_SKY else tr('western-sky')
    return f"{direction_text} {elevation.elevation}\u00B0"


def create_solar_elevation_ini_text(elevation: SolarElevationKey):
    return f"{elevation.direction} {elevation.elevation}" if elevation else ''


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


def tr(source_text: str, disambiguation: str = None):
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
    # with '-' replaced with ' '.
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
</small>
</quote>
"""

# Use Linux/UNIX signals for interprocess communication to trigger preset changes - 16 presets should be enough
# for anyone.
PRESET_SIGNAL_MIN = 40
PRESET_SIGNAL_MAX = 55

signal_wakeup_handler = None

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


#: Could be a str enumeration of VCP types
CONTINUOUS_TYPE = 'C'
SIMPLE_NON_CONTINUOUS_TYPE = 'SNC'
COMPLEX_NON_CONTINUOUS_TYPE = 'CNC'
# The GUI treats SNC and CNC the same - only DdcUtil needs to distinguish them.
GUI_NON_CONTINUOUS_TYPE = SIMPLE_NON_CONTINUOUS_TYPE

log_to_syslog = False


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
    log_wrapper(syslog.LOG_DEBUG, *args)


def log_info(*args):
    log_wrapper(syslog.LOG_INFO, *args)


def log_warning(*args):
    log_wrapper(syslog.LOG_WARNING, *args)


def log_error(*args):
    log_wrapper(syslog.LOG_ERR, *args)


def is_logging_in():
    # If the time is near the login time, maybe the user is logging in
    try:
        # DO NOT USE use os.getlogin(), openbox doesn't define a tty - which makes os.getlogin() fail.
        username = os.environ.get('USER', '')
        if username == '':
            log_error("Non critical error, environment variable USER is not defined, cannot determine is_logging_in")
            return False
        last_login_cmd = ["last", "--time-format=iso", username, "-1"]
        login_datetime = datetime.fromisoformat(subprocess.check_output(last_login_cmd).split()[3].decode("ascii"))
        return datetime.now(login_datetime.tzinfo) - login_datetime <= timedelta(seconds=30)
    except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError) as e:
        log_error(f"Non critical error, cannot determine is_logging_in: {last_login_cmd} {e}")
        return False


class VcpCapability:
    """Representation of a VCP (Virtual Control Panel) capability for a VDU."""

    def __init__(self, vcp_code: str, vcp_name: str, vcp_type: str, values: List = None,
                 causes_config_change: bool = False, icon_source: bytes = None, enabled: bool = False):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.vcp_type = vcp_type
        self.icon_source = icon_source
        self.causes_config_change = causes_config_change
        # Default config enablement
        self.enabled = enabled
        # For future use if we want to implement non-continuous types of VCP (VCP types SNC or CNC)
        self.values = [] if values is None else values

    def property_name(self) -> str:
        return re.sub('[^A-Za-z0-9_-]', '-', self.name).lower()


class DdcUtil:
    """
    Interface to the command line ddcutil Display Data Channel Utility for interacting with VDU's.
    The exception callback can return True if we should retry after errors (after the callback takes
    corrective action such as increasing the sleep_multiplier).
    """

    def __init__(self, debug: bool = False, common_args=None, default_sleep_multiplier: float = 1.0) -> None:
        super().__init__()
        self.debug = debug
        self.supported_codes = None
        self.default_sleep_multiplier = default_sleep_multiplier
        self.common_args = [] if common_args is None else common_args
        self.vcp_type_map = {}

    def change_settings(self, debug: bool, default_sleep_multiplier: float):
        self.debug = debug
        self.default_sleep_multiplier = default_sleep_multiplier

    def __run__(self, *args, sleep_multiplier: float = None) -> subprocess.CompletedProcess:
        if self.debug:
            log_debug("subprocess run    - ", DDCUTIL, args)
        multiplier_str = str(self.default_sleep_multiplier if sleep_multiplier is None else sleep_multiplier)
        result = subprocess.run(
            [DDCUTIL, '--sleep-multiplier', multiplier_str] + self.common_args + list(args),
            stdout=subprocess.PIPE, check=True)
        if self.debug:
            log_debug("subprocess result - ", result)
        return result

    def detect_monitors(self) -> List[Tuple[str, str, str, str]]:
        """Return a list of (vdu_id, desc) tuples."""
        display_list = []
        result = self.__run__('detect')
        # Going to get rid of anything that is not a-z A-Z 0-9 as potential rubbish
        rubbish = re.compile('[^a-zA-Z0-9]+')
        # This isn't efficient, it doesn't need to be, so I'm keeping re-defs close to where they are used.
        key_prospects = {}
        for display_str in re.split("\n\n", result.stdout.decode('utf-8')):
            display_match = re.search('Display ([0-9]+)', display_str)
            if display_match is not None:
                vdu_id = display_match.group(1)
                log_info(f"checking possible ID's for display {vdu_id}")
                fields = {m.group(1).strip(): m.group(2).strip() for m in re.finditer('[ \t]*([^:\n]+):[ \t]+([^\n]*)',
                                                                                      display_str)}
                model_name = rubbish.sub('_', fields.get('Model', 'unknown_model'))
                manufacturer = rubbish.sub('_', fields.get('Mfg id', 'unknown_mfg'))
                serial_number = rubbish.sub('_', fields.get('Serial number', ''))
                bin_serial_number = rubbish.sub('_', fields.get('Binary serial number', '').split('(')[0].strip())
                man_date = rubbish.sub('_', fields.get('Manufacture year', ''))
                i2c_bus_id = fields.get('I2C bus', '').replace("/dev/", '').replace("-", "_")
                for candidate in serial_number, bin_serial_number, man_date, i2c_bus_id, f"DisplayNum{vdu_id}":
                    if candidate.strip() != '':
                        possibly_unique = (model_name, candidate)
                        if possibly_unique in key_prospects:
                            # Not unique - it's already been encountered.
                            log_info(f"Ignoring non-unique key {possibly_unique[0]}_{possibly_unique[1]}"
                                     f" - it matches displays {vdu_id} and {key_prospects[possibly_unique][0]}")
                            del key_prospects[possibly_unique]
                        else:
                            log_debug(possibly_unique)
                            key_prospects[possibly_unique] = vdu_id, manufacturer
            elif len(display_str.strip()) != 0:
                log_warning(f"Ignoring unparsable {display_str}")

        # Try and pin down a unique id that won't change even if other monitors are turned off.
        # Ideally this should yield the same result for the same monitor - DisplayNum is the worst
        # for that, so it's the fallback.
        key_already_assigned = {}
        for model_and_main_id, vdu_id_and_manufacturer in key_prospects.items():
            vdu_id, manufacturer = vdu_id_and_manufacturer
            if vdu_id not in key_already_assigned:
                model_name, main_id = model_and_main_id
                log_info(f"Unique key for display={vdu_id} mfg={manufacturer} is (model={model_name} id={main_id})")
                display_list.append((vdu_id, manufacturer, model_name, main_id))
                key_already_assigned[vdu_id] = 1

        # For testing bad VDU's:
        # display_list.append(("3", "maker_y", "model_z", "1234"))
        return display_list

    def query_capabilities(self, vdu_id: str) -> str:
        """Return a vpc capabilities string."""
        result = self.__run__('--display', vdu_id, 'capabilities')
        capability_text = result.stdout.decode('utf-8')
        return capability_text

    def get_type(self, vcp_code):
        return self.vcp_type_map[vcp_code] if vcp_code in self.vcp_type_map else None

    def get_attribute(self, vdu_id: str, vcp_code: str, sleep_multiplier: float = None) -> Tuple[str, str]:
        """
        Given a VDU id and vcp_code, retrieve the attribute's current value from the VDU.

        Two values are returned, the monitor reported current value, and the monitor reported maximum value. Only
        attributes with "Continuous" values have a maximum, for consistency the method will return a zero maximum
        for "Non-Continuous" attributes.
        """
        value_pattern = re.compile(r'VCP ' + vcp_code + r' ([A-Z]+) (.+)\n')
        c_pattern = re.compile(r'([0-9]+) ([0-9]+)')
        snc_pattern = re.compile(r'x([0-9a-f]+)')
        cnc_pattern = re.compile(r'x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+)')
        # Try a few times in case there is a glitch due to a monitor being turned off/on
        for i in range(3):
            result = self.__run__('--brief', '--display', vdu_id, 'getvcp', vcp_code, sleep_multiplier=sleep_multiplier)
            value_match = value_pattern.match(result.stdout.decode('utf-8'))
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
            log_warning(f"obtained garbage '{result.stdout.decode('utf-8')}' will try again.")
            log_warning(f"ddcutil maybe running too fast for monitor {vdu_id}, try increasing --sleep-multiplier.")
            time.sleep(2)
        log_error(f"ddcutil failed all attempts to get value for monitor {vdu_id} vcp_code {vcp_code}")
        raise ValueError(
            f"ddcutil returned garbage for monitor {vdu_id} vcp_code {vcp_code}, try increasing --sleep-multiplier")

    def set_attribute(self, vdu_id: str, vcp_code: str, new_value: str, sleep_multiplier: float = None) -> None:
        """Send a new value to a specific VDU and vcp_code."""
        if self.get_type(vcp_code) == COMPLEX_NON_CONTINUOUS_TYPE:
            new_value = 'x' + new_value
        current, _ = self.get_attribute(vdu_id, vcp_code)
        if new_value != current:
            self.__run__('--display', vdu_id, 'setvcp', vcp_code, new_value, sleep_multiplier=sleep_multiplier)

    def vcp_info(self) -> str:
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return self.__run__('--verbose', 'vcpinfo').stdout.decode('utf-8')

    def get_supported_vcp_codes(self) -> Mapping[str, str]:
        """Returns a map of descriptions keyed by vcp_code, the codes that ddcutil appears to support."""
        if self.supported_codes is not None:
            return self.supported_codes
        self.supported_codes = {}
        info = DdcUtil().vcp_info()
        code_definitions = info.split("\nVCP code ")
        for code_def in code_definitions[1:]:
            # print(code_def)
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


def si(widget: QWidget, icon_number: int):
    return widget.style().standardIcon(icon_number)


class DialogSingletonMixin:
    """
    A mixin that can augment a QDialog or QMessageBox with code to enforce a singleton UI.
    For example, it is used so that only ones settings editor can be active at a time.
    """
    _dialogs_map = {}
    debug = False

    def __init__(self) -> None:
        """Registers the concrete class as a singleton so it can be reused later."""
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
        """
        If the dialog exists(), call this to make it visible by raising it.
        Internal, used by the class method show_existing_dialog()
        """
        # .show() is non-modal, .exec() is modal
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
        '10': VcpCapability('10', QT_TR_NOOP('brightness'), 'C', icon_source=BRIGHTNESS_SVG, enabled=True),
        '12': VcpCapability('12', QT_TR_NOOP('contrast'), 'C', icon_source=CONTRAST_SVG, enabled=True),
        '62': VcpCapability('62', QT_TR_NOOP('audio volume'), 'C', icon_source=VOLUME_SVG),
        '8D': VcpCapability('8D', QT_TR_NOOP('audio mute'), 'SNC', icon_source=VOLUME_SVG),
        '8F': VcpCapability('8F', QT_TR_NOOP('audio treble'), 'C', icon_source=VOLUME_SVG),
        '91': VcpCapability('91', QT_TR_NOOP('audio bass'), 'C', icon_source=VOLUME_SVG),
        '64': VcpCapability('91', QT_TR_NOOP('audio mic volume'), 'C', icon_source=VOLUME_SVG),
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
            except ValueError as ve:
                log_error(f"Illegal version number {version} should be i.j.k where i, j and k are integers.")
        return 1, 6, 0

    def is_version_ge(self, major, minor, release):
        current_major, current_minor, current_release = self.get_version()
        if current_major < major:
            return False
        if current_minor < minor:
            return False
        if current_release < release:
            return False
        return True

    def save(self, config_path, backup_dir_name: str | None = None) -> None:
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        if backup_dir_name is not None and config_path.exists():
            backup_dir = config_path.parent / backup_dir_name
            backup_dir.mkdir(exist_ok=True)
            file_version = 0
            backup_path = backup_dir / config_path.name
            while backup_path.exists():
                file_version += 1
                backup_path = backup_path.with_suffix(f".conf_{file_version}")
            config_path.rename(backup_path)
            log_info(f"Backed up old config as {backup_path.as_posix()}")
        with open(config_path, 'w') as config_file:
            self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_VERSION_OPTION] = VDU_CONTROLS_VERSION
            self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_TIMESTAMP_OPTION] = str(zoned_now())
            self.write(config_file)
        log_info(f"Wrote config to {config_path.as_posix()}")

    def duplicate(self):
        new_ini = ConfigIni()
        for section in self:
            if section != configparser.DEFAULTSECT and section != ConfigIni.METADATA_SECTION:
                new_ini.add_section(section)
            for option in self[section]:
                log_info(f"{section} {option}")
                new_ini[section][option] = self[section][option]
        return new_ini


class GeoLocation:
    def __init__(self, latitude: float, longitude: float, place_name: str):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.place_name: str = place_name

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, GeoLocation):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self.latitude == other.latitude and self.longitude == other.longitude and \
               self.place_name == other.place_name


class VduControlsConfig:
    """
    A vdu_controls config that can be read or written from INI style files by the standard configparser package.
    Includes a method that can fold in values from command line arguments parsed by the standard argparse package.
    """

    def __init__(self, config_name: str, default_enabled_vcp_codes: List = None, include_globals: bool = False) -> None:
        self.config_name = config_name
        self.ini_content = ConfigIni()
        # augment the configparser with type-info for run-time widget selection (default type is 'boolean')
        self.config_type_map = {
            QT_TR_NOOP('enable-vcp-codes'): 'csv', QT_TR_NOOP('sleep-multiplier'): 'float',
            QT_TR_NOOP('capabilities-override'): 'text',
            QT_TR_NOOP('location'): 'location',
        }

        if include_globals:
            self.ini_content[QT_TR_NOOP('vdu-controls-globals')] = {
                QT_TR_NOOP('system-tray-enabled'): 'no',
                QT_TR_NOOP('translations-enabled'): 'no',
                QT_TR_NOOP('splash-screen-enabled'): 'yes',
                QT_TR_NOOP('warnings-enabled'): 'no',
                QT_TR_NOOP('debug-enabled'): 'no',
                QT_TR_NOOP('syslog-enabled'): 'no',
                QT_TR_NOOP('location'): '',
            }

        self.ini_content[QT_TR_NOOP('vdu-controls-widgets')] = {}
        self.ini_content[QT_TR_NOOP('ddcutil-parameters')] = {}
        self.ini_content[QT_TR_NOOP('ddcutil-capabilities')] = {}

        for vcp_code, item in VDU_SUPPORTED_CONTROLS.by_code.items():
            self.ini_content['vdu-controls-widgets'][item.property_name()] = 'yes' if item.enabled else 'no'

        self.ini_content['vdu-controls-widgets']['enable-vcp-codes'] = ''

        self.ini_content['ddcutil-parameters']['sleep-multiplier'] = str(0.5)

        self.ini_content['ddcutil-capabilities']['capabilities-override'] = ''

        if default_enabled_vcp_codes is not None:
            for code in default_enabled_vcp_codes:
                if code in VDU_SUPPORTED_CONTROLS.by_code:
                    self.enable_supported_vcp_code(code)
                else:
                    self.enable_unsupported_vcp_code(code)
        self.file_path = None

    def get_config_type(self, section: str, option: str) -> str:
        if option in self.config_type_map:
            return self.config_type_map[option]
        return 'boolean'

    def restrict_to_actual_capabilities(self, vdu_capabilities: Mapping[str, VcpCapability]) -> None:
        for option in self.ini_content['vdu-controls-widgets']:
            if self.get_config_type('vdu-controls-widgets', option) == 'boolean' \
                    and VDU_SUPPORTED_CONTROLS.by_arg_name[option].vcp_code not in vdu_capabilities:
                del self.ini_content['vdu-controls-widgets'][option]

    def get_config_name(self) -> str:
        return self.config_name

    def is_system_tray_enabled(self) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', 'system-tray-enabled', fallback=False)

    def is_translations_enabled(self) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', 'translations-enabled', fallback=False)

    def is_splash_screen_enabled(self) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', 'splash-screen-enabled', fallback=True)

    def are_warnings_enabled(self) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', 'warnings-enabled', fallback=True)

    def is_debug_enabled(self) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', 'debug-enabled', fallback=False)

    def is_syslog_enabled(self) -> bool:
        return self.ini_content.getboolean('vdu-controls-globals', 'syslog-enabled', fallback=False)

    def get_sleep_multiplier(self) -> float:
        return self.ini_content.getfloat('ddcutil-parameters', 'sleep-multiplier', fallback=0.5)

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
            code = vcp_code.strip()
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
        log_info("using config file '" + config_path.as_posix() + "'")
        if re.search(r'(\[ddcutil-capabilities])|(\[ddcutil-parameters])|(\[vdu-controls-\w])', config_text) is None:
            log_info(f"old style config file {basename} overrides ddcutils capabilities")
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
        log_info(f"creating new config file {config_path.as_posix()}")
        self.ini_content.save(config_path)

    def parse_args(self, args=None) -> argparse.Namespace:
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
        parser.add_argument('--show',
                            default=[],
                            action='append',
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
        parser.add_argument('--translations-enabled', default=False, action='store_true',
                            help='enable langauage translations')
        parser.add_argument('--debug', default=False, action='store_true', help='enable debug output to stdout')
        parser.add_argument('--warnings', default=False, action='store_true',
                            help='popup a warning when a VDU lacks an enabled control')
        parser.add_argument('--syslog', default=False, action='store_true', help='enable diagnostic output to syslog')
        parser.add_argument('--no-splash', default=False, action='store_true', help="don't show the splash screen")
        parser.add_argument('--sleep-multiplier', type=float, default="0.5",
                            help='protocol reliability multiplier for ddcutil (typically 0.1 .. 2.0, default is 0.5)')
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

        if parsed_args.no_splash:
            self.ini_content['vdu-controls-globals']['splash-screen-enabled'] = 'no'
        if parsed_args.debug:
            self.ini_content['vdu-controls-globals']['debug-enabled'] = 'yes'
        if parsed_args.warnings:
            self.ini_content['vdu-controls-globals']['warnings-enabled'] = 'yes'
        if parsed_args.syslog:
            self.ini_content['vdu-controls-globals']['syslog-enabled'] = 'yes'
        if parsed_args.system_tray:
            self.ini_content['vdu-controls-globals']['system-tray-enabled'] = 'yes'
        if parsed_args.location:
            self.ini_content['vdu-controls-globals']['location'] = parsed_args.location
        if parsed_args.translations_enabled:
            self.ini_content['vdu-controls-globals']['translations-enabled'] = 'yes'

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
    two Display-Port inputs and it only has one.
    """

    vdu_setting_changed = pyqtSignal()

    def __init__(self, vdu_id: str, vdu_model_name: str, vdu_serial: str, manufacturer: str,
                 default_config: VduControlsConfig,
                 ddcutil: DdcUtil,
                 ignore_monitor: bool = False, assume_standard_controls: bool = False) -> None:
        super().__init__()
        self.vdu_id = vdu_id
        self.model_name = vdu_model_name
        self.serial = vdu_serial
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.sleep_multiplier = None
        self.enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        self.vdu_stable_id = proper_name(vdu_model_name, vdu_serial)
        # Provides backward compatibility for pre 1.7 presets where DisplayN was used in the section name.
        # In older versions sometimes DisplayN was used as part of the ID, that gets messy if a monitor is turned off
        # because the numbering changes.  Not all ID's prior to v1.7 would be display based, only those that lacked
        # a text serial number,
        self.pre1_7_display_based_id = proper_name(vdu_model_name.strip(), f"Display{vdu_id}")
        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text = None
        self.config = None
        self.convert_to_v1_7_check(default_config)
        for config_name in (self.vdu_stable_id, self.pre1_7_display_based_id, self.vdu_model_id):
            config_path = get_config_path(config_name)
            log_info("checking for config file '" + config_path.as_posix() + "'")
            if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
                config = VduControlsConfig(config_name,
                                           default_enabled_vcp_codes=default_config.get_all_enabled_vcp_codes())
                config.parse_file(config_path)
                if default_config.is_debug_enabled():
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
            config.set_capabilities_alt_text(self.capabilities_text)
            config.write_file(save_config_path)
            self.config = config

    def get_vdu_description(self) -> str:
        """Return a unique description using the serial-number (if defined) or vdu_id."""
        return self.model_name + ':' + (self.serial if len(self.serial) != 0 else self.vdu_id)

    def get_full_id(self) -> Tuple[str, str, str, str]:
        """Return a tuple that defines this VDU: (vdu_id, manufacturer, model, serial-number)."""
        return self.vdu_id, self.manufacturer, self.model_name, self.serial

    def get_attribute(self, vcp_code: str) -> Tuple[str, str]:
        try:
            return self.ddcutil.get_attribute(self.vdu_id, vcp_code, sleep_multiplier=self.sleep_multiplier)
        except subprocess.CalledProcessError as e:
            alert = MessageBox(QMessageBox.Critical)
            alert.setText(tr("Failed to obtain monitor {} vcp_code {}").format(self.vdu_id, vcp_code))
            alert.setInformativeText(
                "Problem communicating with monitor {} {}. Controls may be incorrect.".format(self.vdu_id, str(e)))
            alert.exec()
            return '0', '0'

    def set_attribute(self, vcp_code: str, value: str) -> None:
        self.ddcutil.set_attribute(self.vdu_id, vcp_code, value, sleep_multiplier=self.sleep_multiplier)
        self.vdu_setting_changed.emit()

    def _parse_capabilities(self, capabilities_text=None) -> Mapping[str, VcpCapability]:
        """Return a map of vpc capabilities keyed by vcp code."""

        def parse_values(values_str: str) -> List[str]:
            stripped = values_str.strip()
            values_list = []
            if len(stripped) != 0:
                lines_list = stripped.split('\n')
                if len(lines_list) == 1:
                    range_pattern = re.compile('Values:\s+([0-9]+)..([0-9]+)')
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
        feature_map: Mapping[str, VcpCapability] = {}
        for feature_text in capabilities_text.split(' Feature: '):
            feature_match = feature_pattern.match(feature_text)
            if feature_match:
                vcp_code = feature_match.group(1)
                vcp_name = feature_match.group(2)
                values = parse_values(feature_match.group(3))
                # Guess type from existence or not of value list
                vcp_type = CONTINUOUS_TYPE if len(values) == 0 or values[0] == "%%Range%%" else GUI_NON_CONTINUOUS_TYPE
                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None)
                feature_map[vcp_code] = capability
        return feature_map

    def convert_to_v1_7_check(self, default_config: VduControlsConfig):
        # Only some config files will have old display based names - those whose monitor lacked a text serial number.
        old_config_path = get_config_path(self.pre1_7_display_based_id)
        if old_config_path.exists():
            new_config_path = get_config_path(self.vdu_stable_id)
            if new_config_path.exists():
                if old_config_path.exists():
                    log_warning(f"Skipping conversion of {old_config_path.as_posix()} to v1.7+ "
                                f" '{new_config_path.as_posix()} already exists")
            else:
                new_config = VduControlsConfig(self.vdu_stable_id,
                                               default_enabled_vcp_codes=default_config.get_all_enabled_vcp_codes())
                new_config.parse_file(old_config_path)
                new_config.ini_content.save(new_config_path, backup_dir_name='pre-v1.7')
                log_warning(f"Converted {old_config_path.as_posix()} to v1.7+ "
                            f" {new_config_path.as_posix()}")


class SettingsEditor(QDialog, DialogSingletonMixin):
    """
    Application Settings Editor, edits a default global settings file, and a settings file for each VDU.
    The files are in INI format.  Internally the settings are VduControlsConfig wrappers around
    the standard class ConfigIni.
    """

    @staticmethod
    def invoke(default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig],
               change_callback: callable) -> None:
        if SettingsEditor.exists():
            SettingsEditor.show_existing_dialog()
        else:
            SettingsEditor(default_config, vdu_config_list, change_callback)

    def __init__(self, default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig],
                 change_callback) -> None:
        super().__init__()
        self.setWindowTitle(tr('Settings'))
        self.setMinimumWidth(1024)
        layout = QVBoxLayout()
        self.setLayout(layout)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        self.editors = []
        self.change_callback = change_callback
        for config in [default_config, ] + vdu_config_list:
            tab = SettingsEditorTab(self, config, change_callback)
            tab.save_all_clicked.connect(self.save_all)
            tabs.addTab(tab, config.get_config_name())
            self.editors.append(tab)
        # .show() is non-modal, .exec() is modal
        self.make_visible()

    def save_all(self, nothing_to_save_warning: bool = True):
        nothing_was_saved = True
        # Do the main config last - it may cause a restart of the app
        self.setEnabled(False)
        save_order = self.editors[1:] + [self.editors[0]]
        for editor in save_order:
            if editor.is_unsaved():
                editor.save(cancel=QMessageBox.Ignore)
                nothing_was_saved = False
        if nothing_to_save_warning and nothing_was_saved:
            alert = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Yes | QMessageBox.No, default=QMessageBox.No)
            alert.setText(tr("Nothing needs saving. Do you wish to save anyway?"))
            if alert.exec() == QMessageBox.Yes:
                for editor in save_order:
                    editor.save(cancel=QMessageBox.Ignore, force=True)
        self.setEnabled(True)

    def closeEvent(self, event) -> None:
        self.save_all(nothing_to_save_warning=False)
        super().closeEvent(event)


class SettingsEditorTab(QWidget):
    """A tab corresponding to a settings file, generates UI widgets for each tab based on what's in the config. """

    save_all_clicked = pyqtSignal()

    def __init__(self, parent: QWidget, vdu_config: VduControlsConfig, change_callback: callable) -> None:
        super().__init__()
        editor_layout = QVBoxLayout()
        self.change_callback = change_callback
        self.changed = {}
        self.setLayout(editor_layout)
        self.config_path = get_config_path(vdu_config.config_name)
        self.ini_before = vdu_config.ini_content
        self.change_callback = change_callback
        self.ini_editable = self.ini_before.duplicate()
        self.field_list = []

        def field(widget: SettingsEditor.SettingsEditorFieldBase) -> QWidget:
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
                data_type = vdu_config.get_config_type(section, option)
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
                self.save(cancel=QMessageBox.Cancel)
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

    def save(self, cancel: int = QMessageBox.Close, force: bool = False) -> None:
        if self.is_unsaved() or force:
            confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | cancel, default=QMessageBox.Save)
            message = tr('Update existing {}?') if self.config_path.exists() else tr("Create new {}?")
            message = message.format(self.config_path.as_posix())
            confirmation.setText(message)
            if confirmation.exec() == QMessageBox.Save:
                self.ini_editable.save(self.config_path)
                copy = pickle.dumps(self.ini_editable)
                self.ini_before = pickle.loads(copy)
                # After file is closed...
                self.change_callback(self.changed)
                self.changed = {}
            else:
                copy = pickle.dumps(self.ini_before)
                self.ini_editable = pickle.loads(copy)
                self.reset()

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

    def translate_option(self):
        return translate_option(self.option)


class SettingsEditorBooleanWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        layout = QHBoxLayout()
        self.setLayout(layout)
        checkbox = QCheckBox(self.translate_option())
        checkbox.setChecked(section_editor.ini_editable.getboolean(section, option))

        def toggled(is_checked: bool) -> None:
            # print(section, option, is_checked)
            section_editor.ini_editable[section][option] = 'yes' if is_checked else 'no'

        checkbox.toggled.connect(toggled)
        layout.addWidget(checkbox)
        self.checkbox = checkbox

    def reset(self):
        self.checkbox.setChecked(self.section_editor.ini_before.getboolean(self.section, self.option))


class SettingsEditorFloatWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        layout = QHBoxLayout()
        self.setLayout(layout)
        text_label = QLabel(self.translate_option())
        layout.addWidget(text_label)
        text_input = QLineEdit()
        text_input.setMaximumWidth(100)
        text_input.setMaxLength(4)
        text_validator = QDoubleValidator()
        text_validator.setRange(0.1, int(3.0), 4)
        text_input.setValidator(text_validator)
        text_input.setText(section_editor.ini_editable[section][option])

        def editing_finished() -> None:
            # print(section, option, text_input.text())
            section_editor.ini_editable[section][option] = str(text_input.text())

        text_input.editingFinished.connect(editing_finished)
        layout.addWidget(text_input)
        layout.addStretch(1)
        self.text_input = text_input

    def reset(self):
        self.text_input.setText(self.section_editor.ini_before[self.section][self.option])


class SettingsEditorCsvWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        layout = QVBoxLayout()
        self.setLayout(layout)
        text_label = QLabel(self.translate_option())
        layout.addWidget(text_label)
        text_input = QLineEdit()
        text_input.setMaximumWidth(1000)
        text_input.setMaxLength(500)
        # TODO - should probably also allow spaces as well as commas, but the regexp is getting a bit tricky?
        # Validator matches CSV of two digit hex or the empty string.
        validator = QRegExpValidator(QRegExp(r"^([0-9a-fA-F]{2}([ \t]*,[ \t]*[0-9a-fA-F]{2})*)|$"))
        text_input.setValidator(validator)
        text_input.setText(section_editor.ini_editable[section][option])

        def editing_finished() -> None:
            # print(section, option, text_input.text())
            section_editor.ini_editable[section][option] = str(text_input.text())

        def input_rejected() -> None:
            text_input.setStyleSheet("QLineEdit { color : red; }")

        def text_edited() -> None:
            text_input.setStyleSheet(None)

        text_input.editingFinished.connect(editing_finished)
        text_input.inputRejected.connect(input_rejected)
        text_input.textEdited.connect(text_edited)
        layout.addWidget(text_input)
        self.text_input = text_input

    def reset(self):
        self.text_input.setText(self.section_editor.ini_before[self.section][self.option])


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
                except ValueError as e:
                    return QValidator.Intermediate, text, pos
        return result


class SettingsEditorLocationWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str) -> None:
        super().__init__(section_editor, option, section)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)
        text_label = QLabel(self.translate_option())
        layout.addWidget(text_label)
        text_input = QLineEdit()
        text_input.setFixedWidth(500)
        text_input.setMaximumWidth(500)
        text_input.setMaxLength(250)

        validator = LatitudeLongitudeValidator()
        text_input.setValidator(validator)
        text_input.setText(section_editor.ini_editable[section][option])

        def editing_finished() -> None:
            # print(section, option, text_input.text())
            section_editor.ini_editable[section][option] = str(text_input.text())

        def input_rejected() -> None:
            text_input.setStyleSheet("QLineEdit { color : red; }")

        def text_edited() -> None:
            text_input.setStyleSheet(None)

        text_input.editingFinished.connect(editing_finished)
        text_input.inputRejected.connect(input_rejected)
        text_input.textEdited.connect(text_edited)
        text_input.setToolTip(tr("Latitude,Longitude for solar elevation calculations."))

        def detection_location():
            data_csv = self.location_dialog()
            if data_csv:
                text_input.setText(data_csv)
                editing_finished()

        detect_location_button = QPushButton(tr("Detect"))
        detect_location_button.clicked.connect(detection_location)
        detect_location_button.setToolTip(tr("Detect location by querying this desktop's external IP address."))
        layout.addWidget(text_input)
        layout.addWidget(detect_location_button)
        layout.addStretch(1)

        self.text_input = text_input

    def reset(self):
        self.text_input.setText(self.section_editor.ini_before[self.section][self.option])

    def retrieve_ipinfo(self) -> Mapping:
        """
        https://stackoverflow.com/a/55432323/609575
        """
        from urllib.request import urlopen
        from json import load
        with urlopen(self.get_ipinfo_url()) as res:
            return load(res)

    def get_ipinfo_url(self):
        return os.getenv('VDU_CONTROLS_IPINFO_URL', default='https://ipinfo.io/json')

    def location_dialog(self) -> str | None:
        ask_permission = MessageBox(QMessageBox.Question, buttons=QMessageBox.Yes | QMessageBox.No)
        ask_permission.setText(
            tr('Query {} to obtain information based on your IP-address?').format(self.get_ipinfo_url()))
        if ask_permission.exec() == QMessageBox.Yes:
            try:
                ipinfo = self.retrieve_ipinfo()
                info_text = f"{tr('Use the following info?')}\n" f"{ipinfo['loc']}\n" + \
                            ','.join([ipinfo[key] for key in ('city', 'region', 'country') if key in ipinfo])
                full_text = f"Queried {self.get_ipinfo_url()}\n" + \
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
                    tr("Failed to obtain info from {}: {}").format(self.get_ipinfo_url(), e))
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
            # print(section, option, text_editor.toPlainText())
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
    alert = MessageBox(QMessageBox.Critical)
    alert.setText(reason)
    alert.setInformativeText(tr('When this message is dismissed, vdu_controls will restart.'))
    alert.exec()
    QCoreApplication.exit(EXIT_CODE_FOR_RESTART)


class VduControlSlider(QWidget):
    """
    GUI control for a DDC continuously variable attribute.

    A compound widget with icon, slider, and text-field.  This is a duck-typed GUI control widget (could inherit
    from an abstract type if we wanted to get formal about it).
    """
    connected_vdus_changed = pyqtSignal()

    def __init__(self, vdu_model: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__()

        self.vdu_model = vdu_model
        self.vcp_capability = vcp_capability
        self.current_value: int | None = None
        self.max_value: int | None = None
        # Populates the None ints above:
        self.refresh_data()

        layout = QHBoxLayout()
        self.setLayout(layout)
        self.svg_icon = None

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
        if len(vcp_capability.values) != 0:
            slider.setRange(int(vcp_capability.values[1]), int(vcp_capability.values[2]))
        else:
            slider.setRange(0, int(self.max_value))
        slider.setValue(int(self.current_value))
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setOrientation(Qt.Horizontal)
        # Don't rewrite the ddc value too often - not sure of the implications
        slider.setTracking(False)
        layout.addWidget(slider)

        text_input = QLineEdit()
        text_input.setMaximumWidth(50)
        text_input.setMaxLength(4)
        text_validator = QIntValidator()
        text_validator.setRange(0, int(self.max_value))
        text_input.setValidator(text_validator)
        text_input.setText(str(slider.value()))
        layout.addWidget(text_input)

        def slider_changed(value: int) -> None:
            self.current_value = str(value)
            text_input.setText(self.current_value)
            while True:
                try:
                    self.vdu_model.set_attribute(self.vcp_capability.vcp_code, self.current_value)
                    if self.vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                            VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].causes_config_change:
                        # The VCP command has turned one off a VDU or changed what it is connected to.
                        # VDU ID's will now be out of whack - restart the GUI.
                        self.connected_vdus_changed.emit()
                    return
                except subprocess.SubprocessError:
                    msg = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Retry | QMessageBox.Close, default=QMessageBox.Retry)
                    msg.setText(tr("Set value: Failed to communicate with display {}").format(self.vdu_model.vdu_id))
                    msg.setInformativeText(tr('Is the monitor switched off?<br>'
                                              'Is the sleep-multiplier setting too low?'))
                    if msg.exec() != QMessageBox.Retry:
                        self.connected_vdus_changed.emit()
                        return

        slider.valueChanged.connect(slider_changed)

        def slider_moved(value: int) -> None:
            text_input.setText(str(value))

        slider.sliderMoved.connect(slider_moved)

        def text_changed() -> None:
            slider.setValue(int(text_input.text()))

        text_input.editingFinished.connect(text_changed)

    def refresh_data(self) -> None:
        """Query the VDU for a new data value and cache it (maybe called from a task thread, so no GUI op's here)."""
        for i in range(4):
            try:
                new_value, max_value = self.vdu_model.get_attribute(self.vcp_capability.vcp_code)
                if self.max_value is None:
                    # Validate as integer
                    int(new_value)
                    int(max_value)
                    self.current_value, self.max_value = new_value, max_value
                else:
                    int(new_value)
                    self.current_value = new_value
                return
            except ValueError as ve:
                # Might be initializing at login - can cause transient errors due to X11 talking to
                # the monitor.
                log_warning(f"Non integer values for slider {self.vdu_model.vdu_stable_id} "
                            f"{self.vcp_capability.name} = {new_value} (max={max_value})")
                log_warning("have to repeat vdu_model.get_attribute - maybe --sleep-multiplier is set too low?")
                sleep_secs = 3.0
                log_warning(f"will try again in {sleep_secs} seconds in case this a transient error due to session "
                            f"initialisation.")
                time.sleep(sleep_secs)
                continue
        # Something is wrong with ddcutils - pass the buck
        raise ValueError(
            f"Non integer values for slider {self.vdu_model.vdu_stable_id} {self.vcp_capability.name} = {new_value} (max={max_value})")

    def refresh_view(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        self.slider.setValue(int(self.current_value))

    def event(self, event: QEvent) -> bool:
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.svg_icon.load(handle_theme(VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].icon_source))
        event.accept()
        return True


class VduControlComboBox(QWidget):
    """
    GUI control for a DDC non-continuously variable attribute, one that has a list of choices.

    This is a duck-typed GUI control widget (could inherit from an abstract type if we wanted to get formal about it).
    """
    connected_vdus_changed = pyqtSignal()

    def __init__(self, vdu_model: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the combobox control and initialize its values from the VDU."""
        super().__init__()

        self.vdu_model = vdu_model
        self.vcp_capability = vcp_capability
        self.current_value = vdu_model.get_attribute(vcp_capability.vcp_code)[0]

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

        self.validate_value()
        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))

        def index_changed(index: int) -> None:
            self.current_value = self.combo_box.currentData()
            self.validate_value()
            while True:
                try:
                    self.vdu_model.set_attribute(self.vcp_capability.vcp_code, self.current_value)
                    if self.vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                            VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].causes_config_change:
                        self.connected_vdus_changed.emit()
                    return
                except subprocess.SubprocessError:
                    msg = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Retry | QMessageBox.Close, default=QMessageBox.Retry)
                    msg.setText(tr("Set option: failed to communicate with display {}").format(self.vdu_model.vdu_id))
                    msg.setInformativeText(tr('Is the monitor switched off?<br>'
                                              'Is the sleep-multiplier setting too low?'))
                    if msg.exec() == QMessageBox.Close:
                        self.connected_vdus_changed.emit()
                        return

        combo_box.currentIndexChanged.connect(index_changed)

    def translate_label(self, source: str):
        canonical = source.lower()
        maybe = tr(canonical)
        result = maybe if maybe != canonical else source
        # Default to capitalized version of each word
        return ' '.join(w[:1].upper() + w[1:] for w in result.split(' '))

    def refresh_data(self) -> None:
        """Query the VDU for a new data value and cache it (maybe called from a task thread, so no GUI op's here)."""
        self.current_value, _ = self.vdu_model.get_attribute(self.vcp_capability.vcp_code)

    def refresh_view(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
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
                    vdesc=self.vdu_model.get_vdu_description(),
                    vnum=self.vdu_model.vdu_id,
                    code=self.vcp_capability.vcp_code,
                    cdesc=self.vcp_capability.name,
                    value=self.current_value,
                    valid=self.keys))
            alert.setInformativeText(
                tr('If you want to extend the set of permitted values, you can edit the metadata '
                   'for {} in the settings panel.  For more details see the man page concerning '
                   'VDU/VDU-model config files.').format(self.vdu_model.get_vdu_description()))
            alert.exec()


class VduControlPanel(QWidget):
    """
    Widget that contains all the controls for a single VDU (monitor/display).

    The widget maintains a list of GUI "controls" that are duck-typed and will have refresh_data() and refresh_view()
    methods.
    """
    connected_vdus_changed = pyqtSignal()

    def __init__(self, vdu_model: VduController, warnings: bool) -> None:
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        label.setText(tr('Monitor {}: {}').format(vdu_model.vdu_id, vdu_model.get_vdu_description()))
        layout.addWidget(label)
        self.vdu_model = vdu_model
        self.vcp_controls = []

        for vcp_code in vdu_model.enabled_vcp_codes:
            if vcp_code in vdu_model.capabilities:
                control = None
                capability = vdu_model.capabilities[vcp_code]
                if capability.vcp_type == CONTINUOUS_TYPE:
                    control = VduControlSlider(vdu_model, capability)
                elif capability.vcp_type == GUI_NON_CONTINUOUS_TYPE:
                    try:
                        control = VduControlComboBox(vdu_model, capability)
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
                        vdu_model.get_vdu_description(), tr(missing_vcp)))
                alert.setInformativeText(tr('No read/write ability for vcp_code {}.').format(vcp_code))
                alert.exec()
        if len(self.vcp_controls) != 0:
            self.setLayout(layout)

    def refresh_data(self) -> None:
        """Tell the control widgets to get fresh VDU data (maybe called from a task thread, so no GUI op's here)."""
        for control in self.vcp_controls:
            control.refresh_data()

    def refresh_view(self) -> None:
        """Tell the control widgets to refresh their views from their internally cached values."""
        for control in self.vcp_controls:
            control.refresh_view()

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)

    def copy_state(self, preset_ini: ConfigIni, update_only) -> None:
        vdu_section_name = self.vdu_model.vdu_stable_id
        if not preset_ini.has_section(vdu_section_name):
            preset_ini.add_section(vdu_section_name)
        for control in self.vcp_controls:
            if not update_only or preset_ini.has_option(vdu_section_name, control.vcp_capability.property_name()):
                preset_ini[vdu_section_name][control.vcp_capability.property_name()] = control.current_value

    def restore_vdu_state(self, preset_ini: ConfigIni) -> None:
        self.restore_vdu_state_for_id(preset_ini, self.vdu_model.vdu_stable_id)

    def restore_vdu_state_pre17(self, preset_ini: ConfigIni):
        # Provides backward compatibility for pre 1.7 presets where DisplayN was used in the section name - those
        # monitors that lacked a text serial number.
        self.restore_vdu_state_for_id(preset_ini, self.vdu_model.pre1_7_display_based_id)

    def restore_vdu_state_for_id(self, preset_ini: ConfigIni, vdu_id: str) -> None:
        log_info(f"Preset restoring {vdu_id}")
        for control in self.vcp_controls:
            if control.vcp_capability.property_name() in preset_ini[vdu_id]:
                control.current_value = preset_ini[vdu_id][control.vcp_capability.property_name()]
        self.refresh_view()

    def is_preset_active(self, preset_ini: ConfigIni) -> bool:
        vdu_section = self.vdu_model.vdu_stable_id
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
        self.timer = None
        self.timer_action = None
        self.elevation_time_today = None

    def get_icon_path(self) -> Path | None:
        if self.preset_ini.has_section("preset"):
            path_text = self.preset_ini.get("preset", "icon", fallback=None)
            return Path(path_text) if path_text else None
        return None

    def set_icon_path(self, icon_path: Path):
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
            return create_icon_from_text(abbreviation)

    def load(self) -> ConfigIni:
        if self.path.exists():
            log_info(f"reading preset file '{self.path.as_posix()}'")
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
        log_info(f"deleting preset file '{self.path.as_posix()}'")
        self.remove_elevation_trigger()
        if self.path.exists():
            os.remove(self.path.as_posix())

    def get_solar_elevation(self) -> SolarElevationKey | None:
        elevation_spec = self.preset_ini.get('preset', 'solar-elevation', fallback=None)
        if elevation_spec:
            solar_elevation = parse_solar_elevation_ini_text(elevation_spec)
            return solar_elevation
        return None

    def get_solar_elevation_abbreviation(self) -> str | None:
        elevation = self.get_solar_elevation()
        if elevation is None:
            return ''
        result = format_solar_elevation_abbreviation(elevation)
        if self.elevation_time_today:
            result += ' \u25F4 ' + self.elevation_time_today.strftime("%H:%M")
        else:
            # Not possible today - sun doesn't get that high
            result += ' \u29BB'
        if self.get_weather_restriction_filename() is not None:
            result += ' \u2614'
        if self.timer and self.timer.remainingTime() > 0:
            # This character is too tall - it causes a jump when rendered - but nothing else is quite as appropriate.
            result += ' \u23F3'
        return result

    def get_solar_elevation_description(self) -> str | None:
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
                template = tr("{} earlier today at {}") + weather_suffix
            else:
                template = tr("{} suspended for  {}")
            result = template.format(basic_desc, self.elevation_time_today.strftime(tr("%H:%M")))
        else:
            result = basic_desc + ' ' + tr("the sun does not rise this high today")
        return result

    def start_timer(self, when_local: datetime, action: Callable):
        if self.timer:
            self.timer.stop()
        else:
            self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer_action = action
        self.timer.timeout.connect(partial(action, self))
        millis = int((when_local - zoned_now()) / timedelta(milliseconds=1))
        self.timer.start(millis)
        log_info(
            f"Preset scheduled activation for '{self.name}' at {when_local} in {round(millis / 1000 / 60)} minutes "
            f"{self.get_solar_elevation()}")

    def remove_elevation_trigger(self):
        log_info(f"Preset elevation trigger removed for '{self.name}'")
        if self.timer:
            log_info(f"Preset timer stopped for '{self.name}'")
            self.timer.stop()
            self.timer = None
        if self.elevation_time_today:
            self.elevation_time_today = None

    def toggle_timer(self):
        if self.elevation_time_today and self.elevation_time_today > zoned_now():
            if self.timer.remainingTime() > 0:
                log_info(f"Preset scheduled timer cleared for '{self.name}'")
                self.timer.stop()
            else:
                log_info(f"Preset scheduled timer restored for '{self.name}'")
                self.start_timer(self.elevation_time_today, self.timer_action)

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

    def convert_v1_7(self, new_and_old_ids: List) -> str | None:
        """Returns problem id's if any"""
        if self.preset_ini.is_version_ge(1, 7, 0):
            # Already converted
            return None
        new_indexed_by_old = {old_id: new_id for new_id, old_id in new_and_old_ids}
        for old_id, new_stable_id in new_indexed_by_old.items():
            if self.preset_ini.has_section(old_id):
                if not self.preset_ini.has_section(new_stable_id):
                    self.preset_ini.add_section(new_stable_id)
                for option in self.preset_ini[old_id]:
                    self.preset_ini[new_stable_id][option] = self.preset_ini[old_id][option]
                self.preset_ini.remove_section(old_id)
        for vdu_id in self.preset_ini.data_sections():
            if re.search("_Display[0-9]$", vdu_id):
                log_info(f"Failed to convert Preset {self.name} VDU {vdu_id} to v1.7+,"
                         " a participating display wasn't available.")
                # Not fully converted - probably a display is turned off.
                return vdu_id
        self.preset_ini.save(self.path, backup_dir_name=(self.path.parent / 'pre-v1.7').as_posix())
        log_info(f"Converted preset {self.name} to v1.7+ format.")
        return None

    def is_weather_ok(self, location: GeoLocation):
        weather_restriction_filename = self.get_weather_restriction_filename()
        if weather_restriction_filename is None:
            return True
        if Path(weather_restriction_filename).exists():
            with open(weather_restriction_filename) as weather_file:
                code_list = weather_file.readlines()
            log_info(f"Preset {self.name} weather requirements {weather_restriction_filename}: {code_list}")
            try:
                weather = QueryWeather(location.place_name)
                if weather.area_name == "UNKNOWN":
                    msg = MessageBox(QMessageBox.Warning)
                    msg.setText(
                        tr("Unknown weather location, ignoring weather requirements. Please check Settings Location."))
                    msg.exec()
                    return True
                log_info(f"Current weather: {weather.area_name} {weather.weather_code} {weather.weather_desc}")
                for code_line in code_list:
                    # Allow spaces or commas
                    required_code = code_line.strip().split()[0].split(',')[0]
                    if weather.weather_code.strip() == required_code:
                        log_info("Meet required weather conditions "
                                 f"{weather.area_name} {weather.weather_desc} {weather.weather_code}")
                        return True
                log_info(f"Cancelled due to weather")
            except ValueError as e:
                msg = MessageBox(QMessageBox.Warning)
                msg.setText(
                    tr("Ignoring weather requirements, unable to query local weather: {}").format(str(e.args[0])))
                msg.setInformativeText(e.args[1])
                msg.exec()
                return True
            return False

    def get_weather_restriction_filename(self):
        weather_restriction_filename = \
            self.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None)
        return weather_restriction_filename


class ContextMenu(QMenu):

    def __init__(self,
                 main_window,
                 main_window_action,
                 about_action, help_action, chart_action, settings_action,
                 presets_action, refresh_action, quit_action) -> None:
        super().__init__()
        self.main_window = main_window
        if main_window_action is not None:
            self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Control Panel'), main_window_action)
            self.addSeparator()
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Presets'), presets_action)
        self.presets_separator = self.addSeparator()

        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Grey Scale'), chart_action)
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Settings'), settings_action)
        self.addAction(si(self, QStyle.SP_BrowserReload), tr('Refresh'), refresh_action)
        self.addAction(si(self, QStyle.SP_MessageBoxInformation), tr('About'), about_action)
        self.addAction(si(self, QStyle.SP_DialogHelpButton), tr('Help'), help_action)
        self.addSeparator()
        self.addAction(si(self, QStyle.SP_DialogCloseButton), tr('Quit'), quit_action)

    def insert_preset_menu_item(self, preset: Preset) -> None:
        # Have to add it first and then move it (otherwise it won't appear - weird).

        def restore_preset() -> None:
            self.main_window.restore_named_preset(self.sender().text())

        action = self.addAction(preset.create_icon(), preset.name, restore_preset)
        self.insertAction(self.presets_separator, action)
        # print(self.actions())
        self.update()

    def remove_preset_menu_item(self, preset: Preset):
        self.removeAction(self.get_preset_menu_item(preset.name))

    def refresh_preset_menu(self, reload: bool = False) -> None:
        if reload:
            for name, preset in self.main_window.preset_controller.find_presets().items():
                self.remove_preset_menu_item(preset)
        for name, preset in self.main_window.preset_controller.find_presets().items():
            if not self.has_preset_menu_item(name):
                self.insert_preset_menu_item(preset)

    def has_preset_menu_item(self, name: str) -> bool:
        for action in self.actions():
            if action == self.presets_separator:
                break
            if action.text() == name:
                return True
        return False

    def get_preset_menu_item(self, name: str) -> QAction | None:
        for action in self.actions():
            if action == self.presets_separator:
                break
            if action.text() == name:
                return action
        return None


class BottomToolBar(QToolBar):

    def __init__(self, start_refresh_func, app_context_menu, parent):
        super().__init__(parent=parent)
        self.refresh_action = self.addAction(
            create_icon_from_svg_bytes(REFRESH_ICON_SOURCE), "Refresh settings from monitors", start_refresh_func)
        self.setIconSize(QSize(32, 32))
        self.progress_bar = QProgressBar(self)
        # Disable text percentage label on the spinner progress-bar
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setDisabled(True)
        self.addWidget(self.progress_bar)

        self.menu_button = QToolButton(self)
        self.menu_button.setIcon(create_icon_from_svg_bytes(MENU_ICON_SOURCE))
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setToolTip("Context and Preset Menu")

        self.preset_action = self.addAction(QIcon(), "")
        self.preset_action.setVisible(False)
        self.preset_action.triggered.connect(self.menu_button.click)

        self.addWidget(self.menu_button)

        self.installEventFilter(self)

    def eventFilter(self, target: QObject, event: QEvent) -> bool:
        super().eventFilter(target, event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.refresh_action.setIcon(create_icon_from_svg_bytes(REFRESH_ICON_SOURCE))
            self.menu_button.setIcon(create_icon_from_svg_bytes(MENU_ICON_SOURCE))
        event.accept()
        return True

    def indicate_refresh_in_progress(self):
        self.refresh_action.setDisabled(True)
        self.menu_button.setDisabled(True)
        self.progress_bar.setDisabled(False)
        # Setting range to 0,0 cause the progress bar to pulsate left/right - used as a busy spinner.
        self.progress_bar.setRange(0, 0)

    def indicate_refresh_complete(self):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setDisabled(True)
        self.refresh_action.setDisabled(False)
        self.menu_button.setDisabled(False)

    def display_active_preset(self, preset: Preset | None):
        if preset:
            self.preset_action.setToolTip(f"{preset.name} preset")
            self.preset_action.setIcon(preset.create_icon())
            self.preset_action.setVisible(True)
        else:
            self.preset_action.setToolTip("")
            self.preset_action.setIcon(QIcon())
            self.preset_action.setVisible(False)
        self.layout().update()


class VduControlsMainPanel(QWidget):
    """GUI for detected VDU's, it will construct and contain a control panel for each VDU."""
    refresh_finished = pyqtSignal()
    vdu_detected = pyqtSignal(VduController)
    vdu_setting_changed = pyqtSignal()
    connected_vdus_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.vdu_controllers = []
        self.warnings = None
        self.bottom_toolbar = None
        self.context_menu = None
        self.ddcutil = None
        self.refreshDataTask = None
        self.setObjectName("vdu_controls_main_panel")
        self.non_standard_enabled = None
        self.vdu_control_panels = []
        self.previously_detected_vdus = []
        self.detected_vdus = []
        self.new_and_old_ids = []

    def initialise_control_panels(self, app_context_menu: ContextMenu, main_config: VduControlsConfig,
                                  session_startup: bool):
        if self.layout():
            # Already laid out, must be responding to a configuration change requiring re-layout.
            # Remove all exisiting widgets.
            for i in range(0, self.layout().count()):
                item = self.layout().itemAt(i)
                if isinstance(item, QWidget):
                    self.layout().removeWidget(item)
                    item.deleteLater()
                elif isinstance(item, QWidgetItem):
                    self.layout().removeItem(item)
                    item.widget().deleteLater()

        layout = QVBoxLayout()
        self.setLayout(layout)
        ddcutil_common_args = ['--force', ] if self.is_non_standard_enabled() else []
        self.ddcutil = DdcUtil(debug=main_config.is_debug_enabled(), common_args=ddcutil_common_args,
                               default_sleep_multiplier=main_config.get_sleep_multiplier())
        ddcutil_problem = None
        try:
            self.detected_vdus = self.ddcutil.detect_monitors()
            if session_startup:
                # Loop in case the session is initialising/restoring which can make detection unreliable.
                # Limit to a reasonable number of iterations.
                for i in range(10):
                    log_info("Session appears to be initialising, delaying and looping detection until it stabilises.")
                    time.sleep(1.5)
                    prev_num = len(self.detected_vdus)
                    self.detected_vdus = self.ddcutil.detect_monitors()
                    if prev_num == len(self.detected_vdus):
                        log_info(f"Number of detected monitors is stable at {len(self.detected_vdus)}")
                        break
                    log_info(f"Number of detected monitors changed from {prev_num} to {len(self.detected_vdus)}")
        except Exception as e:
            log_error(e)
            ddcutil_problem = e
        self.previously_detected_vdus = self.detected_vdus
        self.context_menu = app_context_menu
        app_context_menu.refresh_preset_menu()
        controllers_layout = self.layout()
        self.warnings = main_config.are_warnings_enabled()
        self.vdu_controllers = []
        self.new_and_old_ids = []

        for vdu_id, manufacturer, vdu_model_name, vdu_serial in self.detected_vdus:
            controller = None
            while True:
                try:
                    controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, main_config,
                                               self.ddcutil)
                except Exception as e:
                    # Catch any kind of parse related error
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
                        controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, main_config,
                                                   self.ddcutil, ignore_monitor=True)
                        controller.write_template_config_files()
                        warn = MessageBox(QMessageBox.Information)
                        warn.setText(tr('Ignoring {} monitor.').format(vdu_model_name))
                        warn.setInformativeText(
                            tr('Wrote {} config files to {}.').format(vdu_model_name, CONFIG_DIR_PATH))
                        warn.exec()
                    if choice == QMessageBox.Apply:
                        controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, main_config,
                                                   self.ddcutil, assume_standard_controls=True)
                        controller.write_template_config_files()
                        warn = MessageBox(QMessageBox.Information)
                        warn.setText(
                            tr('Assuming {} has brightness and contrast controls.').format(vdu_model_name, CONFIG_DIR_PATH))
                        warn.setInformativeText(
                            tr('Wrote {} config files to {}.').format(vdu_model_name, CONFIG_DIR_PATH) +
                            tr('\nPlease check these files and edit or remove them if they '
                               'cause further issues.'))
                        warn.exec()
                    if choice == QMessageBox.Retry:
                        continue
                break
            if controller is not None:
                self.new_and_old_ids.append((controller.vdu_stable_id, controller.pre1_7_display_based_id))
                self.vdu_controllers.append(controller)
                self.vdu_detected.emit(controller)
                vdu_control_panel = VduControlPanel(controller, self.warnings)
                vdu_control_panel.connected_vdus_changed.connect(self.connected_vdus_changed)
                controller.vdu_setting_changed.connect(self.vdu_setting_changed)
                if vdu_control_panel.number_of_controls() != 0:
                    self.vdu_control_panels.append(vdu_control_panel)
                    controllers_layout.addWidget(vdu_control_panel)
                elif self.warnings:
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
            if self.warnings:
                error_no_monitors = MessageBox(QMessageBox.Critical)
                error_no_monitors.setText(tr('No controllable monitors found.'))
                extra_text = \
                    tr("(Most recent ddcutil error: {})").format(str(ddcutil_problem)) if ddcutil_problem else ''
                error_no_monitors.setInformativeText(
                    tr(
                        "Is ddcutil installed?  Is i2c installed and configured?\n\n"
                        "Run vdu_controls --debug in a console and check for "
                        "additional messages.\n\n{}").format(extra_text))
                error_no_monitors.exec()

        def finish_refresh() -> None:
            # GUI-thread QT signal handler for refresh task completion - execution will be in the GUI thread.
            # Stop the busy-spinner (progress bar).
            self.bottom_toolbar.indicate_refresh_complete()
            self.refresh_view()
            self.refresh_finished.emit()

        self.refreshDataTask = RefreshVduDataTask(self)
        self.refreshDataTask.task_finished.connect(finish_refresh)
        self.bottom_toolbar = \
            BottomToolBar(start_refresh_func=self.start_refresh, app_context_menu=app_context_menu, parent=self)
        layout.addWidget(self.bottom_toolbar)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        def open_context_menu(position: QPoint) -> None:
            self.context_menu.exec(self.mapToGlobal(position))

        self.customContextMenuRequested.connect(open_context_menu)

    def start_refresh(self) -> None:
        # Refreshes from all values from ddcutil.  May be slow, starts a busy spinner and then
        # starts the work in a task thread.
        self.bottom_toolbar.indicate_refresh_in_progress()
        # Start the background task
        self.refreshDataTask.start()

    def refresh_data(self) -> None:
        """Refresh data from the VDU's. Called by a non-GUI task. Not in the GUI-thread, cannot do any GUI op's."""
        self.detected_vdus = self.ddcutil.detect_monitors()
        for control_panel in self.vdu_control_panels:
            if control_panel.vdu_model.get_full_id() in self.detected_vdus:
                control_panel.refresh_data()

    def refresh_view(self) -> None:
        """Invoke when the GUI worker thread completes. Runs in the GUI thread and can refresh the GUI views."""
        if self.detected_vdus != self.previously_detected_vdus:
            self.connected_vdus_changed.emit()
            self.previously_detected_vdus = self.detected_vdus
        for control_panel in self.vdu_control_panels:
            control_panel.refresh_view()

    def is_non_standard_enabled(self) -> bool:
        if self.non_standard_enabled is None:
            self.non_standard_enabled = False
            path = get_config_path("danger")
            if path.exists():
                with open(path, 'r') as f:
                    text = f.read()
                    if text.strip() == DANGER_AGREEMENT_NON_STANDARD_VCP_CODES.strip():
                        log_warning("\n"
                                    "Non standard features may be enabled for write.\n"
                                    "ENABLING NON_STANDARD FEATURES COULD DAMAGE YOUR HARDWARE.\n"
                                    "To disable non-standard features delete the file {}.\n"
                                    "{}".format(path, DANGER_AGREEMENT_NON_STANDARD_VCP_CODES))
                        self.non_standard_enabled = True
        return self.non_standard_enabled

    def display_active_preset(self, preset: Preset | None):
        self.bottom_toolbar.display_active_preset(preset)


class RefreshVduDataTask(QThread):
    """
    Task to refresh VDU data from the physical VDU's.

    Runs as a task because it can be quite slow depending on the number of VDU's, number of controls.  The task runs
    outside the GUI thread and no parts of it can only update the GUI data, not the GUI view.
    """

    task_finished = pyqtSignal()

    def __init__(self, main_widget: VduControlsMainPanel) -> None:
        """Initialise the task that will run in a non-GUI thread to update all the widget's data."""
        super().__init__()
        self.main_widget = main_widget

    def run(self) -> None:
        """Run a task that uses ddcutil to retrieve data for all the visible controls (maybe slow)."""
        # Running in a task thread, cannot interact with GUI thread, just update the data.
        self.main_widget.refresh_data()
        # Tell (qt-signal) the GUI-thread that the task has finished, the GUI thread will then update the view widgets.
        self.task_finished.emit()


class PresetController:
    def __init__(self):
        self.presets = {}
        pass

    def find_presets(self) -> Mapping[str, Preset]:
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

    def which_preset_is_active(self, main_panel: VduControlsMainPanel) -> Preset | None:
        for name, preset in self.find_presets().items():
            if self.is_preset_active(preset, main_panel):
                return preset
        return None

    def is_preset_active(self, preset: Preset, main_panel: VduControlsMainPanel) -> bool:
        for section in preset.preset_ini:
            if section != 'vdu_controls':
                for control_panel in main_panel.vdu_control_panels:
                    if section == control_panel.vdu_model.vdu_stable_id:
                        if not control_panel.is_preset_active(preset.preset_ini):
                            return False
        return True

    def delete_preset(self, preset: Preset) -> None:
        preset.delete()
        del self.presets[preset.name]

    def get_preset(self, preset_number: int) -> Preset | None:
        presets = self.find_presets()
        if preset_number < len(presets):
            return list(presets.values())[preset_number]
        return None

    def convert_presets_v1_7(self, new_and_old_ids: List) -> List:
        problems = []
        for preset_name, preset in self.find_presets().items():
            problem_id = preset.convert_v1_7(new_and_old_ids)
            if problem_id:
                all_done = False
                problems.append((preset_name, problem_id))
        return problems


class MessageBox(QMessageBox):
    def __init__(self, icon: QIcon, buttons: int = QMessageBox.NoButton, default: int | None = None) -> None:
        super().__init__(icon, APPNAME, '', buttons=buttons)
        if default is not None:
            self.setDefaultButton(default)


class PushButtonLeftJustified(QPushButton):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.label = QLabel()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.layout().addWidget(self.label)
        # Not sure if this helps:
        self.setContentsMargins(0, 0, 0, 0)
        # Seems to fix top/bottom clipping on openbox and xfce:
        layout.setContentsMargins(0, 0, 0, 0)

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

        line_layout.addSpacing(10)
        timer_control_button = PushButtonLeftJustified(parent=self)
        timer_control_button.setFlat(True)

        action_desc = {
            'scheduled': tr("Press to skip {}"), 'suspended': tr("Press to re-enable {}"),
            'past': tr("Scheduled {}"), 'unscheduled': tr("Not applicable {}")}

        if preset.get_solar_elevation() is not None:
            def format_description():
                return action_desc[preset.get_timer_status()].format(preset.get_solar_elevation_description())

            def toggle_timer(arg):
                preset.toggle_timer()
                timer_control_button.setText(preset.get_solar_elevation_abbreviation())
                timer_control_button.setToolTip(format_description())

            timer_control_button.setText(preset.get_solar_elevation_abbreviation())
            status = preset.get_timer_status()
            timer_control_button.setToolTip(format_description())
            timer_control_button.mousePressEvent = toggle_timer
        if preset.get_timer_status() in ('past', 'unscheduled'):
            timer_control_button.setDisabled(True)
        # auto_label.setDisabled(True)
        line_layout.addWidget(timer_control_button)


class PresetActivationButton(QPushButton):
    def __init__(self, preset: Preset):
        super().__init__()
        self.preset = preset
        self.setIcon(preset.create_icon())
        self.setText(preset.name)
        self.setToolTip(tr("Activate this preset"))

    def event(self, event: QEvent) -> bool:
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.setIcon(self.preset.create_icon())
        event.accept()
        return True


class PresetChooseIconButton(QPushButton):

    def __init__(self):
        super().__init__()
        self.setIcon(si(self, PresetsDialog.no_icon_icon_number))
        self.setToolTip(tr('Choose a preset icon.'))
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.setAutoDefault(False)
        self.last_selected_icon_path = None
        self.last_icon_dir = Path("/usr/share/icons")
        if not self.last_icon_dir.exists():
            self.last_icon_dir = Path.home()
        self.preset = None
        self.clicked.connect(self.choose_preset_icon_action)

    def set_preset(self, preset: Preset | None):
        self.preset = preset
        self.last_selected_icon_path = self.preset.get_icon_path() if preset else None
        if self.last_selected_icon_path:
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
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.update_icon()
        event.accept()
        return True


class QueryWeather:

    def __init__(self, location_name: str):
        lang = locale.getlocale()[0][:2]
        if location_name is None or location_name.strip() == '':
            location_name = ''
        wttr_url = os.getenv('VDU_CONTROLS_WTTR_URL', default='https://wttr.in')
        self.url = f"{wttr_url}/{location_name}?" + urllib.parse.urlencode({'lang': lang, 'format': 'j1'})
        self.weather_data = None
        try:
            with urllib.request.urlopen(self.url) as request:
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
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(tr("Unknown location {}".format(location_name)),
                                 tr("Please check Location in Settings"))
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(e))
        except URLError as ue:
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(ue))

    def __str__(self):
        if self.weather_data is None:
            return ""
        return f"{self.area_name}, {self.country_name}, {self.weather_desc} ({self.weather_code})," \
               f"cloud_cover {self.cloud_cover}, visibility {self.visibility}, " \
               f"location={self.latitude},{self.longitude}"


class PresetChooseWeatherWidget(QWidget):

    def __init__(self, location_func: Callable):
        super().__init__()
        self.init_weather()
        self.required_weather_filepath: Path | None = None
        self.setLayout(QVBoxLayout())
        self.label = QLabel(tr("Additional weather requirements"))
        self.label.setToolTip(
            tr("Weather conditions will be retrieved from https://wttr.in"))
        self.layout().addWidget(self.label)
        self.chooser = QComboBox()
        self.warned: GeoLocation | None = None

        def select_action(index: int):
            self.required_weather_filepath = self.chooser.itemData(index)
            if self.chooser.itemData(index) is None:
                self.info_label.setText('')
            else:
                self.validate_weather_location(location_func)
                path = self.chooser.itemData(index)
                if path.exists():
                    with open(path) as weather_file:
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
        # self.layout().addStretch(1)

    def init_weather(self):
        if len(list(CONFIG_DIR_PATH.glob("*.weather"))) == 0:
            log_info(f"making good, bad and all weather in {CONFIG_DIR_PATH}")
            with open(CONFIG_DIR_PATH.joinpath('good.weather'), 'w') as weather_file:
                weather_file.write("113 Sunny\n116 Partly Cloudy\n119 Cloudy\n")
            with open(CONFIG_DIR_PATH.joinpath('bad.weather'), 'w') as weather_file:
                weather_file.write(
                    "143 Fog\n179 Light Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 "
                    "Light Snow\n230 Heavy Snow\n248 Fog\n260 Fog\n266 Light Rain\n281 Light Sleet\n284 Light "
                    "Sleet\n293 Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 "
                    "Heavy Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
                    "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
                    "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
                    "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
                    "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
                    "Thundery Snow Showers\n395 HeavySnowShowers\n "
                )
            with open(CONFIG_DIR_PATH.joinpath('all.weather'), 'w') as weather_file:
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

    def validate_weather_location(self, location_func: Callable):
        if self.warned == location_func():
            return
        log_info("Validating weather location.")
        location = location_func()
        try:
            weather = QueryWeather(location.place_name)
            kilometres = calc_kilometers(float(weather.latitude), float(weather.longitude),
                                         location.latitude, location.longitude)
            if kilometres > 200:
                use_km = QLocale.system().measurementSystem() == QLocale.MetricSystem
                msg = MessageBox(QMessageBox.Warning)
                msg.setText(
                    tr("The site https://wttr.in reports your location as {}, {}, {},{} "
                       "which is about {} {} from the latitude and longitude specified in Settings."
                       ).format(weather.area_name, weather.country_name, weather.latitude, weather.longitude,
                                round(kilometres if use_km else kilometres * 0.621371), 'km' if use_km else 'miles'))
                msg.setInformativeText("Please check the location specified in Settings.")
                msg.setDetailedText(f"{weather}")
                msg.exec()
            self.warned = location
        except ValueError as e:
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
        return self.required_weather_filepath.as_posix() if self.required_weather_filepath is not None else None

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


class PresetChooseElevationWidget(QWidget):
    # def create_trigger_widget(self, base_ini: ConfigIni) -> QWidget:
    #
    def __init__(self, location_func: Callable):
        super().__init__()
        self.elevation_key = None
        self.elevation_time_map: Dict[SolarElevationKey, SolarElevationData] = None
        self.location: GeoLocation | None = None
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.default_title = tr("Solar elevation trigger: ")
        slider = QSlider(Qt.Horizontal)
        self.slider = slider
        self.slider.setTracking(True)
        self.slider.setMinimum(-1)
        self.slider.setValue(-1)
        self.slider = self.slider
        self.elevation_steps = []
        self.title_label = QLabel(self.default_title)
        layout.addWidget(self.title_label)
        layout.addWidget(self.slider)
        self.plot = QLabel()
        self.plot.setFixedHeight(200)
        self.plot.setFixedWidth(400)
        layout.addSpacing(16)
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addWidget(self.plot)
        layout.addLayout(self.bottom_layout)
        self.weather_widget = PresetChooseWeatherWidget(location_func)
        self.bottom_layout.addWidget(self.weather_widget)
        self.configure_for_location(location_func())
        self.slider.valueChanged.connect(self.sliding)
        self.sun_image = None

    def sliding(self):
        if self.slider.value() == -1:
            self.title_label.setText(self.default_title)
            self.elevation_key = None
            self.weather_widget.chooser.setCurrentIndex(0)
            self.weather_widget.setEnabled(False)
            return
        self.weather_widget.setEnabled(True)
        self.elevation_key = self.elevation_steps[self.slider.value()]
        elevation_data = self.elevation_time_map[
            self.elevation_key] if self.elevation_key in self.elevation_time_map else None
        occurs_at = elevation_data.when if elevation_data is not None else None
        if occurs_at:
            when_text = tr("today at {}").format(occurs_at.strftime('%H:%M'))
        else:
            when_text = tr("the sun does not rise this high today")
        # https://en.wikipedia.org/wiki/Twilight
        if self.elevation_key.elevation < 1:
            if self.elevation_key.elevation >= -6:
                if self.elevation_key.direction == EASTERN_SKY:
                    when_text += " " + tr("dawn")
                else:
                    when_text += " " + tr("dusk")
            elif self.elevation_key.elevation >= -18:
                # Astronomical twilight
                when_text += " " + tr("twilight")
            else:
                when_text += " " + tr("nighttime")
        display_text = tr("{} {} ({}, {})").format(
            self.default_title,
            format_solar_elevation_abbreviation(self.elevation_key),
            tr(self.elevation_key.direction),
            when_text)
        if display_text != self.title_label.text():
            self.title_label.setText(display_text)
        self.create_plot(self.elevation_key)

    def configure_for_location(self, location: GeoLocation | None):
        self.location = location
        if location is None:
            self.title_label.setText(self.default_title + tr("location undefined (see settings)"))
            self.slider.setDisabled(True)
            return
        self.slider.setEnabled(True)
        self.elevation_time_map = create_todays_elevation_time_map(latitude=location.latitude,
                                                                   longitude=location.longitude)
        self.elevation_steps = []
        for i in range(-19, 90):
            self.elevation_steps.append(SolarElevationKey(EASTERN_SKY, i))
        for i in range(90, -20, -1):
            self.elevation_steps.append(SolarElevationKey(WESTERN_SKY, i))
        self.slider.setMaximum(len(self.elevation_steps) - 1)
        self.slider.setValue(-1)
        self.sliding()
        self.create_plot(None)

    def create_plot(self, ev_key: SolarElevationKey | None):
        width, height, plot_height = self.plot.width(), self.plot.height(), 2 * self.plot.height() // 3
        origin_iy, range_iy = height // 2, self.plot.height() // 3
        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)

        def reverse_x(x_val: int) -> int:
            return width - x_val

        painter.fillRect(0, 0, width, origin_iy, QColor(0x5b93c5))
        painter.fillRect(0, origin_iy, width, height, QColor(0x7d5233))
        painter.setPen(QPen(QColor(0xffffff), 6))
        painter.drawLine(0, origin_iy, width, origin_iy)
        painter.setPen(QPen(QColor(0xff965b), 6))

        today = zoned_now().replace(hour=0, minute=0)
        sun_plot_x, sun_plot_y, sun_plot_time = None, None, None
        max_y = -90.0
        solar_noon_plot_x, solar_noon_plot_y = 0, 0  # Solar noon
        t = today
        while t.day == today.day:
            a, z = calc_solar_azimuth_zenith(t, self.location.latitude, self.location.longitude)
            x, y = ((t - today).total_seconds() / 60.0), math.sin(math.radians(90.0 - z)) * range_iy
            plot_x, plot_y = round(width * x / (60.0 * 24.0)), origin_iy - round(y)
            painter.drawPoint(reverse_x(plot_x), plot_y)
            if y > max_y:
                max_y = y
                solar_noon_plot_x, solar_noon_plot_y = plot_x, plot_y
            if sun_plot_time is None and ev_key and round(90.0 - z) == ev_key.elevation:
                if (ev_key.direction == EASTERN_SKY and round(a) <= 180) or (
                        ev_key.direction == WESTERN_SKY and round(a) >= 180):
                    sun_plot_x, sun_plot_y = plot_x, plot_y
                    sun_plot_time = t
            t += timedelta(minutes=1)
        if sun_plot_x is None:
            sun_plot_x, sun_plot_y = solar_noon_plot_x, solar_noon_plot_y

        painter.setPen(QPen(QColor(0xffffff), 6))
        painter.drawLine(reverse_x(0), origin_iy, reverse_x(width), origin_iy)
        painter.drawLine(reverse_x(solar_noon_plot_x), origin_iy, reverse_x(solar_noon_plot_x), 0)
        if ev_key:
            key_iy = origin_iy - round(math.sin(math.radians(ev_key.elevation)) * range_iy)
            painter.setPen(QPen(QColor(0xffffff if key_iy >= solar_noon_plot_y else 0xcccccc), 6))
            if ev_key.direction == EASTERN_SKY:
                painter.drawLine(reverse_x(0), key_iy, reverse_x(solar_noon_plot_x), key_iy)
            else:
                painter.drawLine(reverse_x(solar_noon_plot_x), key_iy, reverse_x(width), key_iy)

        painter.setPen(QPen(QColor(0xffffff), 6))
        painter.setFont(QFont(QApplication.font().family(), width // 20, QFont.Weight.Bold))
        painter.drawText(reverse_x(solar_noon_plot_x - 150), origin_iy - 20, tr("E"))
        painter.drawText(reverse_x(solar_noon_plot_x + 150), origin_iy - 20, tr("W"))
        time_text = sun_plot_time.strftime("%H:%M") if sun_plot_time else "____"
        painter.drawText(reverse_x(solar_noon_plot_x + width // 4), origin_iy + height // 4,
                         f"{ev_key.elevation if ev_key else 0:3d}\u00B0 {time_text}")
        painter.setPen(QPen(QColor(0xff965b), 2));
        painter.setBrush(QColor(0xff965b))
        painter.drawEllipse(reverse_x(solar_noon_plot_x + 8), origin_iy - 8, 16, 16)
        if ev_key:
            painter.setPen(QPen(QColor(0xff4a23), 6))
            if self.sun_image is None:
                self.sun_image = create_image_from_svg_bytes(BRIGHTNESS_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#ffdd30"))
            painter.drawImage(QPoint(reverse_x(sun_plot_x) - self.sun_image.width() // 2,
                                     sun_plot_y - self.sun_image.height() // 2), self.sun_image)
        painter.end()
        self.plot.setPixmap(pixmap)

    def set_elevation(self, elevation_text: str):
        if elevation_text and len(self.elevation_steps) != 0:
            self.elevation_key = parse_solar_elevation_ini_text(elevation_text)
            if self.elevation_key in self.elevation_steps:
                self.slider.setValue(self.elevation_steps.index(self.elevation_key))
                self.weather_widget.setEnabled(True)
                return
        self.slider.setValue(-1)
        self.weather_widget.setEnabled(False)
        self.weather_widget.chooser.setCurrentIndex(0)

    def get_required_weather_filename(self) -> str | None:
        return self.weather_widget.get_required_weather_filepath()

    def set_required_weather_filename(self, weather_filename: str | None):
        self.weather_widget.set_required_weather_filepath(weather_filename)


class PresetsDialog(QDialog, DialogSingletonMixin):
    """A dialog for creating/updating/removing presets."""
    # TODO has become rather complex - break into parts?

    no_icon_icon_number = QStyle.SP_ComputerIcon

    edit_save_needed = pyqtSignal()

    @staticmethod
    def invoke(main_window: 'MainWindow', main_config: VduControlsConfig) -> None:
        if PresetsDialog.exists():
            PresetsDialog.show_existing_dialog()
        else:
            PresetsDialog(main_window, main_config)

    def __init__(self, main_window: 'MainWindow', main_config: VduControlsConfig) -> None:
        super().__init__()
        self.setWindowTitle(tr('Presets'))
        self.main_window = main_window
        self.main_config = main_config
        self.content_controls = {}
        self.resize(1600, 800)
        self.setMinimumWidth(1280)
        self.setMinimumHeight(800)
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

        self.edit_save_button = QPushButton()  # translate('Add'))  # QPushButton(' \u2003')
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
        self.editor_groupbox.setMinimumWidth(500)
        self.editor_layout = QVBoxLayout()
        self.editor_title = QLabel(tr("New Preset:"))
        self.editor_title.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.editor_layout.addWidget(self.editor_title)
        self.editor_groupbox.setLayout(self.editor_layout)
        self.editor_controls_widget = self.create_preset_content_controls()
        self.editor_layout.addWidget(self.edit_preset_widget)
        self.editor_controls_prompt = QLabel(tr("Controls to include:"))
        self.editor_controls_prompt.setDisabled(True)
        self.editor_layout.addWidget(self.editor_controls_prompt)
        self.editor_layout.addWidget(self.editor_controls_widget)
        self.editor_trigger_widget = PresetChooseElevationWidget(self.main_config.get_location)
        self.editor_layout.addWidget(self.editor_trigger_widget)
        presets_dialog_splitter.addWidget(self.editor_groupbox)

        self.close_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr('close'))
        self.close_button.clicked.connect(self.close)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.close_button, 0, Qt.AlignRight | Qt.AlignBottom)

        self.edit_choose_icon_button.set_preset(None)
        self.editor_controls_widget.setDisabled(True)
        self.editor_trigger_widget.setDisabled(True)
        self.edit_save_button.setDisabled(True)
        layout.addWidget(button_box)
        self.make_visible()

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
                option_control.setChecked(
                    True)  # preset.preset_ini.has_option(section, option) if preset else True)
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
        elevation_ini_text = create_solar_elevation_ini_text(self.editor_trigger_widget.elevation_key)
        if elevation_ini_text is not None:
            if not preset_ini.has_section('preset'):
                preset_ini.add_section('preset')
            preset_ini.set('preset', 'solar-elevation', elevation_ini_text)
            weather_filename = self.editor_trigger_widget.get_required_weather_filename()
            if weather_filename is not None:
                preset_ini.set('preset', 'solar-elevation-weather-restriction', weather_filename)

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
            self.main_window.display_active_preset(None)
            self.preset_widgets_scrollarea.updateGeometry()

    def down_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index < self.preset_widgets_layout.count() - 2:
            self.preset_widgets_layout.removeWidget(target_widget)
            new_preset_widget = self.create_preset_widget(preset)
            self.preset_widgets_layout.insertWidget(index + 1, new_preset_widget)
            target_widget.deleteLater()
            self.main_window.preset_controller.save_order(self.get_presets_name_order())
            self.main_window.display_active_preset(None)
            self.preset_widgets_scrollarea.updateGeometry()

    def restore_preset(self, preset: Preset) -> None:
        self.main_window.restore_preset(preset)
        self.preset_name_edit.setText('')

    def save_preset(self, preset: Preset) -> None:
        preset_path = get_config_path(proper_name('Preset', preset.name))
        if preset_path.exists():
            confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | QMessageBox.Cancel, default=QMessageBox.Save)
            message = tr('Update existing {} preset with current monitor settings?').format(preset.name)
            confirmation.setText(message)
            if confirmation.exec() == QMessageBox.Cancel:
                return
        self.preset_name_edit.setText('')
        self.main_window.save_preset(preset)

    def delete_preset(self, preset: Preset, target_widget: QWidget = None) -> None:
        confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Ok | QMessageBox.Cancel, default=QMessageBox.Cancel)
        confirmation.setText(tr('Delete {}?').format(preset.name))
        rc = confirmation.exec()
        if rc == QMessageBox.Cancel:
            return
        self.main_window.delete_preset(preset)
        self.preset_widgets_layout.removeWidget(target_widget)
        target_widget.deleteLater()
        self.main_window.preset_controller.save_order(self.get_presets_name_order())
        self.preset_name_edit.setText('')
        self.preset_widgets_scrollarea.updateGeometry()

    def change_edit_group_title(self):
        changed_text = self.preset_name_edit.text()
        if changed_text.strip() == "":
            # choose_icon_button.set_preset(None)
            self.editor_controls_widget.setDisabled(True)
            self.editor_trigger_widget.setDisabled(True)
            self.edit_save_button.setDisabled(True)
            self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include:"))
            self.editor_controls_prompt.setDisabled(True)
        else:
            already_exists = self.find_preset_widget(changed_text)
            if already_exists:
                self.editor_title.setText(tr("Edit {}:").format(changed_text))
            else:
                self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include in {}:").format(changed_text))
            self.editor_controls_prompt.setDisabled(False)
            self.editor_controls_widget.setDisabled(False)
            self.editor_trigger_widget.setDisabled(False)
            self.edit_save_button.setDisabled(False)

    def edit_preset(self, preset: Preset) -> None:
        self.main_window.restore_preset(preset)
        self.preset_name_edit.setText(preset.name)
        self.edit_choose_icon_button.set_preset(preset)
        for key, item in self.content_controls.items():
            item.setChecked(preset.preset_ini.has_option(key[0], key[1]))
        if preset.preset_ini.has_section('preset'):
            self.editor_trigger_widget.set_elevation(
                preset.preset_ini.get('preset', 'solar-elevation', fallback=None))
            self.editor_trigger_widget.set_required_weather_filename(
                preset.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None))

    def save_edited_preset(self) -> None:
        preset_name = self.preset_name_edit.text().strip()
        if preset_name == '':
            return
        existing_preset_widget: PresetWidget | None = self.find_preset_widget(preset_name)
        if existing_preset_widget:
            confirmation = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | QMessageBox.Cancel, default=QMessageBox.Save)
            confirmation.setText(tr("Replace existing '{}' preset?").format(preset_name))
            if confirmation.exec() == QMessageBox.Cancel:
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
        self.main_window.display_active_preset(None)

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
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.repaint()
        return True

    def closeEvent(self, event) -> None:
        if self.preset_name_edit.text().strip() != '':
            alert = MessageBox(QMessageBox.Question, buttons=QMessageBox.Save | QMessageBox.Ignore | QMessageBox.Cancel,
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
        super().closeEvent(event)


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


def create_pixmap_from_svg_bytes(svg_bytes: bytes):
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    image = create_image_from_svg_bytes(svg_bytes)
    return QPixmap.fromImage(image)


def create_image_from_svg_bytes(svg_bytes):
    renderer = QSvgRenderer(handle_theme(svg_bytes))
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def create_icon_from_svg_bytes(svg_bytes: bytes) -> QIcon:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    return QIcon(create_pixmap_from_svg_bytes(svg_bytes))


def create_icon_from_path(path: Path) -> QIcon | None:
    if path.exists():
        if path.suffix == '.svg':
            with open(path, 'rb') as icon_file:
                icon_bytes = icon_file.read()
                return create_icon_from_svg_bytes(icon_bytes)
        if path.suffix == '.png':
            return QIcon(path.as_posix())
    else:
        # Copes with the case where the path has been deleted.
        return QApplication.style().standardIcon(QStyle.SP_MessageBoxQuestion)
    return None


def create_icon_from_text(text: str) -> QIcon:
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
        log_info(f"removed {installed_script_path.as_posix()}")
        os.remove(desktop_definition_path)
        log_info(f"removed {desktop_definition_path.as_posix()}")
        os.remove(icon_path)
        log_info(f"removed {icon_path.as_posix()}")
        return

    if installed_script_path.exists():
        log_warning(f"skipping installation of {installed_script_path.as_posix()}, it is already present.")
    else:
        source = open(__file__).read()
        source = source.replace("#!/usr/bin/python3", '#!' + sys.executable)
        log_info(f"creating {installed_script_path.as_posix()}")
        open(installed_script_path, 'w').write(source)
        log_info(f"chmod u+rwx {installed_script_path.as_posix()}")
        os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        log_warning(f"skipping installation of {desktop_definition_path.as_posix()}, it is already present.")
    else:
        log_info(f"creating {desktop_definition_path.as_posix()}")
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
        log_info(f"creating {icon_path.as_posix()}")
        get_splash_image().save(icon_path.as_posix())

    log_info('INFO: installation complete. Your desktop->applications->settings should now contain VDU Controls')


class GreyScaleDialog(QDialog):
    """Creates a dialog with a grey scale VDU calibration image.  Non-model. Have as many as you like - one per VDU."""

    # This stops garbage collection of independent instances of this dialog until the user closes them.
    # If you don't do this the dialog will disappear before it becomes visible.  Could also pass a parent
    # which would achieve the same thing - but would alter where the dialog appears.
    _active_list = []

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


# TODO consider changing to a non-modal QDialog which would also remove the need for a multiple inheritance
class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def invoke():
        if AboutDialog.exists():
            AboutDialog.show_existing_dialog()
        else:
            AboutDialog()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('About'))
        self.setTextFormat(Qt.AutoText)
        self.setText(tr('About vdu_controls'))
        path = find_locale_specific_file("about_{}.txt")
        if path:
            with open(path, encoding='utf-8') as about_for_locale:
                about_text = about_for_locale.read().format(VDU_CONTROLS_VERSION=VDU_CONTROLS_VERSION)
        else:
            about_text = ABOUT_TEXT
        self.setInformativeText(about_text)
        self.setIcon(QMessageBox.Information)
        self.exec()


class HelpDialog(QDialog, DialogSingletonMixin):

    @staticmethod
    def invoke():
        if HelpDialog.exists():
            HelpDialog.show_existing_dialog()
        else:
            HelpDialog()

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
        # TODO maybe compute a minimum from the actual screen size
        self.setMinimumWidth(1600)
        self.setMinimumHeight(1024)
        # .show() is non-modal, .exec() is modal
        self.make_visible()


class MainWindow(QMainWindow):

    def __init__(self, main_config: VduControlsConfig, app: QApplication, session_startup: bool):
        super().__init__()

        global current_desktop
        self.app = app
        self.displayed_preset_name = None
        self.setObjectName('main_window')
        self.geometry_key = self.objectName() + "_geometry"
        self.state_key = self.objectName() + "_window_state"
        self.settings = QSettings('vdu_controls.qt.state', 'vdu_controls')
        self.main_control_panel = None
        self.main_config = main_config
        self.daily_schedule_next_update = datetime.today()

        current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')

        gnome_tray_behaviour = main_config.is_system_tray_enabled() and 'gnome' in current_desktop.lower()

        if gnome_tray_behaviour:
            # Gnome tray doesn't normally provide a way to bring up the main app.
            def main_window_action() -> None:
                self.show()
                self.raise_()
                self.activateWindow()
        else:
            main_window_action = None

        def settings_changed(changed_settings: List):
            if ('vdu-controls-globals', 'system-tray-enabled') in changed_settings:
                restart_application(tr("The change to the system-tray-enabled option requires "
                                       "vdu_controls to restart."))
            if ('vdu-controls-globals', 'translations-enabled') in changed_settings:
                restart_application(tr("The change to the translations-enabled option requires "
                                       "vdu_controls to restart."))
            main_config.reload()
            self.main_control_panel.ddcutil.change_settings(
                debug=main_config.is_debug_enabled(), default_sleep_multiplier=main_config.get_sleep_multiplier())
            create_main_control_panel()
            self.schedule_presets(reset=True)
            presets_dialog = PresetsDialog.get_instance()
            if presets_dialog:
                presets_dialog.reload_data()

        def edit_config() -> None:
            SettingsEditor.invoke(main_config, [vdu.config for vdu in self.main_control_panel.vdu_controllers],
                                  settings_changed)

        def refresh_from_vdus() -> None:
            create_main_control_panel()
            self.main_control_panel.start_refresh()

        def grey_scale() -> None:
            GreyScaleDialog()

        def edit_presets() -> None:
            PresetsDialog.invoke(self, main_config)

        def quit_app() -> None:
            self.app_save_state()
            app.quit()

        for screen in app.screens():
            log_info("Screen", screen.name())

        # Not that useful - doesn't necessarily change if a screen is powered off
        # def screen_changed(screen):
        #     log_info("Screen changed:", screen.name)
        #     settings_changed([])
        # app.screenAdded.connect(screen_changed)
        # app.screenRemoved.connect(screen_changed)

        self.preset_controller = PresetController()

        self.app_context_menu = ContextMenu(main_window=self,
                                            main_window_action=main_window_action,
                                            about_action=AboutDialog.invoke,
                                            help_action=HelpDialog.invoke,
                                            chart_action=grey_scale,
                                            settings_action=edit_config,
                                            presets_action=edit_presets,
                                            refresh_action=refresh_from_vdus,
                                            quit_action=quit_app)

        splash_pixmap = get_splash_image()
        splash = QSplashScreen(splash_pixmap.scaledToWidth(800).scaledToHeight(400),
                               Qt.WindowStaysOnTopHint) if main_config.is_splash_screen_enabled() else None

        if splash is not None:
            splash.show()
            # Attempt to force it to the top with raise and activate
            splash.raise_()
            splash.activateWindow()
        self.app_icon = QIcon()
        self.app_icon.addPixmap(splash_pixmap)

        self.tray = None
        if main_config.is_system_tray_enabled():
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log_warning("no system tray, waiting to see if one becomes available.")
                for i in range(0, SYSTEM_TRAY_WAIT_SECONDS):
                    if QSystemTrayIcon.isSystemTrayAvailable():
                        break
                    time.sleep(1)
            if QSystemTrayIcon.isSystemTrayAvailable():
                log_info("using system tray.")
                # This next call appears to be automatic on KDE, but not on gnome.
                app.setQuitOnLastWindowClosed(False)
                self.tray = QSystemTrayIcon()
                # icon = create_merged_icon(app_icon, create_icon_from_svg_string(MENU_ICON_SOURCE))
                self.tray.setIcon(self.app_icon)
                self.tray.setContextMenu(self.app_context_menu)
            else:
                log_error("no system tray - cannot run in system tray.")

        app.setWindowIcon(self.app_icon)
        self.app_name = "VDU Controls"
        app.setApplicationDisplayName(self.app_name)
        # Make sure all icons use HiDPI - toolbars don't by default, so force it.
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)

        if splash is not None:
            splash.showMessage(tr('\n\nVDU Controls\nLooking for DDC monitors...\n'),
                               Qt.AlignTop | Qt.AlignHCenter)

        def vdu_detected_action(vdu: VduController) -> None:
            if splash is not None:
                splash.showMessage(
                    tr('\n\nVDU Controls {}\nDDC ID {}\n{}').format(VDU_CONTROLS_VERSION,
                                                                    vdu.vdu_id, vdu.get_vdu_description()),
                    Qt.AlignTop | Qt.AlignHCenter)

        def vdu_settings_changed_action() -> None:
            self.display_active_preset(None)

        def respond_to_unix_signal(signal_number: int):
            if signal_number == signal.SIGHUP:
                self.main_control_panel.refresh_data()
            elif PRESET_SIGNAL_MIN <= signal_number <= PRESET_SIGNAL_MAX:
                restore_preset = self.preset_controller.get_preset(signal_number - PRESET_SIGNAL_MIN)
                if restore_preset is not None:
                    self.restore_preset(restore_preset)
                else:
                    # Cannot raise a Qt alert inside the signal handler in case another signal comes in.
                    log_warning(f"ignoring signal {signal_number}, no preset associated with that signal number.")

        global signal_wakeup_handler
        signal_wakeup_handler.signalReceived.connect(respond_to_unix_signal)

        def refresh_finished():
            self.display_active_preset(None)

        def create_main_control_panel():
            # Call on initialisation and whenever the number of connected VDU's changes.
            global log_to_syslog
            log_to_syslog = main_config.is_syslog_enabled()
            existing_width = 0
            if self.main_control_panel:
                # Remove any existing control panel - which may now be incorrect for the config.
                self.main_control_panel.width()
                self.main_control_panel.refresh_finished.disconnect(refresh_finished)
                self.main_control_panel.vdu_detected.disconnect(vdu_detected_action)
                self.main_control_panel.vdu_setting_changed.disconnect(vdu_settings_changed_action)
                self.main_control_panel.connected_vdus_changed.disconnect(create_main_control_panel)
                self.main_control_panel.deleteLater()
            self.main_control_panel = VduControlsMainPanel()
            # Write up the signal/slots first
            self.main_control_panel.refresh_finished.connect(refresh_finished)
            self.main_control_panel.vdu_detected.connect(vdu_detected_action)
            self.main_control_panel.vdu_setting_changed.connect(vdu_settings_changed_action)
            self.main_control_panel.connected_vdus_changed.connect(create_main_control_panel)
            # Then initialise the control panel display
            self.main_control_panel.initialise_control_panels(self.app_context_menu, main_config, session_startup)
            self.setCentralWidget(self.main_control_panel)
            self.setMinimumWidth(existing_width)
            self.display_active_preset(None)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        create_main_control_panel()

        self.app_restore_state()

        if self.tray is not None:
            def show_window():
                if self.isVisible():
                    self.hide()
                else:
                    if len(self.settings.allKeys()) == 0:
                        # No previous state - guess a position near the tray.
                        # Use the mouse pos as a guess to where the system tray is.  The Linux Qt x,y geometry returned by
                        # the tray icon is 0,0, so we can't use that.
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
            log_info(f"Restoring preset {overdue.name} "
                     f"because its scheduled to be active at this time ({zoned_now()}).")
            self.activate_scheduled_preset(overdue)

        if splash is not None:
            splash.finish(self)

        if not main_config.ini_content.is_version_ge(1, 7, 0):
            release_alert = MessageBox(QMessageBox.Information, buttons=QMessageBox.Close)
            release_alert.setText(RELEASE_ANNOUNCEMENT)
            release_alert.setTextFormat(Qt.RichText)
            release_alert.exec()
            if main_config.file_path:
                log_info(f"Converting {main_config.file_path} to version {VDU_CONTROLS_VERSION}")
                main_config.ini_content.save(main_config.file_path, backup_dir_name='pre-v1.7')
            else:
                # Stops the release notes from being repeated.
                main_config.write_file(get_config_path('vdu_controls'))

        # This cannot be completed until all the monitors in each preset are online
        failed_conversion = self.preset_controller.convert_presets_v1_7(self.main_control_panel.new_and_old_ids)
        if len(failed_conversion) != 0:
            log_warning("Not all presets were converted, a monitor that is normally present is probably turned off.")
            cvt_alert = MessageBox(QMessageBox.Warning)
            cvt_alert.setText(tr("Temporarily unable to migrate some presets to {}:\n{}").format(
                VDU_CONTROLS_VERSION,
                '\n'.join(f"   {p} - {v}" for p, v in failed_conversion)))
            cvt_alert.setInformativeText("A monitor that is normally present is probably turned off."
                                         " Old Presets will probably not function for the referenced monitor.\n\n"
                                         "The conversion will be attempted again when next restarted"
                                         " (suggest turning on all monitors before the next restart).")
            cvt_alert.exec()

    def restore_preset(self, preset: Preset) -> Preset:
        log_info(f"Preset changing to {preset.name}")
        preset.load()
        restored_list = []
        for section in preset.preset_ini:
            for control_panel in self.main_control_panel.vdu_control_panels:
                if section == control_panel.vdu_model.vdu_stable_id:
                    control_panel.restore_vdu_state(preset.preset_ini)
                    restored_list.append(control_panel)
        # Cope with mixed pre-post v1.7 in a preset file,
        # if not already restored from post v1.7 section, use pre v1.7 section
        for section in preset.preset_ini:
            for control_panel in self.main_control_panel.vdu_control_panels:
                if control_panel not in restored_list and section == control_panel.vdu_model.pre1_7_display_based_id:
                    control_panel.restore_vdu_state_pre17(preset.preset_ini)
        self.display_active_preset(preset)
        return preset

    def restore_named_preset(self, preset_name: str):
        presets = self.preset_controller.find_presets()
        if preset_name in presets:
            preset = presets[preset_name]
            self.restore_preset(preset)
            return preset

    def save_preset(self, preset: Preset) -> None:
        id_list = self.copy_to_preset_ini(preset.preset_ini, update_only=True)
        ##preset.convert_v1_7_check(id_list)
        self.preset_controller.save_preset(preset)
        if not self.app_context_menu.has_preset_menu_item(preset.name):
            self.app_context_menu.insert_preset_menu_item(preset)
            self.display_active_preset(preset)
        preset.remove_elevation_trigger()
        self.schedule_presets()

    def copy_to_preset_ini(self, preset_ini: ConfigIni, update_only: bool = False) -> List:
        id_list = []
        for control_panel in self.main_control_panel.vdu_control_panels:
            control_panel.copy_state(preset_ini, update_only)
            id_list.append((control_panel.vdu_model.vdu_stable_id, control_panel.vdu_model.pre1_7_display_based_id))
        return id_list

    def delete_preset(self, preset: Preset) -> None:
        self.preset_controller.delete_preset(preset)
        if self.app_context_menu.has_preset_menu_item(preset.name):
            self.app_context_menu.remove_preset_menu_item(preset)
        if self.displayed_preset_name == preset.name:
            self.display_active_preset(None)

    def display_active_preset(self, preset: Preset | None) -> None:
        if preset is None:
            preset = self.preset_controller.which_preset_is_active(self.main_control_panel)
        if preset:
            self.setWindowTitle(preset.name)
            icon = create_merged_icon(self.app_icon, preset.create_icon())
            self.app.setWindowIcon(icon)
            self.main_control_panel.display_active_preset(preset)
            if self.tray:
                self.tray.setToolTip(f"{preset.name} \u2014 {self.app_name}")
                self.tray.setIcon(icon)
        else:
            self.setWindowTitle("")
            self.setWindowIcon(self.app_icon)
            self.main_control_panel.display_active_preset(preset)
            if self.tray:
                self.tray.setToolTip(f"{self.app_name}")
                self.tray.setIcon(self.app_icon)
        self.displayed_preset_name = preset.name if preset else None
        self.app_context_menu.refresh_preset_menu(reload=True)

    def closeEvent(self, event):
        if self.tray is not None:
            self.hide()
            event.ignore()  # hide the window
        else:
            self.app_save_state()
            event.accept()  # let the window close

    def create_config_files(self):
        for vdu_model in self.main_control_panel.vdu_controllers:
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
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.display_active_preset(None)
            self.app_context_menu.refresh_preset_menu(reload=True)
        event.accept()
        return True

    def schedule_presets(self, reset: bool = False) -> Preset:
        location = self.main_config.get_location()
        if location is None:
            return
        log_info(f"Scheduling presets reset={reset}")
        time_map = create_todays_elevation_time_map(latitude=location.latitude, longitude=location.longitude)
        most_recent_overdue = None
        latest_due = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0)
        for name, preset in self.preset_controller.find_presets().items():
            if reset:
                preset.remove_elevation_trigger()
            elevation_key = preset.get_solar_elevation()
            if elevation_key is not None and preset.get_timer_status() == "unscheduled":
                if elevation_key in time_map:
                    when_today = time_map[elevation_key].when
                    local_now = zoned_now()
                    preset.elevation_time_today = when_today
                    if when_today > local_now:
                        preset.start_timer(when_today, self.activate_scheduled_preset)
                    else:
                        if when_today > latest_due:
                            most_recent_overdue = preset
                            latest_due = when_today
                else:
                    log_info(f"Solar activation skipping preset {preset.name} {elevation_key} degrees"
                             " - the sun does not reach that elevation today.")
            # log_debug(f"{name} timer status: {preset.get_timer_status()}")

        # set a timer to rerun this at the beginning of the next day.
        tomorrow = date.today() + timedelta(days=1)
        if self.daily_schedule_next_update != tomorrow:
            daily_update_at = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day).astimezone()
            millis = (daily_update_at - zoned_now()) / timedelta(milliseconds=1)
            log_info(f"Will update solar elevation activations tomorrow at "
                     f" {daily_update_at} (in {round(millis / 1000 / 60)} minutes)")
            QTimer.singleShot(int(millis), partial(self.schedule_presets, True))
            # Testing: QTimer.singleShot(int(1000*30), partial(self.schedule_presets, True))
            self.daily_schedule_next_update = tomorrow
        if reset:
            presets_dialog = PresetsDialog.get_instance()
            if presets_dialog:
                presets_dialog.refresh_view()
        return most_recent_overdue

    def activate_scheduled_preset(self, preset: Preset):
        if preset.is_weather_ok(self.main_config.get_location()):
            log_info(f"Preset {preset.name} activated according the schedule at {zoned_now()}")
            self.restore_preset(preset)
            presets_dialog = PresetsDialog.get_instance()
            if presets_dialog:
                presets_dialog.refresh_view()


class SignalWakeupHandler(QtNetwork.QAbstractSocket):
    # https://stackoverflow.com/a/37229299/609575
    # '''
    # Quoted here: The Qt event loop is implemented in C(++). That means, that while it runs and no Python code is
    # called (eg. by a Qt signal connected to a Python slot), the signals are noted, but the Python signal handlers
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
def calc_kilometers(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (
            1 - math.cos((lon2 - lon1) * p)) / 2
    return 12742 * math.asin(math.sqrt(a))


def create_todays_elevation_time_map(latitude: float, longitude: float) -> Dict[SolarElevationKey, SolarElevationData]:
    """
    Create a minute-by-minute map of today's SolarElevations,
    so for a given mapping[SolarElevation], return the first minute it occurs.
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


def find_locale_specific_file(filename_template: str) -> Path:
    locale_name = QLocale.system().name()
    filename = filename_template.format(locale_name)
    for path in LOCALE_TRANSLATIONS_PATHS:
        full_path = path.joinpath(filename)
        log_info(f"Checking for {locale_name} translation: {full_path}")
        if full_path.exists():
            return full_path
    return None


translator: QTranslator | None = None
ts_translations: Mapping[str, str] = {}


def initialise_locale_translations(app: QApplication) -> QTranslator:
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
        for message in XmlElementTree.parse(ts_path).find('context').findall('message'):
            translation = message.find('translation').text
            if translation:
                ts_translations[message.find('source').text] = translation
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
        log_info("signal received", x, y)

    signal.signal(signal.SIGHUP, signal_handler)
    for i in range(PRESET_SIGNAL_MIN, PRESET_SIGNAL_MAX):
        signal.signal(i, signal_handler)

    sys.excepthook = exception_handler

    locale.setlocale(locale.LC_ALL, '')
    log_info("Python locale", locale.getlocale())

    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)

    # Wayland needs this set in order to find/use the app's desktop icon.
    QGuiApplication.setDesktopFileName("vdu_controls")

    global signal_wakeup_handler
    signal_wakeup_handler = SignalWakeupHandler(app)

    main_config = VduControlsConfig('vdu_controls', include_globals=True)
    default_config_path = get_config_path('vdu_controls')
    log_info("checking for config file '" + default_config_path.as_posix() + "'")
    if Path.is_file(default_config_path) and os.access(default_config_path, os.R_OK):
        main_config.parse_file(default_config_path)

    args = main_config.parse_args()
    global log_to_syslog
    log_to_syslog = main_config.is_syslog_enabled()
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

    log_info(f"application style is {app.style().objectName()}")

    # Assign to variable to stop it being reclaimed as garbage
    if main_config.is_translations_enabled():
        initialise_locale_translations(app)

    if args.about:
        AboutDialog.invoke()

    main_window = MainWindow(main_config, app, session_startup=is_logging_in())

    if args.create_config_files:
        main_window.create_config_files()

    rc = app.exec_()
    log_info(f"app exit rc={rc} {'EXIT_CODE_FOR_RESTART' if rc == EXIT_CODE_FOR_RESTART else ''}")
    if rc == EXIT_CODE_FOR_RESTART:
        log_info(f"Trying to restart - this only works if {app.arguments()[0]} is executable and on your PATH): ", )
        restart_status = QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
        if not restart_status:
            dialog = MessageBox(QMessageBox.Critical, buttons=QMessageBox.Close)
            dialog.setText(tr("Restart of {} failed.  Please restart manually.".format(app.arguments()[0])))
            dialog.setInformativeText(tr("This is probably because {} is not"
                                         " executable or is not on your PATH.".format(app.arguments()[0])))
            dialog.exec()
    sys.exit(rc)


# A fallback in case the hard coded splash screen PNG doesn't exist (which probably means KDE is not installed).
FALLBACK_SPLASH_PNG_BASE64 = b"""
iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAgAElEQVR42u19PYxdx5XmJzdPBX2BweuAD7t4Crp3Mb1BcwF1QgZi0g4kB5xgHVgO6AFMBX
JgDzB0QC1gMpAdSAEZiA6sQJxACqTFQA7cgaXADExjISYNLMhge4PuQJ08YtAPGNyGcA7IneC+9/r+1L236t66f6/rDDSW+t2fulXn+85PnaoCvHjx4sWL
Fy9evHjx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evHjx0ht5rakHf/zxxxQEwdsAdgBs+K
724sVapgAOTk5Onty7d08GQwCffvrp2998880XT548Gc1ms4b6JujPMJk2hSj6n4LblFIGjyEn17h4l8kzdM85OTlBc7qRePOgGWA0CnD16tWTvb29n777
7rtPek8An3766Y0HDx786fj4uEfI67YpFAO/OkdO4jYd0NJ/S4Mt/rsOiEX3ExG2t7cBAIeHRzF+Uql7KPXMst+Tz4heSYnfw1Cwv78PEW4B82olqGJ7e1
Nu3bp1/Wc/+9lTl8/9gcuH/eEPfwj29/c/awf8ABD2Z4TCakoVGlpMU0trKpOtrYiAggCTyeuGVjwNfq1PUNoDBwcHzYE/I+bvkR4TwOHhMT1+/OQr1891
SgBBELz19OnTUS+Q1yMSQIEbTVYqaufiZwhk503w5c2oqaenePr0KQ4PDxGGpyCKrolb9LR1N4xwioPa6QzHx0fNjoNUJ4E+y7ffPpl89tln13tLAAB224
nrBkgCGve/yS/QEsThU6gXx0tC2NzZwWg0WnoXzACzOzuY/kyiyPq3IhVJoM9ewIsXMyBKqjuTS051Pwy11n/81i+xPt6ACtatYrIu3EA7N14BYEh4VhMp
VeJRKvhCmf83xQhGEvedpt/fQjpFQoG6/g4mah0gBS8aTRXG2ekL8OPP84h91FsCyJP118cYT7YQXB4lFVe1gt8KXE8NEYYjdujySapafwiAMOTe9EVP4Q
8JQ0xJYdrSG1shALUeILg8QrAxSg4iGeK0jWQ/c46ycSuKSbUeSfqOY7tnuYUXpU0bglEAL0XWP+ofCtrrJ6cEkJeYOp/9VmaZokrmVOoFcrlZdlUfzB34
DQBlmt6l/ZSBz8e3YihJIFCtjtOl1ei6muBvuaXUGOjTz+xHZ7DHdm/lkgd/c/Brx9KbPbdT6+8ZoLfyAw/+tmiBWnWDVaNkY/7NoQe/23F1XBB2qb3GyQ
UEP7Vg/yn3PxUAlma/p9j1b3BgXOHgghPUQEOAPoOfWqA/KvxPlflRWgd/7W9uK2ap+x72BFBBLWglwU/O7DtpPpAqP0p10E8cn4bsW1LCJUGqOQmodojC
tgS8px6ALQlIdqB6nu3XURZVsrD1BlxVUvL6SiZcFeTkwEg05d2IPZn13EO41C0syKLTh+f2l4Of6ismNanwJU6JjltonndQdd7f15oBsgt0OOYh2Jl5QJ
HrBE53BCCS7pEyEpCGAsv2rYY18KnkO6liU4XcfCqV/C6AGPo8qyGUr6AqJ0zIIwS1Pq96bS8+aqUSsNjwi/k9MhzgO7e8Vi5/dxJeGOBXyClw3oBRtDhK
AOCs1dZ2EwLYev+9sPxU61ejT6YGPeEWCJQFXkw7W+lK48s7cEWSgCXB8cDc/DLgV3rSAI2ox39BTyzDgLm178kAN1AIpGM/HqDWUK37+vNZymwcvPVv2A
MgIOjfakjXHoAMf+Dq3y+2TyX3UHcWBtCFGPhm3VuyAD4PmwDmEqBX23Q1DHzqGPjmlFAyJ0VAlZjFW39dR9oufTfrxF6vBSglgcrFIX21+BWfTG2C3sw7
rdM2j/94//Unvm+dALIZyr56Au4HSPoO/IbaEXr0nwOfqBYb8tAJIN8TwArM4RfH/NR30JuGATYK68EfxfdlxVuWrhOvFgGsotWn8ie3HN93EVmJB37UCV
Jdjc5JtJtKt0se+PWeRU5eZ2OVXUC9vhdwMa3/3M0nFa12qtAHXJNOV6cQaODAb9+F79eW2HJRgQ+2Is++bxfQ/loAD/5BA/9iWf+4xYfR5oalV0i/6HTF
PICLCXxVuS1cqf2y8vtoKWB9PpdvEOMb9Ya4Af2A6gCGCn5q6I2qUTg3CoaYhCu9xW/c1Y8NsjTh1vdjeeslD36Hz6h8vA+3C/7SaSuV00peXeCvB7nG+X
x0LL0msfyRB04Axe4J9xT4fXD3u7L8phvazVV2hWL/aGGeStbpi6ORqdFPMmQCWHWX3+wRqnUIt/EEbs31d1eolOtnkYLSLdChMsO8eh5QywQgjgDSvctP
tVz+jC1yz42FuyjZl65JZTDXvY9rAx5xF349sL7PqB1ii4Ocd5QkHYdfB8BccBDnQOJ9akrZHQA+3cYiMiAy8uvNp/2a8H7MyYD1gXtk7UkV3yeWoHftq3
fkXLRLAAtFbDnn5Qz85Lod4u5zyLDdVOWAD+5B3oLNMGMI/O5qGaQ38b9zAjB3T+Zur7X3S+gMveQS+B0Nd4VvSE77dQv4UkPJ+cDn5vFrd1NP0glOCUBE
7A2bMQn0GfyqbRaJ3ko278xZs1gQBnCroK8UeSf7IzgHPtcGMTsyzVL5LhoaASxFtw0AY7kyOIP8RkMC9y4/WYO/D6fcVHD9OzlSrAoRRsDnPO9KWsVu9Y
+U9kmguRxAnATEomOUSwA1Ge9XAD41hSzqBRDrvafK9F8AtR4HvkPwL7pVmu9M6dATaDYJWGVDIGezYj0Cf6M03szDm7T+XPdmpaDWAzBofgS5OLbg7MYD
MMg0mryiSRJofhYgqDrIHWVFXIK/wTMPlMv54FQewHWGnOtclchBKqjRAvgNu+0tgN++OTJAAugniqtAzvzJ1KRmNZ9PkFYAn3OH9visqHKPiRwk93Le7w
pbXL9/20y9tEoAjPlZ9WR6cb/Av3qklpWwNdAb3GgK/K7B76JIUNoe6cF4AF1uMlIB+EWuuUiP+2AeT0vDgDd5yhz4oCG4+rpHSrUhFoXiw0HpIhJAi0Ap
WNRjlhCmfn2PJQhEmgZ86mmsAz4BFBgCX2qCnl13YcXx9TsCOQ4D3Fn++MavVAeo4u5MLkXuwc8pJeQmBrPgoSoIwEXAd45QbgjwUo/MeYVzAM0CmhoDP+
qCfwAhj0gDoGeDJ6oAWK8CfGkV/GJ8O1V7shR4RolxkgETgHV8TZ22yRr8VFdXHX6v5DxW05bQpcVnQ5DNgW/NUi3F91KPL+wa1uFGoc4JoJudzlxs6qEs
n+r64Eeyx1ictqTa6xkAi+vzrIp8/fkuPGRz7LA47GrLnfmbBL+UhUjNx8CNeAC5BYCqj9Zf6dfI2LarVnPJ/lIxx6Yq+N3apeSKF9gA3zbRJ9UaL7W/1S
H453/iduPmVcgB1Cn5VfXfVfb6QoDVP4pXWegs19HxxdgVluyznmADW4vfDPjFniPcgz8vH8FFjWiOBJwSAMeSPlovQFkCTfUY/LUdFDceDte4xupk39K1
OprARJF5nG+7b77YPJY7ALxJW1mz7IDPEzPUfEMb9QDSCwJ7c2p6W+AXaRT8jeiktc5pLlJB8tRcq0ZIrUaLzUdwh73NOo+kbD3wANcCBLB1A6gaKC+Y5a
/tOTip+mF9nL/4RicbZVb9yRLdCiCXc/CSbeH5TJ/FXoMpEmDmYRFAZf1X3YGfqsb7pdafCka7PWJwM5XM2Ti/8jeYL+cV67blNzme/xUX4NeEMZJ4L1d/
bkPqcalf6CeHDFLH8pOz12YfIGjg4VbKxLX2qONsnE/KLfBTP9Vd1r80JkotFxKLK6c6l7uk3NrbsJusBAEYgk71CPxVXqk1sR0Dfy7hee1vRWsfj/NVjq
kqMlnlyb3qus4aLzK5rbjTAh/Jhb5ZFWTLYO+YANTwLH9vspZuLL84AX7qOK1c7bU8dESa0DHOfgO76cu8PwhXfElH64F64AH0y/JT6pXW4ZdI6U0Ccsst
upplrZcvFudscOrRam71HePHueI3AHgzx8Xe5e8Y/D0ggKbAryxvo+RYmG7npwHeYmf0OAlIwfdIla/MiyZssuVsdh3luvsVdXxFAF/b5c/zIlreinkFtw
SrDn4tkMgijBcp0R8qCx+1z9Udt0AWCisL6892ek4IgEDVx480CHiXoLdsq1Wiz6TQqYPjijokAJNqP2oX/LFxIQOrmomxJSrZFO2jKScohz4gSCXDxMRS
5/yeBr+UACxy9zesJi7ac+tjJYkdnK6z3JzTZmpParDMahJAE0k/B+DXGPSyXDYlHEGVY81jTCLF7ZC6ipl5rsD0ZO+lu7/4DilOdTS3oU1m/i72d24G+N
IA+Dtc5tsVAYgtZtsHf/FRWTbefwIMUrBgo6QkWBrsdjYGP5We2tyeIctZ4tSSxZc8j2rpojsGPq8OARSOqWoC/NbJqcXwUg1YpcEvsF+tRQ7VtTBKLXVh
SAUO2LwB4YbRIeUmAiZWXyq+qMqEwVB3BKIl6smt5W8k/KiiqaqjNlBuRkBr/RPAp0S7e+Gc1i2brcnq2dkSKUZsFfBzKcqH6QHUY6eK4LeaR2sA/NbW32
aJHFXUZgFzfmKO6Nzdl94AviHgV11VXObuS4WXl211LFEk2WZE0JNpQAeWv5QIqEENrrPDUdUSYTH7Nc0niiBdHnTC1j+0A/iMu881HiIWn5XZCaDV0WmA
AAJND6kCvSa3oNMSQUPgN7b+ZKFBhLoqvHT9JQn8zk444so/mgG+YLrWysNhqQn8dL6gGlutgAeQH5fWB7+yxFtT4J8jTalaA60cgz8TQhLmU3t9ALs7NU
9k6mufCO7C6tcE/0VYC1B/ZzMb8FOzLhWHhuDPV3lz8Juf15V4R9CS1W8R9IueInGEmSKrL7YEYtoDEp2RmaO+ajUIIOkFZOdWqZFXcrwMr6mwX0Sr0qoR
d06MMcWLphFZk1M91105B762zkgcGktdks92ByM278LzkqZ85lICcMtFAQ17AEW1tLbr7FS5aknynUo0ROBgdxXdtkxKM+DmW+pF3opS+vK6hBKVeal1rb
7Vtt/ugJ+OWggNzoalrb5UIQ5bL0/MuLzlUKCFEIBywFcN/GyoSiruBYhL3Zk/LGVh2VT1Wfevycwll2SRdaENx5N8hbFW6m5mDX1VJWQ765VXMNcYBupY
fS7O5RT2jpjVGZsYjeHvCWiZDOAaxT48d6vq2rGEsiwAo0VhzkON40OptomtCs7Xo6t0H+ctl+WKwK0O/E5K4xPANQd+svvMD05VyIlbDDqGUWXTliESQE
mCju2hqQW/9plUnQyYQ3Pd56rKagHDudVPJLCZXSYgajFad4DXvLBkRZRmv9Al+Nmmd0yXRYppkLtiBMAFcXMtVyEH3WyaadINImlc/y6LaBYtiLn7DEAc
u4XJz184pjwQwJsBv9Bt5+JzhJROMyWusdJ+P/SBAIxLgec9yMrkwurgN8o2ZQYP2QWDgnqbPLq0wWqeMHQQb+et5iULt6R10JtW1gkb35qguIJYX+mMl6
Q9B03y1jjPwMMmADI9/00bq7YAflNFTZdwc9fWPyo4Yg00pUbtilToxX5ZeWSZOtYhprMwJkeG6gCf1dRkuKCkgj/LAyaASoPaFfhNm7lY69/FDsHC0XJn
TSWfDvxVcUiDA7ymIRLWrEeSYu9ASjyH2P1KCvIKPQF++wTA0J0TpqFFW/CLUyLILk4LF1vltMuOgjn4qfCSSiFPSY9JbwGvbwwLOwc+Cix+8nHZkt68PJ
dyAHylVH8JwDgE0NFo9HUVffiGzDPLORAbt/YxjSA1L+ip4N6XnS5DhkuT+mjlnQK/5CNt2VXyvQOt9WfUfPdgQwCyCAU6DgGEWwJ9rCMWVr+gXxLn2Il5
N9EgAG9ilbnme+suHSyvSWZb0Ju/Xw2cAFx+V4PgD8NzQLoEPGks/uL7Fx4UF2gSVy+RlYEC3gr4bPke234w6HzVg9i+VwTAJoBdVNipHvQKS/6SAZu1BF
Li6i+7RZX0TQ3cUkugbwDwy8cWlce1tvy2vEa5DeBXCrMH4wEoWNT+tOH6q+LDOqiqXmusvjsDdN5W6Qvopdojy+piuR/AT4C/KvCdHVc8WAKAvjxdte/6
R0ZeZcen4HQOs/NwYzP5ZVa/DvibUqQm3PrcWx0D37ZPDE8sVXEHFpbrSnoQIzglgGiKIoR+vs8i/tetqVUtgJ+l8DSe9A9irHqcbDnZ79DTtDHvFPBOgV
/D6lscU6zmoLfKYUv3gO/UA9BbSWXkKTcL/ohpRNzsWKPV2GjBv7XLX8n69zGOrwKMuu0xncoT+35Kq2YhEUh/M4H9Pxw0Df76+4rpRzQMHXvQKS3pK/jb
tvJFwK+ME2kH+Jo25q8kZXtFMvj+XhcC1UB3SYCV/Fu6ZsaJ688Sq7pTboC/fFRQTZcppqeuiK9LwDcFfNutvMRtv6WLfvps8RslAKMpCptptCWJknYgqJ
yGzVQiDPNLbm21I9GWZKIvvVsviYWuqu4AX7b3ySCAX8eN4vKfVWoRkrqIBFDWSVRg6GxtjzPwn4apFqhqWpFpR3GWX7erbbJ/IqaUxgAvhUDnqo8WS5Js
EvjW5ZIVPngO/ES0V+n5Cl0kCFsPAYT0QJNyqOcAJfk4SodfBQcHSygWLgnrzWFmF0hV8FVU+L3xOQgC4cyJoor1bW6n912c7BsrzJKGgW/aTmHbgLbkHd
2EDc0QQN5GnKzHtA34c6/ncs9CYgQReaNz62+6TtMK/FURQ+X7mDoGvOOUgD4XUulVkZtkdpZz/EZxD/jGgG/Xx8OpBNRpsbLpMnL7+jR4w1mCEApLuUy2
/HWSnc3xEAYB+MVLuf6rROy0oIrFZ9uG6W9QTZDMyoYAcaCVet5Siwzyxk0Yy2q/5XPr7HDtbFqGkuuEuBoauW3A17D2eaAvG/XFpTq6NFogzvWBbwT+AU
wGNFAJmGeGlcYXt7OKbpIQsoy1qcKgJZqulNngq/Lvi4Nf2GGRTWOgtwe+6P5Lykc9beBJmzUx0Bhj4LNx37tbALSqSUCqA+IGKv/mW3tTXI24+I1aX0Sp
xMY91cYua8PE8uSZdgGfBb4Y9lvmL2KZQpL4b1J437JNDuL7QsiyqyO9VfN634sQoNCctiDzuD9veo1KdHOxTXbcSGRmHco8C2U/wNw54PWgN+s3+yo9KY
jvxeQ+zpIIFX2XVBuIvPoIVaVv0ytPV4sANCewShkRuGUGCcNSwimvy1Gl91Cpr5hvK4X7Ani2wogU/SJ1v6NaYq8c/OysTJdRTgxWLyjwAodZCsznukBF
2iMN4V8EkLN5LT7ZK6LTTUFFrylctaTWIdBr4CPR1066x01Gn8rYwfi5Nt9FOc1SuX/h5W1Ssyq1QwLInaNUlspMKUWoM/cpAglnsJpNThxEXxP8ZfWzyk
K9mgR8HeCLg8bZAp/tLsjOHOS8K1PbQTkWSdVSCWatDVjREGCuVKoNhUoF4sKhndWXOOnYD0vGyzG4XbiGsambOeAar5O+gJ5zn52eIJQc/yDKVSvDLZPr
DYfuCHF2nbLpVw6gBCS21s9knzuZg39JCGSu0MtruWDIitxNO8Vgl4m6ou5jjYNVdQSlBcBnPokN25Te+zxZoV+KcZcoNN7HNBoVGj4BBM7Av8SuFOufNq
3GYRT3L12BHLRWCjVKT4Qvckoc6hoXehVuI4m6CT1b0LOhBs37XWk2lGU9SWtVwbXprejPy5BLgc8zlGnXmawAX+X3ZOmsJMGf934pg2eVQN8cZAJb618N
8K1behvQ54I9BvRE5jso72UL8qPO905swu3oRQhgFj+Lc2IQQGblPkicaonyw4xCflAND2HbgEf9hF6ZCctbK5AAOVXTBrb7TuoU8P2QhnMAGhJgQFQt7U
Th/rvLrb0oz9fPIl2qMJOq9QVIWP+GsvNNxeXGXgKXrJgkw3MLxB34pL6/1w7geXgEQKQrvlT6b1NVYZOOA2NHQ4dhhCplolVV6wFcgZ87BnxV0EvxeuxE
FYw6r3wke2wbTdNVVKE8U5Kbo2oDjwLT1gzFAzAgOeWitwQIWQP+vFdU7VTVzEBzdThWV6w6gNfNisz7puRQ0/JXi1vwid3PlCLgLk6FZ463LNmKQZ4MJC
aMWmdVBTPAZ4aPq9CBZcVAeZqSl6OKxcHtgL7CiSK5GxIswB636iUTi1IDpdwM8E1yK8begXNwtOcJNFIJWD7PHLPLtgOs268jPFsOmXYmiBehp4l3oOv/
omXOZQPJmf9q3rW3QYAh4DNl1FLuX9fRfG4P9Lr3EQzXebTZxiGFAMkOlPN1mmQwEDYFeOGsWG94sXLXodtfIwXvNHtfCfRpwGs2LlieXGRZFlcX+NwBmN
gyNOgM8DIsAtCxqLHFtQB/4uRhpY8BuDDt46oxLTxJqiqG5O+PtjyjkKorXlUXnzvEAdvpcSvhxyp5AE7dJt34JSw/5ecTDHMLzA5398p5vjjTCKkBeCAq
pqF6qtizZF7TDFy8hXv1gqLs2pHiRq7YyUAVx1HC8gFOhxGsp6PFkX2qDyc51AG81q2Px+5UH2FtWvpaMVPOYbMVD5EoLBMpOZKQbJ5lZEi4vwQgLZxgyR
LOt/VSeVxcoHTZoVEq6zSU8Yoz6y910Kaz8qYW3hXoRdvVqhboXcyJzvuiECw1pp0sziG1O7XMTeXsQAjAbIVd4koJo2KfzIGA1ev5deBm03vywgY2tRZi
r3miAzwBWG8B8Is3F+xYw6Ww1P6yqIqs7Yix+9xNm0E6l1l/x0bWKQGw6a6rVJwQ5Dx2zAW/LfD1Zw2yKjEUrJ9lKB1QcQH4ePMdAn5+WbEHZDZlZ+U9CY
MNgaCqIsbGW+gK+GL3Ea6dbMc5AC5UMELRmXMlS7jCWc5A1QC/Ff3aqxJXCot0hwaSxbeKFeCrWPmiPuGCqJwNXFw2IQPnxj3nyKfaJ7NWBXzBYS/cYw/A
VteND7xZZPypQfA34LJJnY4z3r/Q3K1ng4u4xkdzQVzLTXVyE6MpDrNA4vojepwENGYnG6JYTvfl7J1uHP5TSypksvd93tHAbrP1zlJKDe+vb/q+xidqpG
rjVNIHlGpANdkWbJghgEW4VQj+xc7CRJY7CFPTWlE+ULlWPq99Yt1Mdv09bHlhVeVks8Pg2TUpuN6KzRL4nGcYxIGRHUIIYAL+zF78tNjMg7LGP/aHZGqw
3RqrZT/EOmTJfVrQSyXl5aa03DYOkMYar3kBFTa18JCOJtTAMZ9KSd9Ir0MAFz3MAGRxgo/Soiuzv6vEtlOkNh3+HGUQSR0ERBU3Davi1ld4dpXAXyqixF
k9NJl9itSO4it3MTfBIr0OAcqy6Oson/9bgt+2T85tPpXpiu1Kj9LlvpKx/srFuu3BWnmpl0Oo881Cpa+uXAIkxVXm7gDPzRrZ5kIANkNS7oavcfDbDg8l
wqii/qYybGvyeGRUxEO10w2NAd5IQ2u69dVNoEMeMC8KK1t4qgrSE2z8meJygJz3aatrAc4j96xJlkR9v+pGZ1B8zp0+Ej0HvUi1BnAfAF/XyncGePu8Qd
aiUo1wq75vbjNTKDLYtQD5G0iIhN3tvwSTc2fTdoWKQ4TKe13UdO8ajeUbWOjTWtwbH72c5TjShc5lO5JLnHzpdSmw2QHRqfA5XGb1IyApI0/bXEsqnvWk
2TW8iKFETDEiLjvcOeDPuayBbbpaA7zhg6VLwFfrSNdd79YDMEgBJHI0Z2HSfFITZ6TXyLCSWSwZHfDRkjY5Bn36TIU2dsTNnb5FcwdEDxXw2Uf02AMwjB
OikT3T7I4nhqUeBscD1BIN8JOK2aIlqQD49Nke+T6QnZU3XedOZX5hBvCqbSQOB/ANf47bECDPBWCGCKAWedez0ILnuZwIaiNMFVp70drK839pv86d9SFI
qdKUAz594oKtIlJeIFi4ht6M+CX2jrxTmchyg446mQP3gDcp8+5xEhAsxWeDCgCEFYbDtYVI74lnxyil4G9stVq+lbdWKGeHh3Ju39T95mICipffKuO2lx
4qW/q35hIgJpvF97sUOI5X3cL5xU4+ypaLuSZR6Pa1d+hFMBp/iLSereeKg9+8ry2l41ufYFqTjru5uRAgsyffWWy76S56032cydyQRbCalaqTrefa7ewg
sK7wTcrN9zakpjZUxP0OATT9zoiO6pboQ9Vyn+4qjhVZwDl9TBg3AH57xZVGtJ7dfmIvgd2QYbDts6p2hE31vYEDU9oLAXJyoczRZp7husFqJpW7v3+mm+
a/kdIlbqjBM7QB4fozAXUWjibiLeJ2AZaXl23VwKrqdl5qKXn0BlKG19p1kHAZPQxtLYAC5OwFzo5CnC0PoagvyeP63Ln3i9XGRWt5okkMBoIRBi3iHoRd
ylmrb2uobJVDhGezMoboaQiQo1B0uA/H25nrd09RS9t//kt6KS5RcugEoBSbEyi1269aEkIYhghfTFv3d8PGb2jsIR1IMOhmBI1r07n8wC0oJd8qNGQsqC
5DBxpXUrMHyUJms1knliLoBAPBQAkgHHQzwsJUgvSXAM5DF+qMBCj1i9ErlRlgZ7PTiquxPAlcWHFMAq7TWk4JQExqrholASoFH1mHs2qZ35jNzjrXJ08C
AwxfHJJArz2A7BxleySglEZN0/vvaTJ7ZNiuyPWvQ7/UGgns7e3h5js3EQQBNieb2N7eBgBcv34Vk8kEOzs7AIDRKMDu7i6IgHduvoPr19/E9etXl7/dvH
UTe3tvAgC2t3ews7ODW7few+bmpieB7kiAeksAeny06wkoGwBqzvVSQZZDRBhh6EKZmieBm+/cxI23bkDCEB/f/xgvZi9w94Pf4MaNt/CTmzcxm01x+/3b
AIBbt97D9s427t79DSbjy9jZ2cY///NtEAH3H36M2XSKt27cwDvv/A/cuHEDv7r9PqbTKX774X3vCXREAtLnw0HPICpf8UWPVm6GBLgKxxClmhs9YTqdOW
yd+bmHTgoAABIXSURBVNISExJI69RoPcBvf3cPszDE9vY2wjDEb397Dx/c/QA/e/cfISHwt8ePMZlcRhAQvvz8S9y5ewcPHvweADAejxEEAcIwxHg8xvHR
MZgFz549x+PHj3Fw8Bw7O1cGGA4Eg25KiGYmHt16AFLB+imXwIqBQ+vuK+vHhWGY2q7MfVtdegLjyQRXr74JIsLOzg4IwJ3bd3F0dIz33vslAODbb5/i/v
37oPXo7q3JBDs729jc3MQbb+xChLExGuHRo8/xye8fYn//a1y5soPNza0oHLiy43MCHTRF0PcdgaqmKGt6AsrE76Dsy6iMi4gxc2r9m/cEfv/7B7hz5y5u
3LiBz7/8HG+/9RYeP/4Gn//xS3zwmw8wnozw/PkhQAqPPvkEAPDbDz/C7du3MX0xxewsRBgKvvryf+Hjjz+GQLC/v4+TkxO8mNc/HB8d5fgf3hNovCm93h
MQEqqqSt9QOKB/ozLyPMIwdH4QQ9MkMJ3N8Ov/+WvtNfd+dw8A8N4v38P0ZIrj4xMAwGQ8xtHhESZbEzx/9hwA8Mc/7uOPf9zXPue3936H4cqASUAEzDLr
LQGA8ay8RLp9ErCK/2MyOztzjdPWcwI6efz4MR79yyfL/3769CCqcNwPl6Tg9o2eBFw0hYIxBDjocQ5gtj+ZbM/MlB4OcwKpuX7Kzv2T5dHis9ksueSv0R
2L25siBIDD48OIcmIXP39+aAl+mzf6nICLply7evXoaDJ60lsCePTokWxtb/80MFr374YElMG1pDmv43xFAGVeySL6ab+BkED7+PUk0KgwY3tzW0bj8T8+
vnfPqS/6WhPtfefmr/YOj599MT06Hpe3lvMSChU8eFVCEmTi+c8z/4Ihi188NEACCzKKCKIRruzunkwmk59++fknT1y/8rWmvmVv7wMaT05+CGCnO/N2MY
TD8EOT617f2no0nU4Py64bj8fb3x0d3TLywILgfT8CjYkAOJieTJ48fnyvEYv0mu/j4cvt23f+v8l11/f2fvTjf/jR12XXffWnP7/95PHjP5s888GDj7wO
DVgu+S4YvkwmE+c+1mRzYmafvHgC8NKtjMcbzqOs8cYYngE8AXgZgARBkJn6rAvX0ag8MTb0RKkXTwArIevr60bX2eDVhFBMrvHiCcBLC6IMCiLOLOrITZ
7HzL7jPQF4GYqwnP3kiy++esPguu2+7fjrxROAl3xzbXTZ5PLlW5mcgETHgaa9eaP4XnmS8ATgpQemHUYGOx/UAqlxIJEXTwBeesABXrx4AriAImAQq07e
68UTgJfuGQBC3Ml7vXgC8NI5/gUk1Ml7vXgC8NILD6Cb93rxBOClY2EAqoOyXJ8B8ATgpQcyHo3O1wKJDqhSDa2KFgcuR89N7KwM9wfVeWld/Frugctf/v
LXnfF441nGInOZ985WLn3e4w6fHfyXd99998iPhPcAvHTi/su1dEm+DbhZ7zIYSxBsvAHAE4AnAC8dyY4IpzArBoDmMqNvRCBK0bYfAk8AXjoSRbSVH+Oz
FcDZJiY4F08AngC8dCaCScLlFws7zwWBhXkLxn4QPAF46SoHwHLZJm6XxcVic32hTPwoeALw0h0FBImzDtnQmlMW5WLv/oMhIz8GngC8dBUBCALTw1XExL
7b1hMxNvwoeALw0oF88cUXJJBgsQ5AEiAWCwwv/p99NaGAvQcwYPmB74LhSjAavR2BUKLNPhb/zCsBsv+I9p/z/4PmHy78BwD+9Oc/7/nRGKb4SsAByV//
+teJCoI7HMoPQ+FtCUNa7PJTOIVnV/Q3v8C8GigIAqyPAgkoOFKKHgPy0bVr13xxkCeA4cofPv1ie3MyvhMEwZ5S9DryTt5wtQqvBJEhh5jNwuTe3hSdZF
wE9MLH54DctsI/IAWlYh1BhFEQgAgIQ5PMAxv3jVj1qByxyJPpd9NP/umffvHUa7UnANPY+sbW1vZXQRDkw5uK/kTGiJcChQ9ZMD35DmHBSj9hsYewlF1l
lwtQFIAU5fxGuDzaQMJPEZvWSsUDpDk+uyGn0xe/ePfdnz3y2u0JoFBu3rwZ3Hrvve9GGxsjZQJoKvszWYF+IUffnWA2mxm0mIt/EUPYcDUaWCwUDILik4
RGwTpGow2EuaGF2HswOYSipUSR2cG3T/7bRx99NPVafi5+FiClzzd+/OO7o42NURITglwyED0ZnK+elRI3PPuno6MjTA3AH4YhJAwtvzDn/aVOi0J8++HE
CmFFpTsSTWcMEcFoNCpcnlwX6MkLJN760db2lTsA3offysR7ADpo3Lp1K7j5859/Nwo2gozua+BQxTMo1lwBiPDtE8NwVXV/NNeCFsBmmLqyu4PT6awY6L
E+MnpqKkTi/HApfHbw7L9/9NG97zwJeA8gA9e33rrxYRAEQcYocpYM4jX2Ks8FMJJkFj8Amd/KYpaDVJQE6OK/F7t9sJyTSfzfTQMQNt8dkJSCVAW7IdB1
YcX8zmCyNbkD4FcxJ8Z7AB78wK1bvxrfvPmToyAIKIsqlQ80hRJngXJNP+d5usL49uDA0AlQnXSYJE2r0czB7s4VCBjhLDQAvFgkC8+zmmWIZmF5fnBw5c
GDj45sqdp7ACssb93Y+5AWWf9MXJ+up1e53oHVklrOXnk6/Q5bW9u4dnUXBwfPERbE+ASCCfRU7FWJSD691ZfoQpf0IgM1LwA6/ztz8Q7BgSJcvXoNW1sT
fP31Y6hgvaJlT055lnsM8/alum2yuXUXwC2v9d4DIAC4c/fu62/vvfV/KVj4vpQX+hdk/atb4vhyXg4Fzw+f4eq1awADs9kpDg8PMcshgnVSUaPiOG3ZKR
AWiCa7vx4EuLK9jc3NCTbGY3y9/02yXqAQ8LZgZ7OwIApX5PnzZ9cePvjo2UX3ArwHAODKzu59IkXn2iMpax4jBNGTQu1TcubPVUFURLO/v4+rV9+EIoWd
3V0oAqbTGY6Oj3A2OyeDKPmeyqo3tFcn5TgJchbrqXWFyesTBOtRbQAFAWazM3zzzecgIgSjCcIzqQd207CDc2dgaHMyuQvgHe8BeOu/vffm3jMVULEVVy
5tfn5EsHDNpydTPHn6NwDAtatv4vJ4jI0gwPp6lCScvZhhejrFyckLzGan9UG9DOyVkcezdO+DAKONEYJ5u8IzAYcCgKFI4eT4CKenM1y7dhWjyyPMZrOo
epGNgiQry25kys+JQ/7f8+c/fPjwwbcX2Qu48ATw2WdffD3ZnOwVIZ+MScEBAwBQiqJFOiFjNpvh4OAAzIKtrU3s7u5idHmEURBABQE4jEqEp7MZwtMZzo
TBIhAOwaEgFIawIDwLs6FNyVQlrSuQoqjUNyCQCqBi54izSDI04eh9J0fHmL6YYmM0whu7uxhfHmEUbGAWhsXFTYbJRDOwc+nM5Gw2+/re+7/+B08AF9X6
37m7u7e39+1y/3tDy0cNB9kCXr5DwEuLOTub4fjwEMxAMFrH1uuvY3NzE6EIZqchZmfh3PomQxIihUBFibfljOA8bbD49yjpLiAQwgXAJFzW8p/jfnlxtC
IwDDGdvoiALYwgCLD595sIgo3IOwjWQYGKyCw8Q9rXd2XZ2WTx0rw0Mv6s4+OjHz188NFfLioJXOgcwJUrOw8XgT2nUS/5SUCbeD9OFjb3SSwYVkQRiIMA
k8uXl1oahiGePH2K2WyG8DTE2VkIBqL4OwgQKIJaD0AgzHCq/yDO1iomLKcwQhZIGCKUEBKeLRMBpIDR+giTyQTb29HeoNGaADX/nRCKQKZndWN2a+seS/
gVyuXRxm8A/CUVEXkPYNWt/90PPrx+9eobf6HyifyMO6AKn1wt+QeDHJ6iqJBGgZbvYhGEIeMsDBHKGTgEwCHCMMSZhAhnYQRgYUBkOaFZZDBpnoiIE08Q
rGM9COaeg1p+cHRtegqCzT6cy8DOWUKqAXbJyTAenRz/+JMHD/YvohdwYT2Aza3Nh1mrrKA/ZVsSyOc85FdWHbNaAeZomjBUlCADIV6gFhQIEIwQbIwiZ5
fj3i/r8mtILgiQzLeV1xqVTUGYJP1Y5whUDgvEZDpBogqPUTB+H8D+RfQCLpoHsLD+N3Z33/gqY7SpONPX/QG8msqheNQimFv58wuKLH0S//Zzh/n7kBps
L2qS3Y81sGymQAw6Me8qYWD64uSnnzx88NVF8wIuXTTwA8DmZHIfIvN4PmnBc8tUqEwr7IjCuKpd8v9Mc9AnTBbFghoBlNZriYghORugcomlEKFiEr+zzh
EoYqOC9VJmYC/MuGgqF4P10V1gsg+c8EXyAl67aATwwYf339ne3v6sPNy32guknHbstrKx+DWlq8bL/SXXqUCBxdY9K7spiUGGnw0sO6CtMNRHF5LfWwUb
nsabPptN3/3k4YPPLpIXcOkigR8AxpfH95FZj6bL/ksu6sWGBiqpUfnC93hlvh7o5dlFk7X3xrv1lGX5DefuReqCXco4J5cSg/Xgzng8/nI6nV4YL+C1i0
QAH3x4/1dbm1v3cy15nRkAx8LWbKLRV8Mse6l7XlKqm5mDZwNX3gDsRXF7vvehA3uOD8TZ75vNZr949MnDRxfFC7h0UcA/Ho/V+PL4g+WoU3Kfn1S4r1d+
lQcSF+lBu/P7shv5SDnQxTTpZgbgpcE1mr83AXxxpYQUWfcSsOvqHTSvB6n1u5OdnS9Pnj8PL4IXcGGSgLdv/+YOKQp0mW+VwrLk2XvOg707HSl/Ujqdlz
PvbrLxZ+k+gFx+i3b+nXXL+RsCvD3Yo9yC/l5FmLx97fqtR8+fP/Q5gBWx/ru7u8HocvB+Jj5cZsjzdvLhwhJhcRYclG+Qx7b35pvHHFhw2S3a54oJ4GOm
v4iQCqcsi6YqudhfkaS/X9A9i32Dgjvbu7ufHx4cnK66F3AhPICbN3/+AQCSHJ3P3YRLpcih0ETnK5hpbZyRf8CG8b9J7G9CMJo4Wcpc+9zDStyAvSzgkZ
K6BhYU9xdjfHVn973Dg4MPvQcwcOsPQIHUrbRSKa0lV4WZJKONc21ttPmZGDk3K81VbBEK6C8qmyGQBKDKJi6lGM8FgNUl6jJ/KTrgRPT3S84YL4cyGN0B
8GB+xcp6ARfCA9jamqjT6WxeH89ahVVp7qAef5CURutmmQY2IZk0qMpLbItAawvifEdEip9ncNhpJiIkIJifX7A52VSPPvE5gOFbfyCYjCfh1d2ro6OTk2
iPPcoz3sVbeuoZg4odgrxtdPS0Y+RRWDyhcWEToOesETI6Iqx0Y9DiegeTKdA4uWyMNrC9NcG3B88YQBC7ZCW9gAsxDcjAFIRRxPJKGz2TKgFQYhVcDuOo
HDCq/J+0ZwhRXpSvQLpN/1QxFyotaMgK4No8BgPrOT8k7ljsAbqOxBbgAdLJO8o6KCrZbsoAXOlHvBSqtExixrk8OI8Nw3kTw1UGx9qKf9cagL+b/dts9p
8n/+m//vu/h3/3/cvv134ga1hTL8F4idfwEsAaXr0E1l6+AtZyuuQVsLb2Ephfr33hWn7X6n8yAb8CYQ3A2vy2tXPQr8X/k7CW/j9aiz4n9Q+tRX/X/fNq
DaD5/2L59+hf1tbWsPYq9vy1NbzEq+TzX2LZ1uiql1iLuu/829eAtVfn//lqefOrZV8j/ri0LX9ZYt3lJThxb9b3l5evztuEqJjp+++/B16+EpHv/+1fv/
rXf/nff/vb/wHwfexVr1YNKKtaCbiAUQBgA8AmgCsA/h7ABgVBMB5PJqP10UgpRWVb/LCwkyR+K1WEpBrerqi4L1z0lDjytDU+uyaTyCIip9Pp9EUYzk4B
vABwAuAZgGMApzEvQDwBDAf8yxwAgBGAyfx/N+Z/W5//ThpsErysihQdnyzzf5c5yBf/zABM52QQpoKclSKBi1IJGM5ZfTYf1AXo12Pg96C/eISwAP+CCM
IUGay8XFrRAaYctl+w+cLyhwbgVx4zgxOuSARxQhDNc/wswMC9gCA2uPr9r/T3eVndkCBuICRFBt4DWCFLoOZgptSA+9jf5wQk5QkglSNYWVnl/QDSyUBK
ufTkXX0fIuSQgA78vhR4xQY8XVEjHheeDDREsNKy6jsC6Vx6ZXidl4sXCpR5B54AVogIYEgOXlbbE6xCEp4AVpwIvHjv4ELIa36sPVF4MHvx4sWLFy9evH
jx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evHjx4sWLFy9evAxR/gNu4YLnYz5xiAAAAABJRU5ErkJggg==
"""

if __name__ == '__main__':
    main()
