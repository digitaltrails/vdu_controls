# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from vdu_controls.qt_imports import QFontMetrics, QLabel
import vdu_controls.logging as log
from vdu_controls.constants import DEVELOPERS_NATIVE_FONT_HEIGHT

desktop_font_height_pixels: int | None = None  # A metric for use in sizing components relative to DEVELOPERS_NATIVE_FONT_HEIGHT.


def desktop_font_height(scaled: int | float = 1) -> int:  # In real hardware pixels
    global desktop_font_height_pixels
    if desktop_font_height_pixels is None:
        desktop_font_height_pixels = QFontMetrics(QLabel("ABC").font()).height()
        log.info(f"{desktop_font_height_pixels=}")
    pixels = round(desktop_font_height_pixels * scaled)
    # log.debug(f"{pixels=}")
    return pixels


def npx(developers_pixels: int):  # developers original value scaled to desktop pixels on this user's desktop
    return round((desktop_font_height() * developers_pixels) / DEVELOPERS_NATIVE_FONT_HEIGHT)

def dpx(developers_pixels: int):  # developers original value scaled to desktop pixels on this user's desktop
    desktop_pixels = round((desktop_font_height() * developers_pixels) / DEVELOPERS_NATIVE_FONT_HEIGHT)
    # log.debug(f"{developers_pixels=} {desktop_pixels=}")
    return desktop_pixels
