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
                     [--enable-vcp-code vcp_code] [--system-tray] [--debug] [--warnings]
                     [--no-splash] [--sleep-multiplier multiplier]
                     [--create-config-files]
                     [--install] [--uninstall]

Optional arguments:
-------------------

      -h, --help            show this help message and exit
      --detailed-help       full help in markdown format
      --about               about vdu_controls
      --show control_name
                            show specified control only (--show may be specified multiple times)
      --hide control_name
                            hide/disable a control (--hide may be specified multiple times)
      --enable-vcp-code vcp_code
                            enable a control for a vcp-code unavailable via hide/show (may be specified multiple times)
      --system-tray         start up as an entry in the system tray
      --debug               enable debug output to stdout
      --warnings            popup a warning when a VDU lacks an enabled control
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

By default ``vdu_controls`` offers a subset of possible controls including brightness and contrast.  Further controls
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
the restriction resulting in its contrast-control appearing to do nothing.

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

    - Correct manufacturer built-in meta data.
    - Customise which controls are to be provided for each VDU.
    - Set a optimal ``ddcutil`` DDC communication speed-multiplier for each VDU.

It should be noted that config files can only be used to alter definitions of VCP codes already supported
by ``ddcutil``.  If a VCP code is listed as a *manufacturer specific feature* it is not supported. Manufacturer
specific features should not be experimented with, some may have destructive or irreversible consequences that
may brick the hardware. It is possible to enable any codes by  creating a  ``ddcutil`` user
definition (``--udef``) file, BUT THIS SHOULD ONLY BE USED WITH EXTREME CAUTION AND CANNOT BE RECOMMENDED.

The config files are in INI-format divided into a number of sections as outlined below:

        # The vdu-controls-globals section is only required in $HOME/.config/vdu_controls/vdu_controls.conf
        [vdu-controls-globals]
        system-tray-enabled = yes|no
        splash-screen-enabled = yes|no
        warnings-enabled = yes|no
        debug-enabled = yes|no

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
        # The enable-vcp-codes option is a list of two-digit hex values in CSV format.
        # This option enables ddcutil supported codes that are not in the default set provided by vdu_controls.
        enable-vcp-codes = NN, NN, NN

        [ddcutil-parameters]
        # Useful values appear to be >=0.1
        sleep-multiplier = 0.5

        [ddcutil-capabilities]
        # The (possibly edited) output from "ddcutil --display N capabilities" with leading spaces retained.
        capabilities-override =

As well as using the ``Settings``, config files may also be created by the command line option

        vdu_controls --create-config-files

which will create initial templates based on the currently connected VDU's.

The config files are completely optional, they need not be used if the existing command line options are found to be
adequate to the task at hand.

Presets
-------

A custom named preset can be used to save the current VDU settings for later recall. Any number of presets can be
created to suit different lighting conditions or different applications, for example: *Night*, *Day*, *Overcast*,
*Sunny*, *Photography*, and *Video*.

The ``Presets`` item in right-mouse ``context-menu`` will bring up a dialog for managing and applying presets.
The ``context-menu`` also includes a shortcut for applying each existing presets.

The preset files are named as follows:

    ``$HOME/.config/vdu_controls/Preset_<preset_name>.conf``

Presets are saved in INI-file format for ease of editing.  Each preset file contains a section for each connected
VDU, something similar to the following example:

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

import argparse
import base64
import configparser
import glob
import inspect
import os
import pickle
import re
import signal
import stat
import subprocess
import sys
import textwrap
import time
import traceback
from functools import partial
from pathlib import Path
from typing import List, Tuple, Mapping, Type

from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QRegExp, QPoint
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon, QCursor, QImage, QPainter, QDoubleValidator, QRegExpValidator
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
    QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction

VDU_CONTROLS_VERSION = '1.5.1'


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

#: A high resolution image, will fallback to an internal PNG if this file isn't found on the local system
DEFAULT_SPLASH_PNG = "/usr/share/icons/oxygen/base/256x256/apps/preferences-desktop-display.png"

#: Assuming ddcutil is somewhere on the PATH.
DDCUTIL = "ddcutil"

#: Internal special exit code used to signal that the exit handler should restart the program.
EXIT_CODE_FOR_RESTART = 1959


def get_splash_image() -> QPixmap:
    """Get the splash pixmap from a KDE oxygen PNG file or, failing that, a small base64 encoded internal PNG."""
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


