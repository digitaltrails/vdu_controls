# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from importlib.resources import files as resources_files

import vdu_controls.logging as log
from vdu_controls.qt_imports import QColor


def load_svg_source(source_filename: str) -> bytes:
    log.debug(f'Loading SVG source from {source_filename}')
    svg_file = resources_files('vdu_controls') / 'resources' / 'icons' / 'app' / source_filename
    return svg_file.read_bytes()


SVG_LIGHT_THEME_COLOR = b"#232629"
SVG_LIGHT_THEME_TEXT_COLOR = b"#000000"
SVG_DARK_THEME_COLOR = b"#f3f3f3"
SVG_DARK_THEME_TEXT_COLOR = SVG_DARK_THEME_COLOR

SVG_WHITE_COLOR = b"#ffffff"
SVG_BLACK_COLOR = b"#000000"

SVG_MONOCHROME_LIGHT_FG_COLOR = b"#000000"
SVG_MONOCHROME_DARK_FG_COLOR = b"#ffffff"

SVG_PRESET_DIALOG_SUN_COLOR = b"#fecf70"

SVG_AUTO_LUX_LED_COLOR = b'#ff8500'
SVG_AUTO_LUX_OFF_LED_COLOR = b'#84888c'

AUTO_LUX_LED_QCOLOR = QColor(SVG_AUTO_LUX_LED_COLOR.decode('utf-8'))
PRESET_TRANSITIONING_LED_QCOLOR = QColor(0x55ff00)

SVG_SWATCH_ICON_BASE_COLOR = b"#ffffff"

TRAY_COLOR_ICON_SVG = load_svg_source('tray_color_icon.svg')   # Works on light or dark tray themes (kinda)

TRAY_MONOCHROME_ICON_SVG = load_svg_source('tray_monochrome_icon.svg')   # Needs handling on theme changes.

FALLBACK_SPLASH_SVG = load_svg_source('fallback-splash.svg')    # Not currently used.

BRIGHTNESS_SVG = load_svg_source('brightness.svg')

SUN_SVG = load_svg_source('sun.svg')

CONTRAST_SVG = load_svg_source('contrast.svg')

PRESET_DIALOG_SUN_SVG = SUN_SVG.replace(SVG_LIGHT_THEME_COLOR, SVG_PRESET_DIALOG_SUN_COLOR)

AUTO_LUX_ON_SVG = load_svg_source('auto_lux_on.svg').replace(SVG_LIGHT_THEME_COLOR, SVG_AUTO_LUX_LED_COLOR)

AUTO_LUX_OFF_SVG = AUTO_LUX_ON_SVG.replace(SVG_LIGHT_THEME_COLOR, SVG_AUTO_LUX_OFF_LED_COLOR)

COLOR_TEMPERATURE_SVG = load_svg_source('color_temperature.svg')

VOLUME_SVG = load_svg_source('volume.svg')

MENU_ICON_SVG = load_svg_source('menu_icon.svg')

VDU_CONNECTED_ICON_SVG = load_svg_source('vdu_connected_icon.svg')

PANEL_CONNECTED_ICON_SVG = load_svg_source('panel_connected_icon.svg')

VDU_POWER_ON_ICON_SVG = load_svg_source('vdu_power_on_icon.svg')

VDU_PRESET_ICON_SVG = load_svg_source('vdu_preset_icon.svg')

AMBIENT_PANEL_ICON_SVG = load_svg_source('ambient_panel_icon.svg')

REFRESH_ICON_SVG = load_svg_source('refresh_icon.svg')

LIGHTING_CHECK_SVG = load_svg_source('lighting_check.svg')

LIGHTING_CHECK_OFF_SVG = LIGHTING_CHECK_SVG.replace(SVG_AUTO_LUX_LED_COLOR, SVG_AUTO_LUX_OFF_LED_COLOR)

TRANSITION_ICON_SVG = load_svg_source('transition_icon.svg')

SWATCH_ICON_SVG = load_svg_source('swatch_icon.svg')

LUX_SUNLIGHT_SVG = load_svg_source('lux_sunlight.svg')

LUX_DAYLIGHT_SVG = load_svg_source('lux_daylight.svg')

LUX_OVERCAST_SVG = load_svg_source('lux_overcast.svg')

LUX_TWILIGHT_SVG = load_svg_source('lux_twilight.svg')

LUX_SUBDUED_SVG = load_svg_source('lux_subdued.svg')

LUX_DARK_SVG = load_svg_source('lux_dark.svg')