#!/usr/bin/python3
"""
vdu_controls: A Qt GUI wrapper for ddcutil
------------------------------------------

A GUI for controlling connected *Visual Display Units* (*VDU*'s) (also known as *displays*, or *monitors*).

Usage::
-------

        vdu_controls [-h]
                     [--show {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--hide {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--enable-vcp-code vcp_code] [--system-tray] [--debug] [--warnings]
                     [--no-splash] [--sleep-multiplier multiplier]

Optional arguments:
^^^^^^^^^^^^^^^^^^^

      -h, --help            show this help message and exit
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
      --install             installs the vdu_controls in the current user's path and desktop application menu.
      --uninstall           uninstalls the vdu_controls application menu file and script for the current user.

Description
-----------

``vdu_controls`` is a virtual control panel for physically connected VDU's.  It displays a set of controls for
each  DVI/DP/HDMI/USB connected VDU and uses the ``ddcutil`` command line utility to issue *Display Data Channel*
(*DDC*) *Virtual Control Panel*  (*VCP*) commands to each of them. The intent is not to provide a comprehensive set
of controls but rather to provide a simple panel with a selection of essential controls for the desktop.

By default ``vdu_controls`` offers a subset of possible controls including brightness, contrast.  Additional controls
can be enabled via the ``--enable-vcp-code`` option. ``vdu_controls`` may optionally run as a entry in the system
tray.

Builtin laptop displays normally don't implement DDC and those displays are not supported, but a laptop's
externally connected VDU's are likely to be controllable.

Some controls change the number of connected devices (for example, some VDU's support a power-off command). If
such controls are used, ``vdu_controls`` will detect the change and will restart itself to reconfigure the controls
for the new situation (for example, DDC VDU 2 may now be DD VDU 1).  Similarly, if you physically unplug monitor, the
same thing will happen.

Note that some VDU settings may disable or enable other settings. For example, setting a monitor to a specific
picture-profile might result in the contrast-control being disabled, but ``ddc_controls`` will not be aware of
the restriction resulting in its contrast-control appearing to do nothing.

Configuration
-------------

Most configuration is supplied via command line parameters.

Command line options can be added to the desktop application-menu by editing the application menu item
directly in the desktop (for *KDE-Plasma* this can be achieved by right-mousing on the **VDU Controls** menu
item and selecting **Edit Application**).  Alternatively, it is just as easy to use your preferred text editor to
edit the desktop definition file ``$HOME/.local/share/applications/vdu_controls.desktop`` and add options to
the ``Exec=`` line.

VDU/VDU-model config files
^^^^^^^^^^^^^^^^^^^^^^^^^^

An optional config file can be setup for each VDU or VDU-model.

The VDU config files are provided so that manufacturer supplied meta data when it proves to be inaccurate. These
config files can be model specific, or model and serial-number specific. For example, a VCP query to my
LG monitor reports that it has four inputs, but in reality it only has three.  I can correct this as follows:

    1 Run ``vdu_control`` in a console window and not which config files it's looking for::

        % ./vdu_controls.py
        INFO: checking for config file 'file:///home/michael/.config/vdu_controls/LG_HDR_4K_SN43328.conf'
        INFO: checking for config file 'file:///home/michael/.config/vdu_controls/LG_HDR_4K.conf'

    2 Run ``ddcutil`` to generate an initial text file of VDU capabilities::

        % ddcutil --display 2 capabilities > /home/michael/.config/vdu_controls/LG_HDR_4K.conf

    3 Edit the config file find the appropriate feature, in this case ``Feature: 60 (Input Source)``::

        # Use a text editor to find the erroneous DisplayPort-2 and get rid of it.
        % vi /home/michael/.config/vdu_controls/LG_HDR_4K.conf

    4 Run ``vdu_control`` and confirm the the config file is being used and the correct number of inputs is shown::

        % ./vdu_controls.py
        INFO: checking for config file '/home/michael/.config/vdu_controls/LG_HDR_4K_SN43328.conf'
        INFO: checking for config file '/home/michael/.config/vdu_controls/LG_HDR_4K.conf'
        WARNING: using config file '/home/michael/.config/vdu_controls/LG_HDR_4K.conf'

In the case where the manufacturers serial number cannot be retrieved, ``vdu_controls`` will look for a config file
containing the display number instead.

The VDU Config files read by ``vdu_controls`` can only be used to alter definitions of VCP codes already supported
by ``ddcutil``.  If the file lists a VCP code as a *manufacturer specific feature* then ``ddcutil`` will refuse to
set values for that code.  In the future it will be possible to fully enable such codes by creating a ``ddcutil``
user definition (``--udef``) file.  The ``ddcutil --udef`` option is still work in progress and unavailable at the
time at the time of writing.

Possible codes to try might be found in the output of ``ddcutil vcpinfo`` which lists all known codes in the standard.

Responsiveness
^^^^^^^^^^^^^^

If your VDU's are modern, you may find a smaller ``--sleep-multiplier`` will speed up the ``ddcutil`` to VDU protocol
exchanges making both ``ddcutil`` and ``vdu_controls`` much more responsive.

Using VDU/VDU-model config files files may speed up the startup by eliminating the need to run ``ddcutil`` to retrieve
VDU capabilities.

Examples
--------

    ``vdu_controls``
        All default controls.

    ``vdu_controls --show brightness --show contrast``
        Specified controls only:

    ``vdu_controls --hide contrast --hide audio-volume``
        All default controls except for those to be hidden.

    ``vdu_controls --system-tray --no-splash --show brightness --show audio-volume``
        Start as a system tray entry without showing the splash-screen.

    ``vdu_controls --enable-vcp-code 70 --warnings --debug``
        All default controls, plus a control for VCP_CODE 70, show any warnings, output debugging info.

    ``vdu_controls --sleep-multiplier 0.1``
        All default controls, speed up or slow down ddcutil by passing a sleep multiplier.

This script often refers to displays and monitors as VDU's in order to
disambiguate the noun/verb duality of "display" and "monitor"

Prerequisites
-------------
Described for OpenSUSE, similar for other distros:

Software::

    zypper install python38-QtPy
    zypper install ddcutil

Kernel Modules::

    lsmod | grep i2c_dev

Read ddcutil readme concerning config of i2c_dev with nvidia GPU's. Detailed ddcutil info at https://www.ddcutil.com/


vdu_controls Copyright (C) 2021 Michael Hamilton
-------------------------------------------------
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
import os
import re
import signal
import stat
import subprocess
import sys
import textwrap
import time
import traceback
from pathlib import Path
from typing import List, Tuple, Mapping

from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon, QCursor, QImage, QPainter
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu


def translate(source_text: str):
    """For future internationalization - recommended way to do this at this time."""
    return QCoreApplication.translate('vdu_controls', source_text)


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

QUIT_APP_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <defs id="defs3051">
    <style type="text/css" id="current-color-scheme">
      .ColorScheme-Text { color:#232629; }
      .ColorScheme-NegativeText { color:#da4453; }
      </style>
  </defs>
 <path 
     style="fill:currentColor;fill-opacity:1;stroke:none" 
     d="m2 2v12h12v-12h-12m1 2h10v9h-10v-9" class="ColorScheme-Text"/>
 <path 
     d="m6.2 6l-.707.707 1.793 1.793-1.793 1.793.707.707 1.793-1.793 1.793 1.793.707-.707-1.793-1.793 1.793-1.793-.707-.707-1.793 1.793"
      style="fill:currentColor;fill-opacity:1;stroke:none" class="ColorScheme-NegativeText"
    />
</svg>
"""