class VcpCapability:
    """Representation of a VCP (Virtual Control Panel) capability for a VDU."""

    def __init__(self, vcp_code: str, vcp_name: str, vcp_type: str, values: List = None,
                 causes_config_change: bool = False, icon_source: bytes = None):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.vcp_type = vcp_type
        self.icon_source = icon_source
        self.causes_config_change = causes_config_change
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

    def __run__(self, *args, sleep_multiplier: float = None) -> subprocess.CompletedProcess:
        if self.debug:
            print("DEBUG: subprocess run    - ", DDCUTIL, args)
        multiplier_str = str(self.default_sleep_multiplier if sleep_multiplier is None else sleep_multiplier)
        result = subprocess.run(
            [DDCUTIL, '--sleep-multiplier', multiplier_str] + self.common_args + list(args),
            stdout=subprocess.PIPE, check=True)
        if self.debug:
            print("DEBUG: subprocess result - ", result)
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
                print(f"INFO: checking {display_str}")
                vdu_id = display_match.group(1)
                monitor_match = monitor_pattern.search(display_str)
                manufacturer, model_name, serial_number = \
                    monitor_match.group(1).split(':') if monitor_match else ['', 'Unknown Model', '']
                if serial_number == '':
                    serial_number = 'Display' + vdu_id
                display_list.append((vdu_id, manufacturer, model_name, serial_number))
            elif len(display_str.strip()) != 0:
                print(f"WARNING: ignoring {display_str}")
        return display_list

    def query_capabilities(self, vdu_id: str) -> str:
        """Return a vpc capabilities string."""
        result = self.__run__('--display', vdu_id, 'capabilities')
        capability_text = result.stdout.decode('utf-8')
        return capability_text

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
                        return '{:x}'.format(int(cnc_match.group(3), 16) << 8 | int(cnc_match.group(4), 16)), '0'
                else:
                    raise TypeError(f'Unsupported VCP type {type_indicator} for monitor {vdu_id} vcp_code {vcp_code}')
            print(f"WARNING: obtained garbage '{result.stdout.decode('utf-8')}' will try again.")
            print(f"WARNING: ddcutil maybe running too fast for monitor {vdu_id}, try increasing --sleep-multiplier.")
            time.sleep(2)
        print(f"ERROR: ddcutil failed all attempts to get value for monitor {vdu_id} vcp_code {vcp_code}")
        raise ValueError(
            f"ddcutil returned garbage for monitor {vdu_id} vcp_code {vcp_code}, try increasing --sleep-multiplier")

    def set_attribute(self, vdu_id: str, vcp_code: str, new_value: str, sleep_multiplier: float = None) -> None:
        """Send a new value to a specific VDU and vcp_code."""
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
            print(code_def)
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


class DialogSingletonMixin():
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
            print(f'DEBUG: SingletonDialog created for {class_name}')
        DialogSingletonMixin._dialogs_map[class_name] = self

    def closeEvent(self, event) -> None:
        """Subclasses that implement their own closeEvent must call this closeEvent to deregister the singleton"""
        class_name = self.__class__.__name__
        if DialogSingletonMixin.debug:
            print(f'DEBUG: SingletonDialog remove {class_name}')
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
            print(f'DEBUG: SingletonDialog show existing {class_name}')
        instance = DialogSingletonMixin._dialogs_map[class_name]
        instance.make_visible()

    @classmethod
    def exists(cls: Type) -> bool:
        """Returns true if the dialog has already been created."""
        class_name = cls.__name__
        if DialogSingletonMixin.debug:
            print(f'DEBUG: SingletonDialog exists {class_name} {class_name in DialogSingletonMixin._dialogs_map}')
        return class_name in DialogSingletonMixin._dialogs_map


