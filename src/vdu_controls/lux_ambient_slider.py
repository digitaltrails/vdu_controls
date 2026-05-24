# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import partial
from typing import Dict, TYPE_CHECKING

from vdu_controls.qt_imports import pyqtSignal, Qt, QSize
from vdu_controls.qt_imports import QFont
from vdu_controls.qt_imports import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSlider, QLabel, QApplication, QSpinBox

from vdu_controls.constants import TOOLTIP_DURATION_MSEC
from vdu_controls.app_locale import tr
from vdu_controls.lux_meters import LuxMeterSemiAutoDevice

from vdu_controls.scaling import desktop_font_height, dpx
from vdu_controls.svg import LUX_SUNLIGHT_SVG, LUX_DAYLIGHT_SVG, LUX_OVERCAST_SVG, LUX_TWILIGHT_SVG, LUX_SUBDUED_SVG, LUX_DARK_SVG, \
    AMBIENT_PANEL_ICON_SOURCE
from vdu_controls.widgets import ThemedSvgWidget, alter_margins, TitleButton, ClickableSlider, LineEditAll, StdButton, \
    ThemedSvgButton

if TYPE_CHECKING:
    from vdu_controls.lux_auto import LuxAutoController

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
        self.status_icon = ThemedSvgWidget(self.zones[0].icon_svg, desktop_font_height(scaled=2.0), desktop_font_height(scaled=2.0),
                                           self)
        self.current_name: str | None = None
        self.current_zone: LuxZone | None = None

        top_layout = QVBoxLayout()
        self.setLayout(top_layout)
        top_layout.setSpacing(0)
        alter_margins(top_layout, top=0, bottom=0, default=self.style())

        label = TitleButton(AMBIENT_PANEL_ICON_SOURCE, tr("Ambient Light Level"), tr("lux"),
                            clicked=self.title_button_pressed_qtsignal)   # type: ignore
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
        self.slider.setMinimumWidth(dpx(100))
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
                                          alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)   # type: ignore

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
        log10_icon_size = QSize(desktop_font_height(scaled=1), desktop_font_height(scaled=1))
        self.label_map: Dict[StdButton, bytes] = {}
        for zone in reversed(self.zones):
            zone_button = ThemedSvgButton(zone.icon_svg, icon_size=log10_icon_size,
                                          clicked=partial(self.lux_input_field.setValue, zone.icon_svg_lux), flat=True,
                                          tip=zone.name)
            slider_panel_layout.addWidget(zone_button, 0, col, 1, zone.column_span,
                                          alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)  # type: ignore
            self.label_map[zone_button] = zone.icon_svg
            col += zone.column_span
        value = 1000
        if controller.lux_meter is not None:
            metered_value = controller.lux_meter.get_value()
            if metered_value is not None:
                value = round(metered_value)
        self.set_current_value(value)  # don't trigger side-effects.

    def set_current_value(self, value: int, source: QWidget | None = None) -> None:
        # log.debug("set_current_value ", value, source, self.in_flux)
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
                semi_auto_source = self.controller.lux_meter is not None and self.controller.lux_meter.has_semi_auto_capability
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