# Encode some default graphics to make the script self contained
DEFAULT_SPLASH_PNG = "/usr/share/icons/oxygen/base/256x256/apps/preferences-desktop-display.png"

#: Assumed location of ddcutil on a linux system.
DDCUTIL = "/usr/bin/ddcutil"

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

    def __init__(self, vcp_code: str, vcp_name: str, vcp_type: str, values: List = None, icon_source: bytes = None):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.vcp_type = vcp_type
        self.icon_source = icon_source
        # For future use if we want to implement non-continuous types of VCP (VCP types SNC or CNC)
        self.values = [] if values is None else values


class VcpGuiControlDef:
    """Defines a potential VCP GUI control."""

    def __init__(self, vcp_code, vcp_name, causes_config_change: bool = False, icon_source: bytes = None):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.causes_config_change = causes_config_change
        self.icon_source = icon_source

    def arg_name(self) -> str:
        return re.sub('[^A-Za-z0-9_-]', '-', self.name).lower()


SUPPORTED_VCP_CONTROLS = {
    '10': VcpGuiControlDef('10', 'Brightness', icon_source=BRIGHTNESS_SVG),
    '12': VcpGuiControlDef('12', 'Contrast', icon_source=CONTRAST_SVG),
    '62': VcpGuiControlDef('62', 'Audio volume', icon_source=VOLUME_SVG),
    '60': VcpGuiControlDef('60', 'Input Source', causes_config_change=True),
    'D6': VcpGuiControlDef('D6', 'Power mode', causes_config_change=True),
    'CC': VcpGuiControlDef('CC', 'OSD Language'),
}