class VduGuiSupportedControls:
    """Maps of controls supported by name on the command line and in config files."""
    by_code = {
        '10': VcpCapability('10', 'Brightness', 'C', icon_source=BRIGHTNESS_SVG),
        '12': VcpCapability('12', 'Contrast', 'C', icon_source=CONTRAST_SVG),
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
        # hardware given some of the weird settings that appear to be available and the sometimes dodgy
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
                'debug-enabled': 'no', }

        self.ini_content['vdu-controls-widgets'] = {}
        self.ini_content['ddcutil-parameters'] = {}
        self.ini_content['ddcutil-capabilities'] = {}

        for vcp_code, item in VDU_SUPPORTED_CONTROLS.by_code.items():
            self.ini_content['vdu-controls-widgets'][item.property_name()] = 'no'

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

    def get_sleep_multiplier(self) -> float:
        return self.ini_content.getfloat('ddcutil-parameters', 'sleep-multiplier', fallback=0.5)

    def get_capabilities_alt_text(self) -> str:
        return self.ini_content['ddcutil-capabilities']['capabilities-override']

    def set_capabilities_alt_text(self, alt_text: str) -> None:
        self.ini_content['ddcutil-capabilities']['capabilities-override'] = alt_text

    def enable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content['vdu-controls-widgets'][VDU_SUPPORTED_CONTROLS.by_code[vcp_code].property_name()] = 'yes'

    def disable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content['vdu-controls-widgets'][VDU_SUPPORTED_CONTROLS.by_code[vcp_code].property_name()] = 'no'

    def enable_unsupported_vcp_code(self, vcp_code: str) -> None:

        if vcp_code in VDU_SUPPORTED_CONTROLS.by_code:
            print(f"WARNING: vdu_controls supported VCP_CODE {vcp_code} "
                  f" ({VDU_SUPPORTED_CONTROLS.by_code[vcp_code].property_name()})"
                  f" is enabled in the list for unsupported codes.")
            self.enable_supported_vcp_code(vcp_code)
            return
        # No very efficient
        csv_list = [] if 'enable-vcp-codes' not in self.ini_content['vdu-controls-widgets'] else \
            self.ini_content['vdu-controls-widgets']['enable-vcp-codes'].split(',')

        if vcp_code not in csv_list:
            csv_list.append(vcp_code)
            self.ini_content['vdu-controls-widgets']['enable-vcp-codes'] = ','.join(csv_list)

    def get_all_enabled_vcp_codes(self) -> List[str]:
        # No very efficient
        enabled_vcp_codes = []
        for control_name, control_def in VDU_SUPPORTED_CONTROLS.by_arg_name.items():
            if self.ini_content['vdu-controls-widgets'].getboolean(control_name, fallback=False):
                enabled_vcp_codes.append(control_def.vcp_code)
        for vcp_code in self.ini_content['vdu-controls-widgets']['enable-vcp-codes'].split(","):
            if vcp_code.strip() != '':
                enabled_vcp_codes.append(vcp_code.strip())
        return enabled_vcp_codes

    def parse_file(self, config_path: Path) -> None:
        """Parse config values from file"""
        self.file_path = config_path
        basename = os.path.basename(config_path)
        config_text = Path(config_path).read_text()
        print("INFO: using config file '" + config_path.as_posix() + "'")
        if re.search(r'(\[ddcutil-capabilities])|(\[ddcutil-parameters])|(\[vdu-controls-\w])', config_text) is None:
            print(f"Info: old style config file {basename} overrides ddcutils capabilities")
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
                print(f"DEBUG: {origin} [{section}] {option} = {self.ini_content[section][option]}")

    def write_file(self, config_path: Path, include_globals: bool = True, overwrite: bool = False) -> None:
        """Write the config to a file.  Used for creating initial template config files."""
        self.file_path = config_path
        if config_path.is_file():
            if not overwrite:
                print(f"ERROR: {config_path.as_posix()} exists, remove the file if you really want to replace it.")
                return
        print(f"WARNING: creating new config file {config_path.as_posix()}")
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
    Holds model+controller specific to an individual VDU including a map of its capabilities. A model object in MVC speak.

    The model configuration can optionally be read from an INI-format config file held in $HOME/.config/vdu-control/

    Capabilities are either extracted from ddcutil output or read from the INI-format files.  File read
    capabilities are provided so that the output from "ddcutil --display N capabilities" can be corrected (because
    it is sometimes incorrect due to sloppy implementation by manufacturers). For example, my LG monitor reports
    two Display-Port inputs and it only has one.
    """

    def __init__(self, vdu_id: str, vdu_model_name: str, vdu_serial: str, manufacturer: str,
                 default_config: VduControlsConfig,
                 ddcutil: DdcUtil) -> None:
        self.vdu_id = vdu_id
        self.model_name = vdu_model_name
        self.serial = vdu_serial
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.sleep_multiplier = None
        self.enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        unacceptable_char_pattern = re.compile(r'[^A-Za-z0-9._-]')
        self.vdu_model_and_serial_id = proper_name(vdu_model_name.strip(), vdu_serial.strip())
        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text = None
        self.config = None
        for config_name in (self.vdu_model_and_serial_id, self.vdu_model_id):
            config_path = get_config_path(config_name)
            print("INFO: checking for config file '" + config_path.as_posix() + "'")
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
            self.capabilities_text = ddcutil.query_capabilities(vdu_id)
        self.capabilities = self._parse_capabilities(self.capabilities_text)
        self.config.restrict_to_actual_capabilities(self.capabilities)
        if self.config is None:
            # In memory only config - in case it's needed by a future config editor
            self.config = VduControlsConfig(self.vdu_model_and_serial_id,
                                            default_enabled_vcp_codes=self.enabled_vcp_codes)
            self.config.set_capabilities_alt_text(self.capabilities_text)

    def write_template_config_files(self) -> None:
        """Write template config files to $HOME/.config/vdu_controls/"""
        for config_name in (self.vdu_model_and_serial_id, self.vdu_model_id):
            save_config_path = get_config_path(config_name)
            config = VduControlsConfig(config_name, default_enabled_vcp_codes=self.enabled_vcp_codes)
            config.set_capabilities_alt_text(self.capabilities_text)
            config.write_file(save_config_path, include_globals=False)
            self.config = config

    def get_vdu_description(self) -> str:
        """Return a unique description using the serial-number (if defined) or vdu_id."""
        return self.model_name + ':' + (self.serial if len(self.serial) != 0 else self.vdu_id)

    def get_full_id(self) -> Tuple[str, str, str, str]:
        """Return a tuple that defines this VDU: (vdu_id, manufacturer, model, serial-number)."""
        return self.vdu_id, self.manufacturer, self.model_name, self.serial

    def get_attribute(self, vcp_code: str) -> Tuple[str, str]:
        return self.ddcutil.get_attribute(self.vdu_id, vcp_code, sleep_multiplier=self.sleep_multiplier)

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
                vcp_type = CONTINUOUS_TYPE if len(values) == 0 else SIMPLE_NON_CONTINUOUS_TYPE
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
        self.show()

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
            # TODO - should probably also allow spaces as well as commas, but the rexexp is getting a bit tricky?
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
                ini_editable[section][option] = text_editor.toPlainText()

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
        """Construct the slider control an initialize its values from the VDU."""
        super().__init__()

        self.vdu_model = vdu_model
        self.vcp_capability = vcp_capability
        self.current_value, self.max_value = vdu_model.get_attribute(self.vcp_capability.vcp_code)

        layout = QHBoxLayout()
        self.setLayout(layout)

        if vcp_capability.vcp_code in VDU_SUPPORTED_CONTROLS.by_code and \
                VDU_SUPPORTED_CONTROLS.by_code[vcp_capability.vcp_code].icon_source is not None:
            svg_icon = QSvgWidget()
            svg_icon.load(VDU_SUPPORTED_CONTROLS.by_code[vcp_capability.vcp_code].icon_source)
            svg_icon.setFixedSize(50, 50)
            svg_icon.setToolTip(translate(vcp_capability.name))
            layout.addWidget(svg_icon)
        else:
            label = QLabel()
            label.setText(vcp_capability.name)
            layout.addWidget(label)

        self.slider = slider = QSlider()
        slider.setMinimumWidth(200)
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
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here)."""
        self.current_value, _ = self.vdu_model.get_attribute(self.vcp_capability.vcp_code)

    def refresh_view(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        self.slider.setValue(int(self.current_value))


class VduControlComboBox(QWidget):
    """
    GUI control for a DDC non-continuously variable attribute, one that has a list of choices.

    This is a duck-typed GUI control widget (could inherit from an abstract type if we wanted to get formal about it).
    """

    def __init__(self, vdu_model: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the combobox control an initialize its values from the VDU."""
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

        if self.current_value not in self.keys:
            raise ValueError(translate('VCP_CODE {} ({}) value {} is not in allowed list: {}').format(
                vcp_capability.vcp_code, vcp_capability.name, self.current_value, self.keys))
        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))

        def index_changed(index: int) -> None:
            self.current_value = self.combo_box.currentData
            try:
                self.vdu_model.set_attribute(self.vcp_capability.vcp_code, self.combo_box.currentData())
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
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here)."""
        self.current_value, _ = self.vdu_model.get_attribute(self.vcp_capability.vcp_code)

    def refresh_view(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))


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
                elif capability.vcp_type == SIMPLE_NON_CONTINUOUS_TYPE:
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
        """Tell the control widgets to get fresh VDU data (may be called from a task thread, so no GUI op's here)."""
        for control in self.vcp_controls:
            control.refresh_data()

    def refresh_view(self) -> None:
        """Tell the control widgets to refresh their views from their internally cached values."""
        for control in self.vcp_controls:
            control.refresh_view()

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)

    def save_state(self, preset_ini: configparser.ConfigParser) -> None:
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


