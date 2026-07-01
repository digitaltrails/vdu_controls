# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
import os
import pathlib
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Dict, List, Tuple, TYPE_CHECKING, cast

import vdu_controls.logging as log
from vdu_controls.app_locale import tr, TitledStrEnum
from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import MsgDestination, DF_PLACES
from vdu_controls.ddcutil_abstract import BRIGHTNESS_VCP_CODE
from vdu_controls.ddcutil_aggregator import VduStableId
from vdu_controls.icon_utils import si, StdPixmap, create_icon_from_svg_bytes, create_image_from_svg_bytes
from vdu_controls.lux_config import LuxConfig, LuxPoint
from vdu_controls.lux_meters import LuxMeterSemiAutoDevice, LuxMeterDevice
from vdu_controls.misc import intV, zoned_now, clamp
from vdu_controls.qt_imports import QColor, QPixmap, QPainter, QPen, QFont, QResizeEvent, QPolygon, QMouseEvent, QFrame, QGroupBox
from vdu_controls.qt_imports import QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING
from vdu_controls.qt_imports import QT_TR_NOOP, Qt, QTimer, pyqtSignal, QPointF, QPoint
from vdu_controls.qt_imports import QVBoxLayout, QComboBox, QCheckBox, QLabel, QSpinBox, QListWidget, \
    QStatusBar, QHBoxLayout, QListWidgetItem, QApplication, QInputDialog
from vdu_controls.scaling import dpx, desktop_font_height
from vdu_controls.solar_calc import calc_solar_lux
from vdu_controls.svg import SWATCH_ICON_SVG, SUN_SVG, SVG_LIGHT_THEME_COLOR, SVG_SWATCH_ICON_BASE_COLOR, VDU_CONNECTED_ICON_SVG, \
    AMBIENT_PANEL_ICON_SVG
from vdu_controls.unicode import TIMER_RUNNING_SYMBOL
from vdu_controls.vdu_exceptions import VduException
from vdu_controls.widgets import SubWinDialog, DialogSingletonMixin, StdButton, FasterFileDialog, MBox, MIcon, MBtn, ChoiceBox, \
    TitleLabel, LocaleFormatterMixin

if TYPE_CHECKING:
    from vdu_controls.vdu_controls_application import VduAppController

@dataclass(frozen=True)
class LuxProfileTemplate:
    name: str
    interpolate: bool
    values: List[LuxPoint]


class LuxProfileTemplates:  # Context for QT_TR_NOOP translations
    LIST = [
        LuxProfileTemplate(name=QT_TR_NOOP("Older monitor, dimmer backlight, sunlit room."),
                           interpolate=True,
                           values=[LuxPoint(0, 90), LuxPoint(30, 90), LuxPoint(1016, 100), LuxPoint(100000, 100)]),
        LuxProfileTemplate(QT_TR_NOOP("Newer Monitor, brighter backlight, sunlit room"),
                           interpolate=True,
                           values=[LuxPoint(0, 13), LuxPoint(30, 13), LuxPoint(60, 13), LuxPoint(279, 70),
                                   LuxPoint(726, 90), LuxPoint(9690, 90), LuxPoint(98435, 100)]),
    ]


class LuxDeviceType(TitledStrEnum):
    SEMI_AUTO = ("calculator", QT_TR_NOOP("Semi-automatic geolocated"))
    ARDUINO = ("arduino", QT_TR_NOOP("Arduino tty device"))
    FIFO = ("fifo", QT_TR_NOOP("Linux FIFO"))
    EXECUTABLE = ("executable", QT_TR_NOOP("Script/program"))


class LuxDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def show_dialog(main_controller: VduAppController) -> None:
        LuxDialog.show_existing_dialog() if LuxDialog.exists() else LuxDialog(main_controller)

    @staticmethod
    def reconfigure_instance():
        if LuxDialog.exists():
            LuxDialog.get_instance().reconfigure()

    @staticmethod
    def lux_dialog_message(message: str, timeout: int, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        if LuxDialog.exists():
            LuxDialog.get_instance().status_message(message, timeout, destination)

    @staticmethod
    def lux_dialog_show_brightness(vdu_stable_id: VduStableId, brightness: int) -> None:
        if LuxDialog.exists():
            lux_dialog = LuxDialog.get_instance()
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
        self.setMinimumWidth(dpx(600))
        self.path = ConfIni.get_path('AutoLux')
        self.device_name = ''
        self.lux_config: LuxConfig = main_controller.get_lux_auto_controller().get_lux_config()

        main_layout = QVBoxLayout(self)

        existing_device = self.lux_config.get_device_name()
        existing_device_type = self.lux_config.get('lux-meter', 'lux-device-type', fallback='')
        self.meter_device_selector = QComboBox()
        self.meter_device_selector.setToolTip(tr("Select light-metering device."))
        for i, dev_type in enumerate(LuxDeviceType):
            if dev_type.value == existing_device_type:  # List existing device and device type, set it as selected.
                self.meter_device_selector.addItem(f"{tr(dev_type.localized_name)}: {existing_device}", dev_type)
                self.meter_device_selector.setCurrentIndex(i)
            else:
                self.meter_device_selector.addItem(tr(dev_type.localized_name), dev_type)  # List device type only.

        main_layout.addWidget(TitleLabel(icon_source=AMBIENT_PANEL_ICON_SVG, main_text=tr("Light Meter")))

        top_outer_layout = QHBoxLayout()
        main_layout.addLayout(top_outer_layout)

        top_left_layout = QVBoxLayout()
        top_right_layout = QVBoxLayout()
        top_right_layout.setContentsMargins(0, 0, 0, 0)
        top_outer_layout.addLayout(top_left_layout)
        top_outer_layout.addSpacing(dpx(10))
        top_outer_layout.addLayout(top_right_layout, stretch=1)
        top_right_layout.addSpacing(dpx(10))

        self.lux_gauge_widget = LuxGaugeWidget(self)

        top_left_layout.addWidget(self.lux_gauge_widget)

        meter_source_prompt = QLabel(tr("Meter"))
        meter_source_prompt.setToolTip(tr("Select light-metering device."))
        meter_source_layout = QHBoxLayout()
        meter_source_layout.addWidget(meter_source_prompt)
        meter_source_layout.addWidget(self.meter_device_selector)
        meter_source_layout.addStretch()
        top_right_layout.addLayout(meter_source_layout)

        self.enabled_checkbox = QCheckBox(tr("Enable automatic brightness adjustment"))
        self.enabled_checkbox.setToolTip(tr("Enable periodic automatic brightness adjustment based on metered light values."))
        top_right_layout.addWidget(self.enabled_checkbox)

        self.interpolate_checkbox = QCheckBox(tr("Interpolate brightness values"))
        self.interpolate_checkbox.setToolTip(tr("When selecting brightness, interpolate between the profile points."))
        top_right_layout.addWidget(self.interpolate_checkbox)

        interval_layout = QHBoxLayout()
        self.interval_label = QLabel(tr("Brightness adjustment interval (minutes)"))
        self.interval_label.setToolTip(tr("Brightness adjustment interval in minutes."))
        interval_layout.addWidget(self.interval_label)
        self.interval_selector = QSpinBox()
        self.interval_selector.setToolTip(tr("Brightness adjustment interval in minutes."))
        self.interval_selector.setMinimum(1)
        self.interval_selector.setMaximum(120)
        interval_layout.addWidget(self.interval_selector, alignment=Qt.AlignmentFlag.AlignLeft)
        interval_layout.addStretch(1)
        top_right_layout.addLayout(interval_layout)

        self.setMinimumSize(top_outer_layout.minimumSize())

        top_right_layout.addStretch(1)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        top_right_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignBottom)

        self.templates_button = StdButton(icon=si(self, StdPixmap.SP_DirOpenIcon), title=tr("Templates"),
                                          clicked=self.choose_template,
                                          tip=tr("Select from typical profile templates."))
        profiles_title = TitleLabel(icon_source=VDU_CONNECTED_ICON_SVG, main_text=tr("Profiles"), sub_text='',
                                    widgets=[self.templates_button])
        main_layout.addWidget(profiles_title)

        self.profile_selector_widget = QListWidget(parent=self)
        self.profile_selector_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.profile_selector_widget.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        self.profile_selector_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.profile_selector_widget.setSpacing(0)
        self.profile_selector_widget.setMinimumWidth(dpx(550))
        self.profile_selector_widget.setMinimumHeight(desktop_font_height(scaled=1.4))

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
            new_dev_path = ''  # No sure if this could escape the following if - so initialize just in case.
            if new_dev_type == LuxDeviceType.SEMI_AUTO:
                new_dev_path = LuxMeterSemiAutoDevice.device_name
            elif new_dev_type in (LuxDeviceType.ARDUINO, LuxDeviceType.FIFO, LuxDeviceType.EXECUTABLE):
                if current_dev_type == new_dev_type.name:
                    default_file = current_dev
                else:
                    default_file = "/dev/arduino" if new_dev_type == LuxDeviceType.ARDUINO else Path.home().as_posix()
                new_dev_path = FasterFileDialog.getOpenFileName(
                    self, tr("Select: {}").format(tr(new_dev_type.localized_name)), default_file)[0]
            if not self.validate_device(new_dev_path, required_type=new_dev_type):
                new_dev_path = ''
            if new_dev_path == '':  # Nothing selected, set back to what was in config
                config_device_type = self.lux_config.get('lux-meter', 'lux-device-type', fallback='')
                for dev_num in range(self.meter_device_selector.count()):
                    if self.meter_device_selector.itemData(dev_num).value == config_device_type:
                        self.meter_device_selector.setCurrentIndex(dev_num)
            else:
                if new_dev_path != current_dev:
                    self.meter_device_selector.setItemText(index, tr(new_dev_type.localized_name) + ': ' + new_dev_path)
                    self.lux_config.set('lux-meter', "lux-device", new_dev_path)
                    self.lux_config.set('lux-meter', "lux-device-type", new_dev_type.value)
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
            if not self.interpolate_checkbox.hasFocus():  # being set programmatically
                self.lux_config.set('lux-meter', 'interpolate-brightness',
                                    'yes' if checked == intV(Qt.CheckState.Checked) else 'no')
                return
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
            data = self.profile_selector_widget.item(index).data(Qt.ItemDataRole.UserRole)  # type: ignore
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
        log.debug("{self.lux_config.is_auto_enabled()=}") if log.debug_enabled else None
        self.enabled_checkbox.setChecked(self.lux_config.is_auto_enabled())
        self.interpolate_checkbox.setChecked(self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=False))
        self.has_profile_changes = False
        self.current_brightness_map.clear()
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)
        self.adjust_now_button.setText(f"{TIMER_RUNNING_SYMBOL} 00:00")
        self.adjust_now_button.setVisible(self.lux_config.is_auto_enabled())

        connected_id_list: List[VduStableId] = []  # List of all currently connected VDUs
        for index, vdu_sid in enumerate(self.main_controller.get_vdu_stable_id_list()):
            value_range = (0, 100)
            if self.main_controller.is_vcp_code_enabled(vdu_sid, BRIGHTNESS_VCP_CODE):
                value_range = self.main_controller.get_range(vdu_sid, BRIGHTNESS_VCP_CODE, fallback=value_range)
                self.range_restrictions_map[vdu_sid] = value_range   # type: ignore - will definitely have a value
                try:
                    self.current_brightness_map[vdu_sid] = self.main_controller.get_value(vdu_sid, BRIGHTNESS_VCP_CODE)
                except VduException as ve:
                    self.current_brightness_map[vdu_sid] = 0
                    log.warning("VDU may not be available:", str(ve), trace=True)
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
        candidate_id = cast(VduStableId, self.lux_config.get('lux-ui', 'selected-profile', fallback=None))
        if connected_id_list and (candidate_id is None or candidate_id not in connected_id_list):
            candidate_id = connected_id_list[0]
        if candidate_id is not None:
            try:
                self.profile_selector_widget.blockSignals(True)  # Stop initialization from causing signal until all data is aligned.
                if connected_id_list != existing_id_list:  # List of connected VDUs has changed
                    self.profile_selector_widget.clear()
                    random.seed(int(self.lux_config.get("lux-ui", "vdu_color_seed", fallback='0x543fff'), 16))
                    self.drawing_color_map.clear()
                    for index, vdu_sid in enumerate(connected_id_list):
                        color = QColor.fromHsl(int(index * 137.508) % 255, random.randint(64, 128), random.randint(192, 200))
                        self.drawing_color_map[vdu_sid] = color
                        color_icon = create_icon_from_svg_bytes(
                            SWATCH_ICON_SVG.replace(SVG_SWATCH_ICON_BASE_COLOR, bytes(color.name(), 'utf-8')))
                        key_item = QListWidgetItem(color_icon, self.main_controller.get_vdu_preferred_name(vdu_sid))
                        key_item.setData(Qt.ItemDataRole.UserRole, vdu_sid)
                        self.profile_selector_widget.addItem(key_item)
                        if vdu_sid == candidate_id:
                            self.profile_selector_widget.setCurrentRow(index)
                            self.profile_plot.current_vdu_sid = candidate_id
                    self.profile_selector_widget.setFixedHeight(
                        desktop_font_height(scaled=1.5) * (1 if len(connected_id_list) <= 3 else 5))
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
                 msg=tr("<h3>Semi-automatic adjustment: quick start instructions.</h3>"
                        "<hr/>"
                        "<p>Use the ambient-light-level slider to indicate your current lighting condition.</p>"
                        "<p>This establishes a baseline from which the application will periodically reestimate "
                        "your ambient-light-level as a proportion of the estimated sunlight for your location.</p>"
                        "<p>If conditions change, adjust the slider to alter the baseline proportion.</p>"
                        "<p>The projected trajectory is shown in the <i>Light Metering Dialog</i>, along with "
                        "the <i>Estimate of outdoor lux</i> (<b>Eo</b>) and the <i>Daylight Factor</i> (<b>DF</b>), "
                        "the baseline ratio of indoor to outdoor lux.</p>"),
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
                info = ''
                if path.is_char_device() and path.group() != "root":
                    info = tr("You might need to be a member of the {} group.").format(path.group())
                MBox(MIcon.Critical, msg=tr("No read access to {}").format(device), info=info).exec()
                return False
        else:
            if device == '':
                return False
            MBox(MIcon.Critical, msg=tr("Expecting {0}, but {1} was selected.").format(tr(required_type.localized_name), device)).exec()
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


    def choose_template(self) -> None:
        sid = self.profile_plot.current_vdu_sid
        if sid == '':
            MBox(MIcon.Critical, tr("No displays available.")).exec()
            return
        #icon = create_icon_from_svg_bytes(AMBIENT_PANEL_ICON_SOURCE)
        template_chooser = ChoiceBox(title=tr("Choose profile for {}").format(sid),
                                     choices=[tr(template.name) for template in LuxProfileTemplates.LIST])
        template_chooser.exec()
        if template_chooser.selected_item_number != -1:
            template = LuxProfileTemplates.LIST[template_chooser.selected_item_number]
            self.lux_profiles_map[sid] = template.values[:]
            self.interpolate_checkbox.setChecked(template.interpolate)
            self.profile_plot.show_changes(True)


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
            if answer == MBtn.Discard:
                self.reconfigure()
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