class DdcUtil:
    """Interface to the command line ddcutil Display Data Channel Utility for interacting with VDU's."""

    def __init__(self, debug: bool = False, common_args: List[str] = None):
        super().__init__()
        self.debug = debug
        self.supported_codes = None
        self.common_args = [] if common_args is None else common_args

    def __run__(self, *args) -> subprocess.CompletedProcess:
        if self.debug:
            print("DEBUG: subprocess run    - ", DDCUTIL, args)
        result = subprocess.run([DDCUTIL, ] + self.common_args + list(args), stdout=subprocess.PIPE, check=True)
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
                print("INFO: checking {}".format(display_str))
                vdu_id = display_match.group(1)
                monitor_match = monitor_pattern.search(display_str)
                manufacturer, model_name, serial_number = \
                    monitor_match.group(1).split(':') if monitor_match else ['', 'Unknown Model', '']
                if serial_number == '':
                    serial_number = 'Display' + vdu_id
                display_list.append((vdu_id, manufacturer, model_name, serial_number))
            elif len(display_str.strip()) != 0:
                print("WARNING: ignoring {}".format(display_str))
        return display_list

    def query_capabilities(self, vdu_id: str, alternate_text=None) -> Mapping[str, VcpCapability]:
        """Return a map of vpc capabilities keyed by vcp code."""

        def parse_values(values_str: str):
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
        if alternate_text is None:
            result = self.__run__('--display', vdu_id, 'capabilities')
            capability_text = result.stdout.decode('utf-8')
        else:
            capability_text = alternate_text
        for feature_text in capability_text.split(' Feature: '):
            feature_match = feature_pattern.match(feature_text)
            if feature_match:
                vcp_code = feature_match.group(1)
                vcp_name = feature_match.group(2)
                values = parse_values(feature_match.group(3))
                # Guess type from existance or not of value list
                vcp_type = CONTINUOUS_TYPE if len(values) == 0 else SIMPLE_NON_CONTINUOUS_TYPE
                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None)
                feature_map[vcp_code] = capability
        if self.debug:
            print("DEBUG: capabilities", feature_map.keys())
        return feature_map

    def get_attribute(self, vdu_id: str, vcp_code: str) -> Tuple[str, str]:
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
            result = self.__run__('--brief', '--display', vdu_id, 'getvcp', vcp_code)
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
                    raise TypeError('Unsupported VCP type {} for monitor {} vcp_code {}'.format(
                        type_indicator, vdu_id, vcp_code))
            print("WARNING: obtained garbage '" + result.stdout.decode('utf-8') + "' will try again.")
            print("WARNING: ddcutil maybe running too fast for monitor {}, try increasing --sleep-multiplier.".format(
                vdu_id))
            time.sleep(2)
        print("ERROR: ddcutil failed all attempts to get value for monitor {} vcp_code {}".format(vdu_id, vcp_code))
        raise ValueError(
            "ddcutil returned garbage for monitor {} vcp_code {}, try increasing --sleep-multiplier".format(
                vdu_id, vcp_code))

    def set_attribute(self, vdu_id: str, vcp_code: str, new_value: str):
        """Send a new value to a specific VDU and vcp_code."""
        current, _ = self.get_attribute(vdu_id, vcp_code)
        if new_value != current:
            self.__run__('--display', vdu_id, 'setvcp', vcp_code, new_value)

    def vcp_info(self):
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return self.__run__('--verbose', 'vcpinfo').stdout.decode('utf-8')

    def get_supported_vcp_codes(self):
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
                vcp_def = VcpGuiControlDef(vcp_code=vcp_code, vcp_name=vcp_name)
                if vcp_code not in self.supported_codes:
                    self.supported_codes[vcp_code] = vcp_def
        return self.supported_codes


