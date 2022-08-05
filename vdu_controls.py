#!/usr/bin/python3
"""
vdu_controls: A Qt GUI wrapper for ddcutil
==========================================

A GUI for controlling connected *Visual Display Units* (*VDU*'s) (also known as *displays*, or *monitors*).

Usage:
======

        vdu_controls [-h]
                     [--about] [--detailed-help]
                     [--show {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--hide {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--enable-vcp-code vcp_code] [--system-tray] [--debug] [--warnings] [--syslog]
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

``vdu_controls`` is a virtual control panel for physically connected VDU's.  It displays a set of controls for
each  DVI/DP/HDMI/USB connected VDU and uses the ``ddcutil`` command line utility to issue *Display Data Channel*
(*DDC*) *Virtual Control Panel*  (*VCP*) commands to each of them. The intent is not to provide a comprehensive set
of controls but rather to provide a simple panel with a selection of essential controls for the desktop.

A context menu containing this help is available by pressing the right-mouse button either in the main user interface
or on the system-tray icon.  ``vdu_controls`` may be run as a system-tray entry by using the ``--system-tray`` option.

By default, ``vdu_controls`` offers a subset of possible controls including brightness and contrast.  Additional controls
can be added by using the ``--enable-vcp-code`` option to add any other codes supported by ``ddcutil``.  The full list
of VCP codes supported by ``ddcutil`` can be listed by running ``ddcutil vcpinfo --verbose``. For example, the
VCP code 66 is listed as an on/off control for an ambient light sensor, this can be enabled for ``vdu_controls`` by
passing ``--enable-vcp-code 66`` (the control will only appear in the user interface if the VDU reports that it
has that capability).

Builtin laptop displays normally don't implement DDC and those displays are not supported, but a laptop's
externally connected VDU's are likely to be controllable.

Some controls change the number of connected devices (for example, some VDU's support a power-off command). If
such controls are used, ``vdu_controls`` will detect the change and will restart itself to reconfigure the controls
for the new situation (for example, DDC VDU 2 may now be DD VDU 1).  Similarly, if you physically unplug monitor, the
same thing will happen.

Note that some VDU settings may disable or enable other settings. For example, setting a monitor to a specific
picture-profile might result in the contrast-control being disabled, but ``vdu_controls`` will not be aware of
the restriction resulting in its contrast-control erring or appearing to do nothing.

Configuration
=============

Configuration is supplied via command line parameters and config-files.  The command line provides an immediate way
to temporarily alter the behaviour of the application. The config files provide a more comprehensive and permanent
solution for altering the application's configuration.

Settings Menu and Config files
------------------------------

The right-mouse context-menu ``Settings`` item can be used to customise the application by writing to a set of config
files.  The ``Settings`` item will feature a tab for editing each config file.  The config files are named according
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

The ``Presets`` item in right-mouse ``context-menu`` will bring up a dialog for managing and applying presets.
The ``context-menu`` also includes a shortcut for applying each existing presets. Any small SVG or PNG can be
selected as a preset's icon.  Monochrome SVG icons that conform to the Plasma color conventions will be automatically
inverted if the desktop them is changed from dark to light.

The preset files are named as follows: ``$HOME/.config/vdu_controls/Preset_<preset_name>.conf``

Presets are saved in INI-file format for ease of editing.  Each preset file contains a section for each connected
VDU, something similar to the following example::

    [preset]
    icon = /usr/share/icons/breeze/status/16/cloudstatus.svg

    [HP_ZR24w_CNT008]
    brightness = 50
    osd-language = 02

    [LG_HDR_4K_Display2]
    brightness = 13
    audio-speaker-volume = 16
    input-source = 0f

Whe the GUI is used to create a preset file it saves a value for every VDU and every visible control.  A preset
file need not include all VDu's or settings, it can be manually edited to remove VDU's and settings that aren't
desired.

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

        zypper install python38-QtPy
        zypper install ddcutil

Kernel Modules::

        lsmod | grep i2c_dev

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
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import List, Tuple, Mapping, Type

from PyQt5 import QtNetwork
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QRegExp, QPoint, QObject, QEvent, \
    QSettings, QSize
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon, QCursor, QImage, QPainter, QDoubleValidator, QRegExpValidator, \
    QPalette, QGuiApplication, QColor
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
    QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction, QMainWindow, QToolBar, QToolButton, QFileDialog

VDU_CONTROLS_VERSION = '1.7.0'


def proper_name(*args):
    return re.sub(r'[^A-Za-z0-9._-]', '_', '_'.join([arg.strip() for arg in args]))


def translate(source_text: str):
    """For future internationalization - recommended way to do this at this time."""
    return QCoreApplication.translate('vdu_controls', source_text)


ABOUT_TEXT = f"""

<b>vdu_controls version {VDU_CONTROLS_VERSION}</b>
<p>
A virtual control panel for external Visual Display Units. 
<p>
Run vdu_controls --help in a console for help.
<p>
Visit <a href="https://github.com/digitaltrails/vdu_controls">https://github.com/digitaltrails/vdu_controls</a> for 
more details.
<p><p>

<b>vdu_controls Copyright (C) 2021 Michael Hamilton</b>
<p>
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.
<p>
This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.
<p>
You should have received a copy of the GNU General Public License along
with this program. If not, see <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.

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
        last_login_cmd = ["last", "--time-format=iso", f"{os.getlogin()}", "-1"]
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
        result = self.__run__('detect', '--terse')
        display_pattern = re.compile('Display ([0-9]+)')
        monitor_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for display_str in re.split("\n\n", result.stdout.decode('utf-8')):
            display_match = display_pattern.match(display_str)
            if display_match is not None:
                log_info(f"checking {display_str}")
                vdu_id = display_match.group(1)
                monitor_match = monitor_pattern.search(display_str)
                manufacturer, model_name, serial_number = \
                    monitor_match.group(1).split(':') if monitor_match else ['', 'Unknown Model', '']
                if serial_number == '':
                    serial_number = 'Display' + vdu_id
                display_list.append((vdu_id, manufacturer, model_name, serial_number))
            elif len(display_str.strip()) != 0:
                log_warning(f"ignoring {display_str}")
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


