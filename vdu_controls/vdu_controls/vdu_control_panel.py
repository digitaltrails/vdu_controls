# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Callable, List

from vdu_controls.qt_imports import Qt, pyqtSignal
from vdu_controls.qt_imports import QWidget, QVBoxLayout, QFrame, QApplication, QHBoxLayout, QLabel, QSlider, QSpinBox, QComboBox

from vdu_controls.config_ini import VcpCapability, SUPPORTED_VCP_BY_CODE
from vdu_controls.constants import TOOLTIP_DURATION_MSEC
from vdu_controls.ddcutil_abstract import CONTINUOUS_TYPE, SIMPLE_NON_CONTINUOUS_TYPE, COMPLEX_NON_CONTINUOUS_TYPE, VcpValue, \
    VcpOrigin
from vdu_controls.internationalization import tr
from vdu_controls.logging import log_info
from vdu_controls.misc import proper_name, clamp
from vdu_controls.preset import Preset
from vdu_controls.scaling import native_font_height, npx
from vdu_controls.svg import PANEL_CONNECTED_ICON_SOURCE, VDU_CONNECTED_ICON_SOURCE
from vdu_controls.vdu_controller import VduController
from vdu_controls.vdu_exceptions import VduException
import vdu_controls.gui_misc as gui_misc
from vdu_controls.widgets import alter_margins, TitleButton, MBox, MIcon, ThemedSvgWidget, ClickableSlider, LineEditAll


class VduControlPanel(QWidget):
    """Widget that contains all the controls for a single VDU (monitor/display)."""

    def __init__(self, controller: VduController, vdu_exception_handler: Callable) -> None:
        super().__init__()
        self.controller: VduController = controller
        layout = QVBoxLayout()
        alter_margins(layout, top=0, bottom=0, default=self.style())
        if int(controller.vdu_number) < 1:
            self.title_button = TitleButton(PANEL_CONNECTED_ICON_SOURCE,
                                            controller.get_vdu_preferred_name(),
                                            tr("Panel {}".format(-int(controller.vdu_number))),
                                            clicked=controller.edit_config)
        else:
            self.title_button = TitleButton(VDU_CONNECTED_ICON_SOURCE,
                                            controller.get_vdu_preferred_name(),
                                            tr("Monitor {}".format(controller.vdu_number)),
                                            clicked=controller.edit_config)
        layout.addWidget(self.title_button, alignment=Qt.AlignmentFlag.AlignTop)  # other params fix Qt5 theme changes

        self.vcp_controls: List[VduControlBase] = []
        self.vdu_exception_handler = vdu_exception_handler

        for capability in controller.enabled_capabilities:
            control = None
            if capability.vcp_type == CONTINUOUS_TYPE:
                try:
                    control = VduControlSlider(controller, capability)
                except ValueError as valueError:
                    MBox(MIcon.Critical, msg=str(valueError)).exec()
            elif capability.vcp_type in (SIMPLE_NON_CONTINUOUS_TYPE, COMPLEX_NON_CONTINUOUS_TYPE):
                try:
                    control = VduControlComboBox(controller, capability)
                except ValueError as valueError:
                    MBox(MIcon.Critical, msg=valueError.args[0],
                         info=tr('If you want to extend the set of permitted values, see the man page concerning '
                                 'VDU/VDU-model config files.').format(capability.vcp_code, capability.name)).exec()
            else:
                raise TypeError(f'No GUI support for VCP type {capability.vcp_type} for vcp_code {capability.vcp_code}')
            if control is not None:
                layout.addWidget(control)
                self.vcp_controls.append(control)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        if len(self.vcp_controls) != 0:
            self.setLayout(layout)

        self.update_stats()
        try:
            self.refresh_from_vdu()
        except VduException as e:
            self.vdu_exception_handler(e)

    def get_control(self, vcp_code: str) -> VduControlBase | None:
        return next((c for c in self.vcp_controls if c.vcp_capability.vcp_code == vcp_code), None)

    def refresh_from_vdu(self) -> None:
        """Tell the control widgets to get fresh VDU data (maybe called from a task thread, so no GUI operations here)."""
        if values := self.controller.get_vcp_values([control.vcp_capability.vcp_code for control in self.vcp_controls]):
            for control, value in zip(self.vcp_controls, values):
                control.update_from_vdu(value)

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)

    def is_preset_active(self, preset: Preset) -> bool:
        vdu_section = self.controller.vdu_stable_id
        if vdu_section == proper_name(preset.name):
            return False  # ignore VDU initialization-presets
        count = 0
        preset_ini = preset.preset_ini
        for control in self.vcp_controls:
            if control.vcp_capability.property_name() in preset_ini[vdu_section]:
                # Prior to version vdu_controls 1.21 we stored lower, but ddcutil expects upper
                if control.get_current_text_value() != preset_ini[vdu_section][control.vcp_capability.property_name()].upper():
                    return False  # immediately fail if even one value differs
                count += 1
        return count > 0  # true unless no values were tested.

    def update_stats(self):
        name, sid = self.controller.get_vdu_preferred_name(), self.controller.vdu_stable_id
        title_txt = sid if id == name else f"{name}\n({sid})"
        writes_txt = tr("Set-VCP writes: {}").format(self.controller.get_write_count())
        if (disp_number := int(self.controller.vdu_number)) >= 0:
            disp_numumber_txt = tr("Monitor {}").format(disp_number)
        else:
            disp_numumber_txt = tr("Panel {}").format(-disp_number)
        click_txt = tr("(Click for Settings)")
        self.title_button.setToolTip(f"{title_txt}\n{writes_txt}\n{disp_numumber_txt}\n{click_txt}")