class DdcVdu:
    """
    Holds data specific to an individual VDU including a map of its capabilities.

    Capabilities are either extracted from ddcutil output or read from a ~/.config/vdu-control/ file.
    The file option is available so that the output from "ddcutil --display N capabilities" can be corrected because
    it is sometimes incorrect (due to sloppy implementation by manufacturers). For example, my LG monitor reports
    two Display-Port inputs and it only has one.
    """

    def __init__(self, vdu_id, vdu_model, vdu_serial, manufacturer, ddcutil: DdcUtil):
        self.id = vdu_id
        self.model = vdu_model
        self.serial = vdu_serial
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        alt_capability_text = None
        unacceptable_char_pattern = re.compile('[^A-Za-z0-9._-]')
        serial_config = re.sub(unacceptable_char_pattern, '_', vdu_model.strip() + '_' + vdu_serial.strip()) + '.conf'
        model_config = re.sub(unacceptable_char_pattern, '_', vdu_model.strip()) + '.conf'
        for config_filename in (serial_config, model_config):
            config_path = Path.home().joinpath('.config').joinpath('vdu_controls').joinpath(config_filename)
            print("INFO: checking for config file '" + config_path.as_posix() + "'")
            if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
                alt_capability_text = Path(config_path).read_text()
                print("WARNING: using config file '" + config_path.as_posix() + "'")
                break
        self.capabilities = ddcutil.query_capabilities(vdu_id, alt_capability_text)

    def get_description(self) -> str:
        """Return a unique description using the serial-number (if defined) or vdu_id."""
        return self.model + ':' + (self.serial if len(self.serial) != 0 else self.id)

    def get_full_id(self) -> Tuple[str, str, str, str]:
        """Return a tuple that defines this VDU: (vdu_id, manufacturer, model, serial-number)."""
        return self.id, self.manufacturer, self.model, self.serial


def restart_due_to_config_change():
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


class DdcSliderWidget(QWidget):
    """
    GUI control for a DDC continuously variable attribute.

    A compound widget with icon, slider, and text-field.  This is a duck-typed GUI control widget (could inherit
    from an abstract type if we wanted to get formal about it).
    """

    def __init__(self, vdu: DdcVdu, vcp_capability: VcpCapability):
        """Construct the slider control an initialize its values from the VDU."""
        super().__init__()

        self.vdu = vdu
        self.vcp_capability = vcp_capability
        self.current_value, self.max_value = vdu.ddcutil.get_attribute(vdu.id, self.vcp_capability.vcp_code)

        layout = QHBoxLayout()
        self.setLayout(layout)

        if vcp_capability.vcp_code in SUPPORTED_VCP_CONTROLS and \
                SUPPORTED_VCP_CONTROLS[vcp_capability.vcp_code].icon_source is not None:
            svg_icon = QSvgWidget()
            svg_icon.load(SUPPORTED_VCP_CONTROLS[vcp_capability.vcp_code].icon_source)
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

        def slider_changed(value):
            self.current_value = str(value)
            text_input.setText(self.current_value)
            self.vdu.ddcutil.set_attribute(self.vdu.id, self.vcp_capability.vcp_code, self.current_value)
            if self.vcp_capability.vcp_code in SUPPORTED_VCP_CONTROLS and \
                    SUPPORTED_VCP_CONTROLS[self.vcp_capability.vcp_code].causes_config_change:
                # The VCP command has turned one off a VDU or changed what it is connected to.
                # VDU ID's will now be out of whack - restart the GUI.
                restart_due_to_config_change()

        slider.valueChanged.connect(slider_changed)

        def slider_moved(value):
            text_input.setText(str(value))

        slider.sliderMoved.connect(slider_moved)

        def text_changed():
            slider.setValue(int(text_input.text()))

        text_input.editingFinished.connect(text_changed)

    def refresh_data(self):
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here)."""
        self.current_value, _ = self.vdu.ddcutil.get_attribute(self.vdu.id, self.vcp_capability.vcp_code)

    def refresh_view(self):
        """Copy the internally cached current value onto the GUI view."""
        self.slider.setValue(int(self.current_value))


class DdcComboBox(QWidget):
    """
    GUI control for a DDC non-continuously variable attribute, one that has a list of choices.

    This is a duck-typed GUI control widget (could inherit from an abstract type if we wanted to get formal about it).
    """

    def __init__(self, vdu: DdcVdu, vcp_capability: VcpCapability):
        """Construct the combobox control an initialize its values from the VDU."""
        super().__init__()

        self.vdu = vdu
        self.vcp_capability = vcp_capability
        self.current_value = vdu.ddcutil.get_attribute(vdu.id, vcp_capability.vcp_code)[0]

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

        def index_changed(index: int):
            self.current_value = self.combo_box.currentData
            self.vdu.ddcutil.set_attribute(self.vdu.id, self.vcp_capability.vcp_code, self.combo_box.currentData())
            if self.vcp_capability.vcp_code in SUPPORTED_VCP_CONTROLS and \
                    SUPPORTED_VCP_CONTROLS[self.vcp_capability.vcp_code].causes_config_change:
                restart_due_to_config_change()

        combo_box.currentIndexChanged.connect(index_changed)

    def refresh_data(self):
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here)."""
        self.current_value, _ = self.vdu.ddcutil.get_attribute(self.vdu.id, self.vcp_capability.vcp_code)

    def refresh_view(self):
        """Copy the internally cached current value onto the GUI view."""
        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))