class VduGuiSupportedControls:
    """Maps of controls supported by name on the command line and in config files."""
    by_code = {
        '10': VcpCapability('10', 'Brightness', 'C', icon_source=BRIGHTNESS_SVG, enabled=True),
        '12': VcpCapability('12', 'Contrast', 'C', icon_source=CONTRAST_SVG, enabled=True),
        '62': VcpCapability('62', 'Audio volume', 'C', icon_source=VOLUME_SVG),
        '8D': VcpCapability('8D', 'Audio mute', 'SNC', icon_source=VOLUME_SVG),
        '8F': VcpCapability('8F', 'Audio treble', 'C', icon_source=VOLUME_SVG),
        '91': VcpCapability('91', 'Audio bass', 'C', icon_source=VOLUME_SVG),
        '64': VcpCapability('91', 'Audio mic volume', 'C', icon_source=VOLUME_SVG),
        '60': VcpCapability('60', 'Input Source', 'SNC', causes_config_change=True),
        'D6': VcpCapability('D6', 'Power mode', 'SNC', causes_config_change=True),
        'CC': VcpCapability('CC', 'OSD Language', 'SNC'),
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

CONFIG_DIR_PATH = Path.home().joinpath('.config').joinpath('vdu_controls')


def get_config_path(config_name: str) -> Path:
    return CONFIG_DIR_PATH.joinpath(config_name + '.conf')


class VduControlsConfig:
    """
    A vdu_controls config that can be read or written from INI style files by the standard configparser package.
    Includes a method that can fold in values from command line arguments parsed by the standard argparse package.
    """

    def __init__(self, config_name: str, default_enabled_vcp_codes: List = None, include_globals: bool = False) -> None:
        self.config_name = config_name
        self.ini_content = configparser.ConfigParser()
        # augment the configparser with type-info for run-time widget selection (default type is 'boolean')
        self.config_type_map = {
            'enable-vcp-codes': 'csv', 'sleep-multiplier': 'float', 'capabilities-override': 'text'}

        if include_globals:
            self.ini_content['vdu-controls-globals'] = {
                'system-tray-enabled': 'no',
                'splash-screen-enabled': 'yes',
                'warnings-enabled': 'no',
                'debug-enabled': 'no',
                'syslog-enabled': 'no', }

        self.ini_content['vdu-controls-widgets'] = {}
        self.ini_content['ddcutil-parameters'] = {}
        self.ini_content['ddcutil-capabilities'] = {}

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
        log_warning(f"creating new config file {config_path.as_posix()}")
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        with open(config_path, 'w') as config_file:
            self.ini_content.write(config_file)

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


class VduController:
    """
    Holds model+controller specific to an individual VDU including a map of its capabilities. A model object in
    MVC speak.

    The model configuration can optionally be read from an INI-format config file held in $HOME/.config/vdu-control/

    Capabilities are either extracted from ddcutil output or read from the INI-format files.  File read
    capabilities are provided so that the output from "ddcutil --display N capabilities" can be corrected (because
    it is sometimes incorrect due to sloppy implementation by manufacturers). For example, my LG monitor reports
    two Display-Port inputs and it only has one.
    """

    def __init__(self, vdu_id: str, vdu_model_name: str, vdu_serial: str, manufacturer: str,
                 default_config: VduControlsConfig,
                 ddcutil: DdcUtil,
                 ignore_monitor: bool = False, assume_standard_controls: bool = False) -> None:
        self.vdu_id = vdu_id
        self.model_name = vdu_model_name
        self.serial = vdu_serial
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.sleep_multiplier = None
        self.enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        self.vdu_model_and_serial_id = proper_name(vdu_model_name.strip(), vdu_serial.strip())
        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text = None
        self.config = None
        for config_name in (self.vdu_model_and_serial_id, self.vdu_model_id):
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
            self.config = VduControlsConfig(self.vdu_model_and_serial_id,
                                            default_enabled_vcp_codes=self.enabled_vcp_codes)
            self.config.set_capabilities_alt_text(self.capabilities_text)
        self.config.restrict_to_actual_capabilities(self.capabilities)

    def write_template_config_files(self) -> None:
        """Write template config files to $HOME/.config/vdu_controls/"""
        for config_name in (self.vdu_model_and_serial_id, self.vdu_model_id):
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
            alert = QMessageBox()
            alert.setText(translate("Failed to obtain monitor {} vcp_code {}").format(self.vdu_id, vcp_code))
            alert.setInformativeText(
                "Problem communicating with monitor {} {}. Controls may be incorrect.".format(self.vdu_id, str(e)))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()
            return '0', '0'

    def set_attribute(self, vcp_code: str, value: str) -> None:
        self.ddcutil.set_attribute(self.vdu_id, vcp_code, value, sleep_multiplier=self.sleep_multiplier)

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


class SettingsEditor(QDialog, DialogSingletonMixin):
    """
    Application Settings Editor, edits a default global settings file, and a settings file for each VDU.
    The files are in INI format.  Internally the settings are VduControlsConfig wrappers around
    the standard class configparser.ConfigParser.
    """

    @staticmethod
    def invoke(default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig]) -> None:
        if SettingsEditor.exists():
            SettingsEditor.show_existing_dialog()
        else:
            SettingsEditor(default_config, vdu_config_list)

    def __init__(self, default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig]) -> None:
        super().__init__()
        self.setWindowTitle(translate('Settings'))
        self.setMinimumWidth(1024)
        layout = QVBoxLayout()
        self.setLayout(layout)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        self.editors = []
        for vdu_config in [default_config, ] + vdu_config_list:
            tab = self.SettingsEditorTab(self, vdu_config)
            tabs.addTab(tab, vdu_config.get_config_name())
            self.editors.append(tab)
        # .show() is non-modal, .exec() is modal
        self.make_visible()

    def closeEvent(self, event) -> None:
        something_changed = False
        for editor in self.editors:
            editor.save()
            something_changed = editor.has_made_changes or something_changed
        # if one of the edits has saved some changes, we need to restart to pick them up - crude, but effective.
        if something_changed:
            restart_message = QMessageBox()
            restart_message.setText(translate("vdu_controls will now reset and use the new settings."))
            restart_message.setIcon(QMessageBox.Warning)
            restart_message.setStandardButtons(QMessageBox.Ok)
            restart_message.exec()
            QCoreApplication.exit(EXIT_CODE_FOR_RESTART)
        # Must call the super closeEvent to ensure we unregister as a singleton dialog.
        super().closeEvent(event)

    class SettingsEditorTab(QWidget):
        """A tab corresponding to a settings file, generates UI widgets for each tab based on what's in the config. """

        def __init__(self, parent: QWidget, vdu_config: VduControlsConfig) -> None:
            super().__init__()
            editor_layout = QVBoxLayout()
            self.has_made_changes = False
            self.setLayout(editor_layout)
            self.config_path = get_config_path(vdu_config.config_name)
            self.ini_before = vdu_config.ini_content
            copy = pickle.dumps(self.ini_before)
            self.ini_editable = pickle.loads(copy)
            for section in self.ini_editable:
                if section == 'DEFAULT':
                    continue
                editor_layout.addWidget(QLabel('<b>' + section.replace('-', ' ') + '</b>'))
                booleans_panel = QWidget()
                booleans_grid = QGridLayout()
                booleans_panel.setLayout(booleans_grid)
                editor_layout.addWidget(booleans_panel)
                n = 0
                for option in self.ini_editable[section]:
                    data_type = vdu_config.get_config_type(section, option)
                    if data_type == 'boolean':
                        booleans_grid.addWidget(
                            SettingsEditor.SettingsEditorBooleanWidget(
                                self.ini_editable, option, section), n // 3, n % 3)
                        n += 1
                    elif data_type == 'float':
                        editor_layout.addWidget(
                            SettingsEditor.SettingsEditorFloatWidget(self.ini_editable, option, section))
                    elif data_type == 'text':
                        editor_layout.addWidget(
                            SettingsEditor.SettingsEditorTextEditorWidget(self.ini_editable, option, section))
                    elif data_type == 'csv':
                        editor_layout.addWidget(
                            SettingsEditor.SettingsEditorCsvWidget(self.ini_editable, option, section))

            def save_clicked() -> None:
                if self.is_unsaved():
                    self.save(cancel=QMessageBox.Cancel)
                else:
                    save_message = QMessageBox()
                    message = translate('No unsaved changes for {}.').format(vdu_config.config_name)
                    save_message.setText(message)
                    save_message.setIcon(QMessageBox.Critical)
                    save_message.setStandardButtons(QMessageBox.Ok)
                    save_message.exec()

            buttons_widget = QWidget()
            button_layout = QHBoxLayout()
            buttons_widget.setLayout(button_layout)
            save_button = QPushButton(translate("Save {}").format(vdu_config.config_name))
            save_button.clicked.connect(save_clicked)
            button_layout.addWidget(save_button)
            quit_button = QPushButton(translate("Close"))
            quit_button.clicked.connect(parent.close)
            button_layout.addWidget(quit_button)
            editor_layout.addWidget(buttons_widget)

        def save(self, cancel: int = QMessageBox.Close) -> None:
            if not self.config_path.parent.is_dir():
                os.makedirs(self.config_path.parent)
            if self.is_unsaved():
                save_message = QMessageBox()
                message = translate('Overwrite existing {}?' if self.config_path.exists() else "Create new {}"
                                    ).format(self.config_path.as_posix())
                save_message.setText(message)
                save_message.setIcon(QMessageBox.Question)
                save_message.setStandardButtons(QMessageBox.Save | cancel)
                rc = save_message.exec()
                if rc == QMessageBox.Save:
                    with open(self.config_path, 'w') as config_file:
                        self.ini_editable.write(config_file)
                        copy = pickle.dumps(self.ini_editable)
                        self.ini_before = pickle.loads(copy)
                        self.has_made_changes = True

        def is_unsaved(self) -> bool:
            return pickle.dumps(self.ini_before) != pickle.dumps(self.ini_editable) \
                   or not self.config_path.exists()

    class SettingsEditorBooleanWidget(QWidget):
        def __init__(self, ini_editable: configparser.ConfigParser, option: str, section: str) -> None:
            super().__init__()
            layout = QHBoxLayout()
            self.setLayout(layout)
            checkbox = QCheckBox(option.replace('-', ' '))
            checkbox.setChecked(ini_editable.getboolean(section, option))

            def toggled(is_checked: bool) -> None:
                # print(section, option, is_checked)
                ini_editable[section][option] = 'yes' if is_checked else 'no'

            checkbox.toggled.connect(toggled)
            layout.addWidget(checkbox)

    class SettingsEditorFloatWidget(QWidget):
        def __init__(self, ini_editable: configparser.ConfigParser, option: str, section: str) -> None:
            super().__init__()
            layout = QVBoxLayout()
            self.setLayout(layout)
            text_label = QLabel(option.replace('-', ' '))
            layout.addWidget(text_label)
            text_input = QLineEdit()
            text_input.setMaximumWidth(100)
            text_input.setMaxLength(4)
            text_validator = QDoubleValidator()
            text_validator.setRange(0.1, int(3.0), 4)
            text_input.setValidator(text_validator)
            text_input.setText(ini_editable[section][option])

            def editing_finished() -> None:
                # print(section, option, text_input.text())
                ini_editable[section][option] = str(text_input.text())

            text_input.editingFinished.connect(editing_finished)
            layout.addWidget(text_input)

    class SettingsEditorCsvWidget(QWidget):
        def __init__(self, ini_editable: configparser.ConfigParser, option: str, section: str) -> None:
            super().__init__()
            layout = QVBoxLayout()
            self.setLayout(layout)
            text_label = QLabel(option.replace('-', ' '))
            layout.addWidget(text_label)
            text_input = QLineEdit()
            text_input.setMaximumWidth(1000)
            text_input.setMaxLength(500)
            # TODO - should probably also allow spaces as well as commas, but the regexp is getting a bit tricky?
            # Validator matches CSV of two digit hex or the empty string.
            validator = QRegExpValidator(QRegExp(r"^([0-9a-fA-F]{2}([ \t]*,[ \t]*[0-9a-fA-F]{2})*)|$"))
            text_input.setValidator(validator)
            text_input.setText(ini_editable[section][option])

            def editing_finished() -> None:
                # print(section, option, text_input.text())
                ini_editable[section][option] = str(text_input.text())

            def input_rejected() -> None:
                text_input.setStyleSheet("QLineEdit { color : red; }")

            def text_edited() -> None:
                text_input.setStyleSheet("QLineEdit { color : black; }")

            text_input.editingFinished.connect(editing_finished)
            text_input.inputRejected.connect(input_rejected)
            text_input.textEdited.connect(text_edited)
            layout.addWidget(text_input)

    class SettingsEditorTextEditorWidget(QWidget):
        def __init__(self, ini_editable: configparser.ConfigParser, option: str, section: str) -> None:
            super().__init__()
            layout = QVBoxLayout()
            self.setLayout(layout)
            text_label = QLabel(option.replace('-', ' '))
            layout.addWidget(text_label)
            text_editor = QPlainTextEdit(ini_editable[section][option])

            def text_changed() -> None:
                # print(section, option, text_editor.toPlainText())
                ini_editable[section][option] = text_editor.toPlainText().replace("%", "%%")

            text_editor.textChanged.connect(text_changed)
            layout.addWidget(text_editor)


def restart_due_to_config_change() -> None:
    """
    Force a restart of the application.

    To be invoked when part of the GUI executes a VCP command that changes the number of connected monitors or
    when the GUI detects the number of monitors has changes.
    """
    alert = QMessageBox()
    alert.setText(translate('The physical monitor configuration has changed. A restart is required.'))
    alert.setInformativeText(translate('Dismiss this message to automatically restart.'))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QCoreApplication.exit(EXIT_CODE_FOR_RESTART)


class VduControlSlider(QWidget):
    """
    GUI control for a DDC continuously variable attribute.

    A compound widget with icon, slider, and text-field.  This is a duck-typed GUI control widget (could inherit
    from an abstract type if we wanted to get formal about it).
    """

    def __init__(self, vdu_model: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__()

        self.vdu_model = vdu_model
        self.vcp_capability = vcp_capability
        self.current_value = self.max_value = None
        self.refresh_data()

        layout = QHBoxLayout()
        self.setLayout(layout)
        self.svg_icon = None

        if vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                VDU_SUPPORTED_CONTROLS.by_code[vcp_capability.vcp_code].icon_source is not None:
            svg_icon = QSvgWidget()
            svg_icon.load(handle_theme(VDU_SUPPORTED_CONTROLS.by_code[vcp_capability.vcp_code].icon_source))
            svg_icon.setFixedSize(50, 50)
            svg_icon.setToolTip(translate(vcp_capability.name))
            self.svg_icon = svg_icon
            layout.addWidget(svg_icon)
        else:
            label = QLabel()
            label.setText(vcp_capability.name)
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
            try:
                self.vdu_model.set_attribute(self.vcp_capability.vcp_code, self.current_value)
                if self.vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                        VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].causes_config_change:
                    # The VCP command has turned one off a VDU or changed what it is connected to.
                    # VDU ID's will now be out of whack - restart the GUI.
                    restart_due_to_config_change()
            except subprocess.SubprocessError:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText(translate("Failed to communicate with {}").format(self.vdu_model.get_vdu_description()))
                msg.setInformativeText(translate('Is the monitor switched off?<br>Is --sleep-multiplier set too low?'))
                msg.exec()

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
                log_warning(f"Non integer values for slider {self.vdu_model.vdu_model_and_serial_id} "
                            f"{self.vcp_capability.name} = {new_value} (max={max_value})")
                log_warning("have to repeat vdu_model.get_attribute - maybe --sleep-multiplier is set too low?")
                sleep_secs = 3.0
                log_warning(f"will try again in {sleep_secs} seconds in case this a transient error due to session "
                            f"initialisation.")
                time.sleep(sleep_secs)
                continue
        # Something is wrong with ddcutils - pass the buck
        raise ValueError(
            f"Non integer values for slider {self.vdu_model.vdu_model_and_serial_id} {self.vcp_capability.name} = {new_value} (max={max_value})")

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

    def __init__(self, vdu_model: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the combobox control and initialize its values from the VDU."""
        super().__init__()

        self.vdu_model = vdu_model
        self.vcp_capability = vcp_capability
        self.current_value = vdu_model.get_attribute(vcp_capability.vcp_code)[0]

        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel()
        label.setText(vcp_capability.name)
        layout.addWidget(label)

        self.combo_box = combo_box = QComboBox()
        layout.addWidget(combo_box)

        self.keys = []
        for value, desc in self.vcp_capability.values:
            self.keys.append(value)
            combo_box.addItem(desc, value)

        self.validate_value()
        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))

        def index_changed(index: int) -> None:
            self.current_value = self.combo_box.currentData()
            self.validate_value()
            try:
                self.vdu_model.set_attribute(self.vcp_capability.vcp_code, self.current_value)
                if self.vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                        VDU_SUPPORTED_CONTROLS.by_code[self.vcp_capability.vcp_code].causes_config_change:
                    restart_due_to_config_change()
            except subprocess.SubprocessError:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText(translate("Failed to communicate with {}").format(self.vdu_model.get_vdu_description()))
                msg.setInformativeText(translate('Is the monitor switched off?<br>Is --sleep-multiplier set too low?'))
                msg.exec()

        combo_box.currentIndexChanged.connect(index_changed)

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
            alert = QMessageBox()
            alert.setText(
                translate("Display {vnum} {vdesc} feature {code} '({cdesc})' has an undefined value '{value}'. "
                          "Valid values are {valid}.").format(
                    vdesc=self.vdu_model.get_vdu_description(),
                    vnum=self.vdu_model.vdu_id,
                    code=self.vcp_capability.vcp_code,
                    cdesc=self.vcp_capability.name,
                    value=self.current_value,
                    valid=self.keys))
            alert.setInformativeText(
                translate('If you want to extend the set of permitted values, you can edit the metadata '
                          'for {} in the settings panel.  For more details see the man page concerning '
                          'VDU/VDU-model config files.').format(self.vdu_model.get_vdu_description()))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()


class VduControlPanel(QWidget):
    """
    Widget that contains all the controls for a single VDU (monitor/display).

    The widget maintains a list of GUI "controls" that are duck-typed and will have refresh_data() and refresh_view()
    methods.
    """

    def __init__(self, vdu_model: VduController, warnings: bool) -> None:
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        # label.setStyleSheet("font-weight: bold");
        label.setText(translate('Monitor {}: {}').format(vdu_model.vdu_id, vdu_model.get_vdu_description()))
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
                        alert = QMessageBox()
                        alert.setText(valueError.args[0])
                        alert.setInformativeText(
                            translate('If you want to extend the set of permitted values, see the man page concerning '
                                      'VDU/VDU-model config files .').format(capability.vcp_code, capability.name))
                        alert.setIcon(QMessageBox.Critical)
                        alert.exec()
                else:
                    raise TypeError(f'No GUI support for VCP type {capability.vcp_type} for vcp_code {vcp_code}')
                if control is not None:
                    layout.addWidget(control)
                    self.vcp_controls.append(control)
            elif warnings:
                missing_vcp = VDU_SUPPORTED_CONTROLS.by_code[
                    vcp_code].name if vcp_code in VDU_SUPPORTED_CONTROLS.by_code else vcp_code
                alert = QMessageBox()
                alert.setText(
                    translate('Monitor {} lacks a VCP control for {}.').format(
                        vdu_model.get_vdu_description(), translate(missing_vcp)))
                alert.setInformativeText(translate('No read/write ability for vcp_code {}.').format(vcp_code))
                alert.setIcon(QMessageBox.Warning)
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

    def copy_state(self, preset_ini: configparser.ConfigParser) -> None:
        vdu_section = self.vdu_model.vdu_model_and_serial_id
        preset_ini[vdu_section] = {}
        for control in self.vcp_controls:
            preset_ini[vdu_section][control.vcp_capability.property_name()] = control.current_value

    def restore_state(self, preset_ini: configparser.ConfigParser) -> None:
        vdu_section = self.vdu_model.vdu_model_and_serial_id
        for control in self.vcp_controls:
            if control.vcp_capability.property_name() in preset_ini[vdu_section]:
                control.current_value = preset_ini[vdu_section][control.vcp_capability.property_name()]
        self.refresh_view()

    def is_preset_active(self, preset_ini: configparser.ConfigParser) -> bool:
        vdu_section = self.vdu_model.vdu_model_and_serial_id
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
        self.preset_ini = configparser.ConfigParser()

    def get_icon_path(self) -> Path:
        if self.preset_ini.has_section("preset"):
            return Path(self.preset_ini.get("preset", "icon", fallback=None))

    def set_icon_path(self, icon_path: Path):
        if icon_path:
            if not self.preset_ini.has_section("preset"):
                self.preset_ini.add_section("preset")
            self.preset_ini.set("preset", "icon", icon_path.as_posix())

    def create_icon(self) -> QIcon:
        # icon = create_icon_from_path(self.get_icon_path()) \
        #    if self.get_icon_path() else self.style().standardIcon(PresetsDialog.no_icon_icon_number)
        icon_path = self.get_icon_path()
        if icon_path and icon_path.exists():
            return create_icon_from_path(icon_path)
        else:
            return create_icon_from_text(f"({self.name[0]})")

    def load(self) -> configparser.ConfigParser:
        if self.path.exists():
            log_info(f"reading preset file '{self.path.as_posix()}'")
            preset_text = Path(self.path).read_text()
            preset_ini = configparser.ConfigParser()
            preset_ini.read_string(preset_text)
        else:
            preset_ini = configparser.ConfigParser()
        self.preset_ini = preset_ini
        return self.preset_ini

    def save(self):
        log_info(f"saving preset file '{self.path.as_posix()}'")
        if not self.path.parent.is_dir():
            os.makedirs(self.path.parent)
        with open(self.path, 'w') as preset_file:
            self.preset_ini.write(preset_file)

    def delete(self):
        log_info(f"deleting preset file '{self.path.as_posix()}'")
        if self.path.exists():
            os.remove(self.path.as_posix())


class ContextMenu(QMenu):

    def __init__(self,
                 main_window,
                 main_window_action,
                 about_action, help_action, chart_action, settings_action,
                 presets_action, refresh_action, quit_action) -> None:
        super().__init__()
        self.main_window = main_window
        if main_window_action is not None:
            self.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon),
                           translate('Control Panel'),
                           main_window_action)
            self.addSeparator()
        self.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon),
                       translate('Presets'),
                       presets_action)
        self.presets_separator = self.addSeparator()

        self.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon),
                       translate('Grey Scale'),
                       chart_action)
        self.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon),
                       translate('Settings'),
                       settings_action)
        self.addAction(self.style().standardIcon(QStyle.SP_BrowserReload),
                       translate('Refresh'),
                       refresh_action)
        self.addAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation),
                       translate('About'),
                       about_action)
        self.addAction(self.style().standardIcon(QStyle.SP_DialogHelpButton),
                       translate('Help'),
                       help_action)
        self.addSeparator()
        self.addAction(self.style().standardIcon(QStyle.SP_DialogCloseButton),
                       translate('Quit'),
                       quit_action)

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

    def get_preset_menu_item(self, name: str) -> QAction:
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
        self.menu_button = QToolButton(self)
        self.menu_button.setIcon(create_icon_from_svg_bytes(MENU_ICON_SOURCE))
        self.progress_bar = QProgressBar(self)
        # Disable text percentage label on the spinner progress-bar
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setDisabled(True)
        self.addWidget(self.progress_bar)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
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


class VduControlsMainPanel(QWidget):
    """GUI for detected VDU's, it will construct and contain a control panel for each VDU."""
    refresh_finished = pyqtSignal()

    def __init__(self,
                 default_config: VduControlsConfig,
                 detect_vdu_hook: callable,
                 app_context_menu: ContextMenu,
                 session_startup: bool) -> None:
        super().__init__()
        self.setObjectName("vdu_controls_main_panel")
        layout = QVBoxLayout()
        self.non_standard_enabled = None
        ddcutil_common_args = ['--force', ] if self.is_non_standard_enabled() else []
        self.ddcutil = DdcUtil(debug=default_config.is_debug_enabled(), common_args=ddcutil_common_args,
                               default_sleep_multiplier=default_config.get_sleep_multiplier())
        self.vdu_control_panels = []
        self.warnings = default_config.are_warnings_enabled()
        self.previously_detected_vdus = []
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
        self.previously_detected_vdus = self.detected_vdus
        self.context_menu = app_context_menu
        app_context_menu.refresh_preset_menu()

        self.vdu_controllers = []
        for vdu_id, manufacturer, vdu_model_name, vdu_serial in self.detected_vdus:
            controller = None
            while True:
                try:
                    controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, default_config,
                                               self.ddcutil)
                except Exception as e:
                    # Catch any kind of parse related error
                    alert = QMessageBox()
                    alert.setText(
                        translate('Failed to obtain capabilities for monitor {} {} {}.').format(vdu_id,
                                                                                                vdu_model_name,
                                                                                                vdu_serial))
                    alert.setInformativeText(translate(
                        'Cannot automatically configure this monitor.'
                        '\n You can choose to:'
                        '\n 1: Retry obtaining the capabilities.'
                        '\n 2: Ignore this monitor.'
                        '\n 3: Apply standard brightness and contrast controls.'))
                    alert.setIcon(QMessageBox.Critical)
                    alert.setStandardButtons(QMessageBox.Ignore | QMessageBox.Apply | QMessageBox.Retry)
                    choice = alert.exec()
                    if choice == QMessageBox.Ignore:
                        controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, default_config,
                                                   self.ddcutil, ignore_monitor=True)
                        controller.write_template_config_files()
                        warn = QMessageBox()
                        warn.setIcon(QMessageBox.Warning)
                        warn.setText(translate('Ignoring {} monitor.').format(vdu_model_name))
                        warn.setInformativeText(
                            translate('Wrote {} config files to {}.').format(vdu_model_name, CONFIG_DIR_PATH))
                        warn.exec()
                    if choice == QMessageBox.Apply:
                        controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, default_config,
                                                   self.ddcutil, assume_standard_controls=True)
                        controller.write_template_config_files()
                        warn = QMessageBox()
                        warn.setIcon(QMessageBox.Warning)
                        warn.setText(
                            translate('Assuming {} has brightness and contrast controls.').format(vdu_model_name,
                                                                                                  CONFIG_DIR_PATH))
                        warn.setInformativeText(
                            translate('Wrote {} config files to {}.').format(vdu_model_name, CONFIG_DIR_PATH) +
                            translate('\nPlease check these files and edit or remove them if they '
                                      'cause further issues.'))
                        warn.exec()
                    if choice == QMessageBox.Retry:
                        continue
                break
            if controller is not None:
                self.vdu_controllers.append(controller)
                if detect_vdu_hook is not None:
                    detect_vdu_hook(controller)
                vdu_control_panel = VduControlPanel(controller, self.warnings)
                if vdu_control_panel.number_of_controls() != 0:
                    self.vdu_control_panels.append(vdu_control_panel)
                    layout.addWidget(vdu_control_panel)
                elif self.warnings:
                    alert = QMessageBox()
                    alert.setText(
                        translate('Monitor {} {} lacks any accessible controls.').format(controller.vdu_id,
                                                                                         controller.get_vdu_description()))
                    alert.setInformativeText(translate('The monitor will be omitted from the control panel.'))
                    alert.setIcon(QMessageBox.Warning)
                    alert.exec()

        if len(self.vdu_control_panels) == 0:
            alert = QMessageBox()
            alert.setText(translate('No controllable monitors found, exiting.'))
            alert.setInformativeText(translate(
                '''Run vdu_controls --debug in a console and check for additional messages.\
                Check the requirements for the ddcutil command.'''))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()
            sys.exit()

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

        self.setLayout(layout)

        # if len(QCameraInfo().availableCameras()) > 0:
        #
        #     def check_light_level_func():
        #         camera_info = QCameraInfo()
        #         print("cams=", camera_info.availableCameras())
        #         if len(camera_info.availableCameras()) > 0:
        #             camera = QCamera(camera_info.availableCameras()[0])
        #             image_capture = QCameraImageCapture(camera)
        #             if image_capture.isCaptureDestinationSupported(QCameraImageCapture.CaptureToBuffer):
        #                 image_capture.setCaptureDestination(QCameraImageCapture.CaptureToBuffer)
        #
        #
        #                 def capture_func(i, image):
        #                     print(i, image)
        #
        #                 image_capture.imageAvailable.connect(capture_func)
        #
        #                 def capture_error(err,strerr):
        #                     print("error", err, strerr)
        #
        #                 image_capture.error.connect(capture_error)
        #
        #                 viewfinder = QCameraViewfinder()
        #                 viewfinder.show()
        #
        #                 camera.setViewfinder(viewfinder)
        #                 camera.setCaptureMode(QCamera.CaptureStillImage)
        #                 camera.start()
        #                 camera.searchAndLock()
        #                 image_capture.capture()
        #                 camera.unlock()
        #
        #     self.timer = QTimer(self)
        #     self.timer.timeout.connect(check_light_level_func)
        #     self.timer.start(10000);

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
            # The number of VDU's has changed, vdu_id's will no longer match, throw a wobbly
            restart_due_to_config_change()
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
                    if text == DANGER_AGREEMENT_NON_STANDARD_VCP_CODES:
                        log_warning("\n"
                                    "Non standard features may be enabled for write.\n"
                                    "ENABLING NON_STANDARD FEATURES COULD DAMAGE YOUR HARDWARE.\n"
                                    "To disable non-standard features delete the file {}.\n"
                                    "{}".format(path, DANGER_AGREEMENT_NON_STANDARD_VCP_CODES))
                        self.non_standard_enabled = True
        return self.non_standard_enabled


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
        for path_str in glob.glob(CONFIG_DIR_PATH.joinpath("Preset_*.conf").as_posix()):
            preset_name = os.path.splitext(os.path.basename(path_str))[0].replace('Preset_', '').replace('_', ' ')
            if preset_name not in self.presets:
                preset = Preset(preset_name)
                preset.load()
                self.presets[preset_name] = preset
            presets_still_present.append(preset_name)
        for preset_name in self.presets.keys():
            if preset_name not in presets_still_present:
                del self.presets[preset_name]
        return self.presets

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
                    if section == control_panel.vdu_model.vdu_model_and_serial_id:
                        if not control_panel.is_preset_active(preset.preset_ini):
                            return False
        return True

    def delete_preset(self, preset: Preset) -> None:
        preset.delete()
        del self.presets[preset.name]

    def get_preset(self, preset_number: int) -> Preset | None:
        presets = self.find_presets()
        if preset_number < len(presets):
            return presets.values()[preset_number]
        return None