class VduControlBase(QWidget):
    """Base GUI control for a DDC attribute."""

    _refresh_ui_view_in_gui_thread_qtsignal = pyqtSignal()

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__()
        self.controller = controller
        self.vcp_capability = vcp_capability
        self.current_value: int | None = None
        # Using Qt signals to ensure GUI activity occurs in the GUI thread (this thread).
        self._refresh_ui_view_in_gui_thread_qtsignal.connect(self._refresh_ui_view_task)
        self.refresh_ui_only = False
        self.debug = False  # Local debug switch because this is very noisy and only needed rarely.

    def update_from_vdu(self, vcp_value: VcpValue):  # Used for updating from the results of get_attributes() -> List[VcpValue]
        if self.vcp_capability.vcp_type == SIMPLE_NON_CONTINUOUS_TYPE:  # Overrides metadata value-type, enforce simple
            self.current_value = 0x00ff & vcp_value.current  # Mask off high byte
        else:
            self.current_value = vcp_value.current
        self.refresh_ui_view()

    def set_value(self, new_value: int, origin: VcpOrigin = VcpOrigin.NORMAL) -> None:  # Used by controllers to alter physical VDU
        if self.controller.values_cache[self.vcp_capability.vcp_code] != new_value:
            self.controller.set_vcp_value(self.vcp_capability.vcp_code, new_value, origin)
            self.current_value = new_value
        self.refresh_ui_view()

    def ui_change_vdu_attribute(self, new_value: int) -> None:  # Used by UI controls to change values
        log_info("ui_change_vdu_attribute") if self.debug else None
        if self.refresh_ui_only:  # Called from a GUI control when it was already responding to a vdu attribute change.
            log_info(f"Skip change {self.refresh_ui_only=}") if self.debug else None
            return  # Avoid repeating a setvcp by skipping the physical change
        self.controller.set_vcp_value_asynchronously(self.vcp_capability.vcp_code, new_value, VcpOrigin.NORMAL)

    def get_current_text_value(self) -> str | None:  # Return text in correct base: continuous->base10 non-continuous->base16
        assert False, "subclass failed to implement get_current_text_value"

    def refresh_ui_view_implementation(self):  # Subclasses to implement
        assert False, "subclass failed to implement refresh_ui_view_implementation"

    def refresh_ui_view(self) -> None:
        if not gui_misc.is_running_in_gui_thread():
            self._refresh_ui_view_in_gui_thread_qtsignal.emit()
        else:
            self._refresh_ui_view_task()

    def _refresh_ui_view_task(self):
        try:
            self.refresh_ui_only = True  # Stop slider/widget changes from re-propagating changes to the VDU
            self.refresh_ui_view_implementation()
            QApplication.sendPostedEvents(self, 0)  # Flush any change events before resetting the flag
            QApplication.processEvents()  # Force the flushed events to be processed now
        finally:
            self.refresh_ui_only = False