class ContextMenu(QMenu):

    def __init__(self,
                 about_action=None, help_action=None, settings_action=None, presets_action=None,
                 quit_action=None) -> None:
        super().__init__()
        self.vdu_controls_main_window = None
        self.preset_controller = PresetController()
        self.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon),
                       translate('Presets'),
                       presets_action)
        self.presets_separator = self.addSeparator()

        self.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon),
                       translate('Settings'),
                       settings_action)
        self.addAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation),
                       translate('About'),
                       about_action)
        self.addAction(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton),
                       translate('Help'),
                       help_action)
        self.addSeparator()
        self.addAction(self.style().standardIcon(QStyle.SP_DialogCloseButton),
                       translate('Quit'),
                       quit_action)

    def set_vdu_controls_main_window(self, main_window) -> None:
        self.vdu_controls_main_window = main_window

    def insert_preset(self, name: str) -> None:
        # Have to add it first and then move it (otherwise it won't appear - weird).

        def restore_preset() -> None:
            self.preset_controller.restore_preset(self.sender().text(), self.vdu_controls_main_window)

        action = self.addAction(self.style().standardIcon(QStyle.SP_CommandLink), name, restore_preset)
        self.insertAction(self.presets_separator, action)
        # print(self.actions())
        self.update()

    def refresh_preset_menu(self) -> None:
        for name, path_str in self.preset_controller.find_preset_paths().items():
            if not self.has_preset(name):
                self.insert_preset(name)

    def has_preset(self, name: str) -> bool:
        for action in self.actions():
            if action == self.presets_separator:
                break
            if action.text() == name:
                return True
        return False

    def get_preset(self, name: str) -> QAction:
        for action in self.actions():
            if action == self.presets_separator:
                break
            if action.text() == name:
                return action
        return None


