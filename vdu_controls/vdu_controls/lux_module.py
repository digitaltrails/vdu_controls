from __future__ import annotations

import math
import os
import pathlib
import random
import re
import select
import subprocess
import termios
import time
from ast import literal_eval
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Tuple, List, Dict, TYPE_CHECKING

from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF, QObject, QT_TR_NOOP, QTimer, QSize
from PyQt5.QtGui import QResizeEvent, QPixmap, QPainter, QColor, QPen, QPolygon, QMouseEvent, QFont
from PyQt5.QtWidgets import QLabel, QInputDialog, QWidget, QVBoxLayout, QApplication, QGridLayout, QComboBox, QCheckBox, QSpinBox, \
    QListWidget, QStatusBar, QHBoxLayout, QListWidgetItem, QSlider

from vdu_controls.config_ini import GeoLocation, ConfIni
from vdu_controls.constants import CONFIG_DIR_PATH, MsgDestination, TOOLTIP_DURATION_MSEC
from vdu_controls.ddcutil_abstract import BRIGHTNESS_VCP_CODE

from vdu_controls.ddcutil_aggregator import VduStableId
from vdu_controls.icon_utils import create_image_from_svg_bytes, SVG_LIGHT_THEME_COLOR, si, StdPixmap, create_icon_from_svg_bytes
from vdu_controls.internationalization import tr
from vdu_controls.logging import log_debug, log_debug_enabled, log_info, log_warning, log_error
from vdu_controls.misc import clamp, zoned_now, intV
from vdu_controls.preset import PresetTransitionFlag
from vdu_controls.qt_imports import QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING
from vdu_controls.scaling import npx, native_font_height
from vdu_controls.solar_calc import calc_solar_lux
from vdu_controls.svg import SUN_SVG, SWATCH_ICON_SOURCE, AUTO_LUX_ON_SVG, LIGHTING_CHECK_SVG, AUTO_LUX_OFF_SVG, \
    LIGHTING_CHECK_OFF_SVG, LUX_SUNLIGHT_SVG, LUX_DAYLIGHT_SVG, LUX_OVERCAST_SVG, LUX_TWILIGHT_SVG, LUX_SUBDUED_SVG, LUX_DARK_SVG, \
    AMBIENT_PANEL_ICON_SOURCE
from vdu_controls.unicode import TIMER_RUNNING_SYMBOL, SUN_SYMBOL, PROCESSING_LUX_SYMBOL, STEPPING_SYMBOL, ERROR_SYMBOL, \
    RAISED_HAND_SYMBOL, ALMOST_EQUAL_SYMBOL, SMOOTHING_SYMBOL
from vdu_controls.vdu_bulk_change import BulkChangeWorker, BulkChangeItem

from vdu_controls.vdu_exceptions import VduException
from vdu_controls.vdu_misc import is_running_in_gui_thread
from vdu_controls.widgets import MBox, MIcon, SubWinDialog, DialogSingletonMixin, StdButton, FasterFileDialog, MBtn, ToolButton, \
    ThemedSvgWidget, alter_margins, TitleButton, ClickableSlider, LineEditAll, ThemedSvgButton
from vdu_controls.work_scheduler import WorkerThread, thread_pid

if TYPE_CHECKING:
    from vdu_controls_application import VduAppController

