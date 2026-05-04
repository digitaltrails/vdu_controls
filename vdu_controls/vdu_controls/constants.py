# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path
from importlib.resources import files as resources_files

APPNAME = "VDU Controls"
VDU_CONTROLS_VERSION = '2.6.5'
VDU_CONTROLS_VERSION_TUPLE = tuple(int(i) for i in VDU_CONTROLS_VERSION.split('.'))
assert sys.version_info >= (3, 8), f'{APPNAME} utilizes python version 3.8 or greater (your python is {sys.version}).'

CONFIG_DIR_PATH = Path.home() / '.config/vdu_controls'
CONFIG_FILE_PREFER_QT5 = CONFIG_DIR_PATH / '_prefer_qt5_'

TOOLTIP_DURATION_MSEC = 750

WESTERN_SKY = 'western-sky'
EASTERN_SKY = 'eastern-sky'

IP_ADDRESS_INFO_URL = os.getenv('VDU_CONTROLS_IPINFO_URL', default='https://ipinfo.io/json')
WEATHER_FORECAST_URL = os.getenv('VDU_CONTROLS_WTTR_URL', default='https://wttr.in')
TESTING_TIME_ZONE = os.getenv('VDU_CONTROLS_TEST_TIME_ZONE')  # for example, 'Europe/Berlin' 'Asia/Shanghai'
TESTING_TIME_DELTA = None  # timedelta(hours=-6.2)

HELP_FILENAME = "help.md"

VDU_CONTROLS_DEVELOPER = os.getenv('VDU_CONTROLS_DEVELOPER', default="no") == 'yes'

CURRENT_PRESET_NAME_FILE = CONFIG_DIR_PATH / 'current_preset.txt'
CUSTOM_TRAY_ICON_FILE = CONFIG_DIR_PATH / 'tray_icon.svg'


STANDARD_ICON_PATHS = (Path("/usr/share/vdu_controls/icons"), Path("/usr/share/icons/breeze/actions/24"), Path("/usr/share/icons"),)

# Use a slight hack to make MsgBox.resizable.
RESIZABLE_MESSAGEBOX_HACK = True

DEVELOPERS_NATIVE_FONT_HEIGHT = 32  # The font height in physical pixels being used on my development desktop.


class MsgDestination(Enum):
    DEFAULT = 0
    COUNTDOWN = 1


PRESET_SIGNAL_MIN = 40
PRESET_SIGNAL_MAX = 55

# On Plasma Wayland, the system tray may not be immediately available at login - so keep trying for...
SYSTEM_TRAY_WAIT_SECONDS = 20

# Internal special exit code used to signal that the exit handler should restart the program.
EXIT_CODE_FOR_RESTART = 1959

IGNORE_VDU_MARKER_STR = 'Ignore VDU'

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