class VduControlsMainWindow(QWidget):
    """GUI for detected VDU's, it will construct and contain a control panel for each VDU."""

    def __init__(self,
                 default_config: VduControlsConfig,
                 detect_vdu_hook: callable,
                 app_context_menu: ContextMenu) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.ddcutil = DdcUtil(debug=default_config.is_debug_enabled(), common_args=None,
                               default_sleep_multiplier=default_config.get_sleep_multiplier())
        self.vdu_control_panels = []
        self.warnings = default_config.are_warnings_enabled()
        self.detected_vdus = self.ddcutil.detect_monitors()
        self.context_menu = app_context_menu
        self.context_menu.set_vdu_controls_main_window(self)
        app_context_menu.refresh_preset_menu()

        self.vdu_controllers = []
        for vdu_id, manufacturer, vdu_model_name, vdu_serial in self.detected_vdus:
            controller = VduController(vdu_id, vdu_model_name, vdu_serial, manufacturer, default_config, self.ddcutil)
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

        def start_refresh() -> None:
            # Refreshes from all values from ddcutil.  May be slow, starts a busy spinner and then
            # starts the work in a task thread.
            self.refresh_button.setDisabled(True)
            self.progressBar.setDisabled(False)
            # Setting range to 0,0 cause the progress bar to pulsate left/right - used as a busy spinner.
            self.progressBar.setRange(0, 0)
            # Start the background task
            self.refreshDataTask.start()

        def finish_refresh() -> None:
            # GUI-thread QT signal handler for refresh task completion - execution will be in the GUI thread.
            # Stop the busy-spinner (progress bar).
            self.progressBar.setRange(0, 1)
            self.progressBar.setDisabled(True)
            self.refresh_button.setDisabled(False)
            self.refresh_view()

        self.refreshDataTask = RefreshVduDataTask(self)
        self.refreshDataTask.task_finished.connect(finish_refresh)

        self.progressBar = QProgressBar(self)
        # Disable text percentage label on the spinner progress-bar
        self.progressBar.setTextVisible(False)
        self.progressBar.setRange(0, 1)
        self.progressBar.setDisabled(True)
        layout.addWidget(self.progressBar, Qt.AlignVCenter)

        self.refresh_button = QPushButton(translate("Refresh settings from monitors"))
        self.refresh_button.clicked.connect(start_refresh)
        layout.addWidget(self.refresh_button)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        def open_context_menu(position: QPoint) -> None:
            self.context_menu.exec(self.mapToGlobal(position))

        self.customContextMenuRequested.connect(open_context_menu)

        self.setLayout(layout)

    def refresh_data(self) -> None:
        """Refresh data from the VDU's. Called by a non-GUI task. Not in the GUI-thread, cannot do any GUI op's."""
        self.detected_vdus = self.ddcutil.detect_monitors()
        for control_panel in self.vdu_control_panels:
            if control_panel.vdu_model.get_full_id() in self.detected_vdus:
                control_panel.refresh_data()

    def refresh_view(self) -> None:
        """Invoke when the GUI worker thread completes. Runs in the GUI thread and can refresh the GUI views."""
        if len(self.detected_vdus) != len(self.vdu_control_panels):
            # The number of VDU's has changed, vdu_id's will no longer match, throw a wobbly
            restart_due_to_config_change()
        for control_panel in self.vdu_control_panels:
            control_panel.refresh_view()


class RefreshVduDataTask(QThread):
    """
    Task to refresh VDU data from the physical VDU's.

    Runs as a task because it can be quite slow depending on the number of VDU's, number of controls.  The task runs
    outside the GUI thread and no parts of it can only update the GUI data, not the GUI view.
    """

    task_finished = pyqtSignal()

    def __init__(self, main_widget: VduControlsMainWindow) -> None:
        """Initialise the task that will run in a non-GUI thread to update all the widget's data."""
        super().__init__()
        self.main_widget = main_widget

    def run(self) -> None:
        """Run a task that uses ddcutil to retrieve data for all the visible controls (may be slow)."""
        # Running in a task thread, cannot interact with GUI thread, just update the data.
        self.main_widget.refresh_data()
        # Tell (qt-signal) the GUI-thread that the task has finished, the GUI thread will then update the view widgets.
        self.task_finished.emit()