class DdcVduWidget(QWidget):
    """
    Widget that contains all the controls for a single VDU (monitor/display).

    The widget maintains a list of GUI "controls" that are duck-typed and will have refresh_data() and refresh_view()
    methods.
    """

    def __init__(self, vdu: DdcVdu, enabled_vcp_codes: List[str], warnings: bool):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        # label.setStyleSheet("font-weight: bold");
        label.setText(translate('Monitor {}: {}').format(vdu.id, vdu.get_description()))
        layout.addWidget(label)
        self.vdu = vdu
        self.vcp_controls = []
        for vcp_code in enabled_vcp_codes:
            if vcp_code in vdu.capabilities:
                control = None
                capability = vdu.capabilities[vcp_code]
                if capability.vcp_type == CONTINUOUS_TYPE:
                    control = DdcSliderWidget(vdu, capability)
                elif capability.vcp_type == SIMPLE_NON_CONTINUOUS_TYPE:
                    try:
                        control = DdcComboBox(vdu, capability)
                    except ValueError as valueError:
                        alert = QMessageBox()
                        alert.setText(valueError.args[0])
                        alert.setInformativeText(
                            translate('If you want to extend the set of permitted values, see the man page concerning '
                                      'VDU/VDU-model config files .').format(capability.vcp_code, capability.name))
                        alert.setIcon(QMessageBox.Critical)
                        alert.exec()
                else:
                    raise TypeError(
                        'No GUI support for VCP type {} for vcp_code {}'.format(capability.vcp_type, vcp_code))
                if control is not None:
                    layout.addWidget(control)
                    self.vcp_controls.append(control)
            elif warnings:
                missing_vcp = SUPPORTED_VCP_CONTROLS[vcp_code].name if vcp_code in SUPPORTED_VCP_CONTROLS else vcp_code
                alert = QMessageBox()
                alert.setText(
                    translate('Monitor {} lacks a VCP control for {}.').format(
                        vdu.get_description(), translate(missing_vcp)))
                alert.setInformativeText(translate('No read/write ability for vcp_code {}.').format(vcp_code))
                alert.setIcon(QMessageBox.Warning)
                alert.exec()
        if len(self.vcp_controls) != 0:
            self.setLayout(layout)

    def refresh_data(self):
        """Tell the control widgets to get fresh VDU data (may be called from a task thread, so no GUI op's here)."""
        for control in self.vcp_controls:
            control.refresh_data()

    def refresh_view(self):
        """Tell the control widgets to refresh their views from their internally cached values."""
        for control in self.vcp_controls:
            control.refresh_view()

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)


