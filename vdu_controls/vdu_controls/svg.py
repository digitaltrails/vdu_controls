# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
from importlib.resources import files as resources_files

import vdu_controls.logging as log
from vdu_controls.qt_imports import QColor


def load_svg_source(source_filename: str):
    log.debug(f'Loading SVG source from {source_filename}')
    svg_file = resources_files('vdu_controls') / 'resources' / 'icons' / 'app' / source_filename
    return svg_file.read_bytes()


MONOCHROME_APP_ICON_SOURCE = load_svg_source('monochrome-app-icon.svg')

FALLBACK_SPLASH_SOURCE = load_svg_source('fallback-splash.svg')

BRIGHTNESS_SVG = load_svg_source('brightness.svg')

SUN_SVG = re.sub(b'm0 1c1.662777 0 3 1.3372234[^"]+"', b'"', BRIGHTNESS_SVG)

CONTRAST_SVG = load_svg_source('contrast.svg')

AUTO_LUX_ON_SVG = BRIGHTNESS_SVG.replace(b'viewBox="0 0 24 24"', b'viewBox="3 3 18 18"').replace(b'#232629', b'#ff8500')
AUTO_LUX_OFF_SVG = BRIGHTNESS_SVG.replace(b'viewBox="0 0 24 24"', b'viewBox="3 3 18 18"').replace(b'#232629', b'#84888c')
AUTO_LUX_LED_COLOR = QColor(0xff8500)
PRESET_TRANSITIONING_LED_COLOR = QColor(0x55ff00)

COLOR_TEMPERATURE_SVG = load_svg_source('color_temperature.svg')

VOLUME_SVG = load_svg_source('volume.svg')

MENU_ICON_SOURCE = load_svg_source('menu_icon.svg')

VDU_CONNECTED_ICON_SOURCE = load_svg_source('vdu_connected_icon.svg')

PANEL_CONNECTED_ICON_SOURCE = load_svg_source('panel_connected_icon.svg')

VDU_POWER_ON_ICON_SOURCE = load_svg_source('vdu_power_on_icon.svg')

AMBIENT_PANEL_ICON_SOURCE = load_svg_source('ambient_panel_icon.svg')

REFRESH_ICON_SOURCE = load_svg_source('refresh_icon.svg')

LIGHTING_CHECK_SVG = load_svg_source('lighting_check.svg')

LIGHTING_CHECK_OFF_SVG = LIGHTING_CHECK_SVG.replace(b'#ff8500', b'#84888c')

TRANSITION_ICON_SOURCE = load_svg_source('transition_icon.svg')

SWATCH_ICON_SOURCE = load_svg_source('swatch_icon.svg')

LUX_SUNLIGHT_SVG = load_svg_source('lux_sunlight.svg')

LUX_DAYLIGHT_SVG = load_svg_source('lux_daylight.svg')

LUX_OVERCAST_SVG = load_svg_source('lux_overcast.svg')

LUX_TWILIGHT_SVG = load_svg_source('lux_twilight.svg')

LUX_SUBDUED_SVG = load_svg_source('lux_subdued.svg')

LUX_DARK_SVG = load_svg_source('lux_dark.svg')