class PresetController:
    def __init__(self):
        pass

    def find_preset_paths(self) -> Mapping[str, str]:
        preset_paths = {}
        for path_str in glob.glob(CONFIG_DIR_PATH.joinpath("Preset_*.conf").as_posix()):
            preset_name = os.path.splitext(os.path.basename(path_str))[0].replace('Preset_', '').replace('_', ' ')
            preset_paths[preset_name] = path_str
        return preset_paths

    def save_preset(self, preset_name: str, main_window: VduControlsMainWindow, context_menu: ContextMenu) -> None:
        preset_ini = configparser.ConfigParser()
        preset_path = get_config_path(proper_name('Preset', preset_name))
        if preset_path.exists():
            save_message = QMessageBox()
            message = translate('Overwrite existing {}?').format(preset_path.as_posix())
            save_message.setText(message)
            save_message.setIcon(QMessageBox.Question)
            save_message.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            rc = save_message.exec()
            if rc == QMessageBox.Cancel:
                return
        print(f"INFO: saving preset file '{preset_path.as_posix()}'")
        for control_panel in main_window.vdu_control_panels:
            control_panel.save_state(preset_ini)
        if not preset_path.parent.is_dir():
            os.makedirs(preset_path.parent)
        with open(preset_path, 'w') as preset_file:
            preset_ini.write(preset_file)
        if not context_menu.has_preset(preset_name):
            context_menu.insert_preset(preset_name)

    def restore_preset(self, preset_name: str, main_window: VduControlsMainWindow) -> None:
        preset_path = get_config_path(proper_name('Preset', preset_name))
        print(f"INFO: reading preset file '{preset_path.as_posix()}'")
        preset_text = Path(preset_path).read_text()
        preset_ini = configparser.ConfigParser()
        preset_ini.read_string(preset_text)
        for section in preset_ini:
            for control_panel in main_window.vdu_control_panels:
                if section == control_panel.vdu_model.vdu_model_and_serial_id:
                    control_panel.restore_state(preset_ini)

    def delete_preset(self, preset_name: str, context_menu: ContextMenu) -> None:
        preset_path = get_config_path(proper_name('Preset', preset_name))
        print(f"INFO: deleting preset file '{preset_path.as_posix()}'")
        if preset_path.exists():
            os.remove(preset_path.as_posix())
        if context_menu.has_preset(preset_name):
            context_menu.removeAction(context_menu.get_preset(preset_name))