class LuxProfileWidget(QLabel):

    def __init__(self, lux_dialog: LuxDialog) -> None:
        super().__init__(parent=lux_dialog)
        self.lux_dialog = lux_dialog
        self.chart_changed_callback = lux_dialog.chart_changed_callback
        self.profiles_map = lux_dialog.lux_profiles_map
        self.preset_points = lux_dialog.preset_points
        self.main_controller: VduAppController = lux_dialog.main_controller
        self.vdu_chart_colors = self.lux_dialog.drawing_color_map
        self.range_restrictions = lux_dialog.range_restrictions_map  # Passed to chart
        self.current_lux = 0
        self.snap_to_margin = lux_dialog.lux_config.getint('lux-ui', 'snap-to-margin-pixels', fallback=4)
        self.current_vdu_sid = VduStableId('') if len(self.profiles_map) == 0 else list(self.profiles_map.keys())[0]
        self.x_origin, self.y_origin = 0, 0
        self.plot_width, self.plot_height = 0, 0
        self.setMouseTracking(True)  # Enable mouse move events so we can draw cross-hairs
        self.setMinimumWidth(npx(600))
        self.setMinimumHeight(npx(550))

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        self.create_plot()

    def create_plot(self) -> None:
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(self.width() * dp_ratio), round(self.height() * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.plot_width, self.plot_height = self.width() - npx(200), self.height() - npx(170)
        self.x_origin, self.y_origin = npx(120), self.plot_height + npx(80)
        std_line_width = npx(4)
        interpolating = self.lux_dialog.is_interpolating()
        painter.fillRect(0, 0, self.width(), self.height(), QColor(0x5b93c5))
        painter.setPen(QPen(Qt.GlobalColor.white, std_line_width))
        painter.drawText(self.width() // 3, npx(30), tr("Lux Brightness Response Profiles"))

        tick_len = npx(5)
        painter.drawLine(self.x_origin, self.y_origin, self.x_origin + self.plot_width + 25, self.y_origin)  # Draw x-axis
        for lux in [0, 10, 100, 1_000, 10_000, 100_000]:  # Draw x-axis ticks
            x = self.x_from_lux(lux)
            painter.drawLine(self.x_origin + x, self.y_origin + tick_len, self.x_origin + x, self.y_origin - tick_len)
            painter.drawText(self.x_origin + x - npx(8) * len(str(lux)), self.y_origin + npx(40), str(lux))
        painter.drawText(self.x_origin + self.plot_width // 2 - len(str("Lux")), self.y_origin + npx(70), str("Lux"))

        painter.drawLine(self.x_origin, self.y_origin, self.x_origin, self.y_origin - self.plot_height)  # Draw y-axis
        for brightness in range(0, 101, 10):  # Draw y-axis ticks
            y = self.y_from_percent(brightness)
            painter.drawLine(self.x_origin - tick_len, self.y_origin - y, self.x_origin + tick_len, self.y_origin - y)
            painter.drawText(self.x_origin - npx(50), self.y_origin - y + npx(5), str(brightness))
        painter.save()
        painter.translate(self.x_origin - npx(70), self.y_origin - self.plot_height // 2 + npx(6) * len(tr("Brightness %")))
        painter.rotate(-90)
        painter.drawText(0, 0, tr("Brightness %"))
        painter.restore()

        if self.current_vdu_sid == '':  # Nothing to draw
            painter.end()
            self.setPixmap(pixmap)
            return

        min_v, max_v = self.range_restrictions.get(self.current_vdu_sid, (0, 100))  # Draw range restrictions (if not 0..100)
        if min_v > 0:
            painter.setPen(QPen(Qt.GlobalColor.red, std_line_width // 2, Qt.PenStyle.DashLine))
            cutoff = self.y_origin - self.y_from_percent(min_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + npx(25), cutoff)
        if max_v < 100:
            painter.setPen(QPen(Qt.GlobalColor.red, std_line_width // 2, Qt.PenStyle.DashLine))
            cutoff = self.y_origin - self.y_from_percent(max_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + npx(25), cutoff)

        point_markers = []  # Draw profile lines/histogram per vdu, current_profile last/on-top, collect point marker locations
        for vdu_sid, vdu_data in [(vid, data) for vid, data in self.profiles_map.items() if vid != self.current_vdu_sid] + \
                                 [(self.current_vdu_sid, self.profiles_map[self.current_vdu_sid])]:
            last_x, last_y = 0, 0
            if vdu_sid not in self.vdu_chart_colors:
                continue  # must have been turned off
            vdu_color_num = self.vdu_chart_colors[vdu_sid]
            vdu_line_color = QColor(vdu_color_num)
            histogram_bar_color = QColor(vdu_line_color)
            histogram_bar_color.setAlpha(50)
            for point_data in vdu_data:
                lux = point_data.lux
                brightness = point_data.brightness
                if brightness >= 0:
                    x = self.x_origin + self.x_from_lux(lux)
                    y = self.y_origin - self.y_from_percent(brightness)
                    if last_x and last_y:  # Join the previous and current point with a line
                        painter.setPen(QPen(vdu_line_color, std_line_width))
                        painter.drawLine(last_x, last_y, x, y)
                    if self.current_vdu_sid == vdu_sid:  # Special handling for the current/selected VDU
                        point_markers.append((point_data, x, y, lux, brightness, vdu_color_num))  # Save data for drawing markers
                    if last_x and last_y:  # draw a histogram-step, or if interpolating, the area under the line
                        painter.setBrush(histogram_bar_color)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawPolygon(
                            QPolygon([QPoint(last_x, last_y), QPoint(x, y if interpolating else last_y),
                                      QPoint(x, self.y_origin), QPoint(last_x, self.y_origin), QPoint(last_x, last_y)]))
                    last_x, last_y = x, y
            if not interpolating and last_x and last_y:  # Show last step
                painter.fillRect(last_x, last_y, 15, self.y_origin - last_y, histogram_bar_color)

        for point_data, x, y, lux, brightness, vdu_color_num in point_markers:  # draw point-markers on top of lines and histograms
            if point_data.preset_name is None:  # Normal point
                marker_diameter = std_line_width * 4
                painter.setPen(QPen(QColor(vdu_color_num), std_line_width))
            else:  # Preset Point - fixed/non-deletable brightness level from Preset
                marker_diameter = std_line_width * 2
                painter.setPen(QPen(QColor(0xebfff9), std_line_width))
            painter.drawEllipse(x - marker_diameter // 2, y - marker_diameter // 2, marker_diameter, marker_diameter)

        pyramid_base = npx(16)
        pyramid = [(-pyramid_base // 2, 0), (0, -pyramid_base), (pyramid_base // 2, 0)]
        for preset_point in self.preset_points:  # for each Preset: draw a vertical-line and white-triangle below axis
            painter.setPen(QPen(Qt.GlobalColor.white, std_line_width // 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.GlobalColor.white)
            x = self.x_origin + self.x_from_lux(preset_point.lux)
            painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + npx(18) + ty) for tx, ty in pyramid]))

        lux_color = QColor(0xfeC053)  # 0xfec053)
        if self.current_lux is not None:  # Draw a vertical-line at current lux
            painter.setPen(QPen(lux_color, npx(2)))  # fbc21b 0xffdd30 #fec053
            x_current_lux = self.x_origin + self.x_from_lux(self.current_lux)
            painter.drawLine(x_current_lux, self.y_origin + npx(10), x_current_lux, self.y_origin - self.plot_height - npx(10))
            for brightness in range(10, 101, 10):  # Draw y-axis ticks on lux current lux
                y = self.y_from_percent(brightness)
                painter.drawLine(x_current_lux - 2, self.y_origin - y, x_current_lux + 2, self.y_origin - y)
            trangle_h = npx(32)
            current_brightness_pointer = [(0, 0), (-trangle_h, trangle_h // 2), (-trangle_h, -trangle_h // 2)]
            # Indicate current brightness at current lux
            for vdu_sid, brightness in self.lux_dialog.current_brightness_map.items():
                if vdu_sid not in self.vdu_chart_colors:
                    continue  # must have been turned off
                vdu_color_num = self.vdu_chart_colors[vdu_sid]
                vdu_line_color = QColor(vdu_color_num)
                y = self.y_origin - self.y_from_percent(brightness)
                painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                painter.setBrush(vdu_line_color)
                painter.drawPolygon(
                    QPolygon([QPoint(x_current_lux - 2 + tx // 2, y + 0 + ty // 2) for tx, ty in current_brightness_pointer]))

        marker_diameter = std_line_width * 4
        mouse_pos = self.mapFromGlobal(self.cursor().pos())  # Draw cross-hairs at mouse pos
        mouse_x, mouse_y, margin = mouse_pos.x(), mouse_pos.y(), self.snap_to_margin
        if margin <= mouse_x <= self.width() - margin and margin <= mouse_y <= self.height() - margin:
            x = clamp(mouse_x, self.x_origin, self.x_origin + self.plot_width)
            y = clamp(mouse_y, self.y_origin - self.plot_height, self.y_origin)
            match = self.find_close_to(x - self.x_origin, self.y_origin - y, self.current_vdu_sid)
            if match[0] is not None:  # Existing Point: snap to position for deleting the point under the mouse.
                x, y, lux, brightness, point_data = match[0] + self.x_origin, self.y_origin - match[1], match[2], match[3], match[4]
                point_preset_name = point_data.preset_name if point_data.preset_name is not None else ''
                if not point_preset_name:  # Existing normal point: cross-hairs, white for add, red for delete
                    painter.setPen(QPen(Qt.GlobalColor.red if match[0] is not None else Qt.GlobalColor.white, 2))
                    if match[0]:  # deletable: add a red circle
                        painter.setBrush(Qt.GlobalColor.white)
                        painter.drawEllipse(x - marker_diameter // 2, y - marker_diameter // 2, marker_diameter, marker_diameter)
                    painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + npx(5), y)
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - npx(5))
                else:  # Existing Preset point: vertical line; plus removal hint, a red triangle below axis
                    painter.setPen(QPen(Qt.GlobalColor.red if mouse_y > self.y_origin else Qt.GlobalColor.white, 2))
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - npx(5))
                    painter.setPen(QPen(Qt.GlobalColor.red, npx(2)))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + npx(18) + ty) for tx, ty in pyramid]))
                    if mouse_y > self.y_origin:  # Remove-Preset hint
                        painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                        painter.drawText(x + npx(10), self.y_origin - npx(35), tr("Click remove preset at {} lux").format(lux))
            else:  # Potential new Point - show precise position for adding a new point
                lux, brightness = self.lux_from_x(x - self.x_origin), self.percent_from_y(y - self.y_origin)
                point_preset_name = ''
                painter.setPen(QPen(Qt.GlobalColor.white, npx(1)))
                painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + npx(5), y)
                painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - npx(5))
                if mouse_y > self.y_origin:  # Below axis, show a hint for adding a Preset point: draw a red triangle below axis
                    painter.setPen(QPen(Qt.GlobalColor.red, npx(2)))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + npx(18) + ty) for tx, ty in pyramid]))
                    painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                    painter.drawText(x + 10, self.y_origin - npx(35), tr("Click to add preset at {} lux").format(lux))
            painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
            painter.drawText(x + 10, y - 10, f"{lux} lux, {brightness}% {point_preset_name}")  # Tooltip lux and percent

        painter.end()
        self.setPixmap(pixmap)

    def set_current_profile(self, name: VduStableId) -> None:
        self.current_vdu_sid = name
        self.create_plot()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event:
            changed = False
            x = event.pos().x() - self.x_origin
            y = self.y_origin - event.pos().y()
            if event.button() == Qt.MouseButton.LeftButton:  # click along bottom (y=0) to attache presets
                changed = self.lux_point_edit(x, y) if y >= 0 else self.lux_preset_edit(x)
            if changed:
                self.show_changes()
        event.accept()

    def lux_point_edit(self, x, y) -> bool:
        assert self.current_vdu_sid != ''
        vdu_data = self.profiles_map[self.current_vdu_sid]
        _, _, existing_lux, existing_percent, existing_point = self.find_close_to(x, y, self.current_vdu_sid)
        if existing_lux is not None:  # Remove
            if existing_point.preset_name is None:
                vdu_data.remove(existing_point)
        else:  # Add
            percent = self.percent_from_y(y)
            lux = self.lux_from_x(x)
            vdu_data.append(LuxPoint(lux, percent))
            vdu_data.sort()
        return True

    def lux_preset_edit(self, x) -> bool:
        if point := self.find_preset_point_close_to(x):  # Delete
            self.preset_points.remove(point)
            for vdu_sid, profile in self.profiles_map.items():
                for profile_point in profile:
                    if profile_point == point:  # Note: these will not be the same object
                        if profile_point.preset_name and profile_point.brightness > 0:
                            # Convert to normal point - as a convenience for the user
                            profile_point.preset_name = None
                        else:  # Either an uncommitted LuxPoint or Preset without a brightness value, remove it.
                            profile.remove(profile_point)
                        break
            return True
        presets = self.main_controller.find_presets_map()
        if len(presets):
            ask_preset = QInputDialog()
            ask_preset.setComboBoxItems(list(presets.keys()))
            ask_preset.setOption(QInputDialog.InputDialogOption.UseListViewForComboBoxItems)
            if ask_preset.exec() == QInputDialog.DialogCode.Accepted:
                preset_name = ask_preset.textValue()
                if preset := self.main_controller.find_preset_by_name(preset_name):
                    point = LuxPoint(self.lux_from_x(x), -1, preset_name)
                    self.preset_points.append(point)
                    self.preset_points.sort()
                    for vdu_sid, profile in self.profiles_map.items():
                        preset_brightness = preset.get_brightness(vdu_sid) if preset is not None else -1
                        point = LuxPoint(self.lux_from_x(x), preset_brightness, preset_name)
                        profile.append(point)
                        profile.sort()
                    return True
        else:
            MBox(MIcon.Information, msg=tr("There are no Presets."), info=tr("Use the Presets Dialog to create some.")).exec()
        return False

    def show_changes(self, profile_changes=True) -> None:
        self.create_plot()
        if profile_changes:
            self.chart_changed_callback()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        self.create_plot()

    def find_close_to(self, x: int, y: int, vdu_sid: VduStableId) -> Tuple:
        r = self.snap_to_margin
        for vdu_pd in self.profiles_map[vdu_sid]:
            existing_lux = vdu_pd.lux
            if vdu_pd.preset_name is None:
                existing_percent = vdu_pd.brightness
            else:
                if preset := self.main_controller.find_preset_by_name(vdu_pd.preset_name):
                    existing_percent = preset.get_brightness(vdu_sid)
                else:
                    continue  # Must have been deleted
            existing_x = self.x_from_lux(existing_lux)
            existing_y = self.y_from_percent(existing_percent)
            if existing_x - r <= x <= existing_x + r and (existing_y - r <= y <= existing_y + r or vdu_pd.preset_name is not None):
                return existing_x, existing_y, existing_lux, existing_percent, vdu_pd
        return None, None, None, None, None

    def find_preset_point_close_to(self, x: int) -> LuxPoint | None:
        for point in self.preset_points:
            point_x = self.x_from_lux(point.lux)
            if abs(point_x - x) <= self.snap_to_margin:
                return point
        return None

    def percent_from_y(self, y) -> int:
        percent = round(100.0 * abs(y) / self.plot_height)
        min_v, max_v = self.range_restrictions[self.current_vdu_sid]
        if percent > max_v:
            return max_v
        if percent < min_v:
            return min_v
        return percent

    def y_from_percent(self, percent) -> int:
        return round(self.plot_height * percent / 100)

    def lux_from_x(self, x) -> int:
        lux = 0 if x <= 0 else round(10.0 ** ((x / self.plot_width) * math.log10(100_000)))
        if lux > 100_000:
            return 100_000
        return lux

    def x_from_lux(self, lux: int) -> int:
        return round(math.log10(lux) / (math.log10(100000) / self.plot_width)) if lux > 0 else 0


@dataclass
class LuxGaugeHistory:
    lux: int
    when: datetime


class LuxGaugeWidget(QWidget):
    lux_changed_qtsignal = pyqtSignal(int)

    def __init__(self, parent: LuxDialog) -> None:
        super().__init__(parent=parent)
        self.max_history = 240
        self.history: List[LuxGaugeHistory | None] = [None] * (self.max_history // 10)
        self.sun_image = None
        self.lux_bar_color = QColor(0xfec053)
        self.white_line_color = w = QColor(0xfefefe)
        self.white_transparent_color = QColor(w.red(), w.green(), w.blue(), 30)
        self.orange_line_color = QColor(0xff8500)
        self.common_background_color = QColor(0x5b93c5)
        self.setLayout(widget_layout := QVBoxLayout())
        self.current_lux_display = QLabel()
        big_font = self.current_lux_display.font()
        big_font.setPointSize(big_font.pointSize() + 8)
        self.current_lux_display.setFont(big_font)
        widget_layout.addWidget(self.current_lux_display)
        self.plot_widget = QLabel()
        self.plot_widget.setFixedWidth(npx(340))
        self.plot_widget.setFixedHeight(npx(100))
        widget_layout.addWidget(self.plot_widget)
        self.current_meter: LuxMeterDevice | None = None
        self.stats_label = QLabel()
        self.help_text = tr("Left:\t Rolling display of metered lux (ML).\n"
                            "Right:\t 1) Estimated outside solar illumination (Eo) for\n"
                            "\t     the set geolocation for the current day.\n"
                            "\t 2) Estimated inside illumination (Ei = DF * Eo).\n"
                            "________________________________________________________________________________\n"
                            "Daylight Factor DF = ML/Eo\n"
                            "Eo = unit_constants * sin(radians(solar_altitude)) * 10 ** (-0.1 * air_mass)\n"
                            "Estimates of Ei are used by the semi-automatic metering option.")
        self.setToolTip(self.help_text)
        widget_layout.addWidget(self.stats_label)
        self.updates_enabled = True
        self.append_new_value(0)

    def mousePressEvent(self, a0):
        MBox(MIcon.Information, msg=self.help_text).exec()

    def append_new_value(self, lux: int) -> None:
        self.history = self.history[-self.max_history:]
        self.history.append(LuxGaugeHistory(lux, zoned_now()))
        if self.updates_enabled:
            self.current_lux_display.setText(tr("Lux: {}".format(lux)))
            self.update_plot()
            self.lux_changed_qtsignal.emit(lux)

    def update_plot(self):
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(self.plot_widget.width() * dp_ratio), round(self.plot_widget.height() * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING:
            painter.setRenderHint(QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING)
        plot_height = self.plot_widget.height()
        # Create a plot of recent historical lux readings.
        lux_plot_width = self.plot_widget.height()  # Square with height
        line_width = npx(4)
        thin_line_width = npx(2)

        painter.fillRect(0, 0, lux_plot_width, plot_height, self.common_background_color)
        painter.setPen(QPen(self.lux_bar_color, 1))
        most_recent_lux_xy = (None, None)  # draw pos of most recent
        for x, item in enumerate(self.history[-lux_plot_width:]):  # list position corresponds to x position
            if item:
                y = self._y_from_lux(item.lux, plot_height)
                painter.drawLine(x, plot_height, x, y)
                most_recent_lux_xy = (x, y)
            else:
                painter.drawLine(x, plot_height, x, self._y_from_lux(0, plot_height))
        if most_recent_lux_xy[0] is not None:
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawLine(most_recent_lux_xy[0], plot_height, most_recent_lux_xy[0], most_recent_lux_xy[1])
        # Create plot of Eo (outside illumination) and Ei (inside illumination)
        margin = line_width
        painter.setPen(QPen(self.white_line_color, margin))
        painter.drawLine(lux_plot_width + margin // 2, plot_height, lux_plot_width + margin // 2, 0)
        df_plot_width = self.plot_widget.width() - lux_plot_width - margin
        minutes_per_point = (24 * 60) / df_plot_width
        df_plot_day = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0)
        df_plot_left = lux_plot_width + margin  #plot_width - df_plot_width - 30
        painter.fillRect(df_plot_left, 0, df_plot_left + df_plot_width, plot_height, self.common_background_color)
        # Plot the DF, Eo, Ei history as a block
        painter.setPen(QPen(self.lux_bar_color, 1))
        most_recent_df_xy = (None, None)  # Indicate the last history position with a red dot
        most_recent_item = None
        for item in self.history:  # Block fill for history
            if item and item.when > df_plot_day:
                t = (item.when - df_plot_day).total_seconds() // 60
                i = int(df_plot_left + t // minutes_per_point)
                item_y_pos = self._y_from_lux(item.lux, plot_height)
                painter.drawLine(i, plot_height, i, item_y_pos)
                most_recent_df_xy = (i, item_y_pos)
                most_recent_item = item
        # Plot Eo and Ei
        eo_points = []
        ei_points = []
        painter.setPen(QPen(self.white_transparent_color, thin_line_width))
        t = df_plot_day + timedelta(minutes=0)
        df = LuxMeterSemiAutoDevice.get_daylight_factor()
        if location := LuxMeterSemiAutoDevice.get_location():
            for i in range(df_plot_left, df_plot_left + df_plot_width):
                eo_y = self._y_from_lux(calc_solar_lux(t, location, 1.0), plot_height * 10)  # scale * 10 for more accuracy
                eo_points.append(QPointF(i, eo_y / 10.0))  # scale down to floating-point precision drawing co-ordinates
                eo_x = self._y_from_lux(calc_solar_lux(t, location, df), plot_height * 10)
                ei_points.append(QPointF(i, eo_x / 10.0))  # scale down to floating-point precision drawing co-ordinates
                t += timedelta(minutes=minutes_per_point)
                painter.drawLine(i, plot_height, i, eo_y)  # Fill under eo line
            # Actually plot the two datasets
            painter.setPen(QPen(self.orange_line_color, thin_line_width * 3))
            painter.drawPolyline(eo_points)
            painter.setPen(QPen(self.white_line_color, thin_line_width * 3))
            painter.drawPolyline(ei_points)
        # Add text to the axis
        painter.setPen(QPen(self.white_line_color, thin_line_width))
        painter.setFont(QFont(QApplication.font().family(), fz := 5, QFont.Weight.Normal))
        middle = df_plot_left - margin // 2
        for i in (10, 100, 1_000, 10_000, 100_000):
            painter.drawLine(middle - line_width, y := self._y_from_lux(i, plot_height), middle + line_width, y)
            painter.drawText(QPointF(middle + npx(6), y + 4), str(i))
        # Draw hour ticks along the bottom
        tick_len = line_width * 2
        points_per_hour = df_plot_width / 24
        for hour in range(24):  # Tick length multiplier: 3 for 0/12, 2 for multiples of 3, else 1
            x = round(df_plot_left + points_per_hour * hour)
            painter.drawLine(x, plot_height, x, plot_height - tick_len * (3 if hour % 12 == 0 else (2 if hour % 3 == 0 else 1)))
        # Draw the sun
        if most_recent_df_xy and most_recent_item and most_recent_df_xy[0]:
            if self.sun_image is None:
                self.sun_image = create_image_from_svg_bytes(SUN_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#feC053")).scaled(
                    npx(36), npx(36))
            t = (most_recent_item.when - df_plot_day).total_seconds() // 60
            i = int(df_plot_left + t // minutes_per_point)
            if location:
                sun_y = self._y_from_lux(calc_solar_lux(most_recent_item.when, location, 1.0), plot_height)
                if sun_y <= plot_height - self.sun_image.height() // 2 - 1:
                    painter.drawImage(QPoint(i - self.sun_image.width() // 2, sun_y - self.sun_image.height() // 2 - 1),
                                      self.sun_image)
        if most_recent_df_xy[0] is not None:
            painter.setPen(QPen(Qt.GlobalColor.red, thin_line_width))
            painter.drawLine(most_recent_df_xy[0], plot_height, most_recent_df_xy[0], most_recent_df_xy[1])
        # Draw dots at current points
        dot_size = line_width * 2
        half_dot_size = dot_size // 2
        for x, y in (most_recent_lux_xy, most_recent_df_xy):
            if x is not None and y is not None:
                painter.setPen(QPen(Qt.GlobalColor.red, half_dot_size))
                painter.setBrush(self.white_line_color)
                painter.drawEllipse(x - half_dot_size, y - half_dot_size, dot_size, dot_size)
        painter.end()  # End of plotting
        self.plot_widget.setPixmap(pixmap)
        # Add some text to the bottom
        if location:
            eo = calc_solar_lux(zoned_now(), location, 1.0)
            self.stats_label.setText(tr("Eo={:,} lux    DF={:,.4f}").format(eo, df))
        else:
            self.stats_label.setText(tr("Eo=?   DF=?   (location not set)"))

    def connect_meter(self, new_lux_meter: LuxMeterDevice | None) -> None:
        if self.current_meter:
            self.current_meter.new_lux_value_qtsignal.disconnect(self.append_new_value)
        self.current_meter = new_lux_meter
        if self.current_meter:
            self.current_meter.new_lux_value_qtsignal.connect(self.append_new_value)
            if new_lux_meter and new_lux_meter.has_manual_capability:
                if lux := new_lux_meter.get_value():
                    self.append_new_value(round(lux))
            self.enable_gauge(True)

    def enable_gauge(self, enable: bool = True) -> None:
        if enable:
            self.history = (self.history + [None] * 2)[-self.max_history:]  # Make a little gap in the history to show where we are
            self.update_plot()
        self.updates_enabled = enable

    def _y_from_lux(self, lux: int, required_height: int) -> int:
        if lux <= 0:
            return required_height
        return required_height - round(math.log10(lux) / math.log10(200000) * required_height)


def lux_create_device(device_name: str) -> LuxMeterDevice:
    if device_name == LuxMeterSemiAutoDevice.device_name:
        return LuxMeterSemiAutoDevice()
    if not pathlib.Path(device_name).exists():
        raise LuxDeviceException(tr("Failed to set up {} - path does not exist.").format(device_name))
    if not os.access(device_name, os.R_OK):
        raise LuxDeviceException(tr("Failed to set up {} - no read access to device.").format({device_name}))
    if pathlib.Path(device_name).is_char_device():
        return LuxMeterSerialDevice(device_name)
    elif pathlib.Path(device_name).is_fifo():
        return LuxMeterFifoDevice(device_name)
    elif pathlib.Path(device_name).exists() and os.access(device_name, os.X_OK):
        return LuxMeterExecutableDevice(device_name)
    raise LuxDeviceException(tr("Failed to set up {} - not a recognized kind of device or not executable.").format(device_name))


class LuxMeterDevice(QObject):
    new_lux_value_qtsignal = pyqtSignal(int)

    def __init__(self, requires_worker: bool = True, manual: bool = False, semi_auto: bool = False) -> None:
        super().__init__()
        log_debug(f"LuxMeterDevice init {manual=} {semi_auto=}") if log_debug_enabled else None
        self.current_value: float | None = None
        self.requires_worker = requires_worker
        self.has_manual_capability = manual  # Can be both manual and semi-automatic
        self.has_semi_auto_capability = semi_auto
        self.has_auto_capability = not self.has_manual_capability or self.has_semi_auto_capability
        if self.requires_worker:  # use a thread to prevent any blocking due to slow updating
            log_info(f"LuxMeterDevice: starting worker for {self.__class__}")
            self.worker = WorkerThread(task_body=self.update_from_worker_thread, task_finished=self.cleanup, loop=True)

    def get_value(self) -> float | None:  # an un-smoothed raw value - TODO should smoothing be moved here?
        if self.current_value is None and self.requires_worker:
            self.worker.start() if not self.worker.isRunning() else None
            while self.current_value is None and not self.worker.stop_requested:  # have to block on the first time through.
                time.sleep(0.1)
        return self.current_value

    def update_from_worker_thread(self, _: WorkerThread) -> None:  # Only for meters that have background workers.
        pass

    def set_current_value(self, new_value: float) -> None:
        self.current_value = max(new_value, 1.0)  # Never less than 1 - for safety - don't want to dim to zero.
        self.new_lux_value_qtsignal.emit(round(new_value))

    def cleanup(self, _: WorkerThread):
        pass

    def stop_metering(self) -> None:
        if self.requires_worker:
            self.worker.stop()

    def get_status(self) -> Tuple[bool, str]:  # True if OK, plus any message
        return True, ''


class LuxMeterFifoDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.device_name = device_name
        self.fifo: int | None = None
        self.buffer = b''

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        try:
            if self.fifo is None:
                log_info(f"Initialising fifo {self.device_name} - waiting on fifo data.")
                self.fifo = os.open(self.device_name, os.O_RDONLY | os.O_NONBLOCK)
            while not self.worker.stop_requested and len(select.select([self.fifo], [], [], 1.0)[0]) == 1:
                byte = os.read(self.fifo, 1)
                if byte is None:
                    self.cleanup()  # Fifo has closed, maybe meter is resetting
                elif byte == b'\n':
                    if len(self.buffer) > 0:
                        self.set_current_value(float(self.buffer.decode()))
                        self.buffer = b''
                else:
                    self.buffer += byte
        except (OSError, ValueError) as se:
            self.cleanup()
            self.buffer = b''
            log_warning(f"Reopen and retry {self.device_name=} {self.buffer=}", se, trace=True)

    def cleanup(self, worker: WorkerThread | None = None):
        if self.fifo is not None:
            log_info("closing fifo")
            os.close(self.fifo)
            self.fifo = None


class LuxMeterExecutableDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.runnable = device_name
        self.sleep_time = float(os.getenv("LUX_METER_RUNNABLE_SLEEP", default='60.0'))

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        try:
            result = subprocess.run([self.runnable], stdout=subprocess.PIPE, check=True)
            self.set_current_value(float(result.stdout))
        except (OSError, ValueError, subprocess.CalledProcessError) as se:
            log_warning(f"Error running {self.runnable}, will retry in {self.sleep_time} seconds", se, trace=True)
        self.worker.doze(self.sleep_time)  # Don't re-run too fast


class LuxMeterSerialDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.device_name = device_name
        self.serial_device = None
        self.line_matcher = re.compile(r'\A([0-9]+[.][0-9]+)\r\n\Z', re.DOTALL)  # Be precise to try and catch errors
        self.backoff_secs = self.initial_backoff_secs = 10
        try:
            self.serial_module = import_module('serial')
        except ModuleNotFoundError as mnf:
            raise LuxDeviceException(tr("The required pyserial serial-port module is not installed on this system.")) from mnf

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        problem = None
        try:
            if self.serial_device is None:
                log_info(f"LuxMeterSerialDevice: Initialising character device {self.device_name}")
                self.serial_device = self.serial_module.Serial(self.device_name)
            if self.serial_device is not None:
                self.serial_device.reset_input_buffer()
                buffer = self.serial_device.read_until()
                decoded = buffer.decode('utf-8', errors='surrogateescape')
                if match := self.line_matcher.match(decoded):  # only accept correctly formatted output
                    self.set_current_value(float(match.group(1)))
                    self.backoff_secs = self.initial_backoff_secs
                else:
                    problem = f"value that failed to parse: {decoded.encode('unicode_escape')}"
            self.worker.doze(1.0)
        except (self.serial_module.SerialException, termios.error, FileNotFoundError, ValueError) as se:
            problem = se
        if problem:
            log_warning(f"Retry read of {self.device_name}, will reopen feed in {self.backoff_secs} seconds. Cause:", problem,
                        trace=True)
            self.cleanup()
            self.worker.doze(self.backoff_secs)
            self.backoff_secs = self.backoff_secs * 2 if self.backoff_secs < 300 else 300

    def cleanup(self, worker: WorkerThread | None = None):
        if self.serial_device is not None:
            log_debug("closing serial device") if log_debug_enabled else None
            self.serial_device.close()
            self.serial_device = None


class LuxMeterSemiAutoDevice(LuxMeterDevice):  # is both manual and automatic - semi-automatic
    obsolete_device_name = 'Slider-Control'
    device_name = 'solar-lux-calculator'
    location: GeoLocation | None = None
    daylight_factor: float | None = None

    def __init__(self) -> None:
        super().__init__(requires_worker=False, manual=True, semi_auto=True)
        self.current_value: float = LuxMeterSemiAutoDevice.get_stored_value()
        LuxMeterSemiAutoDevice.daylight_factor = None  # Force initialization from file
        _ = LuxMeterSemiAutoDevice.get_daylight_factor()

    def get_value(self) -> float | None:
        if location := LuxMeterSemiAutoDevice.get_location():
            if lux := calc_solar_lux(zoned_now(), location, LuxMeterSemiAutoDevice.get_daylight_factor()):
                self.set_current_value(lux)  # only set if in daylight
        return self.current_value

    def set_current_value(self, new_value: float) -> None:
        if (new_value := round(new_value)) != round(self.current_value):
            self.save_stored_value(new_value)
        super().set_current_value(new_value)

    def stop_metering(self) -> None:
        pass

    def get_status(self) -> Tuple[bool, str]:
        return (False, tr('No location defined.')) if self.location is None else super().get_status()

    @staticmethod
    def get_stored_value() -> float:
        persisted_path = CONFIG_DIR_PATH.joinpath("lux_manual_value.txt")
        if persisted_path.exists():
            try:
                return float(persisted_path.read_text())
            except ValueError:
                log_error(f"LuxSemiAuto: failed to parse stored lux value, removing {persisted_path.as_posix()}")
                persisted_path.unlink()
        return 1000.0

    @staticmethod
    def save_stored_value(new_value: float):
        if CONFIG_DIR_PATH.exists():
            CONFIG_DIR_PATH.joinpath("lux_manual_value.txt").write_text(str(round(new_value)))

    @staticmethod
    def get_daylight_factor() -> float:
        if LuxMeterSemiAutoDevice.daylight_factor is None:
            daylight_factor = 1.0
            persisted_path = CONFIG_DIR_PATH.joinpath("lux_daylight_factor.txt")
            if persisted_path.exists():
                try:
                    daylight_factor = float(persisted_path.read_text())
                except ValueError:
                    log_error(f"LuxSemiAuto: failed to parse daylight_factor, removing {persisted_path.as_posix()}")
                    persisted_path.unlink()
            else:
                log_error(f"LuxSemiAuto: {persisted_path.as_posix()} does not exist")
            log_debug(f'LuxSemiAuto: {daylight_factor=} ({persisted_path.as_posix()})') if log_debug_enabled else None
            LuxMeterSemiAutoDevice.daylight_factor = daylight_factor
        return LuxMeterSemiAutoDevice.daylight_factor

    @staticmethod
    def update_df_from_lux_value(new_lux_value: float, semi_auto_source: bool):
        if location := LuxMeterSemiAutoDevice.location:
            solar_lux = calc_solar_lux(zoned_now(), location, 1.0)
            if solar_lux > (0 if semi_auto_source else 1000):  # only for reasonable daylight lux levels or if the user is driving.
                daylight_factor = new_lux_value / solar_lux
                LuxMeterSemiAutoDevice.set_daylight_factor(daylight_factor, internal=True, persist=semi_auto_source)

    @staticmethod
    def set_daylight_factor(daylight_factor: float, internal: bool = False, persist: bool = False):
        daylight_factor = round(daylight_factor, 4)
        if LuxMeterSemiAutoDevice.daylight_factor is None or abs(LuxMeterSemiAutoDevice.daylight_factor - daylight_factor) > 0.001:
            if persist:
                if CONFIG_DIR_PATH.exists():
                    persisted_path = CONFIG_DIR_PATH.joinpath("lux_daylight_factor.txt")
                    log_debug(f"LuxSemiAuto: save {daylight_factor=} to {persisted_path.as_posix()}") if log_debug_enabled else None
                persisted_path.write_text(f"{daylight_factor:.4f}")
            LuxMeterSemiAutoDevice.daylight_factor = daylight_factor
            if not internal:
                LuxDialog.reconfigure_instance()

    @staticmethod
    def get_location() -> GeoLocation | None:
        return LuxMeterSemiAutoDevice.location

    @staticmethod
    def set_location(location: GeoLocation | None):
        LuxMeterSemiAutoDevice.location = location


class LuxSmooth:
    def __init__(self, n: int, alpha: float = 0.5) -> None:
        self.length: int = n
        self.input: List[float] = []
        self.output: List[float] = []
        self.alpha: float = alpha

    def smooth(self, v: float) -> int:  # A low pass filter
        # The smaller the alpha, the more each previous value affects the following value. Smaller alpha results => more smoothing.
        # https://stackoverflow.com/questions/4611599/smoothing-data-from-a-sensor
        # https://en.wikipedia.org/wiki/Low-pass_filter#Simple_infinite_impulse_response_filter
        if len(self.input) == self.length:
            self.input.pop(0)
            self.output.pop(0)
        self.input.append(v)
        self.output.append(v)  # extend to same length - value will be overwritten if there is more than one sample.
        for i in range(1, len(self.input)):
            self.output[i] = self.output[i - 1] + self.alpha * (self.input[i] - self.output[i - 1])
        return round(self.output[-1])


class LuxStepStatus(Enum):
    ENCOUNTERED_ERROR = -2
    UNEXPECTED_CHANGE = -1
    FINISHED = 0,
    MORE_TO_DO = 1,


@dataclass
class LuxToDo:
    vdu_sid: VduStableId
    brightness: int
    preset_name: str | None
    current_brightness: int | None = None


class LuxAutoWorker(WorkerThread):  # Why is this so complicated?

    _lux_dialog_message_qtsignal = pyqtSignal(str, int, MsgDestination)

    def __init__(self, auto_controller: LuxAutoController, single_shot: bool) -> None:
        super().__init__(task_body=self._adjust_for_lux, task_finished=self._adjust_for_lux_finished)
        self.single_shot = single_shot  # Called for an on-demand single time assessment with immediate effect.
        self.main_controller = auto_controller.main_controller
        self.adjust_now_requested = False
        lux_config = auto_controller.get_lux_config()
        log_info(f"LuxAuto: lux-meter.interval-minutes={lux_config.get_interval_minutes()} {single_shot=}")
        self.sleep_seconds = lux_config.get_interval_minutes() * 60
        self.consecutive_error_count = 0

        def _get_prop(prop: str, fallback: bool | int | float | str) -> bool | int | float:
            op = {bool: lux_config.getboolean, int: lux_config.getint, float: lux_config.getfloat}[type(fallback)]
            value = op('lux-meter', prop, fallback=fallback)
            log_info(f"LuxAuto: lux-meter.{prop}={value}")
            return value

        samples_per_minute = _get_prop('samples-per-minute', fallback=3)
        self.sampling_interval_seconds = 60 // samples_per_minute
        self.smoother = LuxSmooth(_get_prop('smoother-n', fallback=5), alpha=_get_prop('smoother-alpha', fallback=0.5))
        self.interpolation_enabled = _get_prop('interpolate-brightness', fallback=True)
        self.sensitivity_percent = _get_prop('interpolation-sensitivity-percent', fallback=10)
        self.step_pause_millis = _get_prop('step-pause-millis', fallback=1000)
        self._lux_dialog_message_qtsignal.connect(LuxDialog.lux_dialog_message)
        self._lux_dialog_message_qtsignal.connect(self.main_controller.main_window.status_message)
        self.status_message(f"{TIMER_RUNNING_SYMBOL} 00:00", 0, MsgDestination.COUNTDOWN)

    def status_message(self, message: str, timeout: int = 0, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        self._lux_dialog_message_qtsignal.emit(message, timeout, destination)

    def _adjust_for_lux(self, _: WorkerThread) -> None:
        try:
            lux_auto_controller = self.main_controller.get_lux_auto_controller()
            # Give any previous thread a chance to exit, plus let the GUI and presets settle down
            self.doze(2) if not self.single_shot else None
            log_info(f"LuxAuto: monitoring commences {thread_pid()=}")
            assert lux_auto_controller is not None
            while not self.stop_requested:
                error_count = self.consecutive_error_count
                busy_main_controller = self.main_controller.busy_doing()
                if lux_meter := lux_auto_controller.lux_meter:
                    if (status := lux_meter.get_status())[0]:
                        if metered_lux := lux_meter.get_value():
                            if not busy_main_controller:
                                if to_do_list := self.assemble_required_work(lux_auto_controller, metered_lux,
                                                                             not lux_meter.has_manual_capability):
                                    self.do_work(to_do_list)
                    elif status[1]:
                        self.status_message(status[1], timeout=5000)
                    if self.single_shot:
                        break
                else:  # In-app config change - things are in a state of flux
                    log_error("Exiting, no lux meter available.")
                    break
                if error_count == self.consecutive_error_count:  # no change - must be OK now
                    log_debug("LuxAuto: clearing consecutive_error_count") if log_debug_enabled else None
                    self.consecutive_error_count = 0
                self.idle_sampling(lux_meter, busy_main_controller)  # Sleep and sample for rest of cycle
        finally:
            log_info(f"LuxAuto: exiting (stop_requested={self.stop_requested}) {thread_pid()=}")

    def assemble_required_work(self, lux_auto_controller: LuxAutoController, metered_lux: float, requires_smoothing) -> List[
        LuxToDo]:
        lux = self.smoother.smooth(metered_lux) if requires_smoothing else round(metered_lux)
        summary_text = self.lux_summary(metered_lux, lux)
        self.status_message(f"{SUN_SYMBOL} {summary_text} {PROCESSING_LUX_SYMBOL}", timeout=3000)
        to_do_list: List[LuxToDo] = []
        for vdu_sid in self.main_controller.get_vdu_stable_id_list():  # For each VDU, do one step of its profile
            if self.stop_requested:
                return []
            value_range = self.main_controller.get_range(vdu_sid, BRIGHTNESS_VCP_CODE, fallback=(0, 100))
            lux_profile = lux_auto_controller.get_lux_profile(vdu_sid, value_range)
            if to_do := self.determine_changes(vdu_sid, lux, lux_profile):
                to_do_list.append(to_do)
        self.assess_presets_collectively(to_do_list)
        return to_do_list

    def assess_presets_collectively(self, to_do_list: List[LuxToDo]) -> None:
        if to_do_list:  # See if all items are in agreement on whether a preset should be used
            for preset_name in [x.preset_name for x in to_do_list]:
                if preset := self.main_controller.find_preset_by_name(preset_name):
                    sids_present = set(self.main_controller.get_vdu_stable_id_list())
                    sids_present_and_in_preset = sids_present.intersection(set(preset.get_vdu_sids()))
                    items_with_this_preset = [x for x in to_do_list if x.preset_name == preset_name]
                    sids_of_items_with_this_preset = set([x.vdu_sid for x in items_with_this_preset])
                    log_debug(f"LuxAuto: {sids_present_and_in_preset=} {sids_of_items_with_this_preset=}")
                    if sids_present_and_in_preset == sids_of_items_with_this_preset:
                        log_debug(f"LuxAuto: applying Preset {preset_name}")
                        for item in items_with_this_preset:
                            if (preset_brightness := preset.get_brightness(item.vdu_sid)) > 0:
                                item.brightness = preset_brightness
                    else:
                        log_debug(f"LuxAuto: ignoring Preset {preset_name} doesn't match for all VDUs present.")
                        for item in items_with_this_preset:
                            item.preset_name = None
                else:
                    log_debug(f"LuxAuto: ignoring Preset {preset_name} no longer exists.")

    def do_work(self, to_do_list: List[LuxToDo]):
        to_do_preset_names = []
        bulk_changer = BulkChangeWorker('LuxAutoBulk', main_controller=self.main_controller,
                                        progress_callable=self._to_do_progress, finished_callable=self._to_do_finished,
                                        step_interval=self.step_pause_millis / 1000.0, context=to_do_preset_names)
        for to_do in to_do_list:
            if to_do.brightness != -1:
                bulk_change_item = BulkChangeItem(to_do.vdu_sid, BRIGHTNESS_VCP_CODE, to_do.brightness,
                                                  current_value=to_do.current_brightness,
                                                  transition=True)  # only transitions if protect-nvram is False.
                bulk_changer.add_item(bulk_change_item)
            if to_do.preset_name and to_do.preset_name not in to_do_preset_names:
                to_do_preset_names.append(to_do.preset_name)
        bulk_changer.run()  # Call run instead of start; run in this thread instead of a new thread.

    def _to_do_progress(self, _: BulkChangeWorker):
        self.status_message(f"{SUN_SYMBOL} {STEPPING_SYMBOL}")

    def _to_do_finished(self, worker: BulkChangeWorker):
        if worker.completed:
            if to_do_preset_names := worker.context:
                self.doze(0.5)  # Give the user a chance to read messages
                for preset_name in to_do_preset_names:  # if a point had a Preset attached, activate it now
                    # Restoring the Preset's non-brightness settings. Invoke now, so it will happen in this thread's sleep period.
                    if preset := self.main_controller.find_preset_by_name(preset_name):  # Check that it still exists
                        log_debug(f"LuxAuto: restoring Preset {preset.name=}") if log_debug_enabled else None
                        self.main_controller.restore_preset(
                            preset, immediately=PresetTransitionFlag.SCHEDULED not in preset.get_transition_type(),
                            background_activity=True)
                    else:
                        log_debug("LuxAuto: Preset {preset.name} no longer exists - ignoring") if log_debug_enabled else None
                        self.main_controller.update_window_status_indicators()
        else:
            log_debug("LuxAuto: bulk worker failed to complete.") if log_debug_enabled else None
            self.status_message(f"{SUN_SYMBOL} {ERROR_SYMBOL} {RAISED_HAND_SYMBOL}")
            self.consecutive_error_count += 1

    def _adjust_for_lux_finished(self, _: WorkerThread) -> None:
        log_debug("LuxAuto: worker finished") if log_debug_enabled else None
        if self.work_exception:
            log_error(f"LuxAuto: exited with exception={self.work_exception}")

    def idle_sampling(self, lux_meter: LuxMeterDevice, busy_main_controller: str | None):
        seconds = 2 if self.consecutive_error_count == 1 else self.sleep_seconds
        log_debug(f"LuxAuto: sleeping {seconds=}") if log_debug_enabled else None
        if busy_main_controller:
            self.status_message(
                tr("Task waiting for {} to finish.").format(busy_main_controller), timeout=0, destination=MsgDestination.DEFAULT)
        for second in range(seconds, -1, -1):
            if busy_main_controller and not self.main_controller.busy_doing():
                break  # the main controller is no longer busy
            if self.stop_requested or self.adjust_now_requested:  # Respond to stop requests while sleeping
                self.adjust_now_requested = False
                break
            if not lux_meter.has_manual_capability:  # Update the smoother every n seconds, but not at the start or end of the period.
                if (0 < second < self.sleep_seconds) and second % self.sampling_interval_seconds == 0:
                    if metered_lux := lux_meter.get_value():  # Update the smoothing while sleeping
                        self.status_message(
                            f"{SUN_SYMBOL} {self.lux_summary(metered_lux, self.smoother.smooth(metered_lux))}", timeout=3000)
            self.status_message(f"{TIMER_RUNNING_SYMBOL} {second // 60:02d}:{second % 60:02d}", 0, MsgDestination.COUNTDOWN)
            self.doze(1)

    def determine_changes(self, vdu_sid: VduStableId, smoothed_lux: int, lux_profile: List[LuxPoint]) -> LuxToDo | None:
        previous_normal_point = matched_point = lower_point = LuxPoint(0, 0)
        proposed_brightness = 0
        # Update/bind the current Preset values onto the LuxPoints and wrap with min and max values.
        for profile_point in [LuxPoint(0, 0), *lux_profile, LuxPoint(100000, 100)]:
            # Moving up the lux steps, seeking the step below smoothed_lux
            if smoothed_lux > profile_point.lux:  # Possible result, there may be something higher, keep going...
                # if profile_point.brightness is -1, this is a Preset that doesn't change the VDU's brightness control
                if profile_point.brightness >= 0:  # else use existing result_brightness
                    proposed_brightness = profile_point.brightness
                matched_point = profile_point
            else:  # Step is too high, if interpolating check against the following point, if not, the previous match is the result.
                if self.interpolation_enabled:  # Only interpolate if lux is not an exact match and next_point has a brightness
                    if smoothed_lux != matched_point.lux and profile_point.brightness >= 0:
                        # if profile_point.brightness is -1, this is a Preset that doesn't change the VDU's brightness control
                        lower_point = matched_point if matched_point.brightness >= 0 else previous_normal_point
                        proposed_brightness = self.interpolate_brightness(smoothed_lux, lower_point, profile_point)
                break
            if profile_point.brightness > 0:
                previous_normal_point = profile_point
        try:
            preset_name = self.assess_preset_proximity(proposed_brightness, lower_point, matched_point, profile_point)
            current_brightness = self.main_controller.get_value(vdu_sid, BRIGHTNESS_VCP_CODE)
            diff = proposed_brightness - current_brightness
            if self.interpolation_enabled and preset_name is None and abs(diff) < self.sensitivity_percent:
                log_info(f"LuxAuto: {smoothed_lux=} {vdu_sid=} {current_brightness=} {proposed_brightness=} ignored, too small")
                self.status_message(f"{SUN_SYMBOL} {proposed_brightness}% {ALMOST_EQUAL_SYMBOL} {current_brightness}% {vdu_sid}",
                                    timeout=5000)
                return None
            if log_debug_enabled:
                log_debug(f"LuxAuto: {smoothed_lux=} {vdu_sid=} {current_brightness=}% {proposed_brightness=}% {preset_name=}")
            return LuxToDo(vdu_sid, proposed_brightness, preset_name, current_brightness)
        except VduException as e:
            self.consecutive_error_count += 1
            log_debug(f"LuxAuto: {self.consecutive_error_count=} error getting brightness: {e}") if log_debug_enabled else None
        return None

    def interpolate_brightness(self, smoothed_lux: int, current_point: LuxPoint, next_point: LuxPoint) -> int:

        def _x_from_lux(lux: int) -> float:
            return (math.log10(lux) / math.log10(100000)) if lux > 0 else 0

        interpolated_brightness = float(current_point.brightness)
        x_smoothed = _x_from_lux(smoothed_lux)
        x_current_point = _x_from_lux(current_point.lux)
        x_next_point = _x_from_lux(next_point.lux)
        interpolated_brightness += (next_point.brightness - current_point.brightness) * (
                x_smoothed - x_current_point) / (x_next_point - x_current_point)
        return round(interpolated_brightness)

    def assess_preset_proximity(self, proposed_brightness: float,
                                previous_normal_point: LuxPoint, matched_point: LuxPoint, next_point: LuxPoint) -> str | None:
        # Brightness is a better indicator of nearness for deciding whether to activate a preset
        ordered = sorted([(abs(proposed_brightness - matched_point.brightness), matched_point),
                          (abs(proposed_brightness - previous_normal_point.brightness), previous_normal_point),
                          (abs(proposed_brightness - next_point.brightness), next_point)], key=lambda x: x[0])
        for diff, item in ordered:
            if diff < self.sensitivity_percent and (pick := item.preset_name):
                log_debug(f"LuxAuto: assess_preset_proximity {pick=}") if log_debug_enabled else None
                return pick
        return None

    def lux_summary(self, metered_lux: float, smoothed_lux: int) -> str:
        lux_int = round(metered_lux)  # 256 bit char in lux_summary_text can cause issues if stdout not utf8 (force utf8 for stdout)
        return f"{lux_int} {SMOOTHING_SYMBOL} {smoothed_lux} lux {tr('(smoothed)')}" if lux_int != smoothed_lux else f"{lux_int} lux"

    def stop(self) -> None:
        super().stop()
        assert is_running_in_gui_thread()
        self._lux_dialog_message_qtsignal.disconnect()
        log_info("LuxAuto: stopped on request")


@dataclass
class LuxPoint:
    lux: int
    brightness: int
    preset_name: str | None = None

    def __lt__(self, other) -> bool:  # Brightness doesn't matter for comparion purposes.
        return self.lux < other.lux

    def __eq__(self, other) -> bool:  # Brightness doesn't matter for comparion purposes.
        return self.lux == other.lux and self.preset_name == other.preset_name

    def __hash__(self):  # Brightness doesn't matter for comparion purposes.
        return hash((self.lux, self.preset_name))

    def __str__(self):
        return f"({self.lux} lux, {self.brightness}%, preset={self.preset_name})"


class LuxDeviceType(namedtuple('LuxDevice', 'name description'), Enum):
    SEMI_AUTO = "calculator", QT_TR_NOOP("Semi-automatic geolocated")
    ARDUINO = "arduino", QT_TR_NOOP("Arduino tty device")
    FIFO = "fifo", QT_TR_NOOP("Linux FIFO")
    EXECUTABLE = "executable", QT_TR_NOOP("Script/program")


class LuxConfig(ConfIni):

    def __init__(self) -> None:
        super().__init__()
        self.path = ConfIni.get_path('AutoLux')
        self.last_modified_time = 0.0
        self.cached_profiles_map: Dict[str, List[LuxPoint]] = {}

    def get_device_name(self) -> str:
        return self.get("lux-meter", "lux-device", fallback='')

    def get_preset_points(self) -> List[LuxPoint]:
        if self.has_option('lux-presets', 'lux-preset-points'):
            return [LuxPoint(lux, -1, name) for lux, name in literal_eval(self.get('lux-presets', 'lux-preset-points'))]
        return []

    def get_interval_minutes(self) -> int:
        return self.getint('lux-meter', 'interval-minutes', fallback=10)

    def is_auto_enabled(self) -> bool:
        return self.getboolean("lux-meter", "automatic-brightness", fallback=False)

    def load(self, force: bool = False) -> LuxConfig:
        self.cached_profiles_map.clear()
        if self.path.exists():
            if Path.stat(self.path).st_mtime > self.last_modified_time or force:
                log_info(f"Reading autolux file '{self.path.as_posix()}'")
                text = Path(self.path).read_text()
                self.read_string(text)
                self.last_modified_time = Path.stat(self.path).st_mtime
        for section_name in ['lux-meter', 'lux-profile', 'lux-ui', 'lux-presets']:
            if not self.has_section(section_name):
                self.add_section(section_name)
        return self


class LuxDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def invoke(main_controller: VduAppController) -> None:
        LuxDialog.show_existing_dialog() if LuxDialog.exists() else LuxDialog(main_controller)

    @staticmethod
    def reconfigure_instance():
        if lux_dialog := LuxDialog.get_instance():  # type: ignore
            lux_dialog.reconfigure()

    @staticmethod
    def lux_dialog_message(message: str, timeout: int, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        if lux_dialog := LuxDialog.get_instance():  # type: ignore
            lux_dialog.status_message(message, timeout, destination)

    @staticmethod
    def lux_dialog_show_brightness(vdu_stable_id: VduStableId, brightness: int) -> None:
        if lux_dialog := LuxDialog.get_instance():  # type: ignore
            lux_dialog.current_brightness_map[vdu_stable_id] = brightness
            lux_dialog.profile_plot.show_changes(profile_changes=False)

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.setWindowTitle(tr('Light-Metering'))
        self.main_controller: VduAppController = main_controller
        self.lux_profiles_map: Dict[VduStableId, List[LuxPoint]] = {}
        self.range_restrictions_map: Dict[VduStableId, Tuple[int, int]] = {}
        self.preset_points: List[LuxPoint] = []
        self.drawing_color_map: Dict[VduStableId, QColor] = {}
        self.current_brightness_map: Dict[VduStableId, int] = {}
        self.has_profile_changes = False
        self.setMinimumWidth(npx(950))
        self.path = ConfIni.get_path('AutoLux')
        self.device_name = ''
        self.lux_config = main_controller.get_lux_auto_controller().get_lux_config()

        self.setLayout(main_layout := QVBoxLayout())
        main_layout.addWidget(top_box := QWidget())
        top_box.setLayout(top_box_layout := QGridLayout())

        self.lux_gauge_widget = LuxGaugeWidget(self)

        top_box_layout.addWidget(self.lux_gauge_widget, 0, 0, 4, 2,
                                 alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        existing_device = self.lux_config.get_device_name()
        existing_device_type = self.lux_config.get('lux-meter', 'lux-device-type', fallback='')
        self.meter_device_selector = QComboBox()
        for i, dev_type in enumerate(LuxDeviceType):
            if dev_type.name == existing_device_type:  # List existing device and device type, set it as selected.
                self.meter_device_selector.addItem(f"{tr(dev_type.description)}: {existing_device}", dev_type)
                self.meter_device_selector.setCurrentIndex(i)
            else:
                self.meter_device_selector.addItem(tr(dev_type.description), dev_type)  # List device type only.

        top_box_layout.addWidget(self.meter_device_selector, 0, 2, 1, 3)

        self.enabled_checkbox = QCheckBox(tr("Enable automatic brightness adjustment"))
        top_box_layout.addWidget(self.enabled_checkbox, 1, 2, 1, 3)

        self.interval_label = QLabel(tr("Adjustment interval minutes"))
        top_box_layout.addWidget(self.interval_label, 2, 2, 1, 2)

        self.interval_selector = QSpinBox()
        self.interval_selector.setMinimum(1)
        self.interval_selector.setMaximum(120)
        top_box_layout.addWidget(self.interval_selector, 2, 4, 1, 1)

        self.interpolate_checkbox = QCheckBox(tr("Interpolate brightness values"))
        top_box_layout.addWidget(self.interpolate_checkbox, 3, 2, 1, 3)
        self.setMinimumSize(top_box.minimumSize())

        self.profile_selector_widget = QListWidget(parent=self)
        self.profile_selector_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.profile_selector_widget.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        self.profile_selector_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.profile_selector_widget.setSpacing(0)
        self.profile_selector_widget.setMinimumWidth(npx(940))
        self.profile_selector_widget.setMinimumHeight(native_font_height(scaled=1.4))

        main_layout.addWidget(self.profile_selector_widget, stretch=0)

        self.profile_plot = LuxProfileWidget(self)

        def _lux_changed(lux: int) -> None:
            if self.profile_plot:
                self.profile_plot.current_lux = lux
                self.profile_plot.create_plot()

        self.lux_gauge_widget.lux_changed_qtsignal.connect(_lux_changed)

        main_layout.addWidget(self.profile_plot, stretch=1)

        self.status_bar = QStatusBar()
        self.save_button = StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), title=tr("Save Profiles"), clicked=self.save_profiles,
                                     tip=tr("Apply and save profile-chart changes."))
        self.revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=tr("Revert Profiles"),
                                       clicked=self.reconfigure, tip=tr("Abandon profile-chart changes, revert to last saved."))
        quit_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr("Close"), clicked=self.close)
        for button in (self.save_button, self.revert_button, quit_button):
            self.status_bar.addPermanentWidget(button, 0)

        self.status_layout = QHBoxLayout()
        main_layout.addLayout(self.status_layout)
        self.adjust_now_button = StdButton(clicked=self.main_controller.get_lux_auto_controller().adjust_brightness_now,
                                           tip=tr("Press to expire the timer and immediately evaluate brightness."))
        self.status_layout.addWidget(self.adjust_now_button, 0)
        self.adjust_now_button.hide()
        self.status_layout.addWidget(self.status_bar)

        def _choose_device(index: int) -> None:
            current_dev = self.lux_config.get('lux-meter', "lux-device", fallback=LuxMeterSemiAutoDevice.device_name)
            current_dev_type = self.lux_config.get('lux-meter', "lux-device-type", fallback=LuxDeviceType.SEMI_AUTO.name)
            new_dev_type = self.meter_device_selector.itemData(index)
            if new_dev_type == LuxDeviceType.SEMI_AUTO:
                new_dev_path = LuxMeterSemiAutoDevice.device_name
            elif new_dev_type in (LuxDeviceType.ARDUINO, LuxDeviceType.FIFO, LuxDeviceType.EXECUTABLE):
                if current_dev_type == new_dev_type.name:
                    default_file = current_dev
                else:
                    default_file = "/dev/arduino" if new_dev_type == LuxDeviceType.ARDUINO else Path.home().as_posix()
                new_dev_path = FasterFileDialog.getOpenFileName(
                    self, tr("Select: {}").format(tr(new_dev_type.description)), default_file)[0]
            if not self.validate_device(new_dev_path, required_type=new_dev_type):
                new_dev_path = ''
            if new_dev_path == '':  # Mothing selected, set back to what was in config
                for dev_num in range(self.meter_device_selector.count()):
                    config_device_type = self.lux_config.get('lux-meter', 'lux-device-type', fallback='')
                    if self.meter_device_selector.itemData(dev_num).name == config_device_type:
                        self.meter_device_selector.setCurrentIndex(dev_num)
            else:
                if new_dev_path != current_dev:
                    self.meter_device_selector.setItemText(index, tr(new_dev_type.description) + ': ' + new_dev_path)
                    self.lux_config.set('lux-meter', "lux-device", new_dev_path)
                    self.lux_config.set('lux-meter', "lux-device-type", new_dev_type.name)
                    self.lux_config.save(self.path)
                    self.apply_settings()
                    if (device := self.main_controller.get_lux_auto_controller().lux_meter) and device.has_auto_capability:
                        self.main_controller.get_lux_auto_controller().set_auto(
                            True)  # Enable auto if the meter is full auto or semi-auto
                    self.status_message(tr("Meter changed to {}.").format(new_dev_path))

        self.meter_device_selector.activated.connect(_choose_device)

        def _set_auto_monitoring(checked: int) -> None:
            enable = checked == intV(Qt.CheckState.Checked)
            if enable != self.lux_config.is_auto_enabled():
                self.lux_config.set('lux-meter', 'automatic-brightness', 'yes' if enable else 'no')
                self.adjust_now_button.setVisible(enable)
                self.apply_settings()

        self.enabled_checkbox.stateChanged.connect(_set_auto_monitoring)

        def _apply_interval(value: int) -> None:
            if self.interval_selector.value() == value and value != self.lux_config.get_interval_minutes():
                self.lux_config.set('lux-meter', 'interval-minutes', str(value))
                self.apply_settings()
                self.status_message(tr("Interval changed to {} minutes.").format(value))

        def _interval_selector_changed(value: int) -> None:
            if self.interval_selector.value() == value and value != self.lux_config.get_interval_minutes():
                QTimer.singleShot(1200, partial(_apply_interval, value))  # kind of like focus out, no change in a while

        self.interval_selector.valueChanged.connect(_interval_selector_changed)

        def _set_interpolation(checked: int) -> None:
            if checked == intV(Qt.CheckState.Checked):  # need to save setting if not already set
                if not self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=False):  # altering value
                    self.lux_config.set('lux-meter', 'interpolate-brightness', 'yes')
                    MBox(MIcon.Information, msg=tr('Interpolation may increase the number of writes to VDU NVRAM.'),
                         info=tr('Changes specified by each brightness-response curve will only be applied when they '
                                 'cross a minimum threshold (default {}%).\n\n'
                                 'When designing brightness-response curves, consider minimizing '
                                 'brightness changes to reduce wear on NVRAM.').format(10)).exec()
            elif self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=True):
                self.lux_config.set('lux-meter', 'interpolate-brightness', 'no')
            self.apply_settings()
            self.profile_plot.create_plot()

        self.interpolate_checkbox.stateChanged.connect(_set_interpolation)

        def _select_profile(index: int) -> None:
            if self.profile_plot is not None:
                profile_name = list(self.lux_profiles_map.keys())[index]
                self.profile_plot.set_current_profile(profile_name)
                self.status_message(tr("Editing profile {}").format(profile_name))
            data = self.profile_selector_widget.item(index).data(Qt.ItemDataRole.UserRole)
            if self.lux_config.get('lux-ui', 'selected-profile', fallback=None) != data:
                self.lux_config.set('lux-ui', 'selected-profile', data)
                self.apply_settings(requires_metering_restart=False)

        self.profile_selector_widget.currentRowChanged.connect(_select_profile)
        self.reconfigure()
        self.make_visible()

    def chart_changed_callback(self) -> None:
        self.has_profile_changes = True
        self.status_message(tr("Press Save-Profile to activate new profile."))
        self.save_button.setEnabled(True)
        self.revert_button.setEnabled(True)

    def reconfigure(self) -> None:
        assert self.profile_plot is not None
        # Make a copy of the config so the profile changes aren't applied until Apply is pressed.
        lux_auto_controller = self.main_controller.get_lux_auto_controller()
        self.lux_config = lux_auto_controller.get_lux_config().duplicate(LuxConfig())  # type: ignore
        self.device_name = self.lux_config.get("lux-meter", "lux-device", fallback='')
        log_debug("{self.lux_config.is_auto_enabled()=}") if log_debug_enabled else None
        self.enabled_checkbox.setChecked(self.lux_config.is_auto_enabled())
        self.interpolate_checkbox.setChecked(self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=False))
        self.has_profile_changes = False
        self.current_brightness_map.clear()
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)
        self.adjust_now_button.setText(f"{TIMER_RUNNING_SYMBOL} 00:00")
        self.adjust_now_button.setVisible(self.lux_config.is_auto_enabled())

        connected_id_list = []  # List of all currently connected VDUs
        for index, vdu_sid in enumerate(self.main_controller.get_vdu_stable_id_list()):
            value_range = (0, 100)
            if self.main_controller.is_vcp_code_enabled(vdu_sid, BRIGHTNESS_VCP_CODE):
                value_range = self.main_controller.get_range(vdu_sid, BRIGHTNESS_VCP_CODE, fallback=value_range)
                self.range_restrictions_map[vdu_sid] = value_range
                try:
                    self.current_brightness_map[vdu_sid] = self.main_controller.get_value(vdu_sid, BRIGHTNESS_VCP_CODE)
                except VduException as ve:
                    self.current_brightness_map[vdu_sid] = 0
                    log_warning("VDU may not be available:", str(ve), trace=True)
            # All VDUs have a profile, even if they have no brightness control - because a preset may be attached to a lux value.
            self.lux_profiles_map[vdu_sid] = lux_auto_controller.get_lux_profile(vdu_sid, value_range)
            connected_id_list.append(vdu_sid)
        self.preset_points.clear()  # Edit out deleted presets by starting from scratch
        for preset_point in self.lux_config.get_preset_points():
            if preset_point.preset_name is not None and self.main_controller.find_preset_by_name(preset_point.preset_name):
                self.preset_points.append(preset_point)

        self.interval_selector.setValue(self.lux_config.get_interval_minutes())
        existing_id_list = [item.data(Qt.ItemDataRole.UserRole) for item in
                            self.profile_selector_widget.findItems('*', Qt.MatchFlag.MatchWildcard)]
        candidate_id = self.lux_config.get('lux-ui', 'selected-profile', fallback=None)
        if connected_id_list and (candidate_id is None or candidate_id not in connected_id_list):
            candidate_id = connected_id_list[0]
        try:
            self.profile_selector_widget.blockSignals(True)  # Stop initialization from causing signal until all data is aligned.
            if connected_id_list != existing_id_list:  # List of connected VDUs has changed
                self.profile_selector_widget.clear()
                random.seed(int(self.lux_config.get("lux-ui", "vdu_color_seed", fallback='0x543fff'), 16))
                self.drawing_color_map.clear()
                for index, vdu_sid in enumerate(connected_id_list):
                    color = QColor.fromHsl(int(index * 137.508) % 255, random.randint(64, 128), random.randint(192, 200))
                    self.drawing_color_map[vdu_sid] = color
                    color_icon = create_icon_from_svg_bytes(SWATCH_ICON_SOURCE.replace(b"#ffffff", bytes(color.name(), 'utf-8')))
                    key_item = QListWidgetItem(color_icon, self.main_controller.get_vdu_preferred_name(vdu_sid))
                    key_item.setData(Qt.ItemDataRole.UserRole, vdu_sid)
                    self.profile_selector_widget.addItem(key_item)
                    if vdu_sid == candidate_id:
                        self.profile_selector_widget.setCurrentRow(index)
                        self.profile_plot.current_vdu_sid = candidate_id
                self.profile_selector_widget.setFixedHeight(
                    native_font_height(scaled=1.5) * (1 if len(connected_id_list) <= 3 else 5))
        finally:
            self.profile_selector_widget.blockSignals(False)
        self.configure_ui(lux_auto_controller.lux_meter)
        self.profile_plot.create_plot()
        lux_auto_controller.lux_meter.get_value() if lux_auto_controller.lux_meter else None  # prime the UI
        self.status_message('')

    def make_visible(self) -> None:
        self.lux_gauge_widget.enable_gauge(True)
        super().make_visible()

    def is_interpolating(self) -> bool:
        return self.interpolate_checkbox.isChecked()

    def validate_device(self, device, required_type: LuxDeviceType) -> bool:
        if required_type == LuxDeviceType.SEMI_AUTO:
            if self.main_controller.main_config.get_location() is None:
                MBox(MIcon.Critical, msg=tr("Cannot configure a solar lux calculator, no location is defined."),
                     info=tr("Please set a location in the main Settings-Dialog.")).exec()
                self.main_controller.edit_config(self.main_controller.main_config.config_name)
                return False
            MBox(MIcon.Information,
                 msg=tr("Semi-automatic lux adjustment: quick start instructions.\n"
                        "________________________________________________________________________________________\n\n"
                        "Use the ambient-light-level slider to set the current light level.\n\n"
                        "Starting from your chosen level, the application will adjust the light level\n"
                        "according to a trajectory based on the estimated sunlight for your location.\n\n"
                        "If conditions change, adjust the slider to alter the trajectory.\n\n"
                        "The trajectory is shown in the Light Metering Dialog, along with the estimate\n"
                        "of outdoor lux (Eo) and the Daylight-Factor (DF), the ratio of indoor to\n"
                        "outdoor lux.\n"),
                 details=tr("Estimation of indoor illumination (Ei) from solar illumination (Eo):\n"
                            "    Ei = DF * Eo\n"
                            "    DF = Ei / Eo\n"
                            "Ei:\tIndoor Illumination, from slider, or calculated automatically from Eo.\n"
                            "Eo:\tSolar/Outdoor Illumination, calculated from geolocation and datetime.\n"
                            "DF:\tDaylight factor, the ratio of indoor to outdoor illumination. Updated\n"
                            "\twhenever the Ambient Light Level slider is manually altered.")).exec()
            return True
        path = pathlib.Path(device)
        if ((required_type == LuxDeviceType.ARDUINO and path.is_char_device()) or
                (required_type == LuxDeviceType.FIFO and path.is_fifo()) or
                (required_type == LuxDeviceType.EXECUTABLE and path.exists() and os.access(device, os.X_OK))):
            if not os.access(device, os.R_OK):
                info = None
                if path.is_char_device() and path.group() != "root":
                    info = tr("You might need to be a member of the {} group.").format(path.group())
                MBox(MIcon.Critical, msg=tr("No read access to {}").format(device), info=info).exec()
                return False
        else:
            MBox(MIcon.Critical, msg=tr("Expecting {}, but {} was selected.").format(tr(required_type.description), device)).exec()
            return False
        return True

    def apply_settings(self, requires_metering_restart: bool = True) -> None:
        self.lux_config.save(self.path)
        if requires_metering_restart:
            self.main_controller.get_lux_auto_controller().initialize_from_config()  # Causes the LuxAutoWorker to restart
            self.lux_gauge_widget.connect_meter(None)
            meter_device = self.main_controller.get_lux_auto_controller().lux_meter
            self.configure_ui(meter_device)  # Use the new meter for a new lux-display metering thread

    def configure_ui(self, meter_device: LuxMeterDevice | None) -> None:
        if meter_device is not None:  # Set this up first because altering the checkboxes will cause events to use the outcome.
            self.lux_gauge_widget.connect_meter(meter_device)
        if meter_device is None or (meter_device.has_semi_auto_capability
                                    and self.main_controller.main_config.get_location() is None):
            self.enabled_checkbox.setChecked(False)
            self.enabled_checkbox.setEnabled(False)
            self.interval_label.setEnabled(False)
            self.status_message(tr("No metering device set."))
        else:
            self.enabled_checkbox.setEnabled(True)
            self.interval_label.setEnabled(True)

    def save_profiles(self) -> None:
        for vdu_sid, profile in self.profile_plot.profiles_map.items():
            data = [(lux_point.lux, lux_point.brightness) for lux_point in profile if lux_point.preset_name is None]
            self.lux_config.set('lux-profile', vdu_sid, repr(data))
        preset_data = [(lux_point.lux, lux_point.preset_name) for lux_point in self.profile_plot.preset_points]
        self.lux_config.set('lux-presets', 'lux-preset-points', repr(preset_data))
        self.apply_settings()
        self.has_profile_changes = False
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)

    def closeEvent(self, event) -> None:
        if self.has_profile_changes:
            answer = MBox(MIcon.Critical, msg=tr("There are unsaved profile changes?"),
                          buttons=MBtn.Save | MBtn.Discard | MBtn.Cancel, default=MBtn.Cancel).exec()
            if answer == MBtn.Save:
                self.save_profiles()
            elif answer == MBtn.Cancel:
                event.ignore()
                return
        self.lux_gauge_widget.enable_gauge(False)  # Stop updating the display
        super().closeEvent(event)

    def status_message(self, message: str, timeout: int = 0, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        if destination == MsgDestination.COUNTDOWN:
            if not self.adjust_now_button.isHidden():
                self.adjust_now_button.setText(message)
        else:
            self.status_bar.showMessage(message, timeout)
        QApplication.processEvents()  # force messages out


class LuxDeviceException(Exception):
    pass


class LuxAutoController:

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.main_controller = main_controller
        self.lux_config = LuxConfig()
        self.lux_config.load()
        self.lux_meter: LuxMeterDevice | None = None
        self.lux_auto_brightness_worker: LuxAutoWorker | None = None
        self.lux_tool_button: ToolButton | None = None
        self.lux_lighting_check_button: ToolButton | None = None
        self.lux_slider: LuxAmbientSlider | None = None

    def create_tool_button(self) -> ToolButton:  # Used when the application UI has to reinitialize
        # Used when the application UI has to reinitialize
        self.lux_tool_button = ToolButton(AUTO_LUX_ON_SVG, tr("Toggle automatic light metered brightness adjustment"))
        return self.lux_tool_button

    def create_lighting_check_button(self) -> ToolButton:
        # Used when the application UI has to reinitialize
        self.lux_lighting_check_button = ToolButton(LIGHTING_CHECK_SVG, tr("Perform ambient lighting check now"))
        return self.lux_lighting_check_button

    def update_manual_meter(self, value: int):
        if self.is_auto_enabled() and not self.lux_meter.has_semi_auto_capability:  # goto manual unless on semi-auto
            self.set_auto(False)
        self.lux_meter.set_current_value(value)
        self.adjust_brightness_now()

    def update_manual_slider(self, value: int):
        if self.is_auto_enabled() and self.lux_slider:  # May not exist during initialization
            self.lux_slider.set_current_value(value)

    def create_manual_input_control(self) -> LuxAmbientSlider:
        if self.lux_slider is None:
            self.lux_slider = LuxAmbientSlider(self)
            self.lux_slider.new_lux_value_qtsignal.connect(self.update_manual_meter)

            def _toggle_lux_dialog():
                if LuxDialog.exists() and LuxDialog.get_instance().isVisible():
                    LuxDialog.get_instance().close()
                else:
                    LuxDialog.invoke(self.main_controller)

            self.lux_slider.title_button_pressed_qtsignal.connect(_toggle_lux_dialog)
            self.lux_slider.status_icon_pressed_qtsignal.connect(self.adjust_brightness_now)
        return self.lux_slider

    def get_lux_zone(self) -> LuxZone | None:
        if self.lux_slider and self.lux_slider.current_zone:
            return self.lux_slider.current_zone
        return None

    def stop_worker(self):
        if self.lux_auto_brightness_worker is not None:
            self.lux_auto_brightness_worker.stop()
            self.lux_auto_brightness_worker = None

    def start_worker(self, single_shot: bool):
        if self.lux_config.is_auto_enabled() or single_shot:
            if self.lux_meter is not None:
                if self.lux_auto_brightness_worker is not None:
                    self.stop_worker()
                self.lux_auto_brightness_worker = LuxAutoWorker(self, single_shot)
                self.lux_auto_brightness_worker.start()
                try:
                    self.lux_meter.new_lux_value_qtsignal.connect(self.update_manual_slider,
                                                                  type=Qt.ConnectionType.UniqueConnection)
                except TypeError:
                    pass

    def initialize_from_config(self) -> None:
        assert is_running_in_gui_thread()
        self.lux_config.load()
        try:
            if self.lux_meter is not None:
                self.lux_meter.stop_metering()
            device_name = self.lux_config.get_device_name().strip()
            if not device_name or device_name == LuxMeterSemiAutoDevice.obsolete_device_name:
                device_name = LuxMeterSemiAutoDevice.device_name
            LuxMeterSemiAutoDevice.set_location(self.main_controller.main_config.get_location())
            self.lux_meter = lux_create_device(device_name)
            if self.lux_config.is_auto_enabled():
                log_info("Lux auto-brightness settings refresh - restart monitoring.")
                self.start_worker(single_shot=False)
            else:
                log_info("Lux auto-brightness settings refresh - monitoring is off.")
                self.stop_worker()
            self.main_controller.update_window_status_indicators()  # Refresh indicators immediately
        except LuxDeviceException as lde:
            log_error(f"Error setting up lux meter {lde}", trace=True)
            MBox(MIcon.Critical, msg=tr("Error setting up lux meter: {}").format(self.lux_config.get_device_name()),
                 info=str(lde)).exec()
        if self.lux_tool_button:
            self.lux_tool_button.refresh_icon(self.current_auto_svg())  # Refresh indicators immediately
        if self.lux_lighting_check_button:
            self.lux_lighting_check_button.refresh_icon(self.current_check_svg())

    def is_auto_enabled(self) -> bool:
        return self.lux_config is not None and self.lux_config.is_auto_enabled()

    def current_auto_svg(self) -> bytes:
        return AUTO_LUX_ON_SVG if self.is_auto_enabled() else AUTO_LUX_OFF_SVG

    def current_check_svg(self) -> bytes:
        return LIGHTING_CHECK_SVG if self.is_auto_enabled() else LIGHTING_CHECK_OFF_SVG

    def get_lux_config(self) -> LuxConfig:
        assert self.lux_config is not None
        return self.lux_config

    def toggle_auto(self) -> None:
        self.set_auto(not self.is_auto_enabled())

    def set_auto(self, enable: bool):
        assert self.lux_config is not None
        log_debug(f"LuxAutoController: set_auto {enable}")
        if enable:
            if self.lux_meter and self.lux_meter.has_semi_auto_capability and not self.main_controller.main_config.get_location():
                message = tr("Auto disabled, no location defined.")
                enable = False
            elif self.lux_config.is_auto_enabled():
                message = tr("Restarting automatic light metering.")
            else:
                message = tr("Switching to automatic light metering.")
            self.lux_config.set('lux-meter', 'automatic-brightness', 'yes' if enable else 'no')
        else:
            message = tr("Switching to manual input of ambient lux.")
            self.lux_config.set('lux-meter', 'automatic-brightness', 'no')
        self.lux_config.save(ConfIni.get_path('AutoLux'))
        self.main_controller.status_message(message, timeout=5000)
        LuxDialog.lux_dialog_message(message, timeout=5000)
        self.initialize_from_config()
        LuxDialog.reconfigure_instance()

    def adjust_brightness_now(self) -> None:
        if self.is_auto_enabled():
            if self.lux_auto_brightness_worker is not None:
                self.lux_auto_brightness_worker.adjust_now_requested = True
            else:
                log_error("adjust_brightness_now: No worker - unexpected - error?")
        else:
            self.start_worker(single_shot=True)

    def get_lux_profile(self, vdu_stable_id: VduStableId, brightness_range) -> List[LuxPoint]:
        if self.lux_config.has_option('lux-profile', vdu_stable_id):  # initialize removing duplicate points
            lux_points = list(set([LuxPoint(v[0], v[1]) for v in literal_eval(self.lux_config.get('lux-profile', vdu_stable_id))]))
        else:  # Create a default profile:
            min_v, max_v = (0, 100) if brightness_range is None else brightness_range
            defaults = [(0, 0.6), (100, 0.8), (1_000, 0.9), (10_000, 0.9), (100_000, 0.9)]
            lux_points = [LuxPoint(lux, min_v + round(r * (max_v - min_v))) for lux, r in defaults]
        if self.lux_config.has_option('lux-presets', 'lux-preset-points'):  # Merge in preset points
            merge_map = {point.lux: point for point in lux_points}
            for preset_point in self.lux_config.get_preset_points():
                # Look up the Preset's brightness for this VDU - get value from the actual Preset.
                if preset := self.main_controller.find_preset_by_name(preset_point.preset_name):  # Drop any that no longer exist
                    if point := merge_map.get(preset_point.lux):
                        point.preset_name = preset_point.preset_name  # Merge both points
                    else:
                        merge_map[preset_point.lux] = preset_point  # Add this point on its own
                        point = preset_point
                    # Point brightness for this VDU will be -1 if this VDU's brightness-control doesn't participate in the Preset.
                    point.brightness = preset.get_brightness(vdu_stable_id)
            lux_points = list(merge_map.values())
            lux_points.sort()
        log_debug(f"LuxAuto: get_lux_profile({vdu_stable_id=}) => {lux_points=}") if log_debug_enabled else None
        return lux_points


@dataclass
class LuxZone:
    name: str
    icon_svg: bytes
    min_lux: int
    max_lux: int
    icon_svg_lux: int
    column_span: int


class LuxAmbientSlider(QWidget):
    new_lux_value_qtsignal = pyqtSignal(int)
    status_icon_changed_qtsignal = pyqtSignal()
    status_icon_pressed_qtsignal = pyqtSignal()
    title_button_pressed_qtsignal = pyqtSignal()

    def __init__(self, controller: LuxAutoController) -> None:
        super().__init__()
        self.controller = controller
        self.in_flux = False
        self.zones = [  # Using col span as a hacky way to line up icons above the slider
            LuxZone(tr("Sunlight"), LUX_SUNLIGHT_SVG, 20_000, 100_000, 45_000, column_span=2),
            LuxZone(tr("Daylight"), LUX_DAYLIGHT_SVG, 5_000, 20_000, 6_000, column_span=2),
            LuxZone(tr("Overcast"), LUX_OVERCAST_SVG, 400, 5_000, 900, column_span=3),
            LuxZone(tr("Twilight"), LUX_TWILIGHT_SVG, 100, 400, 130, column_span=2),
            LuxZone(tr("Subdued"), LUX_SUBDUED_SVG, 15, 100, 20, column_span=3),
            LuxZone(tr("Dark"), LUX_DARK_SVG, 0, 15, 2, column_span=4), ]
        self.current_value = 10_000
        self.status_icon = ThemedSvgWidget(self.zones[0].icon_svg, native_font_height(scaled=2.0), native_font_height(scaled=2.0),
                                           self)
        self.current_name: str | None = None
        self.current_zone: LuxZone | None = None

        top_layout = QVBoxLayout()
        self.setLayout(top_layout)
        top_layout.setSpacing(0)
        alter_margins(top_layout, top=0, bottom=0, default=self.style())

        label = TitleButton(AMBIENT_PANEL_ICON_SOURCE, tr("Ambient Light Level"), tr("lux"),
                            clicked=self.title_button_pressed_qtsignal)
        label.setToolTip(tr("Ambient light level control for adjusting all monitors.\n(Click for Light-Meter Dialog)"))
        top_layout.addWidget(label, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)

        input_panel = QWidget()
        input_panel_layout = QHBoxLayout()
        alter_margins(input_panel_layout, top=0, bottom=0, default=self.style())
        input_panel.setLayout(input_panel_layout)
        input_panel_layout.addWidget(self.status_icon)

        slider_panel = QWidget()
        slider_panel_layout = QGridLayout()
        slider_panel.setLayout(slider_panel_layout)
        slider_panel_layout.setSpacing(0)
        # Move the slider up a little to line up with left and right elements
        alter_margins(slider_panel_layout, top=0, bottom=slider_panel_layout.contentsMargins().bottom(), default=self.style())

        self.slider = ClickableSlider()
        self.slider.setToolTip(tr("Ambient light level input (lux value)"))
        self.slider.setToolTipDuration(TOOLTIP_DURATION_MSEC)
        self.slider.setMinimumWidth(npx(200))
        self.slider.setRange(0, int(math.log10(100000) * 1000))
        self.slider.setSingleStep(1)
        self.slider.setPageStep(100)
        self.slider.setTickInterval(1000)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setOrientation(Qt.Orientation.Horizontal)  # type: ignore
        self.slider.setTracking(False)  # Don't rewrite the ddc value too often - not sure of the implications
        slider_panel_layout.addWidget(self.slider, 1, 0, 1, 15, alignment=Qt.AlignmentFlag.AlignTop)

        # A hacky way to get custom labels without redefining paint
        for col_num, span, value in ((0, 3, 1), (3, 3, 10), (6, 3, 100), (9, 3, 1000), (12, 3, 10000), (14, 1, 100000)):
            log10_label = QLabel(f"{value:2d}")
            app_font = QApplication.font()
            log10_label.setFont(QFont(app_font.family(), round(app_font.pointSize() * .66), QFont.Weight.Normal))
            slider_panel_layout.addWidget(log10_label, 2, col_num, 1, span,
                                          alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        input_panel_layout.addWidget(slider_panel, stretch=100)

        self.lux_input_field = QSpinBox()
        self.lux_input_field.setLineEdit(LineEditAll())
        self.lux_input_field.setToolTip(tr("Ambient light level input (lux value)"))
        self.lux_input_field.setToolTipDuration(TOOLTIP_DURATION_MSEC)
        self.lux_input_field.setKeyboardTracking(False)
        self.lux_input_field.setRange(1, 100000)
        self.lux_input_field.setValue(self.current_value)
        input_panel_layout.addWidget(self.lux_input_field)

        top_layout.addWidget(input_panel, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)
        top_layout.addStretch(0)

        def _lux_slider_change(new_value: int) -> None:
            actual_value = round(10 ** (new_value / 1000))
            self.set_current_value(actual_value, self.slider)
            self.new_lux_value_qtsignal.emit(actual_value)

        self.slider.valueChanged.connect(_lux_slider_change)

        def _lux_slider_moved(new_value: int) -> None:
            new_lux_value = round(10 ** (new_value / 1000))
            self.set_current_value(new_lux_value, self.slider)

        self.slider.sliderMoved.connect(_lux_slider_moved)

        def _lux_input_field_changed() -> None:
            self.set_current_value(self.lux_input_field.value(), self.lux_input_field)

        self.lux_input_field.valueChanged.connect(_lux_input_field_changed)

        def _input_field_editing_finished():
            self.set_current_value(self.lux_input_field.value(), self.lux_input_field)

        self.lux_input_field.editingFinished.connect(_input_field_editing_finished)

        col = 0
        log10_icon_size = QSize(native_font_height(scaled=1), native_font_height(scaled=1))
        self.label_map: Dict[StdButton, bytes] = {}
        for zone in reversed(self.zones):
            zone_button = ThemedSvgButton(zone.icon_svg, icon_size=log10_icon_size,
                                          clicked=partial(self.lux_input_field.setValue, zone.icon_svg_lux), flat=True,
                                          tip=zone.name)
            slider_panel_layout.addWidget(zone_button, 0, col, 1, zone.column_span,
                                          alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
            self.label_map[zone_button] = zone.icon_svg
            col += zone.column_span

        self.set_current_value(
            round(controller.lux_meter.get_value()) if controller.lux_meter else 1000)  # don't trigger side-effects.

    def set_current_value(self, value: int, source: QWidget | None = None) -> None:
        # log_debug("set_current_value ", value, source, self.in_flux)
        icon_changed = False
        if not self.in_flux and value != self.current_value:
            try:
                if source is None:
                    self.blockSignals(True)
                self.in_flux = True
                for zone in self.zones:
                    if zone.min_lux < value <= zone.max_lux:
                        if self.current_zone != zone:
                            self.current_zone = zone
                            self.status_icon.load_from_icon_source(zone.icon_svg)
                            self.status_icon.setToolTip(zone.name)
                            icon_changed = True
                self.current_value = max(1, value)  # restrict to non-negative and something valid for log10
                if source != self.slider:
                    self.slider.setValue(round(math.log10(self.current_value) * 1000))
                if source != self.lux_input_field:
                    self.lux_input_field.setValue(self.current_value)
                # We can use values from non-semi-auto meters to calibrate the semi-auto-meter.
                semi_auto_source = self.controller.lux_meter and self.controller.lux_meter.has_semi_auto_capability
                if source == self.slider or source == self.lux_input_field or not semi_auto_source:
                    if location := self.controller.main_controller.main_config.get_location():
                        LuxMeterSemiAutoDevice.set_location(location)  # in case it's changed
                        LuxMeterSemiAutoDevice.update_df_from_lux_value(self.current_value, semi_auto_source)
            finally:
                self.in_flux = False
                if source is None:
                    self.blockSignals(False)
                if icon_changed:
                    self.status_icon_changed_qtsignal.emit()