class DdcMainWidget(QWidget):
    """GUI for detected VDU's, it will construct and contain a control panel for each VDU."""

    def __init__(self, enabled_vcp_codes: List[str], warnings: bool, debug: bool, sleep_multiplier: float,
                 detect_vdu_hook: callable):
        super().__init__()
        layout = QVBoxLayout()
        self.ddcutil = DdcUtil(debug=debug, common_args=['--sleep-multiplier', str(sleep_multiplier)])
        self.vdu_widgets = []
        self.enabled_capabilities = enabled_vcp_codes
        self.warnings = warnings
        self.detected_vdus = self.ddcutil.detect_monitors()
        for vdu_id, manufacturer, vdu_model, vdu_serial in self.detected_vdus:
            vdu = DdcVdu(vdu_id, vdu_model, vdu_serial, manufacturer, self.ddcutil)
            if detect_vdu_hook is not None:
                detect_vdu_hook(vdu)
            vdu_widget = DdcVduWidget(vdu, enabled_vcp_codes, warnings)
            if vdu_widget.number_of_controls() != 0:
                self.vdu_widgets.append(vdu_widget)
                layout.addWidget(vdu_widget)
            elif warnings:
                alert = QMessageBox()
                alert.setText(
                    translate('Monitor {} {} lacks any accessible controls.').format(vdu.id, vdu.get_description()))
                alert.setInformativeText(translate('The monitor will be omitted from the control panel.'))
                alert.setIcon(QMessageBox.Warning)
                alert.exec()

        if len(self.vdu_widgets) == 0:
            alert = QMessageBox()
            alert.setText(translate('No controllable monitors found, exiting.'))
            alert.setInformativeText(translate(
                '''Run ddc_control --debug in a console and check for additional messages.\
                Check the requirements for the ddcutil command.'''))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()
            sys.exit()

        def start_refresh():
            # Refreshes from all values from ddcutil.  May be slow, starts a busy spinner and then
            # starts the work in a task thread.
            self.refresh_button.setDisabled(True)
            self.progressBar.setDisabled(False)
            # Setting range to 0,0 cause the progress bar to pulsate left/right - used as a busy spinner.
            self.progressBar.setRange(0, 0)
            # Start the background task
            self.refreshDataTask.start()

        def finish_refresh():
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

        self.setLayout(layout)

    def refresh_data(self):
        """Refresh data from the VDU's. Called by a non-GUI task. Not in the GUI-thread, cannot do any GUI op's."""
        self.detected_vdus = self.ddcutil.detect_monitors()
        for vdu_widget in self.vdu_widgets:
            if vdu_widget.vdu.get_full_id() in self.detected_vdus:
                vdu_widget.refresh_data()

    def refresh_view(self):
        """Invoke when the GUI worker thread completes. Runs in the GUI thread and can refresh the GUI views."""
        if len(self.detected_vdus) != len(self.vdu_widgets):
            # The number of VDU's has changed, vdu_id's will no longer match, throw a wobbly
            restart_due_to_config_change()
        for vdu_widget in self.vdu_widgets:
            vdu_widget.refresh_view()


class RefreshVduDataTask(QThread):
    """
    Task to refresh VDU data from the physical VDU's.

    Runs as a task because it can be quite slow depending on the number of VDU's, number of controls.  The task runs
    outside the GUI thread and no parts of it can only update the GUI data, not the GUI view.
    """

    task_finished = pyqtSignal()

    def __init__(self, ddc_widget):
        """Initialise the task that will run in a non-GUI thread to update all the widget's data."""
        super().__init__()
        self.ddc_widget = ddc_widget

    def run(self):
        """Run a task that uses ddcutil to retrieve data for all the visible controls (may be slow)."""
        # Running in a task thread, cannot interact with GUI thread, just update the data.
        self.ddc_widget.refresh_data()
        # Tell (qt-signal) the GUI-thread that the task has finished, the GUI thread will then update the view widgets.
        self.task_finished.emit()