class PresetWidget(QWidget):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class PresetActivationButton(QPushButton):
    def __init__(self, preset: Preset):
        super().__init__()
        self.preset = preset
        self.setIcon(preset.create_icon())
        self.setText(preset.name)
        self.setToolTip('Activate this preset.')

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
        self.setIcon(self.style().standardIcon(PresetsDialog.no_icon_icon_number))
        self.setToolTip(translate('Choose a preset icon.'))
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.setAutoDefault(False)
        self.last_selected_icon_path = None
        self.last_icon_dir = Path("/usr/share/icons")
        if not self.last_icon_dir.exists():
            self.last_icon_dir = Path.home()
        self.preset = None
        self.clicked.connect(self.choose_preset_icon_action)

    def set_preset(self, preset: Preset|None):
        self.preset = preset
        self.last_selected_icon_path = self.preset.get_icon_path() if preset else None
        if self.last_selected_icon_path:
            self.last_icon_dir = self.last_selected_icon_path.parent
        self.update_icon()

    def choose_preset_icon_action(self) -> None:
        icon_file = QFileDialog.getOpenFileName(self, translate('Icon SVG or PNG file'),
                                                self.last_icon_dir.as_posix(),
                                                translate('SVG or PNG (*.svg *.png)'))
        self.last_selected_icon_path = Path(icon_file[0]) if icon_file[0] != '' else None
        self.update_icon()

    def update_icon(self):
        if self.last_selected_icon_path:
            self.setIcon(create_icon_from_path(self.last_selected_icon_path))
        elif self.preset:
            self.setIcon(self.preset.create_icon())
        else:
            self.setIcon(self.style().standardIcon(PresetsDialog.no_icon_icon_number))

    def event(self, event: QEvent) -> bool:
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.update_icon()
        event.accept()
        return True


