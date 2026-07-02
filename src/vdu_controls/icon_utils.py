# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict

from vdu_controls.qt_imports import (QStyle, QWidget, QImage, QIcon, QPixmap, Qt, QSvgRenderer, QFont, QColor, QPainter,
                                     QPen, QApplication, QSize, QPalette)
from vdu_controls.svg import SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR, SVG_DARK_THEME_TEXT_COLOR, SVG_LIGHT_THEME_TEXT_COLOR, \
    SVG_MONOCHROME_LIGHT_FG_COLOR, SVG_WHITE_COLOR, SVG_BLACK_COLOR, SVG_MONOCHROME_DARK_FG_COLOR


class ThemeType(Enum):  # Indicates how colors should be altered to fit a color theme.
    UNTHEMED = 5,          # Unthemed - for colored app icon - overlay should be unthemed.
    UNDECIDED = 0,         # Theme to be decided - normal icon - will force a dark/light theme lookup
    POLYCHROME_LIGHT = 1,  # Normal icon - after decision
    POLYCHROME_DARK = 2,   # Normal icon
    MONOCHROME_LIGHT = 3,  # Monochrome icon - for tray use - light themed tray
    MONOCHROME_DARK = 4,   # Monochrome icon - for tray use - dark themed tray


StdPixmap = QStyle.StandardPixmap


def si(widget: QWidget, std_pixmap: QStyle.StandardPixmap) -> QIcon:  # Qt bundled standard icons (which are themed)
    widget_style = widget.style()
    assert widget_style is not None
    return widget_style.standardIcon(std_pixmap)


def create_pixmap_from_svg_bytes(svg_bytes: bytes, width: int = 64, height: int = 64) -> QPixmap:
    """There is no QIcon option for loading SVG from a string, only from an SVG file, so roll our own."""
    return QPixmap.fromImage(create_image_from_svg_bytes(svg_bytes, width, height))


def create_image_from_svg_bytes(svg_bytes, width: int = 64, height: int = 64) -> QImage:
    renderer = QSvgRenderer(svg_bytes)
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


svg_icon_cache: Dict[bytes, QIcon] = {}


def create_icon_from_svg_bytes(svg_bytes: bytes, theme_type: ThemeType = ThemeType.UNDECIDED) -> QIcon:
    """
    There is no QIcon option for loading SVG from a string,
    only from an SVG file, so roll our own.
    """
    if theme_type == ThemeType.UNDECIDED:
        theme_type = polychrome_light_or_dark()
    svg_bytes = handle_theme(svg_bytes, theme_type)
    if icon := svg_icon_cache.get(svg_bytes):
        return icon
    icon = QIcon(create_pixmap_from_svg_bytes(svg_bytes))
    svg_icon_cache[svg_bytes] = icon
    return icon


def handle_theme(svg_bytes: bytes, theme_type: ThemeType):
    assert theme_type != ThemeType.UNDECIDED
    if theme_type == ThemeType.MONOCHROME_LIGHT:
        return svg_bytes.replace(SVG_LIGHT_THEME_COLOR, SVG_MONOCHROME_LIGHT_FG_COLOR).replace(SVG_WHITE_COLOR, SVG_BLACK_COLOR)
    elif theme_type == ThemeType.MONOCHROME_DARK:
        return svg_bytes.replace(SVG_LIGHT_THEME_COLOR, SVG_MONOCHROME_DARK_FG_COLOR).replace(SVG_BLACK_COLOR, SVG_WHITE_COLOR)
    elif theme_type == ThemeType.POLYCHROME_LIGHT:
        return svg_bytes
    elif theme_type == ThemeType.POLYCHROME_DARK:
        return svg_bytes.replace(SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR)
    return svg_bytes


def create_icon_from_path(path: Path, theme_type: ThemeType) -> QIcon:
    if path.exists():
        if path.suffix == '.svg':
            with open(path, 'rb') as icon_file:
                icon_bytes = icon_file.read()
                icon = create_icon_from_svg_bytes(icon_bytes, theme_type)
        else:  # Hope the file contains something QIcon can cope with:
            icon = QIcon(path.as_posix())
        return icon
    # Copes with the case where the path has been deleted.
    app_style = QApplication.style()
    assert app_style is not None
    return app_style.standardIcon(StdPixmap.SP_MessageBoxQuestion)


def create_icon_from_text(text: str, theme_type: ThemeType) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    font = QApplication.font()
    font.setPixelSize(24)
    font.setWeight(QFont.Weight.Medium)
    painter.setFont(font)
    painter.setOpacity(1.0)
    if theme_type == ThemeType.MONOCHROME_LIGHT:
        painter.setPen(QColor(SVG_MONOCHROME_LIGHT_FG_COLOR.decode('utf-8')))
    elif theme_type == ThemeType.MONOCHROME_DARK:
        painter.setPen(QColor(SVG_MONOCHROME_DARK_FG_COLOR.decode('utf-8')))
    elif theme_type == ThemeType.POLYCHROME_DARK:
        painter.setPen(QColor(SVG_DARK_THEME_TEXT_COLOR.decode("utf-8")))
    else:  # default to a dark text color
        painter.setPen(QColor(SVG_LIGHT_THEME_TEXT_COLOR.decode("utf-8")))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignTop, text)
    painter.end()
    return QIcon(pixmap)


def create_decorated_app_icon(base_icon: QIcon, overlay_icon: QIcon | None = None,
                              left_indicator: QColor | None = None, right_indicator: QColor | None = None) -> QIcon:
    """
    Non-destructively overlay overlay_icon and indicators within a copy of base_icon.
    """
    icon_size = QSize(64, 64)  # Everything is hard coded based on 64x64
    combined_pixmap = QPixmap(base_icon.pixmap(icon_size, QIcon.Mode.Normal, QIcon.State.On))
    painter = QPainter(combined_pixmap)
    if overlay_icon:
        overlay_pixmap = overlay_icon.pixmap(icon_size, QIcon.Mode.Normal, QIcon.State.On)
        painter.drawPixmap(16, 8, 32, 32, overlay_pixmap)
    painter.setPen(QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine))
    for i, led_color in enumerate((left_indicator, right_indicator)):
        if led_color:
            painter.setBrush(led_color)  # Each indicator resembles/simulates an LED embedded in the app icon.
            painter.drawEllipse(8 if i == 0 else 44, 32, 16, 16)
    painter.end()
    return QIcon(combined_pixmap)

def is_dark_theme() -> bool:
    palette = QPalette()
    text_color, window_color = palette.color(QPalette.ColorRole.WindowText), palette.color(QPalette.ColorRole.Window)
    return text_color.lightness() > window_color.lightness()

def polychrome_light_or_dark():
    return ThemeType.POLYCHROME_DARK if is_dark_theme() else ThemeType.POLYCHROME_LIGHT

