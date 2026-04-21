# SPDX-FileCopyrightText: 2021-2026 Michael Hamilton
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys
from pathlib import Path

APPNAME = "VDU Controls"
VDU_CONTROLS_VERSION = '2.6.0'
VDU_CONTROLS_VERSION_TUPLE = tuple(int(i) for i in VDU_CONTROLS_VERSION.split('.'))
assert sys.version_info >= (3, 8), f'{APPNAME} utilises python version 3.8 or greater (your python is {sys.version}).'

CONFIG_DIR_PATH = Path.home().joinpath('.config', 'vdu_controls')
CONFIG_FILE_PREFER_QT5 = CONFIG_DIR_PATH.joinpath('_prefer_qt5_')

TOOLTIP_DURATION_MSEC = 750

WESTERN_SKY = 'western-sky'
EASTERN_SKY = 'eastern-sky'

IP_ADDRESS_INFO_URL = os.getenv('VDU_CONTROLS_IPINFO_URL', default='https://ipinfo.io/json')
WEATHER_FORECAST_URL = os.getenv('VDU_CONTROLS_WTTR_URL', default='https://wttr.in')
TESTING_TIME_ZONE = os.getenv('VDU_CONTROLS_TEST_TIME_ZONE')  # for example, 'Europe/Berlin' 'Asia/Shanghai'
TESTING_TIME_DELTA = None  # timedelta(hours=-6.2)

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
Vdu_controls relies on <a href="https://www.ddcutil.com/">ddcutil</a>, a robust interface to DDC capable VDUs.
<br>
At your request, your geographic location may be retrieved from <a href="{IP_ADDRESS_INFO_URL}">{IP_ADDRESS_INFO_URL}</a>.
<br>
At your request, weather for your location may be retrieved from <a href="{WEATHER_FORECAST_URL}">{WEATHER_FORECAST_URL}</a>.
</small>
</quote>
"""

VDU_CONTROLS_DEVELOPER = os.getenv('VDU_CONTROLS_DEVELOPER', default="no") == 'yes'


CURRENT_PRESET_NAME_FILE = CONFIG_DIR_PATH.joinpath('current_preset.txt')
CUSTOM_TRAY_ICON_FILE = CONFIG_DIR_PATH.joinpath('tray_icon.svg')
LOCALE_TRANSLATIONS_PATHS = [
    Path.cwd().joinpath('translations')] if VDU_CONTROLS_DEVELOPER else [] + [
    Path(CONFIG_DIR_PATH).joinpath('translations'), Path("/usr/share/vdu_controls/translations"), ]
STANDARD_ICON_PATHS = (Path("/usr/share/vdu_controls/icons"), Path("/usr/share/icons/breeze/actions/24"), Path("/usr/share/icons"),)

# Use a slight hack to make MsgBox.resizable.
RESIZABLE_MESSAGEBOX_HACK = True


DEVELOPERS_NATIVE_FONT_HEIGHT = 32  # The font height in physical pixels being used on my development desktop.