class PresetsDialog(QDialog, DialogSingletonMixin):
    """A dialog for creating/updating/removing presets."""

    no_icon_icon_number = QStyle.SP_ComputerIcon

    @staticmethod
    def invoke(main_window: 'MainWindow') -> None:
        if PresetsDialog.exists():
            PresetsDialog.show_existing_dialog()
        else:
            PresetsDialog(main_window)

    def __init__(self, main_window: 'MainWindow') -> None:
        super().__init__()
        self.setWindowTitle(translate('Presets'))
        self.main_window = main_window
        self.setMinimumWidth(512)
        layout = QVBoxLayout()
        self.setLayout(layout)
        presets_panel = QWidget()
        self.presets_panel = presets_panel
        presets_layout = QVBoxLayout()
        presets_panel.setLayout(presets_layout)
        layout.addWidget(presets_panel)
        button_box = QWidget()
        button_layout = QHBoxLayout()
        button_box.setLayout(button_layout)
        main_window.app_context_menu.refresh_preset_menu()

        def restore_preset(preset: Preset) -> None:
            self.main_window.restore_preset(preset)

        def save_preset(preset: Preset) -> None:
            preset_path = get_config_path(proper_name('Preset', preset.name))
            if preset_path.exists():
                save_message = QMessageBox()
                message = translate('Overwrite existing {}?').format(preset_path.as_posix())
                save_message.setText(message)
                save_message.setIcon(QMessageBox.Question)
                save_message.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                rc = save_message.exec()
                if rc == QMessageBox.Cancel:
                    return
            self.main_window.save_preset(preset)

        def delete_preset(preset: Preset, target_widget: QWidget = None) -> None:
            log_info(f"delete preset {preset.name}")
            delete_confirmation = QMessageBox()
            message = translate('Delete {}?').format(preset.name)
            delete_confirmation.setText(message)
            delete_confirmation.setIcon(QMessageBox.Question)
            delete_confirmation.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            rc = delete_confirmation.exec()
            if rc == QMessageBox.Cancel:
                return
            self.main_window.delete_preset(preset)
            presets_layout.removeWidget(target_widget)
            target_widget.deleteLater()
            presets_panel.adjustSize()
            presets_panel.repaint()

        def edit_preset(preset: Preset) -> None:
            self.main_window.restore_preset(preset)
            add_preset_name_edit.setText(preset.name)
            choose_icon_button.set_preset(preset)
            icon_path = preset.get_icon_path()

        for preset_def in self.main_window.preset_controller.find_presets().values():
            preset_widget = self.create_preset_widget(
                preset_def,
                restore_action=restore_preset,
                save_action=save_preset,
                delete_action=delete_preset,
                edit_action=edit_preset)
            presets_layout.addWidget(preset_widget)

        add_preset_widget = QWidget()
        add_preset_layout = QHBoxLayout()
        add_preset_widget.setLayout(add_preset_layout)
        add_preset_widget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))

        choose_icon_button = PresetChooseIconButton()
        add_preset_layout.addWidget(choose_icon_button)

        add_preset_name_edit = QLineEdit()
        add_preset_name_edit.setToolTip(translate('Enter a new preset name.'))
        add_preset_name_edit.setClearButtonEnabled(True)
        add_preset_layout.addWidget(add_preset_name_edit)

        add_button = QPushButton()  # translate('Add'))  # QPushButton(' \u2003')
        add_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
        add_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        # add_button.setStyleSheet('QPushButton { border: none; margin: 0px; padding: 0px;}')
        add_button.setFlat(True)
        add_button.setToolTip(translate('Save current VDU settings to a new preset.'))
        add_preset_layout.addWidget(add_button)

        def add_preset() -> None:
            new_name = add_preset_name_edit.text().strip()
            if new_name == '':
                return
            existing_preset_widget = self.find_preset_widget(new_name)
            if existing_preset_widget:
                save_message = QMessageBox()
                message = translate("Replace existing '{}' preset?").format(new_name)
                save_message.setText(message)
                save_message.setIcon(QMessageBox.Question)
                save_message.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                if save_message.exec() == QMessageBox.Cancel:
                    return
            if choose_icon_button.last_selected_icon_path is None:
                save_message = QMessageBox()
                message = translate("No icon has been selected for '{}' preset?").format(new_name)
                save_message.setText(message)
                save_message.setIcon(QMessageBox.Question)
                save_message.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                if save_message.exec() == QMessageBox.Cancel:
                    return
            new_preset = Preset(new_name)
            new_preset.set_icon_path(choose_icon_button.last_selected_icon_path)
            self.main_window.save_preset(new_preset)
            new_preset_widget = self.create_preset_widget(
                new_preset,
                restore_action=restore_preset,
                save_action=save_preset,
                delete_action=delete_preset,
                edit_action=edit_preset)
            if existing_preset_widget:
                presets_layout.replaceWidget(existing_preset_widget, new_preset_widget)
                # The deleteLater removes the widget from the tree so that it is no longer findable and can be freed.
                existing_preset_widget.deleteLater()
                self.make_visible()
            else:
                presets_layout.addWidget(new_preset_widget)
            add_preset_name_edit.setText('')
            choose_icon_button.set_preset(None)
            main_window.display_active_preset_info(None)

        add_button.clicked.connect(add_preset)

        layout.addWidget(add_preset_widget)

        close_button = QPushButton(translate('close'))
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addWidget(button_box)
        # .show() is non-modal, .exec() is modal
        self.make_visible()

    def find_preset_widget(self, name) -> PresetWidget | None:
        for w in self.presets_panel.children():
            if isinstance(w, PresetWidget):
                if w.name == name:
                    return w
        return None

    def create_preset_widget(self, preset: Preset, restore_action=None, save_action=None, delete_action=None,
                             edit_action=None) -> PresetWidget:
        preset_widget = PresetWidget(preset.name)
        line_layout = QHBoxLayout()
        line_layout.setSpacing(0)
        preset_widget.setLayout(line_layout)

        preset_name_button = PresetActivationButton(preset)

        line_layout.addWidget(preset_name_button)
        preset_name_button.clicked.connect(partial(restore_action, preset=preset))
        preset_name_button.setAutoDefault(False)

        edit_button = QPushButton()
        edit_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        edit_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        edit_button.setFlat(True)
        edit_button.setToolTip(translate('Edit the preset name and icon.'))
        line_layout.addWidget(edit_button)
        edit_button.clicked.connect(partial(edit_action, preset=preset))
        edit_button.setAutoDefault(False)

        save_button = QPushButton()
        save_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
        save_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        save_button.setFlat(True)
        save_button.setContentsMargins(0, 0, 0, 0)
        save_button.setToolTip(translate('Save the current VDU settings to this preset.'))
        line_layout.addWidget(save_button)
        save_button.clicked.connect(partial(save_action, preset=preset))
        save_button.setAutoDefault(False)

        delete_button = QPushButton()
        delete_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        delete_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        delete_button.setFlat(True)
        delete_button.setToolTip('Delete this preset.')
        line_layout.addWidget(delete_button)
        delete_button.clicked.connect(partial(delete_action, preset=preset, target_widget=preset_widget))
        delete_button.setAutoDefault(False)

        return preset_widget

    def event(self, event: QEvent) -> bool:
        super().event(event)
        # PalletChange happens after the new style sheet is in use.
        if event.type() == QEvent.PaletteChange:
            self.repaint()
        event.accept()
        return True