class PresetsDialog(QDialog, DialogSingletonMixin):
    """A dialog for creating/updating/removing presets."""

    @staticmethod
    def invoke(main_window: VduControlsMainWindow, context_menu: ContextMenu) -> None:
        if PresetsDialog.exists():
            PresetsDialog.show_existing_dialog()
        else:
            PresetsDialog(main_window, context_menu)

    def __init__(self, main_window: VduControlsMainWindow, context_menu: ContextMenu) -> None:
        super().__init__()
        self.main_window = main_window
        self.context_menu = context_menu
        self.preset_controller = PresetController()
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
        context_menu.refresh_preset_menu()

        def restore_preset(preset_name: str = None) -> None:
            self.preset_controller.restore_preset(preset_name, self.main_window)

        def save_preset(preset_name: str = None) -> None:
            self.preset_controller.save_preset(preset_name, self.main_window, self.context_menu)

        def delete_preset(preset_name: str = None, target_widget: QWidget = None) -> None:
            print(f"INFO: delete preset {preset_name}")
            self.preset_controller.delete_preset(preset_name, self.context_menu)
            presets_layout.removeWidget(target_widget)
            target_widget.deleteLater()
            presets_panel.repaint()

        for name in self.preset_controller.find_preset_paths().keys():
            preset_widget = self.create_preset_widget(
                name,
                restore_action=restore_preset,
                save_action=save_preset,
                delete_action=delete_preset)
            presets_layout.addWidget(preset_widget)

        add_preset_widget = QWidget()
        add_preset_layout = QHBoxLayout()
        add_preset_widget.setLayout(add_preset_layout)
        add_preset_name_edit = QLineEdit()
        add_preset_name_edit.setToolTip(translate('Enter a new preset name.'))
        add_preset_layout.addWidget(add_preset_name_edit)

        add_button = QPushButton(translate('Add'))
        add_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
        add_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        add_button.setStyleSheet('QPushButton { border: none; margin: 0px; padding: 0px;}')
        add_button.setToolTip(translate('Save current VDU settings to a new preset.'))
        add_preset_layout.addWidget(add_button)

        def add_action() -> None:
            new_name = add_preset_name_edit.text().strip()
            if new_name == '':
                return
            if self.has_preset(new_name):
                print(f"INFO: Already exists {new_name}")
                save_message = QMessageBox()
                message = translate("Preset called '{}' already exists.").format(new_name)
                save_message.setText(message)
                save_message.setIcon(QMessageBox.Critical)
                save_message.setStandardButtons(QMessageBox.Close)
                save_message.exec()
                return
            self.preset_controller.save_preset(new_name, main_window, context_menu)
            new_preset_widget = self.create_preset_widget(
                new_name,
                restore_action=restore_preset,
                save_action=save_preset,
                delete_action=delete_preset)
            presets_layout.addWidget(new_preset_widget)
            add_preset_name_edit.setText('')

        add_button.clicked.connect(add_action)

        layout.addWidget(add_preset_widget)

        close_button = QPushButton(translate('close'))
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addWidget(button_box)
        # .show() is non-modal, .exec() is modal
        self.show()

    def has_preset(self, name) -> bool:
        for w in self.presets_panel.children():
            if isinstance(w, self.PresetWidget):
                if w.name == name:
                    return True
        return False

    def create_preset_widget(self, name, restore_action=None, save_action=None, delete_action=None):
        preset_widget = self.PresetWidget(name)
        line_layout = QHBoxLayout()
        preset_widget.setLayout(line_layout)

        preset_name_button = QPushButton(name)
        # self.preset_name_button.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        preset_name_button.setStyleSheet('QPushButton { text-align: left; }')
        preset_name_button.setToolTip('Activate this preset.')
        line_layout.addWidget(preset_name_button)
        preset_name_button.clicked.connect(partial(restore_action, preset_name=name))
        preset_name_button.setAutoDefault(False)

        save_button = QPushButton()
        save_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
        save_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        save_button.setStyleSheet('QPushButton { border: none; margin: 0px; padding: 0px;}')
        save_button.setToolTip(translate('Save the current VDU settings to this preset.'))
        line_layout.addWidget(save_button)
        save_button.clicked.connect(partial(save_action, preset_name=name))
        save_button.setAutoDefault(False)

        delete_button = QPushButton()
        delete_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        delete_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        delete_button.setStyleSheet('QPushButton { border: none; margin: 0px; padding: 0px;}')
        delete_button.setToolTip('Delete this preset.')
        line_layout.addWidget(delete_button)
        delete_button.clicked.connect(partial(delete_action, preset_name=name, target_widget=preset_widget))
        delete_button.setAutoDefault(False)

        return preset_widget

    class PresetWidget(QWidget):
        def __init__(self, name: str):
            super().__init__()
            self.name = name