def exception_handler(e_type, e_value, e_traceback):
    """Overarching error handler in case something unexpected happens."""
    print("ERROR:\n", ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    alert = QMessageBox()
    alert.setText(translate('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))))
    alert.setInformativeText(
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
        print("ERROR: No desktop directory is present:{}".format(desktop_dir.as_posix()),
              "Cannot proceed - is this a non-standard desktop?")
        return

    bin_dir = Path.home().joinpath('bin')
    if not bin_dir.is_dir():
        print("ERROR: No desktop bin directory is present:{}".format(bin_dir.as_posix()),
              "Cannot proceed - is this a non-standard desktop?")
        return

    installed_script_path = bin_dir.joinpath("vdu_controls")
    desktop_definition_path = desktop_dir.joinpath("vdu_controls.desktop")

    if uninstall:
        os.remove(installed_script_path)
        print('INFO: removed {}'.format(installed_script_path.as_posix()))
        os.remove(desktop_definition_path)
        print('INFO: removed {}'.format(desktop_definition_path.as_posix()))
        return

    if installed_script_path.exists():
        print("WARNING: skipping installation of {}, it is already present.".format(installed_script_path.as_posix()))
    else:
        source = open(__file__).read()
        source = source.replace("#!/usr/bin/python3", '#!' + sys.executable)
        print('INFO: creating {}'.format(installed_script_path.as_posix()))
        open(installed_script_path, 'w').write(source)
        print('INFO: chmod u+rwx {}'.format(installed_script_path.as_posix()))
        os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        print("WARNING: skipping installation of {}, it is already present.".format(desktop_definition_path.as_posix()))
    else:
        print('INFO: creating {}'.format(desktop_definition_path.as_posix()))
        desktop_definition = textwrap.dedent("""
            [Desktop Entry]
            Type=Application
            Exec={} --show brightness --show audio-volume
            Name=VDU Controls
            GenericName=VDU controls
            Comment=Virtual Control Panel for externally connected VDU's
            Icon=preferences-desktop-display-color
            Categories=Qt;Settings;
            """).format(installed_script_path.as_posix())
        open(desktop_definition_path, 'w').write(desktop_definition)

    print('INFO: installation complete. Your desktop->applications->settings should now contain VDU Controls')


def main():
    """vdu_control application main."""
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
        VDU Controls 
          Uses ddcutil to issue Display Data Channel (DDC) Virtual Control Panel (VCP) commands. 
          Controls DVI/DP/HDMI/USB connected monitors (but not builtin laptop displays)."""),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--show',
                        default=[],
                        action='append', choices=[vcp.arg_name() for vcp in SUPPORTED_VCP_CONTROLS.values()],
                        help='show specified control only (--show may be specified multiple times)')
    parser.add_argument('--hide', default=[], action='append',
                        choices=[vcp.arg_name() for vcp in SUPPORTED_VCP_CONTROLS.values()],
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
    parser.add_argument('--install', action='store_true',
                        help="installs the vdu_controls in the current user's path and desktop application menu.")
    parser.add_argument('--uninstall', action='store_true',
                        help='uninstalls the vdu_controls application menu file and script for the current user.')
    args = parser.parse_args()
    if args.install:
        install_as_desktop_application()
        sys.exit()
    if args.uninstall:
        install_as_desktop_application(uninstall=True)
        sys.exit()

    sys.excepthook = exception_handler
    app = QApplication(sys.argv)
    pixmap = get_splash_image()
    splash = None if args.no_splash else QSplashScreen(pixmap.scaledToWidth(800).scaledToHeight(400),
                                                       Qt.WindowStaysOnTopHint)
    if splash is not None:
        splash.show()
        # Attempt to force it to the top with raise and activate
        splash.raise_()
        splash.activateWindow()
    app_icon = QIcon()
    app_icon.addPixmap(pixmap)

    tray = None
    if args.system_tray:
        tray = QSystemTrayIcon()
        tray.setIcon(app_icon)
        menu = QMenu()
        menu.addAction(create_icon_from_svg_string(QUIT_APP_SVG), translate('Quit'), app.quit)
        tray.setContextMenu(menu)

    app.setWindowIcon(app_icon)
    app.setApplicationDisplayName(translate('VDU Controls'))

    if len(args.show) != 0:
        enabled_vcp_codes = [x.vcp_code for x in SUPPORTED_VCP_CONTROLS.values() if x.arg_name() in args.show]
    else:
        enabled_vcp_codes = [x.vcp_code for x in SUPPORTED_VCP_CONTROLS.values() if x.arg_name() not in args.hide]
    if args.enable_vcp_code is not None:
        enabled_vcp_codes.extend(args.enable_vcp_code)
    if splash is not None:
        splash.showMessage(translate('\n\nVDU Controls\nLooking for DDC monitors...\n'), Qt.AlignTop | Qt.AlignHCenter)

    def detect_vdu_hook(vdu: DdcVdu):
        if splash is not None:
            splash.showMessage(translate('\n\nVDU Controls\nDDC ID {}\n{}').format(vdu.id, vdu.get_description()),
                               Qt.AlignTop | Qt.AlignHCenter)

    main_window = DdcMainWidget(enabled_vcp_codes, args.warnings, args.debug, args.sleep_multiplier, detect_vdu_hook)

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
