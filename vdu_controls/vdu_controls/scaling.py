# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from vdu_controls.qt_imports import QFontMetrics, QLabel
from vdu_controls.logging import log_info
from vdu_controls.constants import DEVELOPERS_NATIVE_FONT_HEIGHT

native_font_height_pixels: int | None = None  # A metric for use in sizing components relative to DEVELOPERS_NATIVE_FONT_HEIGHT.


def native_font_height(scaled: int | float = 1):  # In real hardware pixels
    global native_font_height_pixels
    if native_font_height_pixels is None:
        native_font_height_pixels = QFontMetrics(QLabel("ABC").font()).height()
        log_info(f"{native_font_height_pixels=}")
    return round(native_font_height_pixels * scaled)


def npx(developers_pixels: int):  # native pixels - real hardware pixels
    return round((native_font_height() * developers_pixels) / DEVELOPERS_NATIVE_FONT_HEIGHT)