def exception_handler(e_type, e_value, e_traceback):
    """Overarching error handler in case something unexpected happens."""
    print("ERROR:\n", ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    alert = QMessageBox()
    alert.setText(translate('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))))
    alert.setInformativeText(translate('Is --sleep-multiplier set too low?') +
                             '<br>_______________________________________________________<br>')
    alert.setDetailedText(
        translate('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback))))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QApplication.quit()


def create_icon_from_svg_string(svg_str: bytes):
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    renderer = QSvgRenderer(svg_str)
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QIcon(QPixmap.fromImage(image))


def install_as_desktop_application(uninstall: bool = False):
    """Self install this script in the current Linux user's bin directory and desktop applications->settings menu."""
    desktop_dir = Path.home().joinpath('.local', 'share', 'applications')
    if not desktop_dir.exists():
        print(f"ERROR: No desktop directory is present:{desktop_dir.as_posix()}"
              " Cannot proceed - is this a non-standard desktop?")
        return

    bin_dir = Path.home().joinpath('bin')
    if not bin_dir.is_dir():
        print(f"WARNING: creating:{bin_dir.as_posix()}")
        os.mkdir(bin_dir)

    installed_script_path = bin_dir.joinpath("vdu_controls")
    desktop_definition_path = desktop_dir.joinpath("vdu_controls.desktop")

    if uninstall:
        os.remove(installed_script_path)
        print(f'INFO: removed {installed_script_path.as_posix()}')
        os.remove(desktop_definition_path)
        print(f'INFO: removed {desktop_definition_path.as_posix()}')
        return

    if installed_script_path.exists():
        print(f"WARNING: skipping installation of {installed_script_path.as_posix()}, it is already present.")
    else:
        source = open(__file__).read()
        source = source.replace("#!/usr/bin/python3", '#!' + sys.executable)
        print(f'INFO: creating {installed_script_path.as_posix()}')
        open(installed_script_path, 'w').write(source)
        print(f'INFO: chmod u+rwx {installed_script_path.as_posix()}')
        os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        print(f"WARNING: skipping installation of {desktop_definition_path.as_posix()}, it is already present.")
    else:
        print(f'INFO: creating {desktop_definition_path.as_posix()}')
        desktop_definition = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            Exec={installed_script_path.as_posix()}
            Name=VDU Controls
            GenericName=VDU controls
            Comment=Virtual Control Panel for externally connected VDU's
            Icon=preferences-desktop-display-color
            Categories=Qt;Settings;
            """)
        open(desktop_definition_path, 'w').write(desktop_definition)

    print('INFO: installation complete. Your desktop->applications->settings should now contain VDU Controls')

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
        about_message = self
        about_message.setTextFormat(Qt.AutoText)
        about_message.setText(translate('About vdu_controls'))
        about_message.setInformativeText(translate(ABOUT_TEXT))
        about_message.setIcon(QMessageBox.Information)
        about_message.exec()


class HelpDialog(QDialog, DialogSingletonMixin):

    @staticmethod
    def invoke():
        if HelpDialog.exists():
            HelpDialog.show_existing_dialog()
        else:
            HelpDialog()

    def __init__(self):
        super().__init__()
        help_dialog = self
        help_dialog.setWindowTitle('Help')
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setMarkdown(__doc__)
        layout.addWidget(markdown_view)
        help_dialog.setLayout(layout)
        # TODO maybe compute a minimum from the actual screen size
        help_dialog.setMinimumWidth(1600)
        help_dialog.setMinimumHeight(1024)
        # .show() is non-modal, .exec() is modal
        help_dialog.show()


def main():
    """vdu_controls application main."""
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.excepthook = exception_handler

    default_config = VduControlsConfig('vdu_controls', include_globals=True)
    config_path = get_config_path('vdu_controls')
    print("INFO: checking for config file '" + config_path.as_posix() + "'")
    if Path.is_file(config_path) and os.access(config_path, os.R_OK):
        default_config.parse_file(config_path)
    args = default_config.parse_args()
    if args.debug:
        default_config.debug_dump()
    if args.create_config_files:
        default_config.write_file(config_path)
    if args.install:
        install_as_desktop_application()
        sys.exit()
    if args.uninstall:
        install_as_desktop_application(uninstall=True)
        sys.exit()
    if args.detailed_help:
        print(__doc__)
        sys.exit()
    app = QApplication(sys.argv)

    if args.about:
        AboutDialog.invoke()

    def edit_config() -> None:
        SettingsEditor.invoke(default_config, [vdu.config for vdu in main_window.vdu_controllers])

    def edit_presets() -> None:
        PresetsDialog.invoke(main_window, app_context_menu)

    app_context_menu = ContextMenu(about_action=AboutDialog.invoke,
                                   help_action=HelpDialog.invoke,
                                   settings_action=edit_config,
                                   presets_action=edit_presets,
                                   quit_action=app.quit)

    pixmap = get_splash_image()
    splash = QSplashScreen(pixmap.scaledToWidth(800).scaledToHeight(400),
                           Qt.WindowStaysOnTopHint) if default_config.is_splash_screen_enabled() else None

    if splash is not None:
        splash.show()
        # Attempt to force it to the top with raise and activate
        splash.raise_()
        splash.activateWindow()
    app_icon = QIcon()
    app_icon.addPixmap(pixmap)

    tray = None
    if default_config.is_system_tray_enabled():
        tray = QSystemTrayIcon()
        tray.setIcon(app_icon)
        tray.setContextMenu(app_context_menu)

    app.setWindowIcon(app_icon)
    app.setApplicationDisplayName(translate('VDU Controls'))

    if splash is not None:
        splash.showMessage(translate('\n\nVDU Controls\nLooking for DDC monitors...\n'), Qt.AlignTop | Qt.AlignHCenter)

    def detect_vdu_hook(vdu: VduController) -> None:
        if splash is not None:
            splash.showMessage(
                translate('\n\nVDU Controls\nDDC ID {}\n{}').format(vdu.vdu_id, vdu.get_vdu_description()),
                Qt.AlignTop | Qt.AlignHCenter)

    main_window = VduControlsMainWindow(default_config, detect_vdu_hook, app_context_menu)

    if args.create_config_files:
        for vdu_model in main_window.vdu_controllers:
            vdu_model.write_template_config_files()

    if tray is not None:
        def show_window():
            if main_window.isVisible():
                main_window.hide()
            else:
                # Use the mouse pos as a guess to where the system tray is.  The Linux Qt x,y geometry returned by
                # the tray icon is 0,0, so we can't use that.
                p = QCursor.pos()
                wg = main_window.geometry()
                # Also try to cope with the tray not being at the bottom right of the screen.
                x = p.x() - wg.width() if p.x() > wg.width() else p.x()
                y = p.y() - wg.height() if p.y() > wg.height() else p.y()
                main_window.setGeometry(x, y, wg.width(), wg.height())
                main_window.show()
                # Attempt to force it to the top with raise and activate
                main_window.raise_()
                main_window.activateWindow()

        tray.activated.connect(show_window)
        tray.setVisible(True)
    else:
        main_window.show()

    if splash is not None:
        splash.finish(main_window)
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
