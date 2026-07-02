# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os as _os
import re as _re
import sys as _sys
from enum import Enum as _Enum
from pathlib import Path as _Path
import vdu_controls.logging as _log


def getenv_logged(key: str, default: str = '') -> str:
    """Get an environment variable and log the result, returns '' for None"""
    value = _os.getenv(key, default=default)
    _log.info(f"getenv_logged('{key}', default='{default}') -> '{value}'")
    return value


APPNAME = "VDU Controls"

# Version Numbering Example when going beyond 2.10.15 to include beta or rc:
# Problem: there are issues with the generated artifact filenames
# like v2.10.15-rc.1.tgz.  The use of such a filename requires hacks in
# distro-packaging and python-packaging which are each expecting
# names based own their own conventions, they all agree on 2.10.15, but
# after that they're not the same:
#
# - Semantic Versioning internal in this source: 2.10.15-rc.1
# - Git Tag: 2.10.15-rc.1
# - python setup.cfg: 2.10.15rc1
# - Sphinx conf.py: 2.10.15rc1
# - RPM/DEB packaging: 2.10.15~rc.1
# - Arch packaging: 2.10.15_rc.1
#
# While testing packaging it is easier to just use a non-release normal minor
# number, such as 2.10.15, dropping .rc-1 (but keeping it internally and in
# the version reported in the About Dialog).  In this way, wider packaging
# doesn't require hacks to copy with rc/beta suffixes which we are
# never going to appear in delivered distro releases.
VDU_CONTROLS_VERSION = '2.6.5-rc.4'
VDU_CONTROLS_VERSION_TUPLE = tuple(int(i) for i in _re.split(r'[.-]', VDU_CONTROLS_VERSION)[:3])
VDU_CONTROLS_BASE_VERSION = VDU_CONTROLS_VERSION.split('-')[0]
VDU_CONTROLS_PRE_RELEASE = (VDU_CONTROLS_VERSION.split('-') + [ '' ])[1]

assert _sys.version_info >= (3, 8), f'{APPNAME} utilizes python version 3.8 or greater (your python is {_sys.version}).'

VDU_CONTROLS_WEBSITE_URL = 'https://github.com/digitaltrails/vdu_controls'
DDCUTIL_WEBSITE_URL = 'https://www.ddcutil.com/'
DDCUTIL_SERVICE_WEBSITE_URL = 'https://github.com/digitaltrails/ddcutil-service'
BRIGHTNESSCTL_WEBSITE_URL = 'https://github.com/Hummer12007/brightnessctl'

CONFIG_DIR_PATH = _Path.home() / '.config/vdu_controls'
CONFIG_FILE_PREFER_QT5 = CONFIG_DIR_PATH / '_prefer_qt5_'

TOOLTIP_DURATION_MSEC = 750

WESTERN_SKY = 'western-sky'  # TODO seems suspect - not an enum? no translations?
EASTERN_SKY = 'eastern-sky'

IP_ADDRESS_INFO_URL = getenv_logged('VDU_CONTROLS_IPINFO_URL', default='https://ipinfo.io/json')
WEATHER_FORECAST_URL = getenv_logged('VDU_CONTROLS_WTTR_URL', default='https://wttr.in')
TESTING_TIME_ZONE = getenv_logged('VDU_CONTROLS_TEST_TIME_ZONE')  # for example, 'Europe/Berlin' 'Asia/Shanghai'
TESTING_TIME_DELTA = None  # timedelta(hours=-6.2)

HELP_FILENAME = "help.md"

VDU_CONTROLS_DEVELOPER = getenv_logged('VDU_CONTROLS_DEVELOPER', default="no") == 'yes'

CURRENT_PRESET_NAME_FILE = CONFIG_DIR_PATH / 'current_preset.txt'
CUSTOM_TRAY_ICON_FILE = CONFIG_DIR_PATH / 'tray_icon.svg'

STANDARD_ICON_PATHS = (_Path("/usr/share/vdu_controls/icons"),
                       _Path("/usr/share/icons/breeze/actions/24"),
                       _Path("/usr/share/icons"),)

# Use a slight hack to make MsgBox.resizable.
RESIZABLE_MESSAGEBOX_HACK = True

# Determining the size of graphical elements. The dimensions are based on the
# pixel size of a typical character.
#
# The modern approach is to assume everyone is on a virtual 96 DPI scaled to
# physical DPI by the windowing system (X11/Waylang).  But because some software
# isn't scaling aware, scaling can cause issues when tyring to preview images at
# 100%, one image pixel may no longer map to one display pixel.  Similarly, when
# trying to measure with a ruler, 1 inch or 1 cm measured on screen may not
# agree with the value measured on a printout.  This means a window width
# set to X, might not measure X in physical pixels.
#
# In addition to any overall scaling going on, the users selection of font
# size affects spacing.   We take that into account by looking at their
# default QLabel font size versus what was used on the development PC.
#
# This number can be decreased to scale up the sizing, which will make plots
# and window dimensions slightly larger, or reduced to make things
# smaller.
#
# I'm running with hardware 193-DPI (not virtual 96-DPI), Qt thinks my
# QLabel font size is 16 pixels (remembering it this might be virtual
# scaled pixels, not actual pixels).
DEVELOPERS_NATIVE_FONT_HEIGHT = 16

class MsgDestination(_Enum):
    DEFAULT = 0
    COUNTDOWN = 1


PRESET_SIGNAL_MIN = 40
PRESET_SIGNAL_MAX = 55

# On Plasma Wayland, the system tray may not be immediately available at login - so keep trying for...
SYSTEM_TRAY_WAIT_SECONDS = 20

# Internal special exit code used to signal that the exit handler should restart the program.
EXIT_CODE_FOR_RESTART = 1959

IGNORE_VDU_MARKER_STR = 'Ignore VDU'

ASSUMED_CONTROLS_CONFIG_VCP_CODES = [0x10, 0x12]

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

# Minimum DF-adjusted Lux-value, when lux is below this, DF will no longer be updated (not enough daylight).
MIN_DF_ADJUSTED_LUX = 100

# Lowest Daylight factor the user can dial in using the slider
DF_MIN = 0.00001
# How many places to show in the DF when presenting to the user - should have as many places as DF_MIN
DF_PLACES = 5