@dataclass
class LuxGaugeHistory:
    lux: int
    when: datetime


class LuxGaugeWidget(QGroupBox, LocaleFormatterMixin):
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
        widget_layout = QVBoxLayout(self)
        self.current_lux_display = QLabel()
        big_font = self.current_lux_display.font()
        big_font.setPointSize(big_font.pointSize() + 8)
        self.current_lux_display.setFont(big_font)
        widget_layout.addWidget(self.current_lux_display)
        self.plot_widget = QLabel()
        self.plot_widget.setFixedWidth(dpx(175))
        self.plot_widget.setFixedHeight(dpx(50))
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
            self.current_lux_display.setText(tr("Lux: {}".format(self.format_number(lux))))
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
        line_width = dpx(2)
        thin_line_width = dpx(1)

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
        eo_points: List[QPointF] = []
        ei_points: List[QPointF] = []
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
            painter.drawPolyline(eo_points)  # type: ignore
            painter.setPen(QPen(self.white_line_color, thin_line_width * 3))
            painter.drawPolyline(ei_points)  # type: ignore
        else:  # Give them a hint that they have not set location in settings.
            painter.setFont(QFont(QApplication.font().family(), 5, QFont.Weight.Bold))
            painter.setPen(QPen(self.white_line_color, thin_line_width))
            painter.drawText(QPointF(df_plot_left + df_plot_width/3, plot_height/4), tr('Location Unknown'))
        # Add text to the axis
        painter.setPen(QPen(self.white_line_color, thin_line_width))
        painter.setFont(QFont(QApplication.font().family(), 5, QFont.Weight.Normal))
        middle = df_plot_left - margin // 2
        for i in (10, 100, 1_000, 10_000, 100_000):
            painter.drawLine(middle - line_width, y := self._y_from_lux(i, plot_height), middle + line_width, y)
            painter.drawText(QPointF(middle + dpx(3), y + 4), str(i))
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
                    dpx(18), dpx(18))
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
            self.stats_label.setText(tr("Eo={0} lux    DF={1}").format(self.format_number(eo, 5), self.format_number(df, DF_PLACES)))
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
        self.setMinimumWidth(dpx(300))
        self.setMinimumHeight(dpx(275))

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        self.create_plot()

    def create_plot(self) -> None:
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(self.width() * dp_ratio), round(self.height() * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.plot_width, self.plot_height = self.width() - dpx(100), self.height() - dpx(85)
        self.x_origin, self.y_origin = dpx(60), self.plot_height + dpx(40)
        std_line_width = dpx(2)
        interpolating = self.lux_dialog.is_interpolating()
        painter.fillRect(0, 0, self.width(), self.height(), QColor(0x5b93c5))
        painter.setPen(QPen(Qt.GlobalColor.white, std_line_width))
        painter.drawText(self.width() // 3, dpx(15), tr("Lux Brightness Response Profiles"))

        tick_len = dpx(2)
        painter.drawLine(self.x_origin, self.y_origin, self.x_origin + self.plot_width + 25, self.y_origin)  # Draw x-axis
        for lux in [0, 10, 100, 1_000, 10_000, 100_000]:  # Draw x-axis ticks
            x = self.x_from_lux(lux)
            painter.drawLine(self.x_origin + x, self.y_origin + tick_len, self.x_origin + x, self.y_origin - tick_len)
            painter.drawText(self.x_origin + x - dpx(4) * len(str(lux)), self.y_origin + dpx(20), str(lux))
        painter.drawText(self.x_origin + self.plot_width // 2 - len(str("Lux")), self.y_origin + dpx(35), str("Lux"))

        painter.drawLine(self.x_origin, self.y_origin, self.x_origin, self.y_origin - self.plot_height)  # Draw y-axis
        for brightness in range(0, 101, 10):  # Draw y-axis ticks
            y = self.y_from_percent(brightness)
            painter.drawLine(self.x_origin - tick_len, self.y_origin - y, self.x_origin + tick_len, self.y_origin - y)
            painter.drawText(self.x_origin - dpx(25), self.y_origin - y + dpx(2), str(brightness))
        painter.save()
        painter.translate(self.x_origin - dpx(35), self.y_origin - self.plot_height // 2 + dpx(3) * len(tr("Brightness %")))
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
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + dpx(12), cutoff)
        if max_v < 100:
            painter.setPen(QPen(Qt.GlobalColor.red, std_line_width // 2, Qt.PenStyle.DashLine))
            cutoff = self.y_origin - self.y_from_percent(max_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + dpx(12), cutoff)

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

        pyramid_base = dpx(8)
        pyramid = [(-pyramid_base // 2, 0), (0, -pyramid_base), (pyramid_base // 2, 0)]
        for preset_point in self.preset_points:  # for each Preset: draw a vertical-line and white-triangle below axis
            painter.setPen(QPen(Qt.GlobalColor.white, std_line_width // 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.GlobalColor.white)
            x = self.x_origin + self.x_from_lux(preset_point.lux)
            painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + dpx(9) + ty) for tx, ty in pyramid]))

        lux_color = QColor(0xfeC053)  # 0xfec053)
        if self.current_lux is not None:  # Draw a vertical-line at current lux
            painter.setPen(QPen(lux_color, dpx(2)))  # fbc21b 0xffdd30 #fec053
            x_current_lux = self.x_origin + self.x_from_lux(self.current_lux)
            painter.drawLine(x_current_lux, self.y_origin + dpx(5), x_current_lux, self.y_origin - self.plot_height - dpx(5))
            for brightness in range(10, 101, 10):  # Draw y-axis ticks on lux current lux
                y = self.y_from_percent(brightness)
                painter.drawLine(x_current_lux - 2, self.y_origin - y, x_current_lux + 2, self.y_origin - y)
            trangle_h = dpx(16)
            current_brightness_pointer = [(0, 0), (-trangle_h, trangle_h // 2), (-trangle_h, -trangle_h // 2)]
            # Indicate current brightness at current lux
            for vdu_sid, brightness in self.lux_dialog.current_brightness_map.items():
                if vdu_sid not in self.vdu_chart_colors:
                    continue  # must have been turned off
                vdu_color_num = self.vdu_chart_colors[vdu_sid]
                vdu_line_color = QColor(vdu_color_num)
                y = self.y_origin - self.y_from_percent(brightness)
                painter.setPen(QPen(Qt.GlobalColor.black, dpx(1)))
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
                    painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + dpx(2), y)
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - dpx(2))
                else:  # Existing Preset point: vertical line; plus removal hint, a red triangle below axis
                    painter.setPen(QPen(Qt.GlobalColor.red if mouse_y > self.y_origin else Qt.GlobalColor.white, 2))
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - dpx(2))
                    painter.setPen(QPen(Qt.GlobalColor.red, dpx(2)))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + dpx(9) + ty) for tx, ty in pyramid]))
                    if mouse_y > self.y_origin:  # Remove-Preset hint
                        painter.setPen(QPen(Qt.GlobalColor.black, dpx(1)))
                        painter.drawText(x + dpx(5), self.y_origin - dpx(17), tr("Click remove preset at {} lux").format(lux))
            else:  # Potential new Point - show precise position for adding a new point
                lux, brightness = self.lux_from_x(x - self.x_origin), self.percent_from_y(y - self.y_origin)
                point_preset_name = ''
                painter.setPen(QPen(Qt.GlobalColor.white, dpx(1)))
                painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + dpx(2), y)
                painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - dpx(2))
                if mouse_y > self.y_origin:  # Below axis, show a hint for adding a Preset point: draw a red triangle below axis
                    painter.setPen(QPen(Qt.GlobalColor.red, dpx(2)))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + dpx(9) + ty) for tx, ty in pyramid]))
                    painter.setPen(QPen(Qt.GlobalColor.black, dpx(1)))
                    painter.drawText(x + 10, self.y_origin - dpx(17), tr("Click to add preset at {} lux").format(lux))
            painter.setPen(QPen(Qt.GlobalColor.black, dpx(1)))
            painter.drawText(x + 10, y - 10, f"{lux} lux, {brightness}% {point_preset_name}")  # Tooltip lux and percent

        painter.end()
        self.setPixmap(pixmap)

    def set_current_profile(self, name: VduStableId) -> None:
        self.current_vdu_sid = name
        self.create_plot()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is not None:
            changed = False
            x = event.pos().x() - self.x_origin
            y = self.y_origin - event.pos().y()
            if event.button() == Qt.MouseButton.LeftButton:  # click along bottom (y=0) to attach presets
                changed = self.lux_point_edit(x, y) if y >= 0 else self.lux_preset_edit(x)
            if changed:
                self.show_changes()
            event.accept()

    def lux_point_edit(self, x, y) -> bool:
        if self.current_vdu_sid == '':
            MBox(MIcon.Critical, tr("No displays available.")).exec()
            return False
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
        if self.current_vdu_sid == '':
            MBox(MIcon.Critical, tr("No displays available.")).exec()
            return False
        if point := self.find_preset_point_close_to(x):  # Delete
            self.preset_points.remove(point)
            for vdu_sid, profile in self.profiles_map.items():
                for profile_point in profile[:]:   # Copy to prevent any issues due to deleting elements
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
            ask_preset.setLabelText(tr("Select a Preset to attach at {} lux").format(self.lux_from_x(x)))
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