class VduControlSlider(VduControlBase):
    """GUI control for a DDC continuously variable attribute. A compound widget with icon, slider, and text-field."""

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__(controller, vcp_capability)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.svg_icon: ThemedSvgWidget | None = None
        self.setToolTip(tr(vcp_capability.name))
        self.setToolTipDuration(TOOLTIP_DURATION_MSEC)
        if (vcp_capability.vcp_code in SUPPORTED_VCP_BY_CODE
                and SUPPORTED_VCP_BY_CODE[vcp_capability.vcp_code].icon_source is not None):
            svg_icon = ThemedSvgWidget(SUPPORTED_VCP_BY_CODE[vcp_capability.vcp_code].icon_source,
                                       native_font_height(scaled=1.8), native_font_height(scaled=1.8))
            self.svg_icon = svg_icon
            layout.addWidget(svg_icon)
        else:
            layout.addWidget(QLabel(tr(vcp_capability.name)))

        self.slider = slider = ClickableSlider()
        slider.setMinimumWidth(npx(200))
        self.range_restriction = vcp_capability.values
        if self.range_restriction and len(self.range_restriction) >= 2:  # Would > 2 be an error - don't worry about it
            slider.setRange(int(self.range_restriction[1]), int(self.range_restriction[2]))
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setOrientation(Qt.Orientation.Horizontal)  # type: ignore
        slider.setTracking(False)  # Don't rewrite the ddc value too often - not sure of the implications
        layout.addWidget(slider)

        self.spinbox = QSpinBox()
        self.spinbox.setLineEdit(LineEditAll())
        if self.range_restriction and len(self.range_restriction) >= 2:  # >2 would be an error, but not serious
            int_min, int_max = int(self.range_restriction[1]), int(self.range_restriction[2])
            self.spinbox.setRange(int_min, int_max)
            self.slider.setRange(int_min, int_max)

        self.slider.setTracking(True)
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)

        self.spinbox.setValue(slider.value())
        layout.addWidget(self.spinbox)

        def _slider_changed(value: int) -> None:
            self.current_value = value
            self.ui_change_vdu_attribute(value)

        slider.valueChanged.connect(_slider_changed)

    def update_from_vdu(self, vcp_value: VcpValue):
        if not self.range_restriction:
            int_max = int(vcp_value.max)
            self.spinbox.setRange(0, int_max)
            self.slider.setRange(0, int_max)
        super().update_from_vdu(vcp_value)

    def get_current_text_value(self) -> str | None:
        return str(self.current_value) if self.current_value is not None else None

    def refresh_ui_view_implementation(self) -> None:
        if self.current_value is not None:  # Copy the internally cached current value onto the GUI view.
            self.slider.setValue(clamp(int(self.current_value), self.slider.minimum(), self.slider.maximum()))


class VduControlComboBox(VduControlBase):
    """GUI control for a DDC non-continuously variable attribute, one that has a list of choices."""

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        super().__init__(controller, vcp_capability)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(self.translate_label(vcp_capability.name)))
        self.combo_box = combo_box = QComboBox()
        layout.addWidget(combo_box)
        self.setToolTip(tr(vcp_capability.name))
        self.setToolTipDuration(TOOLTIP_DURATION_MSEC)

        self.keys = []
        for value, desc in self.vcp_capability.values:
            self.keys.append(value)
            combo_box.addItem(self.translate_label(desc), value)

        def _index_changed(_: int) -> None:
            self.current_value = int(self.combo_box.currentData(), 16)
            if self.validate_value() >= 0:
                self.ui_change_vdu_attribute(self.current_value)

        combo_box.currentIndexChanged.connect(_index_changed)

    def translate_label(self, source: str) -> str:
        canonical = source.lower()
        maybe = tr(canonical)
        result = maybe if maybe != canonical else source
        return ' '.join(w[:1].upper() + w[1:] for w in result.split())  # Default to capitalized version of each word

    def get_current_text_value(self) -> str | None:
        return f"{self.current_value:02X}" if self.current_value is not None else None

    def refresh_ui_view_implementation(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        value_index = self.validate_value()
        if value_index >= 0:
            self.combo_box.setCurrentIndex(value_index)

    def validate_value(self) -> int:
        value = self.get_current_text_value()
        if value is None:
            return -1
        if value not in self.keys:
            self.keys.append(self.current_value)
            self.combo_box.addItem('UNKNOWN-' + value, self.current_value)
            self.combo_box.model().item(self.combo_box.count() - 1).setEnabled(False)
            MBox(MIcon.Critical,
                 msg=tr("Display {vnum} {vdesc} feature {code} '({cdesc})' has an undefined value '{value}'. "
                        "Valid values are {valid}.").format(
                     vdesc=self.controller.get_vdu_preferred_name(), vnum=self.controller.vdu_number,
                     code=self.vcp_capability.vcp_code, cdesc=self.vcp_capability.name,
                     value=value, valid=self.keys),
                 info=tr('If you want to extend the set of permitted values, you can edit the metadata '
                         'for {} in the settings panel.  For more details see the man page concerning '
                         'VDU/VDU-model config files.').format(self.controller.get_vdu_preferred_name())).exec()
            return -1
        return self.keys.index(value)