def exception_handler(e_type, e_value, e_traceback):
    """Overarching error handler in case something unexpected happens."""
    log_error("\n" + ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    alert = QMessageBox()
    alert.setText(translate('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))))
    alert.setInformativeText(translate('Is --sleep-multiplier set too low?') +
                             '<br>_______________________________________________________<br>')
    alert.setDetailedText(
        translate('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback))))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QApplication.quit()


def handle_theme(svg_str: bytes) -> bytes:
    if is_dark_theme():
        svg_str = svg_str.replace(SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR)
    return svg_str


def create_pixmap_from_svg_bytes(svg_bytes: bytes):
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    renderer = QSvgRenderer(handle_theme(svg_bytes))
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


def create_icon_from_svg_bytes(svg_bytes: bytes):
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    return QIcon(create_pixmap_from_svg_bytes(svg_bytes))


def create_icon_from_path(path: Path):
    if path.exists():
        if path.suffix == '.svg':
            with open(path, 'rb') as icon_file:
                icon_bytes = icon_file.read()
                return create_icon_from_svg_bytes(icon_bytes)
        if path.suffix == '.png':
            return QIcon(path.as_posix())
    else:
        # Copes with the case where the path has been deleted.
        return QStyle.standardIcon(QStyle.SP_MessageBoxQuestion)
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
            GenericName=VDU controls
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
        self.setWindowTitle(translate('Grey Scale Reference'))
        self.setModal(False)
        svg_widget = QSvgWidget()
        svg_widget.renderer().load(GREY_SCALE_SVG)
        svg_widget.setMinimumWidth(600)
        svg_widget.setMinimumHeight(400)
        svg_widget.setToolTip(translate(
            'Grey Scale Reference for VDU adjustment.\n\n'
            'Set contrast toward the maximum (for HDR monitors\n'
            'try something lower such as 70%) and adjust brightness\n'
            'until as many rectangles as possible can be perceived.\n\n'
            'Use the content-menu to create additional charts and\n'
            'drag them onto each display.\n\nThis chart is resizable. '))
        layout.addWidget(svg_widget)
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
        self.setWindowTitle(translate('About'))
        self.setTextFormat(Qt.AutoText)
        self.setText(translate('About vdu_controls'))
        self.setInformativeText(translate(ABOUT_TEXT))
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
        self.setWindowTitle(translate('Help'))
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setMarkdown(__doc__)
        layout.addWidget(markdown_view)
        self.setLayout(layout)
        # TODO maybe compute a minimum from the actual screen size
        self.setMinimumWidth(1600)
        self.setMinimumHeight(1024)
        # .show() is non-modal, .exec() is modal
        self.make_visible()


class MainWindow(QMainWindow):

    def __init__(self, main_config: VduControlsConfig, app: QApplication, session_startup: bool):
        super().__init__()

        self.app = app
        self.displayed_preset_name = None
        self.setObjectName('main_window')
        self.geometry_key = self.objectName() + "_geometry"
        self.state_key = self.objectName() + "_window_state"
        self.settings = QSettings('vdu_controls.qt.state', 'vdu_controls')

        gnome_tray_behaviour = main_config.is_system_tray_enabled() and \
                               os.environ.get('XDG_CURRENT_DESKTOP') is not None \
                               and 'gnome' in os.environ['XDG_CURRENT_DESKTOP'].lower()

        if gnome_tray_behaviour:
            # Gnome tray doesn't normally provide a way to bring up the main app.
            def main_window_action() -> None:
                self.show()
                self.raise_()
                self.activateWindow()
        else:
            main_window_action = None

        def edit_config() -> None:
            SettingsEditor.invoke(main_config, [vdu.config for vdu in self.main_control_panel.vdu_controllers])

        def refresh_from_vdus() -> None:
            self.main_control_panel.start_refresh()

        def grey_scale() -> None:
            GreyScaleDialog()

        def edit_presets() -> None:
            PresetsDialog.invoke(self)

        def quit_app() -> None:
            self.app_save_state()
            app.quit()

        def wrap_invoke(callable_function):
            if gnome_tray_behaviour:
                # Must show main app or tray will shutdown app when popups are closed.
                self.show()
            callable_function()

        self.preset_controller = PresetController()

        self.app_context_menu = ContextMenu(main_window=self,
                                            main_window_action=main_window_action,
                                            about_action=partial(wrap_invoke, AboutDialog.invoke),
                                            help_action=partial(wrap_invoke, HelpDialog.invoke),
                                            chart_action=partial(wrap_invoke, grey_scale),
                                            settings_action=partial(wrap_invoke, edit_config),
                                            presets_action=partial(wrap_invoke, edit_presets),
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
            splash.showMessage(translate('\n\nVDU Controls\nLooking for DDC monitors...\n'),
                               Qt.AlignTop | Qt.AlignHCenter)

        def detect_vdu_hook(vdu: VduController) -> None:
            if splash is not None:
                splash.showMessage(
                    translate('\n\nVDU Controls {}\nDDC ID {}\n{}').format(VDU_CONTROLS_VERSION,
                                                                           vdu.vdu_id, vdu.get_vdu_description()),
                    Qt.AlignTop | Qt.AlignHCenter)

        def respond_to_signal(signal_number: int):
            if signal_number == signal.SIGHUP:
                self.main_control_panel.refresh_data()
            elif PRESET_SIGNAL_MIN <= signal_number <= PRESET_SIGNAL_MAX:
                restore_preset = self.preset_controller.get_preset_name(signal_number - PRESET_SIGNAL_MIN)
                if restore_preset is not None:
                    self.restore_preset(restore_preset)
                else:
                    # Cannot raise a Qt alert inside the signal handler in case another signal comes in.
                    log_warning(f"ignoring signal {signal_number}, no preset associated with that signal number.")

        global signal_wakeup_handler
        signal_wakeup_handler.signalReceived.connect(respond_to_signal)

        self.main_control_panel = VduControlsMainPanel(main_config, detect_vdu_hook, self.app_context_menu,
                                                       session_startup)

        def refresh_finished():
            self.display_active_preset_info(None)

        self.main_control_panel.refresh_finished.connect(refresh_finished)

        self.setCentralWidget(self.main_control_panel)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.adjustSize()

        self.display_active_preset_info(None)

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

        if splash is not None:
            splash.finish(self)

    def restore_preset(self, preset: Preset) -> Preset:
        log_info(f"Preset changing to {preset.name}")
        preset.load()
        for section in preset.preset_ini:
            for control_panel in self.main_control_panel.vdu_control_panels:
                if section == control_panel.vdu_model.vdu_model_and_serial_id:
                    control_panel.restore_state(preset.preset_ini)
        self.display_active_preset_info(preset)
        return preset

    def restore_named_preset(self, preset_name: str) -> None:
        presets = self.preset_controller.find_presets()
        if preset_name in presets:
            self.restore_preset(presets[preset_name])

    def save_preset(self, preset: Preset) -> None:
        for control_panel in self.main_control_panel.vdu_control_panels:
            control_panel.copy_state(preset.preset_ini)
        self.preset_controller.save_preset(preset)
        if not self.app_context_menu.has_preset_menu_item(preset.name):
            self.app_context_menu.insert_preset_menu_item(preset)
            self.display_active_preset_info(preset)

    def delete_preset(self, preset: Preset) -> None:
        self.preset_controller.delete_preset(preset)
        if self.app_context_menu.has_preset_menu_item(preset.name):
            self.app_context_menu.remove_preset_menu_item(preset)
        if self.displayed_preset_name == preset.name:
            self.display_active_preset_info(None)

    def display_active_preset_info(self, preset: Preset|None) -> None:
        if preset is None:
            preset = self.preset_controller.which_preset_is_active(self.main_control_panel)
        if preset:
            self.setWindowTitle(preset.name)
            icon = create_merged_icon(self.app_icon, preset.create_icon())
            self.app.setWindowIcon(icon)
            if self.tray:
                self.tray.setToolTip(f"{preset.name} \u2014 {self.app_name}")
                self.tray.setIcon(icon)
        else:
            self.setWindowTitle("")
            self.setWindowIcon(self.app_icon)
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
            self.display_active_preset_info(None)
            self.app_context_menu.refresh_preset_menu(reload=True)
        event.accept()
        return True


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

    if args.about:
        AboutDialog.invoke()

    main_window = MainWindow(main_config, app, session_startup=is_logging_in())

    if args.create_config_files:
        main_window.create_config_files()

    rc = app.exec_()
    if rc == EXIT_CODE_FOR_RESTART:
        QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
    sys.exit(rc)


# A fallback in case the hard coded splash screen PNG doesn't exist (which probably means KDE is not installed).
FALLBACK_SPLASH_PNG_BASE64 = b"""
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
"""

if __name__ == '__main__':
    main()
