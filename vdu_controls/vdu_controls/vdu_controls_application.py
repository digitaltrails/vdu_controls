#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import glob
import locale
import math
import pathlib
import queue
import random
import select
import signal
import socket
import subprocess
import termios
import threading
import time
from ast import literal_eval
from collections import namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from importlib import import_module
from typing import List, Tuple, Dict, Callable, Any, cast

from vdu_controls.config_ini import ConfIni, ConfOpt, VduControlsConfig, SUPPORTED_VCP_BY_CODE, VcpCapability, GeoLocation
from vdu_controls.constants import *
from vdu_controls.ddcutil_aggregator import DdcutilAggregator, VduStableId
from vdu_controls.ddcutil_abstract import VcpOrigin, VcpValue, DdcutilDisplayNotFound, CONTINUOUS_TYPE, \
    COMPLEX_NON_CONTINUOUS_TYPE, BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE, SIMPLE_NON_CONTINUOUS_TYPE, DdcEventType, \
    DdcutilServiceNotFound
from vdu_controls.ddcutil_emulator import DdcutilEmulatorImpl
from vdu_controls.ddcutil_laptop_panel import DdcutilPanelImpl
from vdu_controls.greyscale import GreyScaleDialog
from vdu_controls.help import HelpDialog
from vdu_controls.icon_utils import ThemeType, polychrome_light_or_dark, SVG_LIGHT_THEME_COLOR, get_splash_image
from vdu_controls.icon_utils import create_image_from_svg_bytes, \
    create_icon_from_svg_bytes, create_icon_from_path, create_decorated_app_icon, StdPixmap, \
    is_dark_theme, si
from vdu_controls.installer import install_as_desktop_application
from vdu_controls.internationalization import tr, initialise_locale_translations, find_locale_specific_file, translate_option
from vdu_controls.logging import *
from vdu_controls.misc import intV, zoned_now, proper_name, clamp
from vdu_controls.preset import Preset, PresetScheduleStatus, PresetTransitionFlag
from vdu_controls.qt_imports import *
from vdu_controls.release import release_notes
from vdu_controls.scaling import native_font_height, npx
from vdu_controls.settings_editor import SettingsDialog
from vdu_controls.solar_calc import calc_solar_lux, create_elevation_map, SolarElevationKey, \
    SolarElevationData, format_solar_elevation_abbreviation, parse_solar_elevation_ini_text, format_solar_elevation_ini_text
from vdu_controls.svg import *
from vdu_controls.unicode import *
from vdu_controls.weather import WeatherQuery
from vdu_controls.widgets import StdButton, SubWinDialog, ThemedSvgWidget, TitleButton, ThemedSvgButton, MIcon, MBox, MBtn, \
    FasterFileDialog, PushButtonLeftJustified, ClickableSlider, LineEditAll, alter_margins, DialogSingletonMixin, ToolButton
from vdu_controls.work_scheduler import WorkerThread, ScheduleWorker, thread_pid, SchedulerJob, SchedulerJobType, WorkException

Shortcut = namedtuple('Shortcut', ['letter', 'annotated_word'])

gui_thread: QThread | None = None




def is_running_in_gui_thread() -> bool:
    return QThread.currentThread() == gui_thread


# Use Linux/UNIX signals to trigger preset changes - 16 presets should be enough for anyone.

unix_signal_handler: SignalWakeupHandler | None = None




original_qt_qpa_platform: str | None = None


def force_xwayland():  # Force Qt to use XWayland, or reverse the previous force
    global original_qt_qpa_platform
    original_qt_qpa_platform = os.environ.get('QT_QPA_PLATFORM', '')  # save original value
    log_info("Forcing Xwayland, setting environment variable QT_QPA_PLATFORM=xcb")
    os.environ['QT_QPA_PLATFORM'] = 'xcb'


def reverse_force_xwayland():
    if original_qt_qpa_platform:
        log_info(f"Restoring environment variable QT_QPA_PLATFORM={original_qt_qpa_platform}")
        os.environ['QT_QPA_PLATFORM'] = original_qt_qpa_platform  # restore original value
    elif original_qt_qpa_platform == '':  # Will be '' if force_xwayland() has been called, otherwise it will be None
        log_info(f"Removing environment variable QT_QPA_PLATFORM")
        os.environ.pop('QT_QPA_PLATFORM')  # before the call to force_xwayland() it did not previously exist, remove it.


class VduControllerAsyncSetter(WorkerThread):  # Used to decouple the set-vcp from the GUI

    def __init__(self):
        super().__init__(task_body=self._async_setvcp_task_body, task_finished=None, loop=True)
        self._async_setvcp_queue: queue.Queue = queue.Queue()
        # limit set_vcp to a sustainable interval - KDE powerdevil recommendation - 0.5s, ddcui 1.0 seconds
        self._idle_seconds = float(os.getenv("VDU_CONTROLS_UI_IDLE_SECS", '0.5'))
        log_info(f"env VDU_CONTROLS_UI_IDLE_SECS={self._idle_seconds}")

    def _async_setvcp_task_body(self, _: WorkerThread):
        latest_pending = {}  # Handle bursts of UI setvcp requests, filtering out repeats for the same feature.
        while not self._async_setvcp_queue.empty():  # Keep going while there is something in the queue
            try:
                # print(f"{self._async_setvcp_queue.qsize()=}")
                controller, vcp_code, value, origin = self._async_setvcp_queue.get_nowait()
                key = (controller, vcp_code)
                if log_debug_enabled:
                    log_debug(f"UI discard earlier op on {controller.vdu_number=} {vcp_code=}") if key in latest_pending else None
                latest_pending[key] = (value, origin)  # keep the latest for each controller+vcp_code.
                self._async_setvcp_queue.task_done()
            except queue.Empty:
                pass
            if latest_pending and self._async_setvcp_queue.empty():  # some setvcp requests are pending,
                self.doze(self._idle_seconds)  # wait a bit in case more arrive - might be dragging a slider or spinning a spinner
        if latest_pending:  # nothing more has arrived, if any setvcp requests are pending, set for real now
            for (controller, vcp_code), (value, origin) in latest_pending.items():
                if controller.values_cache.get(vcp_code, None) != value:
                    log_debug(f"UI set {controller.vdu_number=} {vcp_code=} {value=} {origin}") if log_debug_enabled else None
                    controller.set_vcp_value(vcp_code, value, origin, asynchronous_caller=True)
                else:
                    log_debug(f"UI nochange {controller.vdu_number=} {vcp_code=} {value=} {origin}") if log_debug_enabled else None
        else:
            self.doze(self._idle_seconds)

    def queue_setvcp(self, controller: VduController, vcp_code: str, value: int, origin: VcpOrigin):
        self._async_setvcp_queue.put((controller, vcp_code, value, origin))


class VduController(QObject):
    """
    Holds model+controller specific to an individual VDU including a map of its capabilities. A model object in
    MVC speak.

    The model configuration can optionally be read from an INI-format config file held in $HOME/.config/vdu-control/

    Capabilities are either extracted from ddcutil output or read from the INI-format files.  File read
    capabilities are provided so that the output from "ddcutil --display N capabilities" can be corrected (because
    it is sometimes incorrect due to sloppy implementation by manufacturers). For example, my LG monitor reports
    two Display-Port inputs, and it only has one.
    """

    NORMAL_VDU = 0
    IGNORE_VDU = 1
    ASSUME_STANDARD_CONTROLS = 2
    DISCARD_VDU = 3
    _RANGE_PATTERN = re.compile(r'Values:\s+([0-9]+)..([0-9]+)')
    _FEATURE_PATTERN = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\s(.*)', re.DOTALL | re.MULTILINE)
    _LIMITED_RANGE_KEY = "%%RANGE%%"  # A key internal to vdu_controls for storing Range n..m values.
    _FORCE_REFRESH_NAME_SUFFIX = "*refresh*"

    vcp_value_changed_qtsignal = pyqtSignal(str, str, int, VcpOrigin, bool)
    _async_setvcp_exception_qtsignal = pyqtSignal(str, int, VcpOrigin, Exception)

    _async_setvcp_task: VduControllerAsyncSetter | None = None

    def __init__(self, vdu_number: str, vdu_model_name: str, serial_number: str, manufacturer: str,
                 default_config: VduControlsConfig, ddcutil: DdcutilAggregator, edit_config: Callable,
                 vdu_exception_handler: Callable, remedy: int = 0) -> None:
        super().__init__()
        self.no_longer_in_use = False
        if vdu_model_name.strip() == '':  # laptop monitors can sneak through with no model_name
            vdu_model_name = "Unknown"
        self.vdu_stable_id = VduStableId(proper_name(vdu_model_name, serial_number))
        log_info(f"Initializing controls for {vdu_number=} {vdu_model_name=} {self.vdu_stable_id=}")
        self.vdu_number = vdu_number
        self.model_name = vdu_model_name
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.edit_config_callable = edit_config
        self.vdu_exception_handler = vdu_exception_handler

        def _handle_async_setvcp_exception(vcp_code: str, value: int, origin: VcpOrigin, e: VduException):
            if self.vdu_exception_handler(e, True):
                self.set_vcp_value_asynchronously(vcp_code, value, origin)

        self._async_setvcp_exception_qtsignal.connect(_handle_async_setvcp_exception)
        if VduController._async_setvcp_task is None or VduController._async_setvcp_task.isFinished():
            VduController._async_setvcp_task = VduControllerAsyncSetter()
            VduController._async_setvcp_task.start()

        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text: str | None = None
        self.config = None
        self.values_cache: Dict[str, int] = {}
        self.ignore_vdu = remedy == VduController.IGNORE_VDU
        default_sleep_multiplier: float | None = default_config.get_sleep_multiplier(fallback=None)
        enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        for config_name in (self.vdu_stable_id, self.vdu_model_id):  # Allow for shared single model file (not encouraged).
            config_path = ConfIni.get_path(config_name)
            log_debug("checking for config file '" + config_path.as_posix() + "'") if log_debug_enabled else None
            if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
                self.config = VduControlsConfig(config_name)
                self.config.parse_file(config_path)
                if default_config.is_set(ConfOpt.DEBUG_ENABLED):
                    self.config.debug_dump()
                enabled_vcp_codes = self.config.get_all_enabled_vcp_codes()
                self.capabilities_text = self.config.get_capabilities_alt_text()  # cached, possibly edited, ddc capabilities
                self.ignore_vdu = self.ignore_vdu or self.capabilities_text == '' or self.capabilities_text == IGNORE_VDU_MARKER_STR
                if not self.ignore_vdu:
                    if multiplier := self.config.get_sleep_multiplier(fallback=default_sleep_multiplier):
                        self.ddcutil.set_sleep_multiplier(vdu_number, multiplier)
                    self.ddcutil.set_vdu_specific_args(vdu_number, self.config.get_ddcutil_extra_args(fallback=None))
                break
        if not self.capabilities_text:
            if remedy == VduController.DISCARD_VDU:
                self.capabilities_text = IGNORE_VDU_MARKER_STR
                log_info(f"Capabilities override set to ignore VDU {vdu_number=} {vdu_model_name=} {self.vdu_stable_id=}")
            elif remedy == VduController.IGNORE_VDU:
                self.capabilities_text = ''
            elif remedy == VduController.ASSUME_STANDARD_CONTROLS:
                enabled_vcp_codes = ASSUMED_CONTROLS_CONFIG_VCP_CODES
                self.capabilities_text = ASSUMED_CONTROLS_CONFIG_TEXT
            else:
                self.capabilities_text = ddcutil.query_capabilities(vdu_number)
            self.ignore_vdu = self.capabilities_text == '' or self.capabilities_text == IGNORE_VDU_MARKER_STR
        # print(f"{self.capabilities_text}")
        self.capabilities_supported_by_this_vdu = self._parse_capabilities(self.capabilities_text)
        # Find those capabilities supported by this VDU AND enabled in the GUI:
        self.enabled_capabilities = [c for c in self.capabilities_supported_by_this_vdu.values() if c.vcp_code in enabled_vcp_codes]
        if self.config is None:  # In memory only config - in case it's needed by a future config editor
            self.config = VduControlsConfig(self.vdu_stable_id,
                                            default_enabled_vcp_codes=[c.vcp_code for c in self.enabled_capabilities])
            self.config.set_capabilities_alt_text(self.capabilities_text)
        self.config.restrict_to_actual_capabilities(self.capabilities_supported_by_this_vdu)
        if remedy == VduController.DISCARD_VDU:
            self.write_template_config_files()  # Persist the discard

    def edit_config(self):
        self.edit_config_callable(self.config.config_name)

    def write_template_config_files(self) -> None:
        """Write template config files to $HOME/.config/vdu_controls/"""
        config_name = self.vdu_stable_id
        save_config_path = ConfIni.get_path(config_name)
        config = VduControlsConfig(config_name, default_enabled_vcp_codes=[c.vcp_code for c in self.enabled_capabilities])
        config.set_capabilities_alt_text(self.capabilities_text if self.capabilities_text is not None else '')
        config.write_file(save_config_path)
        self.config = config

    def get_vdu_preferred_name(self, upper: bool = False) -> str:
        return self.config.get_vdu_preferred_name().upper() if upper else self.config.get_vdu_preferred_name()

    def get_full_id(self) -> Tuple[str, str, str, str]:
        """Return a tuple that defines this VDU: (vdu_number, manufacturer, model, serial-number)."""
        return self.vdu_number, self.manufacturer, self.model_name, self.serial_number

    def get_vcp_values(self, vcp_codes: List[str]) -> List[VcpValue]:
        try:
            if len(vcp_codes) == 0:
                return []
            # raise subprocess.SubprocessError("get_attributes")  # for testing
            values = self.ddcutil.get_vcp_values(self.vdu_number, vcp_codes)
            for vcp_code, vcp_value in zip(vcp_codes, values):
                value = vcp_value.current
                cached_value = self.values_cache.get(vcp_code, None)
                if value != cached_value:
                    self.values_cache[vcp_code] = value
                    if cached_value is not None:  # Not just initialization, but an actual change...
                        if log_debug_enabled:
                            log_debug(
                                f"get_vcp signals vcp_value_changed: {self.vdu_stable_id} {vcp_code=} {value} {VcpOrigin.EXTERNAL}")
                        self.vcp_value_changed_qtsignal.emit(self.vdu_stable_id, vcp_code, value, VcpOrigin.EXTERNAL,
                                                             self.capabilities_supported_by_this_vdu[vcp_code].causes_config_change)
            return values
        except (subprocess.SubprocessError, ValueError, TimeoutError, DdcutilDisplayNotFound) as e:
            raise VduException(vdu_description=self.get_vdu_preferred_name(), vcp_code=",".join(vcp_codes), exception=e,
                               operation="get_vcp_values") from e

    def set_vcp_value(self, vcp_code: str, value: int, origin: VcpOrigin = VcpOrigin.NORMAL,
                      asynchronous_caller: bool = False) -> None:
        if self.no_longer_in_use:
            log_info(f"Expired controller discards set_vcp_value({vcp_code=}, {value=}, {origin=}) {asynchronous_caller=}")
            return
        try:
            # raise subprocess.SubprocessError("set_attribute")  # for testing
            retry_on_error = vcp_code in SUPPORTED_VCP_BY_CODE and SUPPORTED_VCP_BY_CODE[vcp_code].retry_setvcp
            self.ddcutil.set_vcp(self.vdu_number, vcp_code, value, retry_on_error=retry_on_error)
            self.values_cache[vcp_code] = value
            if log_debug_enabled:
                log_debug(f"set_vcp signals vcp_value_changed: {self.vdu_stable_id} {vcp_code=} {value} {origin}")
            self.vcp_value_changed_qtsignal.emit(self.vdu_stable_id, vcp_code, value, origin,
                                                 self.capabilities_supported_by_this_vdu[vcp_code].causes_config_change)
        except (subprocess.SubprocessError, ValueError, TimeoutError, DdcutilDisplayNotFound) as e:
            vdu_exception = VduException(vdu_description=self.get_vdu_preferred_name(), vcp_code=vcp_code, exception=e,
                                         operation="set_vcp_value")
            if not asynchronous_caller:
                raise vdu_exception from e
            self._async_setvcp_exception_qtsignal.emit(vcp_code, value, origin, vdu_exception)

    def set_vcp_value_asynchronously(self, vcp_code: str, value: int, origin: VcpOrigin = VcpOrigin.NORMAL) -> None:
        # Queue the change for the queue processing thread - avoids blocking the GUI.
        VduController._async_setvcp_task.queue_setvcp(self, vcp_code, value, origin)

    def get_range_restrictions(self, vcp_code, fallback: Tuple[int, int] | None = None) -> Tuple[int, int] | None:
        if vcp_code in self.capabilities_supported_by_this_vdu:
            range_restriction = self.capabilities_supported_by_this_vdu[vcp_code].values  # will always be a list
            if len(range_restriction) != 0:
                return int(range_restriction[1]), int(range_restriction[2])
        return fallback

    def get_write_count(self):
        return self.ddcutil.get_write_count(self.vdu_number) if self.ddcutil else 0

    def _parse_capabilities(self, capabilities_text=None) -> Dict[str, VcpCapability]:
        """Return a map of vpc capabilities keyed by vcp code."""

        if capabilities_text == "Ignore VDU":
            return {}

        def _parse_values(values_str: str) -> List[str]:
            values_list = []
            if stripped := values_str.strip():
                lines_list = stripped.split('\n')
                if len(lines_list) == 1:
                    if range_match := VduController._RANGE_PATTERN.match(lines_list[0]):
                        values_list = [VduController._LIMITED_RANGE_KEY, range_match.group(1), range_match.group(2)]
                    else:
                        space_separated = lines_list[0].replace('(interpretation unavailable)', '').strip().split(' ')
                        values_list = [(v.upper(), 'unknown ' + v) for v in space_separated[1:]]
                else:
                    values_list = [(key.upper(), desc.strip()) for key, desc in (v.strip().split(":", 1) for v in lines_list[1:])]
            return values_list

        feature_map = {}
        for feature_text in capabilities_text.split(' Feature: '):
            if feature_match := VduController._FEATURE_PATTERN.match(feature_text):
                vcp_code = feature_match.group(1)
                vcp_name = feature_match.group(2)
                if requires_refresh := vcp_name.lower().endswith(VduController._FORCE_REFRESH_NAME_SUFFIX):
                    vcp_name = vcp_name.replace(VduController._FORCE_REFRESH_NAME_SUFFIX, "")
                values = _parse_values(feature_match.group(3))
                # Guess type from existence or not of value list
                if len(values) == 0:
                    vcp_type = CONTINUOUS_TYPE
                    if vcp_code in SUPPORTED_VCP_BY_CODE:  # Override if we know better
                        vcp_type = SUPPORTED_VCP_BY_CODE[vcp_code].vcp_type
                elif values[0] == VduController._LIMITED_RANGE_KEY:  # Special internal hacked config spec to specify range
                    vcp_type = CONTINUOUS_TYPE
                else:  # two-byte or one-byte continuous type - cannot always trust the VDU metadata on this.
                    try:  # See whether the max is really contained within one byte:
                        max_value = max([int(v, 16) for v, _ in values])
                        vcp_type = COMPLEX_NON_CONTINUOUS_TYPE if max_value > 0xff else SIMPLE_NON_CONTINUOUS_TYPE
                    except ValueError:
                        vcp_type = COMPLEX_NON_CONTINUOUS_TYPE  # Assume two byte

                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None,
                                           can_transition=vcp_type == CONTINUOUS_TYPE, causes_config_change=requires_refresh)
                feature_map[vcp_code] = capability
        return {**{k: feature_map[k] for k in (BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE) if k in feature_map},  # Put B&C first
                **{k: v for k, v in feature_map.items() if k not in (BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE)}}


class VduException(WorkException):

    def __init__(self, vdu_description=None, vcp_code=None, exception=None, operation=None) -> None:
        super().__init__()
        self.vdu_description = vdu_description
        self.attr_id = vcp_code
        self.cause = exception
        self.operation = operation

    def is_display_not_found_error(self) -> bool:
        return self.cause is not None and isinstance(self.cause, DdcutilDisplayNotFound)

    def __str__(self) -> str:
        return f"VduException: {self.vdu_description} op={self.operation} attr={self.attr_id} {self.cause}"


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
        if not is_running_in_gui_thread():
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


class ContextMenu(QMenu):
    PRESET_NAME_PROP = 'preset_name'
    PRESET_SHORTCUT_PROP = 'preset_shortcut'
    BUSY_DISABLE_PROP = 'busy_disable'
    ALT = 'Alt+{}'

    def __init__(self, app_controller: VduAppController, main_window_action, about_action, help_action, gray_scale_action,
                 lux_auto_action, lux_check_action, lux_meter_action, settings_action, presets_dialog_action, refresh_action,
                 quit_action, hide_shortcuts: bool, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.app_controller = app_controller
        self.reserved_shortcuts: List[str] = []
        self.hide_shortcuts = hide_shortcuts
        if main_window_action is not None:
            self._add_action(StdPixmap.SP_ComputerIcon, tr('&Control Panel'), main_window_action)
            self.addSeparator()
        self._add_action(StdPixmap.SP_ComputerIcon, tr('&Presets'), presets_dialog_action)
        self.presets_separator = self.addSeparator()  # Important for finding where to add a preset
        self._add_action(StdPixmap.SP_ComputerIcon, tr('&Grey Scale'), gray_scale_action)
        if lux_meter_action is not None:
            self.lux_auto_action = self._add_action(StdPixmap.SP_ComputerIcon, tr('&Auto/Manual'), lux_auto_action)
            self.lux_check_action = self._add_action(StdPixmap.SP_MediaSeekForward, tr('Lighting &Check'), lux_check_action)
            self._add_action(StdPixmap.SP_ComputerIcon, tr('&Light-Metering'), lux_meter_action)
        self._add_action(StdPixmap.SP_ComputerIcon, tr('&Settings'), settings_action, 'Ctrl+Shift+,')
        self._add_action(StdPixmap.SP_BrowserReload, tr('&Refresh'), refresh_action, QKeySequence.StandardKey.Refresh).setProperty(
            ContextMenu.BUSY_DISABLE_PROP, QVariant(True))
        self._add_action(StdPixmap.SP_MessageBoxInformation, tr('Abou&t'), about_action)
        self._add_action(StdPixmap.SP_DialogHelpButton, tr('&Help'), help_action, QKeySequence.StandardKey.HelpContents)
        self._add_action(StdPixmap.SP_DialogCloseButton, tr('&Quit'), quit_action, QKeySequence.StandardKey.Quit)
        self.reserved_shortcuts_basic = self.reserved_shortcuts.copy()
        self.auto_lux_icon: QIcon | None = None

    def _add_action(self, qt_icon_number: int, text: str, func: Callable, extra_shortcut: str | None = None) -> QAction:
        action = self.addAction(si(self, qt_icon_number), text, func)
        assert action is not None
        amp_pos = text.find('&')
        shortcut_letter = text[amp_pos + 1].upper() if (0 <= amp_pos < len(text) - 1) else None
        if shortcut_letter is not None:
            log_debug(f"Reserve shortcut '{shortcut_letter}'") if log_debug_enabled else None
            if shortcut_letter in self.reserved_shortcuts:
                log_error(f"{shortcut_letter=} already in in {self.reserved_shortcuts=}")
            else:
                self.reserved_shortcuts.append(shortcut_letter)
                action.setShortcuts(self.shortcut_list(ContextMenu.ALT.format(shortcut_letter.upper()), extra_shortcut))
                action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        return action

    def get_preset_menu_action(self, name: str) -> QAction | None:
        for action in self.actions():
            if action.property(ContextMenu.PRESET_NAME_PROP) == name:
                return action
        return None

    def insert_preset_menu_action(self, preset: Preset, issue_update: bool = True) -> None:

        def _menu_restore_preset() -> None:
            self.app_controller.restore_named_preset(self.sender().property(ContextMenu.PRESET_NAME_PROP))

        assert preset.name
        shortcut = self.allocate_preset_shortcut(preset.name)
        action_name = shortcut.annotated_word if shortcut else preset.name
        action = self.addAction(preset.create_icon(), action_name, _menu_restore_preset)  # Have to add it, then move/insert it.
        assert action
        self.insertAction(self.presets_separator, action)  # Insert before the presets_separator
        action.setProperty(ContextMenu.BUSY_DISABLE_PROP, QVariant(True))
        action.setProperty(ContextMenu.PRESET_NAME_PROP, preset.name)
        if shortcut:
            action.setProperty(ContextMenu.PRESET_SHORTCUT_PROP, shortcut)
            action.setShortcuts(self.shortcut_list(ContextMenu.ALT.format(shortcut.letter.upper())))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        else:
            log_warning(f"Failed to allocate shortcut for {preset.name} reserved shortcuts={self.reserved_shortcuts}")
        self.update() if issue_update else None

    def remove_preset_menu_action(self, name: str) -> None:
        if menu_action := self.get_preset_menu_action(name):
            shortcut = menu_action.property(ContextMenu.PRESET_SHORTCUT_PROP)
            if shortcut and shortcut in self.reserved_shortcuts:
                self.reserved_shortcuts.remove(shortcut.letter)
            self.removeAction(menu_action)
            self.update()

    def refresh_preset_menu(self, palette_change: bool = False, reorder: bool = False) -> None:
        changed = 0
        if reorder:  # Remove them all to get them reinserted, icons updated, names updated, etc.
            self.reserved_shortcuts = self.reserved_shortcuts_basic.copy()  # Reset shortcuts
            for action in self.actions():
                self.removeAction(action) if action.property(ContextMenu.PRESET_NAME_PROP) is not None else None
        for name, preset in self.app_controller.preset_controller.find_presets_map().items():
            menu_action = self.get_preset_menu_action(name)
            if menu_action is None or not menu_action.property(ContextMenu.PRESET_NAME_PROP):
                self.insert_preset_menu_action(preset, False)
                changed += 1
            elif palette_change:  # Must redraw icons in case desktop theme changed between light/dark.
                menu_action.setIcon(preset.create_icon())
                changed += 1
        self.update() if changed else None

    def indicate_preset_active(self, preset: Preset | None) -> None:
        changed = 0
        for action in self.actions():
            if action_preset_name := action.property(ContextMenu.PRESET_NAME_PROP):  # Mark active preset or un-mark previous active
                shortcut = action.property(ContextMenu.PRESET_SHORTCUT_PROP)
                suffix = (' ' + MENU_ACTIVE_PRESET_SYMBOL) if preset is not None and preset.name == action_preset_name else ''
                new_text = (shortcut.annotated_word if shortcut else action_preset_name) + suffix
                if new_text != action.text():
                    action.setText(new_text)
                    changed += 1
        self.update() if changed else None

    def indicate_busy(self, is_busy: bool = True) -> None:
        changed = 0
        for action in self.actions():
            if action.property(ContextMenu.BUSY_DISABLE_PROP):
                if (is_busy and action.isEnabled()) or (not is_busy and not action.isEnabled()):
                    action.setDisabled(is_busy)
                    changed += 1
        self.update() if changed else None

    def update_lux_auto_icon(self, icon: QIcon) -> None:
        if self.auto_lux_icon != icon:
            self.auto_lux_icon = icon
            self.lux_auto_action.setIcon(icon)
            self.update()

    def allocate_preset_shortcut(self, word: str) -> Shortcut | None:
        for letter in list(word):
            upper_letter = letter.upper()
            if upper_letter not in self.reserved_shortcuts:
                self.reserved_shortcuts.append(upper_letter)
                return Shortcut(letter=upper_letter, annotated_word=word[:word.index(letter)] + '&' + word[word.index(letter):])
        return None

    def shortcut_list(self, primary: str | QKeySequence, extra: str | QKeySequence | None = None) -> List[str | QKeySequence]:
        shortcuts = [primary] + ([extra] if extra else [])
        return ([''] + shortcuts) if self.hide_shortcuts else shortcuts  # Empty string causes shortcuts to be hidden.


class VduMainToolBar(QToolBar):

    def __init__(self, tool_buttons: List[ToolButton], app_context_menu: ContextMenu, parent: VduControlsMainPanel) -> None:
        super().__init__(parent=parent)
        self.setObjectName('VduPanelToolBar')  # Internal name for persistence - do not change or persistence will be lost.
        self.preset_edit_target: Preset | None = None
        self.setMovable(False)
        self.tool_buttons = tool_buttons
        for button in self.tool_buttons:
            self.addWidget(button)
        self.setIconSize(QSize(native_font_height(), native_font_height()))
        self.status_area = QStatusBar()
        self.addWidget(self.status_area)
        self.menu_button = ToolButton(MENU_ICON_SOURCE, tr("Context and Preset Menu"), self)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.preset_action = self.addAction(QIcon(), "")
        assert self.preset_action
        self.preset_action.setVisible(False)

        def edit_current_preset():
            parent.main_controller.show_presets_dialog(self.preset_edit_target)

        self.preset_action.triggered.connect(edit_current_preset)
        self.addWidget(self.menu_button)

    def refresh_buttons(self):
        for button in self.tool_buttons:
            button.refresh_icon()
        self.menu_button.refresh_icon()

    def indicate_busy(self, is_busy: bool = True) -> None:
        if is_busy:
            self.tool_buttons[0].setBusy(True)
        else:
            self.tool_buttons[0].setBusy(False)
        QApplication.sendPostedEvents(self, 0)  # Flush any change events before resetting the flag
        QApplication.processEvents()  # Force the flushed events to be processed now

    def show_active_preset(self, preset: Preset | None) -> None:
        assert self.preset_action
        if preset is not None:
            self.preset_action.setToolTip(tr("{} preset").format(preset.get_title_name()))
            self.preset_action.setIcon(preset.create_icon())
            self.preset_action.setVisible(True)
            self.preset_edit_target = preset
        else:
            self.preset_action.setToolTip("")
            self.preset_action.setIcon(QIcon())
            self.preset_action.setVisible(False)
            self.preset_edit_target = None
        self.layout().update()


class VduControlsMainPanel(QWidget):
    """GUI for detected VDUs, it will construct and contain a control panel for each VDU."""

    vdu_vcp_changed_qtsignal = pyqtSignal(str, str, int, VcpOrigin, bool)

    def __init__(self) -> None:
        super().__init__()
        self.main_toolbar: VduMainToolBar | None = None
        self.refresh_data_task = None
        self.setObjectName("vdu_controls_main_panel")
        self.vdu_control_panels: Dict[str, VduControlPanel] = {}
        self.alert: QMessageBox | None = None
        self.main_controller: VduAppController | None = None
        self.message_history = []

    def initialise_control_panels(self, main_controller: VduAppController,
                                  app_context_menu: ContextMenu, main_config: VduControlsConfig,
                                  tool_buttons: List[ToolButton], extra_controls: List[QWidget],
                                  splash_message_qtsignal: pyqtSignal) -> None:
        self.main_controller = main_controller

        if old_layout := cast(QVBoxLayout, self.layout()):  # Must be responding to a configuration change requiring re-layout.
            for i in range(0, old_layout.count()):  # Remove all existing widgets.
                item = old_layout.itemAt(i)
                if isinstance(item, QWidget):
                    old_layout.removeWidget(item)
                    item.deleteLater()
                elif isinstance(item, QWidgetItem):
                    old_layout.removeItem(item)
                    item.widget().deleteLater()
        controllers_layout = QVBoxLayout()
        controllers_layout.setSpacing(npx(5))
        alter_margins(controllers_layout, top=npx(5), bottom=npx(5))
        self.setLayout(controllers_layout)

        warnings_enabled = main_config.is_set(ConfOpt.WARNINGS_ENABLED)
        self.vdu_control_panels.clear()
        for controller in self.main_controller.vdu_controllers_map.values():
            splash_message_qtsignal.emit(f"DDC ID {controller.vdu_number}\n{controller.get_vdu_preferred_name()}")
            vdu_control_panel = VduControlPanel(controller, self.show_vdu_exception)
            controller.vcp_value_changed_qtsignal.connect(self.vdu_vcp_changed_qtsignal)
            if vdu_control_panel.number_of_controls() != 0:
                self.vdu_control_panels[controller.vdu_stable_id] = vdu_control_panel
                controllers_layout.addWidget(vdu_control_panel)
            elif warnings_enabled:
                MBox(MIcon.Warning,
                     msg=tr('Monitor {} {} lacks any accessible controls.').format(controller.vdu_number,
                                                                                   controller.get_vdu_preferred_name()),
                     info=tr('The monitor will be omitted from the control panel.')).exec()

        for control in extra_controls:
            controllers_layout.addWidget(control)
        controllers_layout.addStretch(0)

        if len(self.vdu_control_panels) == 0:
            no_vdu_widget = QWidget()
            no_vdu_layout = QHBoxLayout()
            no_vdu_widget.setLayout(no_vdu_layout)
            no_vdu_text = QLabel(tr('No controllable monitors found.\n'
                                    'Use the refresh button if any become available.\n'
                                    'Check that ddcutil and i2c are installed and configured.'))
            no_vdu_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
            no_vdu_image = QLabel()
            no_vdu_image.setPixmap(QApplication.style().standardIcon(StdPixmap.SP_MessageBoxWarning).pixmap(QSize(64, 64)))
            no_vdu_image.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            no_vdu_layout.addSpacing(32)
            no_vdu_layout.addWidget(no_vdu_image)
            no_vdu_layout.addWidget(no_vdu_text)
            no_vdu_layout.addSpacing(32)
            controllers_layout.addWidget(no_vdu_widget)

        self.main_toolbar = VduMainToolBar(tool_buttons=tool_buttons, app_context_menu=app_context_menu, parent=self)
        main_controller.replace_toolbar(self.main_toolbar)

        def _open_context_menu(position: QPoint) -> None:
            assert app_context_menu is not None
            app_context_menu.exec(self.mapToGlobal(position))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(_open_context_menu)

    def indicate_busy(self, is_busy: bool = True, lock_controls: bool = True) -> None:
        if self.main_toolbar is not None:
            self.main_toolbar.indicate_busy(is_busy)
        if lock_controls:
            for control_panel in self.vdu_control_panels.values():
                control_panel.setDisabled(is_busy)

    def is_preset_active(self, preset: Preset) -> bool:
        for section in preset.preset_ini:
            if section not in ('metadata', 'preset') and (panel := self.vdu_control_panels.get(section, None)):
                if not panel.is_preset_active(preset):
                    return False
        return True

    def show_active_preset(self, preset: Preset | None) -> None:
        if self.main_toolbar:
            self.main_toolbar.show_active_preset(preset)

    def show_vdu_exception(self, exception: VduException, can_retry: bool = False) -> bool:
        log_error(f"{exception.vdu_description} {exception.operation} {exception.attr_id} {exception.cause}")
        msg = tr("Set value: Failed to communicate with display {}").format(exception.vdu_description)
        if exception.is_display_not_found_error():
            info = tr('Monitor appears to be switched off or disconnected.')
        else:
            info = tr('Is the monitor switched off?') + '<br>' + tr('Is the sleep-multiplier setting too low?')
        if isinstance(exception.cause, subprocess.SubprocessError):
            details = exception.cause.stderr.decode('utf-8', errors='surrogateescape') + '\n' + str(exception.cause)
        else:
            details = str(exception.cause)
        if self.alert is not None:  # Dismiss any existing alert
            self.alert.done(MBtn.Close)
        self.alert = MBox(MIcon.Critical, msg=msg, info=info, details=details,
                          buttons=MBtn.Close | MBtn.Retry if can_retry else MBtn.Close,
                          default=MBtn.Retry if can_retry else MBtn.Close)
        self.alert.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        answer = self.alert.exec()
        self.alert = None
        return answer == MBtn.Retry

    def status_message(self, message: str, timeout: int):
        if message.strip():  # Only non-empty messages, ignore blank messages, they're just clearing the status bar.
            self.message_history.append(f"\n{datetime.now().strftime('%H:%M:%S')}{MESSAGE_SYMBOL} {message}")
            self.message_history = self.message_history[-9:]
        if self.main_controller.main_config.is_set(ConfOpt.SEPARATE_STATUS_BAR):
            self.main_controller.main_window.statusBar().showMessage(message, timeout)
            self.main_controller.main_window.statusBar().setToolTip("".join([tr('Message history:')] + self.message_history))
        elif self.main_toolbar:
            self.main_toolbar.status_area.showMessage(message, timeout)
            self.main_toolbar.status_area.setToolTip("".join([tr('Message history:')] + self.message_history))


@dataclass
class BulkChangeItem:
    vdu_sid: VduStableId
    vcp_code: str
    final_value: int
    starting_value: int | None = None
    current_value: int | None = None
    transition: bool = False


class BulkChangeWorker(WorkerThread):
    progress_qtsignal = pyqtSignal(object)

    def __init__(self, name: str, main_controller: VduAppController,
                 progress_callable: Callable[[BulkChangeWorker], None],
                 finished_callable: Callable[[BulkChangeWorker], None],
                 step_interval: float = 0.0, ignore_others: bool = True, context: Any = None) -> None:
        super().__init__(task_body=self._perform_changes, task_finished=finished_callable)  # type: ignore
        log_debug(f"BulkChangeHandler: {name} init {ignore_others=}") if log_debug_enabled else None
        self.name = name
        self.ignore_others = ignore_others
        self.context = context
        self.start_time: datetime | None = None
        self.main_controller = main_controller
        self.progress_callable = progress_callable
        self.progress_qtsignal.connect(self.progress_callable)
        self.to_do_list: List[BulkChangeItem] = []
        self.step_interval = step_interval
        self.protect_nvram = self.main_controller.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED)
        self.change_count = 0
        self.total_elapsed_seconds = 0.0
        self.completed = False

    def add_item(self, item: BulkChangeItem):
        if self.protect_nvram or self.step_interval < 0.1:
            item.transition = False
        self.to_do_list.append(item)

    def _perform_changes(self, _: BulkChangeWorker):
        self.start_time = zoned_now()
        try:
            if any([item.current_value is None for item in self.to_do_list]):  # has parent filled out expected values.
                self._refresh_current_values_from_vdu()
            self._do_stepped_changes()  # transitions in a series of steps
            if not self.stop_requested:
                self._do_normal_changes()
                self.completed = len([item for item in self.to_do_list if item.current_value != item.final_value]) == 0
        finally:
            (_ := self).total_elapsed_seconds = (self.start_time - zoned_now()).total_seconds()
            if log_debug_enabled:
                log_debug(f"BulkChangeWorker: {_.name} {_.completed=} {_.change_count=} {_.total_elapsed_seconds=:.3f}")

    def _do_normal_changes(self):
        for item in [item for item in self.to_do_list if not item.transition and item.current_value != item.final_value]:
            if self.stop_requested:
                break
            if item.final_value != item.current_value:
                self.main_controller.set_value(item.vdu_sid, item.vcp_code, item.final_value)
                item.current_value = item.final_value
                self.change_count += 1

    def _do_stepped_changes(self):
        while step_changes := [item for item in self.to_do_list if item.transition and item.current_value != item.final_value]:
            if self.stop_requested:
                break
            for item in step_changes:
                if self.stop_requested:
                    break
                diff = item.final_value - item.current_value
                step_size = max(5, abs(diff) // 2)  # TODO find a good heuristic
                step = int(math.copysign(step_size, diff)) if abs(diff) > step_size else diff
                new_value = item.current_value + step
                origin = VcpOrigin.TRANSIENT if new_value != item.final_value else VcpOrigin.NORMAL
                self.main_controller.set_value(item.vdu_sid, item.vcp_code, new_value, origin)
                item.current_value = new_value
                self.change_count += 1
                # self.doze(0.1)  # TODO do we need to pause to let things settle?
            self.progress_qtsignal.emit(self)
            self.doze(self.step_interval)
            self._refresh_current_values_from_vdu()
            if self.stop_requested:
                break

    def _refresh_current_values_from_vdu(self):
        log_debug(f"BulkChangeWorker {self.name} having to get current_values from VDU") if log_debug_enabled else None
        items_by_vdu: Dict[VduStableId, Dict[str, BulkChangeItem]] = {}
        for item in self.to_do_list:
            if item.vdu_sid not in items_by_vdu:
                items_by_vdu[item.vdu_sid] = {}
            items_by_vdu[item.vdu_sid][item.vcp_code] = item
        for vdu_sid, vdu_items_by_code in items_by_vdu.items():
            for vcp_code, vcp_value in self.main_controller.get_vdu_values(vdu_sid,
                                                                           [item.vcp_code for item in vdu_items_by_code.values()]):
                vdu_current_value = vcp_value.current
                item = vdu_items_by_code[vcp_code]
                if item.current_value is not None and item.current_value != vdu_current_value and not self.ignore_others:
                    log_warning(f"Interrupted bulk change {id=} "
                                f"something else changed the VDU: {vdu_current_value=} != {item.current_value=}")
                    self.stop_requested = True
                    break
                vdu_items_by_code[vcp_code].current_value = vdu_current_value

    def completed_items(self):
        return [item for item in self.to_do_list if item.current_value == item.final_value]


class PresetController:
    def __init__(self) -> None:
        self.presets: Dict[str, Preset] = {}

    def reinitialize(self):
        self.presets = {}

    def find_presets_map(self) -> Dict[str, Preset]:
        presets_still_present = []
        # Use a stable order for the files - alphabetical filename.
        for path_str in sorted(glob.glob(CONFIG_DIR_PATH.joinpath("Preset_*.conf").as_posix()), key=os.path.basename):
            preset_name = os.path.splitext(os.path.basename(path_str))[0].replace('Preset_', '').replace('_', ' ')
            if preset_name not in self.presets:
                preset = Preset(preset_name)
                preset.load()
                self.presets[preset_name] = preset
            presets_still_present.append(preset_name)
        for preset_name in list(self.presets.keys()):
            if preset_name not in presets_still_present:
                del self.presets[preset_name]
        # If Order_Presets.conf exists, reorder according to the CSV Preset names it holds.
        order_presets_path = CONFIG_DIR_PATH.joinpath("Order_Presets.conf")
        if order_presets_path.exists():
            ordering = order_presets_path.read_text().split(",")
            all_presets = list(self.presets.values())
            # Use the Preset-name's position in the Order_Presets.conf CSV as the key-value (or zero if not in the CSV)
            all_presets.sort(key=lambda obj: ordering.index(obj.name) if obj.name in ordering else 0)
            self.presets = {}
            for preset in all_presets:
                self.presets[preset.name] = preset
        return self.presets

    def save_order(self, ordering: List[str]) -> None:
        order_presets_path = CONFIG_DIR_PATH.joinpath("Order_Presets.conf")
        order_presets_path.write_text(','.join(ordering))

    def save_preset(self, preset: Preset) -> None:
        preset.save()
        self.presets[preset.name] = preset

    def delete_preset(self, preset: Preset) -> None:
        preset.delete()
        del self.presets[preset.name]

    def get_preset(self, preset_number: int) -> Preset | None:
        presets = self.find_presets_map()
        if preset_number < len(presets):
            return list(presets.values())[preset_number]
        return None


class PresetItemWidget(QWidget):
    def __init__(self, preset: Preset, restore_action: Callable, save_action: Callable, delete_action: Callable,
                 edit_action: Callable, up_action: Callable, down_action: Callable, protect_nvram: bool):
        super().__init__()
        self.name = preset.name
        self.preset = preset
        line_layout = QHBoxLayout()
        line_layout.setSpacing(0)
        alter_margins(line_layout, top=0, bottom=npx(1))  # Why?
        self.setLayout(line_layout)

        self.preset_name_button = PresetActivationButton(preset)
        line_layout.addWidget(self.preset_name_button)
        self.preset_name_button.clicked.connect(partial(edit_action, preset=preset))
        self.preset_name_button.setToolTip(tr('Activate this Preset and edit its options.'))
        self.preset_name_button.setAutoDefault(False)
        self.preset_name_button.setFixedSize(QSize(npx(300), native_font_height(scaled=1.5)))
        line_layout.addSpacing(npx(20))
        for button in (
                StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), tip=tr("Update this preset from the current VDU settings."),
                          clicked=partial(save_action, from_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_ArrowUp), tip=tr("Move up the menu order."),
                          clicked=partial(up_action, preset=preset, target_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_ArrowDown), tip=tr("Move down the menu order."),
                          clicked=partial(down_action, preset=preset, target_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_DialogDiscardButton), tip=tr('Delete this preset.'),
                          clicked=partial(delete_action, preset=preset, target_widget=self), flat=True)):
            button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            line_layout.addWidget(button)

        if not protect_nvram:
            preset_transition_button = PushButtonLeftJustified(flat=True)
            preset_transition_button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            width = QFontMetrics(preset_transition_button.font()).horizontalAdvance(">____99")
            preset_transition_button.setMaximumWidth(width + 5)
            preset_transition_button.setText(
                f"{preset.get_transition_type().abbreviation()}"
                f"{str(preset.get_step_interval_seconds()) if preset.get_step_interval_seconds() > 0 else ''}")
            if preset.get_step_interval_seconds() > 0:
                preset_transition_button.setToolTip(tr("Transition to {}, each step is {} seconds. {}").format(
                    preset.get_title_name(), preset.get_step_interval_seconds(), preset.get_transition_type().description()))
            else:
                preset_transition_button.setToolTip(tr("Transition to {}. {}").format(
                    preset.get_title_name(), preset.get_transition_type().description()))
            preset_transition_button.clicked.connect(partial(restore_action, preset=preset,
                                                             immediately=preset.get_transition_type() == PresetTransitionFlag.NONE))
            preset_transition_button.setAutoDefault(False)
            if preset.get_transition_type() == PresetTransitionFlag.NONE:
                preset_transition_button.setDisabled(True)
                preset_transition_button.setText('')
            line_layout.addWidget(preset_transition_button)

        line_layout.addSpacing(5)
        self.timer_control_button = PushButtonLeftJustified(parent=self, flat=True)
        self.timer_control_button.setAutoDefault(False)

        if preset.get_solar_elevation() is not None or preset.get_at_time() is not None:
            def _toggle_timer(_) -> None:
                preset.toggle_timer()
                self.update_timer_button()

            self.timer_control_button.clicked.connect(_toggle_timer)

        line_layout.addWidget(self.timer_control_button)
        self.update_timer_button()

    def update_timer_button(self):
        self.timer_control_button.setEnabled(
            self.preset.schedule_status in (PresetScheduleStatus.SCHEDULED, PresetScheduleStatus.SUSPENDED))
        if self.preset.schedule_status == PresetScheduleStatus.SCHEDULED:
            action_desc = tr("Press to skip: ")
        elif self.preset.schedule_status == PresetScheduleStatus.SUSPENDED:
            action_desc = tr("Press to re-enable: ")
        else:
            action_desc = ''
        tip_text = f"{action_desc} {self.preset.get_schedule_description()}"
        self.timer_control_button.setText(self.preset.get_solar_elevation_abbreviation())
        if tip_text.strip():
            self.timer_control_button.setToolTip(tip_text)

    def indicate_active(self, active: bool):
        weight = QFont.Weight.Bold if active else QFont.Weight.Normal
        font = self.preset_name_button.font()
        if font.weight() != weight:
            font.setWeight(weight)
            self.preset_name_button.setFont(font)


class PresetActivationButton(StdButton):
    def __init__(self, preset: Preset) -> None:
        super().__init__(icon=preset.create_icon(), icon_size=QSize(native_font_height(), native_font_height()),
                         title=preset.get_title_name(), tip=tr("Restore {} (immediately)").format(preset.get_title_name()))
        self.preset = preset

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            self.setIcon(self.preset.create_icon())
        return super().event(event)


class PresetIconPickerButton(StdButton):

    def __init__(self) -> None:
        super().__init__(icon_size=QSize(native_font_height(), native_font_height()),
                         clicked=self.choose_preset_icon_action, flat=True, auto_default=False,
                         tip=tr('Choose a preset icon.'))
        self.setIcon(si(self, PresetsDialog.NO_ICON_ICON_NUMBER))
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.last_selected_icon_path: Path | None = None
        self.last_icon_dir = Path.home()
        for path in STANDARD_ICON_PATHS:
            if path.exists():
                self.last_icon_dir = path
                break
        self.preset: Preset | None = None

    def set_preset(self, preset: Preset | None) -> None:
        self.preset = preset
        if preset is not None:
            self.last_selected_icon_path = preset.get_icon_path()
        if self.last_selected_icon_path is not None:
            self.last_icon_dir = self.last_selected_icon_path.parent
        self.update_icon()

    def choose_preset_icon_action(self) -> None:
        try:
            PresetsDialog.get_instance().setDisabled(True)
            PresetsDialog.get_instance().status_message(TIME_CLOCK_SYMBOL + ' ' + tr("Select an icon..."))
            QApplication.processEvents()
            icon_file = FasterFileDialog.getOpenFileName(self, tr('Icon SVG or PNG file'), self.last_icon_dir.as_posix(),
                                                         'SVG or PNG (*.svg *.png)')
            self.last_selected_icon_path = Path(icon_file[0]) if icon_file[0] != '' else None
            if self.last_selected_icon_path:
                self.last_icon_dir = self.last_selected_icon_path.parent
            self.update_icon()
        finally:
            PresetsDialog.get_instance().status_message('')
            PresetsDialog.get_instance().setDisabled(False)

    def update_icon(self) -> None:
        if self.last_selected_icon_path:
            self.setIcon(create_icon_from_path(self.last_selected_icon_path, polychrome_light_or_dark()))
        elif self.preset:
            self.setIcon(self.preset.create_icon(polychrome_light_or_dark()))
        else:
            self.setIcon(si(self, PresetsDialog.NO_ICON_ICON_NUMBER))

    def reset(self):
        self.last_selected_icon_path = None
        self.preset = None
        self.update_icon()

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            self.update_icon()
        return super().event(event)




def weather_bad_location_dialog(weather) -> None:
    kilometres = weather.proximity_km
    use_km = QLocale.system().measurementSystem() == QLocale.MeasurementSystem.MetricSystem
    MBox(MIcon.Warning, msg=tr("The site {} reports your location as {}, {}, {},{} "
                               "which is about {} {} from the latitude and longitude specified in Settings."
                               ).format(WEATHER_FORECAST_URL, weather.area_name, weather.country_name, weather.latitude,
                                        weather.longitude,
                                        round(kilometres if use_km else kilometres * 0.621371), 'km' if use_km else 'miles'),
         info=tr("Please check the location specified in Settings."), details=f"{weather}").exec()


class PresetWeatherWidget(QWidget):
    default_weather_conditions = {
        CONFIG_DIR_PATH.joinpath('good.weather'): "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n",
        CONFIG_DIR_PATH.joinpath('bad.weather'):
            "143 Fog\n179 Light Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 "
            "Light Snow\n230 Heavy Snow\n248 Fog\n260 Fog\n266 Light Rain\n281 Light Sleet\n284 Light "
            "Sleet\n293 Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 "
            "Heavy Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
            "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
            "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
            "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
            "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
            "Thundery Snow Showers\n395 HeavySnowShowers\n",
        CONFIG_DIR_PATH.joinpath('all.weather'):
            "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n122 Very Cloudy\n143 Fog\n176 Light Showers\n179 Light "
            "Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 Light Snow\n230 Heavy "
            "Snow\n248 Fog\n260 Fog\n263 Light Showers\n266 Light Rain\n281 Light Sleet\n284 Light Sleet\n293 "
            "Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 Heavy "
            "Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
            "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
            "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
            "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
            "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
            "Thundery Snow Showers\n395 Heavy Snow Showers\n"}

    def __init__(self, location: GeoLocation | None, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.location = location
        self.init_weather()
        self.main_config = main_config
        self.required_weather_filepath: Path | None = None
        self.setLayout(widget_layout := QVBoxLayout())
        self.label = QLabel(tr("Additional weather requirements"))
        self.label.setToolTip(tr("Weather conditions will be retrieved from {}").format(WEATHER_FORECAST_URL))
        widget_layout.addWidget(self.label)
        self.chooser = QComboBox()

        def _select_action(index: int) -> None:
            self.required_weather_filepath = self.chooser.itemData(index)
            if self.chooser.itemData(index) is None:
                self.info_label.setText('')
            else:
                assert self.location is not None
                self.verify_weather_location(self.location)
                path = self.chooser.itemData(index)
                if path.exists():
                    with open(path, encoding="utf-8") as weather_file:
                        code_list = weather_file.read()
                        self.info_label.setText(code_list)
                else:
                    self.chooser.removeItem(index)
                    self.chooser.setCurrentIndex(0)
            self.populate()

        self.chooser.currentIndexChanged.connect(_select_action)
        self.chooser.setToolTip(self.label.toolTip())
        widget_layout.addWidget(self.chooser)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.populate()
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.info_label)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidgetResizable(True)
        widget_layout.addWidget(scroll_area)

    def init_weather(self) -> None:
        for condition_path, condition_content in PresetWeatherWidget.default_weather_conditions.items():
            if not condition_path.exists():
                with open(condition_path, 'w', encoding="utf-8") as weather_file:
                    log_info(f"Creating {condition_path.as_posix()}")
                    weather_file.write(condition_content)

    def verify_weather_location(self, location: GeoLocation) -> None:
        if not self.main_config.is_set(ConfOpt.WEATHER_ENABLED):
            return
        place_name = location.place_name if location.place_name is not None else 'IP-address'
        # Only do this check if the location has changed.
        vf_file_path = CONFIG_DIR_PATH.joinpath('verified_weather_location.txt')
        if vf_file_path.exists():
            with open(vf_file_path, encoding="utf-8") as vf:
                if vf.read() == place_name:
                    return
        try:
            log_info(f"Verifying weather location by querying {WEATHER_FORECAST_URL}.")
            weather = WeatherQuery(location)
            weather.run_query()
            if weather.proximity_ok:
                MBox(MIcon.Information,
                     msg=tr("Weather for {} will be retrieved from {}").format(place_name, WEATHER_FORECAST_URL)).exec()
                with open(vf_file_path, 'w', encoding="utf-8") as vf:
                    vf.write(place_name)
            else:
                weather_bad_location_dialog(weather)
        except ValueError as e:
            log_error(f"Failed to validate location: {e}", trace=True)
            MBox(MIcon.Critical, msg=tr("Failed to validate weather location: {}").format(e.args[0]), info=e.args[1]).exec()

    def populate(self) -> None:
        if self.chooser.count() == 0:
            self.chooser.addItem(tr("None"), None)
        existing_paths = [self.chooser.itemData(i) for i in range(1, self.chooser.count())]
        for path in sorted(CONFIG_DIR_PATH.glob("*.weather")):
            if path not in existing_paths:
                weather_name = path.stem.replace('_', ' ')
                self.chooser.addItem(weather_name, path)

    def get_required_weather_filepath(self) -> Path | None:
        return self.required_weather_filepath if self.required_weather_filepath is not None else None

    def set_required_weather_filepath(self, weather_filename: str | None) -> None:
        if weather_filename is None:
            self.required_weather_filepath = None
            self.chooser.setCurrentIndex(0)
            self.info_label.setText('')
            return
        self.required_weather_filepath = Path(weather_filename)
        for i in range(1, self.chooser.count()):
            if self.chooser.itemData(i).as_posix() == self.required_weather_filepath.as_posix():
                self.chooser.setCurrentIndex(i)
                return

    def update_location(self, location: GeoLocation) -> None:
        self.location = location
        self.verify_weather_location(self.location)


class PresetTransitionWidget(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.setToolTip(tr("Choose whether this Preset should transition when activated a particular way."))
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(QLabel(tr("Transition")), alignment=Qt.AlignmentFlag.AlignLeft)
        self.transition_type_widget = StdButton(title=PresetTransitionFlag.NONE.description())
        self.button_menu = QMenu()
        self.transition_type = PresetTransitionFlag.NONE
        self.is_setting = False

        for transition_type in PresetTransitionFlag.ALWAYS.component_values():
            action = QAction(transition_type.description(), self.button_menu)
            action.setData(transition_type)
            action.setCheckable(True)
            action.toggled.connect(self.update_value)
            self.button_menu.addAction(action)

        self.transition_type_widget.setMenu(self.button_menu)
        layout.addWidget(self.transition_type_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(20)
        layout.addWidget(QLabel(tr("Transition step")), alignment=Qt.AlignmentFlag.AlignRight)
        self.step_seconds_widget = QSpinBox()
        self.step_seconds_widget.setRange(0, 60)
        layout.addWidget(self.step_seconds_widget, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QLabel(tr("sec.")), alignment=Qt.AlignmentFlag.AlignRight)

    def update_value(self, checked: bool) -> None:
        if self.is_setting:
            return
        if checked:
            MBox(MIcon.Warning,
                 msg=tr('Transitions have been deprecated to minimize wear on VDU NVRAM.'),
                 info=tr('Transitions are slated for removal, please contact the developer if you wish to retain them.')).exec()
        for act in self.button_menu.actions():
            if act.isChecked():
                self.transition_type |= act.data()
            elif act.data() in self.transition_type:
                self.transition_type ^= act.data()
        self.transition_type_widget.setText(str(self.transition_type.description()))

    def set_transition_type(self, transition_type: PresetTransitionFlag) -> None:
        try:
            self.is_setting = True
            self.transition_type = transition_type
            for act in self.button_menu.actions():
                act.setChecked(self.transition_type & act.data())
            self.transition_type_widget.setText(str(self.transition_type.description()))
        finally:
            self.is_setting = False

    def set_step_seconds(self, seconds: int) -> None:
        self.step_seconds_widget.setValue(seconds)

    def get_transition_type(self) -> PresetTransitionFlag:
        return self.transition_type

    def get_step_seconds(self) -> int:
        return self.step_seconds_widget.value()


class PresetElevationChartWidget(QLabel):
    selected_elevation_qtsignal = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(npx(300), npx(350))
        self.sun_image: QImage | None = None
        self.setMouseTracking(True)
        self.in_drag = False
        self.current_pos: QPoint | None = None
        self.cache_solar_by_elevation: Dict[SolarElevationKey, SolarElevationData] = {}
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation | None = None
        self.elevation_steps: List[SolarElevationKey] = []
        for i in range(-19, 90):
            self.elevation_steps.append(SolarElevationKey(EASTERN_SKY, i))
        for i in range(90, -20, -1):
            self.elevation_steps.append(SolarElevationKey(WESTERN_SKY, i))
        self.noon_x: int = npx(100)
        self.noon_y: int = npx(25)
        self.horizon_y: int = npx(75)
        self.radius_of_deletion = npx(50)
        self.solar_max_t: datetime | None = None
        self.last_event_time = time.time()
        self.cache_key: Tuple[datetime, int, int, int] | None = None
        self.cache_curve_points: List[QPoint] = []

    def has_elevation_key(self, key: SolarElevationKey) -> bool:
        return key in self.elevation_steps

    def get_elevation_data(self, elevation_key: SolarElevationKey) -> SolarElevationData | None:
        assert self.cache_solar_by_elevation is not None
        return self.cache_solar_by_elevation[elevation_key] if elevation_key in self.cache_solar_by_elevation else None

    def set_elevation_key(self, elevation_key: SolarElevationKey | None) -> None:
        self.elevation_key = elevation_key
        self.create_plot()

    def configure_for_location(self, location: GeoLocation | None) -> None:
        self.location = location
        if location is not None:
            self.cache_key = None
            self.elevation_key = None
            self.create_plot()

    def _reverse_X(self, x: int) -> int:  # makes thinking right-to-left a bit easier. MAYBE
        return self.width() - x

    def create_plot(self) -> None:
        ev_key = self.elevation_key
        logical_width, logical_height = self.width(), self.height()
        origin_iy, range_iy = round(logical_height / 2), round(logical_height / 2.5)
        self.radius_of_deletion = round(range_iy * 0.8)
        self.horizon_y = origin_iy
        line_width = npx(4)
        thin_line_width = npx(2)
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(logical_width * dp_ratio), round(logical_height * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        def _reverse_x(x_val: int) -> int:  # makes thinking right-to-left a bit easier. MAYBE
            return logical_width - x_val

        painter.fillRect(0, 0, logical_width, origin_iy, QColor(0x5b93c5))
        painter.fillRect(0, origin_iy, logical_width, logical_height, QColor(0x7d5233))
        painter.setPen(QPen(Qt.GlobalColor.white, line_width))  # Horizon
        painter.drawLine(0, origin_iy, logical_width, origin_iy)

        _reverse_x = self._reverse_X

        if self.location is not None:
            self.refresh_day_cache(logical_width, origin_iy, range_iy)
            curve_points = self.cache_curve_points
            solar_noon_x, solar_noon_y = self.noon_x, self.noon_y,
            if ev_key and (solar_data := self.cache_solar_by_elevation.get(ev_key)):
                seconds_since_midnight = (
                            solar_data.when - solar_data.when.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                sun_plot_time = solar_data.when
                sun_plot_x = round(logical_width * seconds_since_midnight / (60.0 * 60.0 * 24.0))
                sun_height = math.sin(math.radians(90.0 - solar_data.zenith)) * range_iy
                sun_plot_y = origin_iy - round(sun_height)
            else:
                sun_plot_time = None
                sun_plot_x = self.noon_x
                sun_plot_y = self.noon_y

            # Draw an elevation curve for today from the accumulated plot points:
            painter.setPen(QPen(QColor(0xff965b), line_width))
            painter.drawPoints(QPolygon(curve_points))

            # Draw various annotations such the horizon-line, noon-line, E & W, and the current degrees:
            painter.setPen(QPen(Qt.GlobalColor.white, line_width))
            painter.drawLine(_reverse_x(0), origin_iy, _reverse_x(logical_width), origin_iy)
            painter.drawLine(_reverse_x(solar_noon_x), origin_iy, _reverse_x(solar_noon_x), 0)
            painter.setPen(QPen(Qt.GlobalColor.white, line_width))
            painter.setFont(QFont(QApplication.font().family(), pt := 18, QFont.Weight.Bold))
            painter.drawText(QPoint(_reverse_x((txt_margin := npx(25)) + pt), origin_iy - npx(32)), tr("E"))
            painter.drawText(QPoint(_reverse_x(logical_width - txt_margin), origin_iy - npx(32)), tr("W"))
            time_text = sun_plot_time.strftime("%H:%M") if sun_plot_time else "____"
            painter.drawText(_reverse_x(solar_noon_x + logical_width // 4), logical_height - npx(25),
                             f"{ev_key.elevation if ev_key else 0:3d}{DEGREE_SYMBOL} {time_text}")

            # Draw pie/compass angle
            if ev_key:
                angle_above_horz = ev_key.elevation if ev_key.direction == EASTERN_SKY else (
                            180 - ev_key.elevation)  # anticlockwise from 0
            else:
                angle_above_horz = 180 + 19
            _, pos_as_radius = self.calc_angle_radius(self.current_pos) if self.current_pos else (0, 21)
            pie_width = pie_height = range_iy * 2
            span_angle = -(angle_above_horz + 19)  # From start angle spanning counterclockwise back toward the right to -19.
            painter.setPen(
                QPen(QColor(
                    0xffffff if self.current_pos is None or self.in_drag or pos_as_radius > self.radius_of_deletion else 0xff0000),
                     2))
            painter.setBrush(QColor(255, 255, 255, 64))
            painter.drawPie(_reverse_x(solar_noon_x) - pie_width // 2, origin_iy - pie_height // 2, pie_width, pie_height,
                            angle_above_horz * 16, span_angle * 16)

            # Draw drag-dot
            painter.setFont(QFont(QApplication.font().family(), 8, QFont.Weight.Normal))
            if self.current_pos is not None or self.in_drag or pos_as_radius >= self.radius_of_deletion:
                painter.setPen(QPen(Qt.GlobalColor.red, npx(6)))
                painter.setBrush(Qt.GlobalColor.white)
                ddot_radians = math.radians(angle_above_horz if ev_key else -19)
                ddot_radius = npx(8)
                ddot_x = round(range_iy * math.cos(ddot_radians)) - ddot_radius
                ddot_y = round(range_iy * math.sin(ddot_radians)) + ddot_radius
                painter.drawEllipse(_reverse_x(solar_noon_x - ddot_x), origin_iy - ddot_y, ddot_radius * 2, ddot_radius * 2)
                if not self.in_drag:
                    painter.setPen(QPen(Qt.GlobalColor.black, 1))
                    painter.drawText(QPoint(_reverse_x(solar_noon_x - ddot_x) + npx(10), origin_iy - ddot_y - npx(5)),
                                     tr("Drag to change."))

            # Draw origin-dot
            painter.setPen(QPen(QColor(0xff965b), thin_line_width))
            if self.current_pos is not None and not self.in_drag:
                if pos_as_radius < self.radius_of_deletion:
                    painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                    painter.drawText(QPoint(_reverse_x(solar_noon_x + 8) + npx(10), origin_iy - npx(8) - npx(5)),
                                     tr("Click to delete."))
                    painter.setPen(QPen(Qt.GlobalColor.red, thin_line_width))
            odot_radius = npx(8)
            painter.setBrush(painter.pen().color())
            painter.drawEllipse(_reverse_x(solar_noon_x + odot_radius), origin_iy - odot_radius, odot_radius * 2, odot_radius * 2)

            if ev_key:
                # Draw a line representing the slider degrees and Twilight indicator - may be higher than the sun for today:
                sky_line_y = origin_iy - round(math.sin(math.radians(ev_key.elevation)) * range_iy)
                if sky_line_y >= solar_noon_y:
                    sky_line_pen = QPen(Qt.GlobalColor.white, thin_line_width)
                else:
                    sky_line_pen = QPen(QColor(0xcccccc), thin_line_width)
                    sky_line_pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(sky_line_pen)
                painter.setBrush(painter.pen().color())

                pyramid_base = npx(16)
                if ev_key.direction == EASTERN_SKY:  # Triangle pointing up
                    pyramid = [(-pyramid_base // 2, 0), (0, -pyramid_base), (pyramid_base // 2, 0)]
                    painter.drawLine(_reverse_x(0), sky_line_y, _reverse_x(solar_noon_x), sky_line_y)
                    painter.setPen(QPen(painter.pen().color(), 1))
                    painter.drawPolygon(
                        QPolygon([QPoint(_reverse_x(0 + npx(20) + tx), sky_line_y - npx(10) + ty) for tx, ty in pyramid]))
                else:  # Triangle pointing down
                    inverted_pyramid = [(-pyramid_base // 2, 0), (0, pyramid_base), (pyramid_base // 2, 0)]
                    painter.drawLine(_reverse_x(solar_noon_x), sky_line_y, _reverse_x(logical_width), sky_line_y)
                    painter.setPen(QPen(painter.pen().color(), 1))
                    painter.drawPolygon(
                        QPolygon([QPoint(_reverse_x(logical_width - npx(18)) + tx, sky_line_y + npx(10) + ty)
                                  for tx, ty in inverted_pyramid]))
                # Draw the sun
                painter.setPen(QPen(QColor(0xff4a23), line_width))
                if self.sun_image is None:
                    sun_image = create_image_from_svg_bytes(SUN_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#fecf70"))
                    self.sun_image = sun_image.scaled(npx(sun_image.width()), npx(sun_image.height()))
                painter.drawImage(QPoint(_reverse_x(sun_plot_x) - self.sun_image.width() // 2,
                                         sun_plot_y - self.sun_image.height() // 2), self.sun_image)
        painter.end()
        self.setPixmap(pixmap)

    def refresh_day_cache(self, logical_width: int, origin_iy: int, range_iy: int) -> None:
        # Perform computations for today's curve and maxima.
        _reverse_x = self._reverse_X
        new_cache_key = ((zoned_now().replace(hour=0, minute=0, second=0, microsecond=0)), logical_width, origin_iy, range_iy)
        if self.cache_key and new_cache_key == self.cache_key:
            return
        log_debug(f"PresetElevationChartWidget: change of key values {new_cache_key=}, recalculating")
        self.cache_key = new_cache_key
        max_sun_height = npx(-90.0)
        solar_noon_x, solar_noon_y = 0, 0  # Solar noon
        curve_points = []

        def _create_curve(a, z, t):  # Gets called for every 1-minute point - to create a smooth curve.
            nonlocal max_sun_height, solar_noon_x, solar_noon_y
            second_of_day = (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            x = round(logical_width * second_of_day / (60.0 * 60.0 * 24.0))
            sun_height = math.sin(math.radians(90.0 - z)) * range_iy
            y = origin_iy - round(sun_height)
            curve_points.append(QPoint(_reverse_x(x), y))  # Save the plot points to a list
            if sun_height > max_sun_height:
                max_sun_height = sun_height
                solar_noon_x, solar_noon_y = x, y
                self.solar_max_t = t

        self.cache_solar_by_elevation = create_elevation_map(zoned_now(),
                                                             latitude=self.location.latitude, longitude=self.location.longitude,
                                                             callback=_create_curve)
        self.noon_x = solar_noon_x
        self.noon_y = solar_noon_y
        self.cache_curve_points = curve_points

    def calc_angle_radius(self, pos: QPoint) -> Tuple[int, int]:
        x, y = pos.x(), pos.y()
        adjacent = x - self._reverse_X(self.noon_x)
        opposite = self.horizon_y - y
        angle = 90 if adjacent == 0 else round(math.degrees(math.atan(opposite / adjacent)))
        radius = round(math.sqrt(adjacent ** 2 + opposite ** 2))
        return angle, radius

    def update_current_pos(self, local_pos: QPoint) -> QPoint | None:
        self.current_pos = local_pos if (0 < local_pos.x() < self.width() and 0 <= local_pos.y() < self.height()) else None
        return self.current_pos

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event:
            if pos := self.update_current_pos(event.pos()):
                angle, radius = self.calc_angle_radius(pos)
                if radius <= self.radius_of_deletion:
                    self.set_elevation_key(None)
                    self.selected_elevation_qtsignal.emit(None)
                else:
                    self.in_drag = True
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event:
            self.update_current_pos(event.pos())
            self.in_drag = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event:
            event.accept()
            if (now := time.time()) - self.last_event_time < 0.1:  # Prevent event overload on Qt6 kwin-wayland
                return
            self.last_event_time = now
            pos = self.update_current_pos(event.pos())
            if pos is not None and 0 <= pos.x() < self.width() and 0 <= pos.y() < self.height():
                angle, radius = self.calc_angle_radius(pos)
                if self.in_drag:
                    self.current_pos = pos
                    angle = -angle if pos.x() < self._reverse_X(self.noon_x) else angle
                    eastern = pos.x() >= self._reverse_X(self.noon_x)
                    key = SolarElevationKey(EASTERN_SKY if eastern else WESTERN_SKY, angle)
                    if not key in self.elevation_steps:
                        key = self.elevation_steps[0 if eastern else -1]
                    self.set_elevation_key(key)
                    self.selected_elevation_qtsignal.emit(key)
            self.create_plot()  # necessary to detect deletions

    def leaveEvent(self, event: QEvent | None) -> None:
        self.current_pos = None
        self.create_plot()
        super().leaveEvent(event)


class PresetDaylightFactorWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.df_checkbox = QCheckBox()
        self.df_label = QLabel(tr("Daylight-Factor"))
        self.df_input = QLineEdit()
        self.df_input.setValidator(QDoubleValidator())
        self.setEnabled(False)
        self.df_checkbox.toggled.connect(self.setEnabled)
        self.setToolTip(tr("Save the current semi-automatic Light-Metering Daylight-Factor (DF) as part of the Preset."))

        def df_init(state):
            if state == Qt.CheckState.Checked:
                if self.df_input.text() == '':
                    self.df_input.setText(f"{LuxMeterSemiAutoDevice.get_daylight_factor():.4f}")
            else:
                self.df_input.setText('')

        self.df_checkbox.stateChanged.connect(df_init)
        for widget in (self.df_checkbox, self.df_label, self.df_input):
            self.layout().addWidget(widget)

    def setEnabled(self, enabled):
        self.df_checkbox.setChecked(enabled)
        self.df_label.setEnabled(enabled)
        self.df_input.setEnabled(enabled)


class PresetScheduleAtWidgetBase(QWidget):  # Abstract

    def __init__(self, description: str):
        super().__init__()
        self.description = description
        self.all_schedule_chooser_widgets: List[PresetScheduleAtWidgetBase] = []

    def set_schedule_widgets(self, all_widgets: List[PresetScheduleAtWidgetBase]):
        self.all_schedule_chooser_widgets = all_widgets

    def clear_others(self, _=None) -> bool:  # Only allow a Preset to be scheduled once.
        others = [w for w in self.all_schedule_chooser_widgets if w != self and w.is_set()]
        if others and MBox(MIcon.Question, msg=tr('Preset already scheduled. Clear existing {}?').format(others[0].description),
                           info=tr('Duplicate the preset if you need to schedule it more than once.'),
                           buttons=MBtn.Ok | MBtn.Cancel).exec() == MBtn.Cancel:
            return False
        for schedule_chooser in others:
            schedule_chooser.clear()
        return True

    def is_set(self) -> bool:  # Abstract
        return False

    def clear(self) -> None:  # Abstract
        pass


class PresetScheduleAtElevationWidget(PresetScheduleAtWidgetBase):
    _slider_select_elevation_qtsignal = pyqtSignal(object)

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__(description=tr("elevation-trigger"))
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation | None = main_config.get_location()
        self.setLayout(main_layout := QVBoxLayout())
        self.title_prefix = tr("Trigger at solar elevation:")
        self.title_label = QLabel(self.title_prefix)
        self.title_label.setFixedHeight(
            native_font_height(scaled=1.5))  # Stop ascenders/descenders in Unicode from altering layout.
        self.title_label.setToolTip(tr("Trigger at a set solar elevation (sun angle at your geolocation and time)."))
        main_layout.addWidget(self.title_label)

        self.elevation_chart = PresetElevationChartWidget()
        self.elevation_chart.selected_elevation_qtsignal.connect(self.set_elevation_key)

        self.df_widget = PresetDaylightFactorWidget()

        self.slider_last_event_time = time.time()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-1)
        self.slider.setValue(-1)
        self.slider.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.slider.setTickInterval(5)
        self.slider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self._slider_select_elevation_qtsignal.connect(self.set_elevation_key)

        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)

        chart_and_slider_layout = QVBoxLayout()
        chart_and_slider_layout.addWidget(self.elevation_chart, 1)
        chart_and_slider_layout.addWidget(self.slider)
        chart_and_slider_layout.addWidget(self.df_widget, 0)
        bottom_layout.addLayout(chart_and_slider_layout, 1)

        self.weather_widget = PresetWeatherWidget(self.location, main_config)
        bottom_layout.addWidget(self.weather_widget, 0)
        self.configure_for_location(self.location)
        self.slider.valueChanged.connect(self.sliding)

        self.setMinimumWidth(npx(400))
        self.sun_image: QImage | None = None

    def is_set(self) -> bool:
        return self.elevation_key is not None

    def clear(self) -> None:
        self.set_elevation_key(None)

    def sliding(self) -> None:
        if (now := time.time()) - self.slider_last_event_time < 0.1:  # Prevent event overload on Qt6 kwin-wayland
            return
        self.slider_last_event_time = now
        value = self.slider.value()
        if value == -1:
            self._slider_select_elevation_qtsignal.emit(None)
            return
        chart = self.elevation_chart
        self._slider_select_elevation_qtsignal.emit(
            chart.elevation_steps[value] if 0 <= value < len(chart.elevation_steps) else None)

    def show_elevation_description(self) -> None:
        if self.elevation_key is None:
            self.title_label.setText(self.title_prefix)
            return
        elevation_data = self.elevation_chart.get_elevation_data(self.elevation_key)
        occurs_at = elevation_data.when if elevation_data is not None else None  # No elev data => sun doesn't rise this high today
        if occurs_at:
            when_text = tr("today at {}").format(occurs_at.strftime('%H:%M'))
        else:
            when_text = tr("the sun does not rise this high today")
        # https://en.wikipedia.org/wiki/Twilight
        if self.elevation_key.elevation < 1:
            if self.elevation_key.elevation >= -6:
                when_text += " " + (tr("dawn") if self.elevation_key.direction == EASTERN_SKY else tr("dusk"))
            elif self.elevation_key.elevation >= -18:  # Astronomical twilight
                when_text += " " + tr("twilight")
            else:
                when_text += " " + tr("nighttime")
        if elevation_data is not None and self.location:
            if lux := calc_solar_lux(elevation_data.when, self.location, 1.0):
                when_text += tr(" {:,} lux").format(lux)
        desc_text = "{} {} ({}, {})".format(
            self.title_prefix, format_solar_elevation_abbreviation(self.elevation_key), tr(self.elevation_key.direction), when_text)
        if desc_text != self.title_label.text():
            self.title_label.setText(desc_text)

    def configure_for_location(self, location: GeoLocation | None) -> None:
        self.elevation_chart.configure_for_location(location)
        self.location = location
        if location is None:
            self.title_label.setText(self.title_prefix + tr("location undefined (see settings)"))
            self.slider.setDisabled(True)
            return
        self.slider.setEnabled(True)
        self.slider.setMaximum(len(self.elevation_chart.elevation_steps) - 1)
        self.slider.setValue(-1)
        self.sliding()
        self.weather_widget.update_location(location)
        if self.elevation_chart.solar_max_t is not None:
            snt = self.elevation_chart.solar_max_t
            if snt.hour > (15 if snt.tzname() == 'CST' else 14) or snt.hour < 10:  # Solar midday seems too far from 12:00 midday.
                log_warning(f"Location {location.longitude},{location.latitude} and timezone {snt.tzname()} seem mismatched.")

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self.elevation_chart.set_elevation_key(self.elevation_key)

    def set_elevation_from_text(self, elevation_text: str | None) -> None:
        if elevation_text is not None and elevation_text.strip() != '' and len(self.elevation_chart.elevation_steps) != 0:
            elevation_key = parse_solar_elevation_ini_text(elevation_text)
            if self.elevation_chart.has_elevation_key(elevation_key):
                self.set_elevation_key(elevation_key)
                return
        self.set_elevation_key(None)

    def set_elevation_key(self, elevation_key: SolarElevationKey | None) -> None:
        if elevation_key is not None:
            if self.clear_others():
                if self.elevation_chart.has_elevation_key(elevation_key):
                    self.elevation_key = elevation_key
                    self.slider.setValue(self.elevation_chart.elevation_steps.index(self.elevation_key))
                    self.slider.setToolTip(f"{self.elevation_key.elevation}{DEGREE_SYMBOL}")
                    self.elevation_chart.set_elevation_key(self.elevation_key)
                    self.weather_widget.setEnabled(True)
                    self.show_elevation_description()
                    return
        self.elevation_key = None
        self.slider.setValue(-1)
        self.elevation_chart.set_elevation_key(None)
        self.weather_widget.setEnabled(False)
        self.weather_widget.chooser.setCurrentIndex(0)
        self.show_elevation_description()

    def get_required_weather_filename(self) -> str | None:
        path = self.weather_widget.get_required_weather_filepath()
        return path.as_posix() if path else None

    def set_required_weather_filename(self, weather_filename: str | None) -> None:
        self.weather_widget.set_required_weather_filepath(weather_filename)


class PresetScheduleAtTimeWidget(PresetScheduleAtWidgetBase):
    class TimeFieldValidator(QValidator):

        def validate(self, text, pos):
            if len(text) < 4:
                return QValidator.State.Intermediate, text, pos
            state = QValidator.State.Invalid
            for acceptable_format in ['%H:%M', '%H%M']:
                try:
                    datetime.strptime(text, acceptable_format)
                    state = QValidator.State.Acceptable
                    break
                except ValueError:
                    pass
            return state, text, pos

    def __init__(self):
        super().__init__(description=tr("time-trigger"))
        self.setToolTip(tr("Trigger at the same time (hh:mm) each day."))
        self.setLayout(at_time_layout := QHBoxLayout())
        at_time_layout.addWidget(QLabel(tr("Trigger at time:")))
        self.editor_at_time_field = QLineEdit()
        self.editor_at_time_field.setValidator(PresetScheduleAtTimeWidget.TimeFieldValidator())
        at_time_layout.addWidget(self.editor_at_time_field)

        def clear_others_ask(_: str):
            if not self.clear_others():
                self.clear()

        self.editor_at_time_field.textChanged.connect(clear_others_ask)
        at_time_layout.addStretch(1)
        at_time_layout.setContentsMargins(0, 0, 0, 0)

    def is_set(self) -> bool:
        return len(self.text()) != 0

    def clear(self) -> None:
        if self.text():
            self.setText('')

    def setText(self, text: str) -> None:
        self.editor_at_time_field.setText(text)

    def text(self) -> str:
        if text := self.editor_at_time_field.text():
            if len(text) == 4:
                text = f"{text[:2]}:{text[2:]}"
        return text


class PresetsDialog(SubWinDialog, DialogSingletonMixin):  # TODO has become rather complex - break into parts?
    """A dialog for creating/updating/removing presets."""
    NO_ICON_ICON_NUMBER = StdPixmap.SP_ComputerIcon

    @staticmethod
    def invoke(main_controller: VduAppController, main_config: VduControlsConfig) -> None:
        PresetsDialog.show_existing_dialog() if PresetsDialog.exists() else PresetsDialog(main_controller, main_config)
        PresetsDialog.show_status_message('')

    @staticmethod
    def show_status_message(message: str = '', timeout: int = 0) -> None:
        if presets_dialog := PresetsDialog.get_instance():  # type: ignore
            if message != '':
                presets_dialog.status_message(message, timeout=timeout)
            elif not presets_dialog.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
                presets_dialog.status_message(
                    WARNING_SYMBOL + ' ' + tr('Preset scheduling is disabled in the Setting-Dialog.'))
            elif not presets_dialog.main_config.is_set(ConfOpt.WEATHER_ENABLED):
                presets_dialog.status_message(WARNING_SYMBOL + ' ' + tr('Weather lookup is disabled in the Setting-Dialog.'),
                                              timeout=60000)
            else:
                presets_dialog.status_message('')

    @staticmethod
    def reconfigure_instance() -> None:
        if presets_dialog := PresetsDialog.get_instance():  # type: ignore
            presets_dialog.reconfigure()

    @staticmethod
    def is_instance_editing() -> bool:
        if presets_dialog := PresetsDialog.get_instance():
            return presets_dialog.preset_name_edit.text() != ''
        return False

    @staticmethod
    def instance_indicate_active_preset(preset: Preset | None = None):
        if presets_dialog := PresetsDialog.get_instance():
            presets_dialog.indicate_active_preset(preset)

    @staticmethod
    def instance_edit_preset(preset: Preset | None = None):
        if presets_dialog := PresetsDialog.get_instance():
            presets_dialog.edit_preset(preset)

    def __init__(self, main_controller: VduAppController, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.setWindowTitle(tr('Presets'))
        self.main_controller = main_controller
        self.main_config = main_config
        self.content_controls_map: Dict[Tuple[str, str], QCheckBox] = {}
        self.resize(npx(1800), npx(1200))
        self.setMinimumSize(npx(1350), npx(600))
        layout = QVBoxLayout()
        self.setLayout(layout)

        dialog_splitter = QSplitter()
        dialog_splitter.setOrientation(Qt.Orientation.Horizontal)
        dialog_splitter.setHandleWidth(npx(10))
        layout.addWidget(dialog_splitter, stretch=1)

        preset_list_panel = QGroupBox()
        preset_list_panel.setMinimumWidth(npx(550))
        preset_list_panel.setFlat(True)
        preset_list_layout = QVBoxLayout()
        preset_list_panel.setLayout(preset_list_layout)
        preset_list_title = QLabel(tr("Presets"))
        preset_list_title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        preset_list_layout.addWidget(preset_list_title)
        self.preset_widgets_scroll_area = QScrollArea(parent=self)
        preset_widgets_content = QWidget()
        self.preset_widgets_layout = QVBoxLayout()
        self.preset_widgets_layout.setSpacing(0)
        preset_widgets_content.setLayout(self.preset_widgets_layout)
        self.preset_widgets_scroll_area.setWidget(preset_widgets_content)
        self.preset_widgets_scroll_area.setWidgetResizable(True)
        preset_list_layout.addWidget(self.preset_widgets_scroll_area)
        dialog_splitter.addWidget(preset_list_panel)

        main_controller.refresh_preset_menu()
        self.base_ini = ConfIni()  # Create a temporary holder of preset values
        main_controller.populate_ini_from_vdus(self.base_ini)

        self.populate_presets_display_list()

        self.edit_panel = QWidget(parent=self)
        edit_panel_layout = QHBoxLayout()
        self.edit_panel.setLayout(edit_panel_layout)
        self.edit_panel.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

        self.edit_choose_icon_button = PresetIconPickerButton()
        edit_panel_layout.addWidget(self.edit_choose_icon_button)

        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setToolTip(tr('Enter a new preset name.'))
        self.preset_name_edit.setClearButtonEnabled(True)
        self.preset_name_edit.textChanged.connect(self.change_edit_group_title)
        self.preset_name_edit.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z0-9][A-Za-z0-9_ .-]{0,60}")))

        self.vip_menu = QMenu()
        self.vip_menu.triggered.connect(self.vip_menu_triggered)
        edit_panel_layout.addWidget(self.preset_name_edit)
        self.vdu_init_button = ToolButton(VDU_POWER_ON_ICON_SOURCE, tr("Create VDU specific\nInitialization-Preset"), self)
        self.vdu_init_button.setMenu(self.vip_menu)
        self.vdu_init_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        edit_panel_layout.addWidget(self.vdu_init_button)

        self.editor_groupbox = QGroupBox()
        self.editor_groupbox.setFlat(True)
        self.editor_groupbox.setMinimumSize(npx(550), npx(768))
        self.editor_layout = QVBoxLayout()
        self.editor_layout.setSpacing(npx(20))
        self.editor_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        self.editor_title = QLabel(tr("New Preset:"))
        self.editor_title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.editor_layout.addWidget(self.editor_title)
        self.editor_groupbox.setLayout(self.editor_layout)

        self.editor_controls_widget = QScrollArea(parent=self)
        self.populate_editor_controls_widget()
        self.editor_layout.addWidget(self.edit_panel)

        self.controls_title_widget = self.editor_controls_prompt = QLabel(tr("Controls to include:"))
        self.controls_title_widget.setDisabled(True)
        self.editor_layout.addWidget(self.controls_title_widget)
        self.editor_layout.addWidget(self.editor_controls_widget)

        self.editor_transitions_widget = PresetTransitionWidget()
        if self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED):
            self.editor_layout.addItem(QSpacerItem(1, 10))
        else:
            self.editor_layout.addWidget(self.editor_transitions_widget)

        self.editor_at_time_widget = PresetScheduleAtTimeWidget()
        self.editor_layout.addWidget(self.editor_at_time_widget)

        self.editor_at_elevation_widget = PresetScheduleAtElevationWidget(self.main_config)
        self.editor_layout.addWidget(self.editor_at_elevation_widget)

        possibles = [self.editor_at_time_widget, self.editor_at_elevation_widget]
        for schedule_choice_widget in possibles:
            schedule_choice_widget.set_schedule_widgets(possibles)

        dialog_splitter.addWidget(self.editor_groupbox)
        dialog_splitter.setCollapsible(0, False)
        dialog_splitter.setCollapsible(1, False)
        dialog_splitter.setSizes([preset_list_panel.minimumSize().width(), self.editor_groupbox.minimumSize().width()])

        self.status_bar = QStatusBar()

        def _revert_callable() -> None:
            preset_widget = self.find_preset_widget(self.preset_name_edit.text().strip())
            if preset_widget is None:
                self.preset_name_edit.setText('')
            else:
                self.edit_preset(preset_widget.preset)

        self.edit_clear_button = StdButton(icon=si(self, StdPixmap.SP_DialogCancelButton), title=tr('Clear'),
                                           clicked=self.reset_editor,
                                           tip=tr("Clear edits and enter a new preset using the defaults."))
        self.edit_save_button = StdButton(icon=si(self, StdPixmap.SP_DialogSaveButton), title=tr('Save'), clicked=self.save_preset,
                                          tip=tr("Save current VDU settings to Preset."))
        self.edit_revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=tr('Revert'),
                                            clicked=_revert_callable,
                                            tip=tr("Abandon edits, revert VDU and Preset settings."))
        self.close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr('Close'), clicked=self.close)
        for button in (self.edit_clear_button, self.edit_save_button, self.edit_revert_button, self.close_button):
            self.status_bar.addPermanentWidget(button)
        layout.addWidget(self.status_bar)

        self.edit_choose_icon_button.set_preset(None)
        self.editor_controls_widget.setDisabled(True)
        self.editor_at_time_widget.setDisabled(True)
        self.editor_transitions_widget.setDisabled(True)
        self.editor_at_elevation_widget.setDisabled(True)
        self.edit_save_button.setDisabled(True)
        self.edit_revert_button.setDisabled(True)

        self.indicate_active_preset(self.main_controller.which_preset_is_active())
        self.editor_controls_widget.adjustSize()
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(npx(1200), npx(768))

    def populate_presets_display_list(self) -> None:
        for i in range(self.preset_widgets_layout.count() - 1, -1, -1):  # Remove existing entries
            if item := self.preset_widgets_layout.itemAt(i):
                w = item.widget()
                if isinstance(w, PresetItemWidget):
                    self.preset_widgets_layout.removeWidget(w)
                    w.deleteLater()
                else:
                    self.preset_widgets_layout.removeItem(item)
        for preset_def in self.main_controller.preset_controller.find_presets_map().values():  # Populate new entries
            self.preset_widgets_layout.addWidget(self.create_preset_widget(preset_def))
        self.preset_widgets_layout.addStretch(1)

    def reconfigure(self) -> None:
        self.populate_presets_display_list()
        existing_content = self.editor_controls_widget.takeWidget()
        existing_content.deleteLater() if existing_content is not None else None
        self.base_ini = ConfIni()
        self.main_controller.populate_ini_from_vdus(self.base_ini)
        self.populate_editor_controls_widget()
        self.reset_editor()
        self.editor_at_elevation_widget.configure_for_location(self.main_config.get_location())

    def reset_editor(self):
        self.preset_name_edit.setText('')
        self.edit_choose_icon_button.reset()
        for checkbox in self.content_controls_map.values():
            checkbox.setChecked(True)

    def status_message(self, message: str, timeout: int = 0) -> None:
        self.status_bar.showMessage(message, msecs=3000 if timeout == -1 else timeout)

    def vip_menu_triggered(self, action: QAction):
        vdu_stable_id = action.data()
        if MBox(MIcon.Information, msg=tr('Create an initialization-preset for {}.').format(action.text()),
                info=tr('Initialization-presets are restored at startup or when ever the VDU is subsequently detected.'),
                buttons=MBtn.Ok | MBtn.Cancel).exec() == MBtn.Cancel:
            return
        self.preset_name_edit.setText(vdu_stable_id)
        for (section, option), checkbox in self.content_controls_map.items():
            checkbox.setChecked(section == vdu_stable_id)

    def find_preset_widget(self, preset_name: str) -> PresetItemWidget | None:
        for i in range(self.preset_widgets_layout.count()):
            w = self.preset_widgets_layout.itemAt(i).widget()
            if isinstance(w, PresetItemWidget) and w.name == preset_name:
                return w
        return None

    def indicate_active_preset(self, preset: Preset | None = None):
        self.preset_widgets_layout.findChildren(PresetItemWidget)
        for i in range(self.preset_widgets_layout.count()):
            if item := self.preset_widgets_layout.itemAt(i):
                w = item.widget()
                if isinstance(w, PresetItemWidget):
                    w.update_timer_button()
                    w.indicate_active(preset is not None and w.name == preset.name)

    def populate_editor_controls_widget(self):
        container = self.editor_controls_widget
        container.setMinimumHeight(native_font_height(scaled=6))  # making this too big throws the parent layout out of wack
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.content_controls_map = {}
        self.vip_menu.clear()  # VIP - VDU Initialization Preset
        for count, vdu_section_name in enumerate(self.base_ini.data_sections()):
            vdu_name = self.main_controller.get_vdu_preferred_name(vdu_section_name)
            if count > 0:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                layout.addWidget(line)
            group_box = QGroupBox(vdu_name)
            group_box.setFlat(True)
            group_box.setToolTip(tr("Choose which settings to save for {}").format(vdu_name))
            group_layout = QHBoxLayout()
            group_box.setLayout(group_layout)
            for option in self.base_ini[vdu_section_name]:
                option_control = QCheckBox(translate_option(option))
                group_layout.addWidget(option_control)
                self.content_controls_map[(vdu_section_name, option)] = option_control
                option_control.setChecked(True)
            layout.addWidget(group_box)
            vip_action = QAction(f"{vdu_section_name} ({vdu_name})" if vdu_section_name != vdu_name else vdu_section_name,
                                 self.vip_menu)
            vip_action.setData(vdu_section_name)
            self.vip_menu.addAction(vip_action)
        container.setWidget(widget)

    def set_widget_values_from_preset(self, preset: Preset):
        self.preset_name_edit.setText(preset.name)
        self.edit_choose_icon_button.set_preset(preset)
        for key, item in self.content_controls_map.items():
            item.setChecked(preset.preset_ini.has_option(key[0], key[1]))
        if preset.preset_ini.has_section('preset'):
            self.editor_at_elevation_widget.clear()  # Clear both fields to stop any cross-field validation triggers.
            self.editor_at_time_widget.clear()
            self.editor_at_time_widget.setText(preset.get_at_time().strftime("%H:%M") if preset.get_at_time() else '')
            self.editor_at_elevation_widget.set_elevation_from_text(
                preset.preset_ini.get('preset', 'solar-elevation', fallback=None))
            self.editor_at_elevation_widget.set_required_weather_filename(
                preset.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None))
            self.editor_transitions_widget.set_transition_type(preset.get_transition_type())
            self.editor_transitions_widget.set_step_seconds(preset.get_step_interval_seconds())
            df = preset.get_daylight_factor()
            self.editor_at_elevation_widget.df_widget.setEnabled(df is not None)
            self.editor_at_elevation_widget.df_widget.df_input.setText(f"{df:.4f}" if df is not None else '')

    def has_changes(self, preset: Preset) -> bool:
        preset_ini_copy = preset.preset_ini.duplicate()
        self.populate_ini_from_gui(preset_ini_copy)  # get ini options from GUI checkbox and field values
        self.main_controller.populate_ini_from_vdus(preset_ini_copy, update_only=True)  # get current VDU values for ini options
        log_debug(f"has_changes {preset.preset_ini.diff(preset_ini_copy)=}") if log_debug_enabled else None
        return len(preset.preset_ini.diff(preset_ini_copy)) > 0

    def populate_ini_from_gui(self, preset_ini: ConfIni) -> None:  # initialise ini options based on GUI checkbox and field values
        for key, checkbox in self.content_controls_map.items():  # Populate ini options to indicate which settings need to be saved
            section, option = key
            if checkbox.isChecked():  # If this property is enabled, set its value
                if not preset_ini.has_section(section):
                    preset_ini.add_section(section)
                value = self.base_ini.get(section, option, fallback="%should not happen%")
                preset_ini.set(section, option, value)  # Just an initial value, it will be updated with the current VDU value later
            elif preset_ini.has_section(section) and preset_ini.has_option(section, option):
                preset_ini.remove_option(section, option)
        if not preset_ini.has_section('preset'):
            preset_ini.add_section('preset')
        if self.edit_choose_icon_button.last_selected_icon_path:
            preset_ini.set("preset", "icon", self.edit_choose_icon_button.last_selected_icon_path.as_posix())
        preset_ini.set('preset', 'at-time', self.editor_at_time_widget.text())
        preset_ini.set('preset', 'solar-elevation', format_solar_elevation_ini_text(self.editor_at_elevation_widget.elevation_key))
        if weather_filename := self.editor_at_elevation_widget.get_required_weather_filename():
            preset_ini.set('preset', 'solar-elevation-weather-restriction', weather_filename)
        elif preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None):
            preset_ini.remove_option('preset', 'solar-elevation-weather-restriction')  # Remove existing restriction from ini
        preset_ini.set('preset', 'transition-type', str(self.editor_transitions_widget.get_transition_type()))
        preset_ini.set('preset', 'transition-step-interval-seconds', str(self.editor_transitions_widget.get_step_seconds()))
        preset_ini.set('preset', 'daylight-factor', str(self.editor_at_elevation_widget.df_widget.df_input.text()))

    def get_preset_widgets(self) -> List[PresetItemWidget]:
        return [self.preset_widgets_layout.itemAt(i).widget()
                for i in range(0, self.preset_widgets_layout.count() - 1)
                if isinstance(self.preset_widgets_layout.itemAt(i).widget(), PresetItemWidget)]

    def get_preset_names_in_order(self) -> List[str]:
        return [w.name for w in self.get_preset_widgets()]

    def add_preset_widget(self, preset_widget: PresetItemWidget) -> None:
        # Insert before trailing stretch item
        self.preset_widgets_layout.insertWidget(self.preset_widgets_layout.count() - 1, preset_widget)

    def up_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index > 0:
            self.preset_widgets_layout.removeWidget(target_widget)
            self.preset_widgets_layout.insertWidget(index - 1, self.create_preset_widget(preset))
            target_widget.deleteLater()
            self.main_controller.save_preset_order(self.get_preset_names_in_order())
            self.preset_widgets_scroll_area.updateGeometry()

    def down_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index < self.preset_widgets_layout.count() - 2:
            self.preset_widgets_layout.removeWidget(target_widget)
            self.preset_widgets_layout.insertWidget(index + 1, self.create_preset_widget(preset))
            target_widget.deleteLater()
            self.main_controller.save_preset_order(self.get_preset_names_in_order())
            self.preset_widgets_scroll_area.updateGeometry()

    def restore_preset(self, preset: Preset, immediately: bool = True) -> None:
        self.main_controller.restore_preset(preset, immediately=immediately)

    def delete_preset(self, preset: Preset, target_widget: QWidget) -> None:
        if MBox(MIcon.Question, msg=tr('Delete {}?').format(preset.name),
                buttons=MBtn.Ok | MBtn.Cancel, default=MBtn.Cancel).exec() == MBtn.Cancel:
            return
        self.main_controller.delete_preset(preset)
        self.preset_widgets_layout.removeWidget(target_widget)
        target_widget.deleteLater()
        self.main_controller.save_preset_order(self.get_preset_names_in_order())
        self.preset_name_edit.setText('')
        self.preset_widgets_scroll_area.updateGeometry()
        self.status_message(tr("Deleted {}").format(preset.name), timeout=-1)

    def change_edit_group_title(self) -> None:
        changed_text = self.preset_name_edit.text()
        if disable_controls := changed_text.strip() == "":
            self.edit_revert_button.setDisabled(True)
            self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include:"))
        else:
            if self.find_preset_widget(changed_text):  # Already exists
                self.edit_revert_button.setDisabled(False)
                self.editor_title.setText(tr("Edit {}:").format(changed_text))
            else:
                self.edit_revert_button.setDisabled(True)
                self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include in {}:").format(changed_text))
        self.editor_controls_widget.setDisabled(disable_controls)
        self.editor_transitions_widget.setDisabled(disable_controls)
        self.editor_at_time_widget.setDisabled(disable_controls)
        self.editor_at_elevation_widget.setDisabled(disable_controls)
        self.controls_title_widget.setDisabled(disable_controls)
        self.editor_transitions_widget.setDisabled(disable_controls)
        self.edit_save_button.setDisabled(disable_controls)
        self.edit_clear_button.setDisabled(disable_controls)

    def edit_preset(self, preset: Preset) -> None:

        def _begin_editing(worker: BulkChangeWorker | None = None) -> None:
            if worker is None or worker.completed:
                self.set_widget_values_from_preset(preset)
            else:
                self.status_message(tr(f"Failed to restore {preset.name} for editing."))
            self.setEnabled(True)

        if preset:
            self.setDisabled(True)  # Stop any editing until after the preset is restored.
            self.main_controller.restore_preset(preset, finished_func=_begin_editing, immediately=True)

    def save_preset(self, _: bool = False, from_widget: PresetItemWidget | None = None,
                    quiet: bool = False) -> MBtn.Ok | MBtn.Cancel:
        preset: Preset | None = None
        widget_to_replace: PresetItemWidget | None = None
        if from_widget:  # A from_widget is requesting that the Preset's VDU current settings be updated.
            widget_to_replace = None  # Updating from widget, no change to icons or symbols, so no need to update the widget.
            preset = from_widget.preset  # Just update the widget's preset from the VDUs current settings
        elif preset_name := self.preset_name_edit.text().strip().replace('_',
                                                                         ' '):  # Saving from the save button, this may be new Preset or update.
            if widget_to_replace := self.find_preset_widget(preset_name):  # Already exists, update preset, replace widget
                preset = widget_to_replace.preset  # Use the widget's existing Preset.
            else:
                preset = Preset(preset_name)  # New Preset
        if preset is None or (quiet and not self.has_changes(preset)):  # Not found (weird), OR don't care if no changes made.
            return MBtn.Ok  # Nothing more to do, everything is OK

        preset_path = ConfIni.get_path(proper_name('Preset', preset.name))
        if preset_path.exists():  # Existing Preset
            if from_widget:  # The from_widget PresetWidget is initiating an update to the Preset from the VDUs settings.
                question = tr('Update existing {} preset with current monitor settings?').format(preset.name)
            else:  # The Preset Editor tab is modifying a Preset and it's PresetWidget.
                question = tr("Replace existing '{}' preset?").format(preset.name)
        else:  # New Preset
            question = tr("Save current edit?")
        answer = MBox(MIcon.Question, msg=question, buttons=MBtn.Save | MBtn.Discard | MBtn.Cancel, default=MBtn.Save).exec()
        if answer == MBtn.Discard:
            self.reset_editor()
            return MBtn.Ok
        elif answer == MBtn.Cancel:
            return MBtn.Cancel

        self.populate_ini_from_gui(preset.preset_ini)  # Initialises the options from the GUI, but does not get the VDU values.
        self.main_controller.populate_ini_from_vdus(preset.preset_ini, update_only=True)  # populate from VDU control values.

        if duplicated_presets := [other_preset for other_name, other_preset in self.main_controller.find_presets_map().items()
                                  if other_name != preset.name
                                     and preset.preset_ini.diff(other_preset.preset_ini, vdu_settings_only=True) == {}]:
            if MBox(MIcon.Warning, msg=tr("Duplicates existing Preset {}, save anyway?").format(duplicated_presets[0].name),
                    buttons=MBtn.Save | MBtn.Cancel, default=MBtn.Cancel).exec() == MBtn.Cancel:
                return MBtn.Cancel

        self.main_controller.save_preset(preset)

        if not from_widget:  # Which means the editor needs to update/create the PresetWidget, its icon, transition, weather, etc
            replacement_widget = self.create_preset_widget(preset)  # Create a new widget - an easy way to update the icon.
            if widget_to_replace:  # Existing widget need to update
                self.preset_widgets_layout.replaceWidget(widget_to_replace, replacement_widget)
                # The deleteLater removes the widget from the tree so that it is no longer findable and can be freed.
                widget_to_replace.deleteLater()
                self.make_visible()
            else:  # Must be a new Preset - create a new widget
                self.add_preset_widget(replacement_widget)
                self.main_controller.save_preset_order(self.get_preset_names_in_order())
                self.preset_widgets_scroll_area.ensureWidgetVisible(replacement_widget)
                QApplication.processEvents()  # TODO figure out why this does not work

        self.reset_editor()
        self.status_message(tr("Saved {}").format(preset.name), timeout=-1)
        return MBtn.Save

    def create_preset_widget(self, preset) -> PresetItemWidget:
        return PresetItemWidget(preset, restore_action=self.restore_preset, save_action=self.save_preset,
                                delete_action=self.delete_preset, edit_action=self.edit_preset,
                                up_action=self.up_action, down_action=self.down_action,
                                protect_nvram=self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED))

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            self.repaint()
            self.vdu_init_button.refresh_icon()
        return super().event(event)

    def closeEvent(self, event) -> None:
        if self.save_preset(quiet=True) == MBtn.Cancel:
            event.ignore()
        else:
            self.reset_editor()
            super().closeEvent(event)


def exception_handler(e_type, e_value, e_traceback) -> None:
    """Overarching error handler in case something unexpected happens."""
    log_error("\n" + ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    MBox(MIcon.Critical, msg=tr('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))),
         details=tr('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback)))).exec()




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


LUX_SUNLIGHT_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <circle cx="12" cy="12" r="4" /> <line x1="3.5" y1="12" x2="5.5" y2="12" />
        <line x1="18.5" y1="12" x2="20.5" y2="12"/> <line x1="12" y1="3.5" x2="12" y2="5.5"/>
        <line x1="12" y1="18.5" x2="12" y2="20.5"/> <line x1="6" y1="6" x2="7.41" y2="7.41"/>
        <line x1="16.59" y1="16.59" x2="18.01" y2="18.01"/> <line x1="18" y1="6" x2="16.59" y2="7.41"/>
        <line x1="7.41" y1="16.59" x2="6" y2="18.01"/>
    </g>
</svg>"""

LUX_DAYLIGHT_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <path d="M6.5,11 a1,1 0 0,1 7,0 " /> <path d="M6.5,11 a1,1 0 0,0 0,6.5 " /> 
        <path d="M14,11 a1,1 0 0,1 0,6.5 " /> <path d="M7,17.5 l6.5,0" stroke-linecap="square"/> 
        <path d="M12.5,8 a1,1 0 0,1 5,4 "/> <path d="M15,10 m 0,-6 l 0,1.25"/>
        <path d="M15,10 m 3.5,-3.5 l 1,-1"/> <path d="M15,10 m -3.5,-3.5 l -1,-1"/>
        <path d="M15,10 m 3.5,3.5 l 1,1"/> <path d="M15,10 m 5,0 l 1.25,0"/>
    </g>
</svg>"""

LUX_OVERCAST_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <path d="M6.5,11 a1,1 0 0,1 7,0 " /> <path d="M6.5,11 a1,1 0 0,0 0,6.5 " />
        <path d="M14,11 a1,1 0 0,1 0,6.5 " /> <path d="M12.5,8.5 a1,1 0 0,1 5,-.5 " />
        <path d="M17.5,8.5 a1,1 0 0,1 0,5.5 " stroke-linecap="square"/>
        <path d="M7,17.5 l6.5,0" stroke-linecap="square"/>
    </g>
</svg>"""

LUX_TWILIGHT_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <path d="M8.25,15 A3.75,3.25 0 0,1 15.75,15 " stroke-linecap="square"/>
        <line x1="12" y1="7.5" x2="12" y2="9.5"/> <line x1="6" y1="10" x2="7.41" y2="11.41"/>
        <line x1="18" y1="10" x2="16.59" y2="11.41"/> <line x1="5" y1="17." x2="19" y2="17"/>
    </g>
</svg>"""

LUX_SUBDUED_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-width="1.25" stroke-linecap="round">
        <circle cx="12" cy="11" r="4.5"/> <rect x="10" y="15.4" width="4" rx="1" ry="1" height="2.6"/>
        <line x1="4" y1="12" x2="5" y2="12" /> <line x1="19" y1="12" x2="20" y2="12"/>
        <line x1="12" y1="3" x2="12" y2="4"/> <line x1="5.75" y1="5.25" x2="6.75" y2="6.25"/>
        <line x1="18.5" y1="5.25" x2="17.5" y2="6.25"/>
    </g>
</svg>"""

LUX_DARK_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<!-- Copyright 2024 Michael Hamilton License Creative Commons - Attribution CC BY -->
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25" 
       transform="translate(24, 24), scale(-1,-1)">
        <path d="M17.5 7.5   A6.25 6.25   0 1 0   16.5 16.5   5 5   0 1 1   17.5 7.5z"/>
    </g>
</svg>
"""


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


class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def invoke(main_controller: VduAppController) -> None:
        if AboutDialog.exists():
            AboutDialog.get_instance().refresh_content()
            AboutDialog.show_existing_dialog()
        else:
            AboutDialog(main_controller)

    @staticmethod
    def refresh():
        if AboutDialog.exists() and AboutDialog.get_instance().isVisible():
            AboutDialog.get_instance().refresh_content()
        else:
            log_debug("About dialog - no refresh - not visible") if log_debug_enabled else None

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.main_controller = main_controller
        self.refresh_content()
        self.setModal(False)
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh_content(self):
        self.setWindowTitle(tr('About'))
        self.setTextFormat(Qt.TextFormat.AutoText)
        self.setText(tr('About vdu_controls'))
        path = find_locale_specific_file("about_{}.txt")
        if path:
            with open(path, encoding='utf-8') as about_for_locale:
                about_text = about_for_locale.read().format(
                    VDU_CONTROLS_VERSION=VDU_CONTROLS_VERSION, IP_ADDRESS_INFO_URL=IP_ADDRESS_INFO_URL,
                    WEATHER_FORECAST_URL=WEATHER_FORECAST_URL)
        else:
            about_text = ABOUT_TEXT
        if self.main_controller and self.main_controller.ddcutil:
            counts_str = ','.join((str(v) for v in DdcutilAggregator.vcp_write_counters.values())) if len(DdcutilAggregator.vcp_write_counters) else '0'
            about_text += (f"<hr><p><small>desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')}; "
                           f"platform: {os.environ.get('XDG_SESSION_TYPE', default='unknown')} "
                           f"({QApplication.platformName()}, qt-{QtCore.qVersion()});<br/>"
                           f"ddcutil-interface: {self.main_controller.ddcutil.ddcutil_version_info()[0]}; "
                           f"ddcutil: {self.main_controller.ddcutil.ddcutil_version_info()[1]} (writes: {counts_str});</small>")
        self.setInformativeText(about_text)
        self.setIcon(MIcon.Information)




@contextmanager  # https://stackoverflow.com/questions/31501487/non-blocking-lock-with-with-statement
def non_blocking_lock(lock: threading.RLock) -> threading.RLock:  # Provide a way to use a with-statement with non-blocking locks
    acquire_succeeded = lock.acquire(False)  # acquire_succeeded will be False if the lock is already locked.
    try:
        yield lock if acquire_succeeded else None  # return None to the with if the lock was not acquired
    finally:
        if acquire_succeeded:
            lock.release()


class VduAppController(QObject):  # Main controller containing methods for high level operations

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.find_vdu_config_files()
        self.application_lock = threading.RLock()  # thread level, thread-safe, access lock
        self.main_config = main_config
        self.ddcutil: DdcutilAggregator | None = None
        self.main_window: VduAppWindow | None = None
        self.vdu_controllers_map: Dict[VduStableId, VduController] = {}
        self.preset_controller = PresetController()
        self.detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.previously_detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.refresh_data_task: WorkerThread | None = None
        self.weather_query: WeatherQuery | None = None
        self.preset_transition_workers: List[BulkChangeWorker] = []  # Not sure if this actually needs to be a list.
        self.lux_auto_controller: LuxAutoController | None = LuxAutoController(self) if self.main_config.is_set(
            ConfOpt.LUX_OPTIONS_ENABLED) else None

        def respond_to_unix_signal(signal_number: int) -> None:
            if signal_number == signal.SIGHUP:
                self.start_refresh(external_event=True)
            elif PRESET_SIGNAL_MIN <= signal_number <= PRESET_SIGNAL_MAX:
                if preset := self.preset_controller.get_preset(signal_number - PRESET_SIGNAL_MIN):
                    immediately = PresetTransitionFlag.SIGNAL not in preset.get_transition_type()
                    log_info(f"Signaled for {preset.name=} {preset.get_transition_type()=} {immediately=} {thread_pid()=}")
                    # Signals occur outside the GUI thread - initiate the restore in the GUI thread
                    self.restore_preset(preset=preset, immediately=immediately, background_activity=True)
                else:
                    # Cannot raise a Qt alert inside the signal handler in case another signal comes in.
                    log_warning(f"ignoring {signal_number=}, no preset associated with that signal number.")

        global unix_signal_handler
        unix_signal_handler.received_unix_signal_qtsignal.connect(respond_to_unix_signal)

    def configure_application(self, main_window: VduAppWindow | None = None, check_schedule: bool = True):
        try:
            log_info(f"Configuring application (reconfiguring={main_window is None})...")
            for controller in self.vdu_controllers_map.values():
                controller.no_longer_in_use = True
            if main_window is not None:  # First time through
                assert self.main_window is None
                self.main_window = main_window
            if self.main_window.main_panel is not None:
                self.main_window.indicate_busy(True)
                QApplication.processEvents()
            log_debug("configure: try to obtain application_lock", trace=False) if log_debug_enabled else None
            with self.application_lock:
                log_debug("configure: holding application_lock") if log_debug_enabled else None
                ScheduleWorker.dequeue_all()
                if self.lux_auto_controller is not None:
                    self.lux_auto_controller.stop_worker()
                    self.lux_auto_controller.lux_slider = None
                self.stop_any_transitioning_presets()
                log_set_syslog(self.main_config.is_set(ConfOpt.SYSLOG_ENABLED))
                self.create_ddcutil()
                self.preset_controller.reinitialize()
                self.main_window.initialise_app_icon()
                self.main_window.create_main_control_panel()
                SettingsDialog.reconfigure_instance(self.get_vdu_configs())
                self.restore_vdu_initialization_presets()
                self.schedule_presets()
                ScheduleWorker.check() if check_schedule else None
            log_debug("configure: released application_lock") if log_debug_enabled else None
            if self.main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED):
                if self.lux_auto_controller is not None:
                    self.lux_auto_controller.initialize_from_config()
                    LuxDialog.reconfigure_instance()
            self.main_window.update_status_indicators()
        finally:
            if self.main_window is not None:
                self.main_window.indicate_busy(False)
        log_info("Completed configuring application")

    def stop_any_transitioning_presets(self):
        for running_worker in [worker for worker in self.preset_transition_workers if worker.isRunning()]:
            running_worker.stop()
            log_debug(f"Stop requested for {running_worker.name=} {running_worker.start_time=!s}")
        self.preset_transition_workers.clear()

    def create_ddcutil(self):

        if self.main_config.is_set(ConfOpt.DBUS_CLIENT_ENABLED) and self.main_config.is_set(ConfOpt.DBUS_EVENTS_ENABLED):

            def _vdu_connectivity_changed_callback(edid_encoded: str, event_type: int, flags: int):
                values_only = False
                if not DdcEventType.UNKNOWN.value <= event_type <= DdcEventType.DISPLAY_DISCONNECTED.value:
                    log_warning(f"Connected VDUs event - unknown {event_type=} treating as DPMS_UNKNOWN.")
                    event_type = DdcEventType.UNKNOWN.value
                if event_type == DdcEventType.DPMS_ASLEEP.value:
                    log_info(f"Connected VDUs event {DdcEventType(event_type)} {flags=} {edid_encoded:.30}...")
                    return  # Don't do anything, the VDUs are just asleep.
                elif event_type == DdcEventType.LAPTOP_BRIGHTNESS_CHANGE.value:
                    log_info(f"Laptop event {edid_encoded:.30}...")
                    values_only = True
                    # self.lux_auto_controller.set_auto(False) - we don't do this for any other manual change - so do nothing?
                    # could do something specific here - but the following refresh will cover it.
                self.start_refresh(external_event=True, values_only=values_only)

            change_handler = _vdu_connectivity_changed_callback
            log_debug("Enabled callback for VDU-connectivity-change D-Bus signals")
        else:
            change_handler = None  # This will force disabling the eventing/polling inside the server, not just the client.

        try:
            self.ddcutil = DdcutilAggregator(common_args=self.main_config.get_ddcutil_extra_args(),
                                             prefer_dbus_client=self.main_config.is_set(ConfOpt.DBUS_CLIENT_ENABLED),
                                             connected_vdus_changed_callback=change_handler)
            if self.main_config.is_set(ConfOpt.LAPTOP_PANEL_ENABLED):
                try:
                    self.ddcutil.add_ddcutil_emulator(DdcutilPanelImpl(callback=change_handler))
                except Exception as e:
                    MBox(MIcon.Critical, msg=tr('Laptop Support: brightessctrl command failed'),
                         info='Check that brightessctrl is installed and is working.', details=str(e)).exec()
            if emulator := self.main_config.ini_content.get(ConfOpt.DDCUTIL_EMULATOR.conf_section,
                                                            ConfOpt.DDCUTIL_EMULATOR.conf_name, fallback=None):
                common_args = self.main_config.get_ddcutil_extra_args()
                log_info(f"add_ddcutil_emulator: {emulator} {common_args}")
                self.ddcutil.add_ddcutil_emulator(DdcutilEmulatorImpl(emulator, common_args))
        except (subprocess.SubprocessError, ValueError, re.error, OSError, DdcutilServiceNotFound) as e:
            self.main_window.show_no_controllers_error_dialog(e)

    def detect_vdus(self) -> Tuple[List[Tuple[str, str, str, str]], Exception | None]:
        if self.ddcutil is None:
            return [], None
        ddcutil_problem = None
        try:
            self.detected_vdu_list = []
            log_debug("Detecting connected monitors, looping detection until it stabilizes.") if log_debug_enabled else None
            # Loop in case the session is initializing/restoring which can make detection unreliable.
            # Limit to a reasonable number of iterations.
            for i in range(1, 11):
                prev_num = len(self.detected_vdu_list)
                self.detected_vdu_list = self.ddcutil.detect_vdus()
                if prev_num == len(self.detected_vdu_list):
                    log_info(f"Number of detected monitors is stable at {len(self.detected_vdu_list)} (loop={i})")
                    break
                elif prev_num > 0:
                    log_info(f"Number of detected monitors changed from {prev_num} to {len(self.detected_vdu_list)} (loop={i})")
                time.sleep(1.5)
        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
            log_error(e)
            ddcutil_problem = e
        self.previously_detected_vdu_list = self.detected_vdu_list
        return self.detected_vdu_list, ddcutil_problem

    def initialize_vdu_controllers(self) -> None:
        assert is_running_in_gui_thread()
        if self.ddcutil is None:
            return
        detected_vdu_list, ddcutil_problem = self.detect_vdus()
        self.vdu_controllers_map = {}
        main_panel_error_handler = self.main_window.get_main_panel().show_vdu_exception
        for vdu_number, manufacturer, model_name, vdu_serial in detected_vdu_list:
            controller = None
            while True:
                try:
                    controller = VduController(vdu_number, model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, self.edit_config, main_panel_error_handler, VduController.NORMAL_VDU)
                except (subprocess.SubprocessError, ValueError, re.error, OSError, DdcutilDisplayNotFound) as e:
                    log_error(f"Problem creating controller for {vdu_number=} {model_name=} {vdu_serial=} exception={e}",
                              trace=True)
                    remedy = self.main_window.ask_for_vdu_controller_remedy(vdu_number, model_name, vdu_serial)
                    if remedy == VduController.NORMAL_VDU:
                        time.sleep(1.0)  # Slow things down in case something is wrong with the GUI or VDU interactions.
                        continue  # Loop and retry as a normal VDU
                    controller = VduController(vdu_number, model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, self.edit_config, main_panel_error_handler, remedy)
                    controller.write_template_config_files()
                break  # Normally expect to just pass through the loop once
            if controller is not None:
                self.vdu_controllers_map[controller.vdu_stable_id] = controller
        if len(self.vdu_controllers_map) == 0:
            if self.main_config.is_set(ConfOpt.WARNINGS_ENABLED):
                self.main_window.show_no_controllers_error_dialog(ddcutil_problem)
        if self.main_config.is_set(ConfOpt.ORDER_BY_NAME):
            self.vdu_controllers_map = {
                c.vdu_stable_id: c for c in sorted(self.vdu_controllers_map.values(), key=VduController.get_vdu_preferred_name)}

    def settings_changed(self, changed_settings: List) -> None:
        if changed_settings is None:  # Special value - means settings have been reset/removed - needs restart.
            self.restart_application(tr("A settings reset requires vdu_controls to restart."))
            return
        for setting in ConfOpt:
            if setting.restart_required and (setting.conf_section, setting.conf_name) in changed_settings:
                self.restart_application(
                    tr("The change to the {} option requires vdu_controls to restart.").format(tr(setting.conf_name)))
                return
        self.main_config.reload()
        log_set_syslog(self.main_config.is_set(ConfOpt.SYSLOG_ENABLED))
        log_set_debug(self.main_config.is_set(ConfOpt.DEBUG_ENABLED))
        log_info("Reconfiguring due to settings change.")
        self.configure_application()

    def edit_config(self, config_name: str | None = None) -> None:
        SettingsDialog.invoke(self.main_config, self.get_vdu_configs(), self.settings_changed)
        SettingsDialog.edit_config(config_name if config_name else self.main_config.config_name)

    def show_presets_dialog(self, preset: Preset | None = None) -> None:
        PresetsDialog.invoke(self, self.main_config)
        if preset:
            PresetsDialog.instance_edit_preset(preset)

    def get_vdu_configs(self) -> List[VduControlsConfig]:
        return [vdu.config for vdu in self.vdu_controllers_map.values() if vdu.config is not None]

    def create_config_files(self) -> None:
        for controller in self.vdu_controllers_map.values():
            controller.write_template_config_files()

    def lux_auto_action(self) -> None:
        if self.lux_auto_controller:
            try:
                self.main_window.setDisabled(True)
                self.lux_auto_controller.toggle_auto()
                self.main_window.update_status_indicators()
            finally:
                self.main_window.setDisabled(False)

    def lux_check_action(self) -> None:
        if self.lux_auto_controller and self.lux_auto_controller.is_auto_enabled():
            self.lux_auto_controller.adjust_brightness_now()

    def start_refresh(self, external_event: bool = False, values_only: bool = False) -> None:

        def _update_from_vdu(worker: WorkerThread) -> None:
            if self.ddcutil is not None:
                with non_blocking_lock(self.application_lock) as acquired_lock:
                    if acquired_lock:  # If acquired_lock is not None, then we have successfully acquired the lock.
                        log_debug(f"_update_from_vdu: holding application_lock") if log_debug_enabled else None
                        try:
                            log_info(f"Refresh commences: {external_event=} {values_only=}") if log_debug_enabled else None
                            if values_only:
                                self.detected_vdu_list = self.ddcutil.detect_vdus()  # TODO Not sure why this is necessary.
                            else:
                                self.ddcutil.refresh_connection()
                                self.detected_vdu_list = self.ddcutil.detect_vdus()
                                self.restore_vdu_initialization_presets()
                            for control_panel in self.main_window.get_main_panel().vdu_control_panels.values():
                                if control_panel.controller.get_full_id() in self.detected_vdu_list:
                                    control_panel.refresh_from_vdu()
                        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
                            if self.refresh_data_task.work_exception is None:
                                self.refresh_data_task.work_exception = VduException(vdu_description="unknown", operation="unknown",
                                                                                     exception=e)
                    else:
                        log_info(f"Application is already busy, can't do a refresh ({external_event=})")
                        worker.stop()  # Stop the thread - which also indicates we did not acquire the lock.
                        return  # Prevents logging unlock (because we don't have the lock if we reach here).
                log_debug(f"_update_from_vdu: released application_lock") if log_debug_enabled else None

        def _update_ui_view(worker: WorkerThread) -> None:
            # Invoke when the worker thread completes. Runs in the GUI thread and can refresh remaining UI views.
            if worker.stop_requested:
                return  # in this case, this means the worker never started anything
            try:  # No need for locking in here - running in the GUI thread effectively single threads the operation.
                assert self.refresh_data_task is not None and is_running_in_gui_thread()
                log_debug(f"Refresh - update UI view {external_event=} {values_only=}") if log_debug_enabled else None
                main_panel = self.main_window.get_main_panel()
                if self.refresh_data_task.work_exception is not None:
                    log_debug(f"Refresh - update UI view - exception {self.refresh_data_task.work_exception} {external_event=}")
                    if not external_event:
                        main_panel.show_vdu_exception(self.refresh_data_task.work_exception, can_retry=False)
                if not values_only:
                    if len(self.detected_vdu_list) == 0 or self.detected_vdu_list != self.previously_detected_vdu_list or (
                            external_event and False):
                        log_info(f"Reconfiguring: detected={self.detected_vdu_list} previously={self.previously_detected_vdu_list}")
                        self.configure_application(check_schedule=False)  # May cause a further refresh?
                        self.previously_detected_vdu_list = self.detected_vdu_list
                    ScheduleWorker.check()  # immediately active the currently applicable preset
                    if self.lux_auto_controller:
                        if LuxDialog.exists():
                            LuxDialog.get_instance().reconfigure()  # Incase the number of connected monitors has changed.
                        if self.lux_auto_controller.is_auto_enabled():
                            self.lux_auto_controller.adjust_brightness_now()
            finally:
                self.main_window.indicate_busy(False)

        if not is_running_in_gui_thread():  # TODO this appears to never be true - remove???
            log_debug(f"Re-invoke start_refresh() in GUI thread {external_event=}") if log_debug_enabled else None
            self.main_window.run_in_gui_thread(partial(self.start_refresh, external_event))
            return
        self.refresh_data_task = WorkerThread(task_body=_update_from_vdu, task_finished=_update_ui_view)
        self.refresh_data_task.start()
        time.sleep(0.1)  # Sleep a bit to see if we acquire the application lock
        if not self.refresh_data_task.stop_requested:  # if the thread has already stopped, it never acquired the application_lock
            self.main_window.indicate_busy(True)  # Refresh has probably commenced, give the user some feedback

    def restore_preset(self, preset: Preset, finished_func: Callable[[BulkChangeWorker], None] | None = None,
                       immediately: bool = False, background_activity: bool = False, initialization_preset: bool = False) -> None:
        if initialization_preset:
            background_activity = True
            immediately = True
        elif self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED):
            immediately = True
        # Starts the restore, but it will complete in the worker thread
        if not is_running_in_gui_thread():  # Transfer this request into the GUI thread
            log_debug(f"restore_preset: '{preset.name}' transferring task to GUI thread") if log_debug_enabled else None
            self.main_window.run_in_gui_thread(partial(self.restore_preset, preset, finished_func,
                                                       immediately, background_activity, initialization_preset))
            return

        log_debug(f"restore_preset: '{preset.name}' try to obtain application_lock", trace=False) if log_debug_enabled else None
        with self.application_lock:  # The lock prevents a transition firing when the GUI/app is reconfiguring

            def _update_progress(worker_thread: BulkChangeWorker) -> None:
                preset.in_transition_step += 1
                self.main_window.show_preset_status(
                    tr("Transitioning to preset {} (elapsed time {} seconds)...").format(
                        preset.name, f"{worker_thread.total_elapsed_seconds:.2f}"))
                #self.transitioning_dummy_preset.update_progress() if self.transitioning_dummy_preset else None
                self.main_window.update_status_indicators(preset)

            def _restore_finished_callback(worker_thread: BulkChangeWorker) -> None:
                # self.transitioning_dummy_preset = None
                if worker_thread.work_exception is not None and not background_activity:  # if it's a GUI request, ask about retry
                    if self.main_window.get_main_panel().show_vdu_exception(worker_thread.work_exception, can_retry=True):
                        self.restore_preset(preset, finished_func=finished_func, immediately=immediately)  # Try again, new thread
                        return  # Don't do anything more, the new thread will take over from here
                preset.in_transition_step = 0
                self.main_window.indicate_busy(False)
                if not initialization_preset:
                    if self.main_window.tray is not None:
                        self.main_window.refresh_tray_menu()
                    if worker_thread.completed:
                        with open(CURRENT_PRESET_NAME_FILE, 'w', encoding="utf-8") as cps_file:
                            cps_file.write(preset.name)
                        self.main_window.update_status_indicators(preset)
                        if worker_thread.change_count != 0:
                            self.main_window.show_preset_status(tr("Restored {} (elapsed time {} seconds)").format(
                                preset.name, f"{worker_thread.total_elapsed_seconds:.2f}"))
                            if (self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED)
                                    and preset.get_transition_type() != PresetTransitionFlag.NONE):
                                log_warning(
                                    f"restore-preset: protect-nvram prevents '{preset.name}' from stepping, changes are immediate.")
                        else:
                            self.main_window.show_preset_status(tr("Already on Preset {} (no changes)").format(preset.name))
                        if df := preset.get_daylight_factor():
                            log_info(f"Daylight-Factor {df:.4f} read from Preset {preset.name}")
                            LuxMeterSemiAutoDevice.set_daylight_factor(df, persist=True)
                    else:  # Interrupted or exception:
                        self.main_window.update_status_indicators()
                        self.main_window.show_preset_status(tr("Interrupted restoration of {}").format(preset.name))
                if finished_func is not None:
                    finished_func(worker_thread)

            log_debug(f"restore_preset: '{preset.name}' holding application_lock", trace=False) if log_debug_enabled else None
            if not immediately:
                self.main_window.show_preset_status(tr("Transitioning to preset {}").format(preset.name))
                self.main_window.update_status_indicators(preset)  # TODO - create a transitioning indicator
            self.main_window.indicate_busy(True, lock_controls=immediately)
            preset.load()
            bulk_changer = BulkChangeWorker('RestorePreset', self, _update_progress, _restore_finished_callback,
                                            step_interval=0.0 if immediately else 5.0,
                                            ignore_others=initialization_preset, context=preset)
            for vdu_stable_id in self.get_vdu_stable_id_list():
                if vdu_stable_id in preset.preset_ini:
                    for vcp_capability in self.get_enabled_capabilities(vdu_stable_id):
                        property_name = vcp_capability.property_name()
                        if property_name in preset.preset_ini[vdu_stable_id]:
                            if vcp_capability.vcp_type == CONTINUOUS_TYPE:
                                final_value = preset.preset_ini.getint(vdu_stable_id, property_name)
                            else:
                                final_value = int(preset.preset_ini[vdu_stable_id][property_name], 16)
                            bulk_changer.add_item(BulkChangeItem(vdu_stable_id, vcp_capability.vcp_code, final_value,
                                                                 transition=vcp_capability.can_transition))
            self.preset_transition_workers.append(bulk_changer)
            log_debug(f"restore_preset: '{preset.name}' handover to WorkerThread") if log_debug_enabled else None
            bulk_changer.start()
            if initialization_preset:  # Don't allow anything else until it's finished
                bulk_changer.wait()
        log_debug(f"restore_preset: '{preset.name}' released application_lock") if log_debug_enabled else None

    def restore_vdu_initialization_presets(self):
        # Find presets that match the name of each VDU name+serial and restore them...
        for stable_id in self.vdu_controllers_map.keys():
            for preset in self.preset_controller.find_presets_map().values():
                preset_proper_name = proper_name(preset.name)
                if stable_id == preset_proper_name:
                    log_info(f"Found initialization-preset for {stable_id}")

                    def _restored_initialization_preset(worker: BulkChangeWorker) -> None:
                        if worker.work_exception is not None:
                            log_error(f"Error during restoration of '{preset.name}'")
                            self.status_message(tr("Error during restoration preset {}").format(preset.name), timeout=5)
                            return
                        log_info(f"Restored initialization-preset '{worker.context.name}'")
                        message = tr("Restored I-Preset {}").format(worker.context.name)
                        self.status_message(message, timeout=5)
                        self.main_window.splash_message_qtsignal.emit(message)
                        time.sleep(1.0)  # Pause to give the message time to display - TODO find non-delaying solution
                        self.main_window.update_status_indicators()  # Refresh to restore other non-init preset icons

                    self.restore_preset(preset, finished_func=_restored_initialization_preset, initialization_preset=True)

    def schedule_create_timetable(self, start_of_day: datetime, location: GeoLocation) -> Dict[datetime, Preset]:
        log_debug(f"Create preset timetable for {start_of_day}") if log_debug_enabled else None
        timetable_for_day: Dict[datetime, Preset] = {}  # Create a timetable for the entire day from 00:00:00 to 23:59:59
        time_elevation_map = create_elevation_map(start_of_day, latitude=location.latitude, longitude=location.longitude)
        for preset in self.preset_controller.find_presets_map().values():
            if elevation_key := preset.get_solar_elevation():
                if elevation_data := time_elevation_map.get(elevation_key):
                    preset.elevation_time_today = elevation_data.when
                    timetable_for_day[elevation_data.when] = preset
                else:
                    log_debug(f"schedule_create_timetable: Skipped preset '{preset.name}' {elevation_key} degrees,"
                              " the sun does not reach that elevation today.")
            if at_time := preset.get_at_time():
                timetable_for_day[at_time] = preset
        return {when: preset for when, preset in sorted(list(timetable_for_day.items()))}

    def schedule_presets(self) -> None:
        assert is_running_in_gui_thread()
        location = self.main_config.get_location()
        if location and self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log_debug("schedule_presets: try to obtain application_lock") if log_debug_enabled else None
            with self.application_lock:
                log_debug("schedule_presets: holding application_lock") if log_debug_enabled else None
                ScheduleWorker.dequeue_all(SchedulerJobType.RESTORE_PRESET)
                start_of_today = zoned_now(rounded_to_minute=True).replace(hour=0, minute=0)
                timetable_for_today = self.schedule_create_timetable(start_of_today, location)
                if len(timetable_for_today) > 0:  # Use the timetable to schedule jobs
                    now = zoned_now()
                    if future_presets := [(when, preset) for when, preset in timetable_for_today.items() if when > now]:
                        for when, preset in future_presets:  # Schedule future part of day
                            preset.schedule(when, self.activate_scheduled_preset_in_gui, self.skip_scheduled_preset)
                    # Schedule the preset that might apply right now, either the first overdue, or last from yesterday
                    if overdue_presets := [(when, preset) for when, preset in timetable_for_today.items() if when <= now]:
                        when_overdue, most_recent_overdue_preset = overdue_presets[-1]  # first is the most recently applicable
                        if most_recent_overdue_preset.schedule_status != PresetScheduleStatus.SUCCEEDED:  # not already run
                            most_recent_overdue_preset.schedule(when_overdue, self.activate_scheduled_preset_in_gui, overdue=True)
                        for when, preset in overdue_presets[:-1]:  # The rest have been superseded (if not already succeeded)
                            if preset.schedule_status != PresetScheduleStatus.SUCCEEDED:  # not already run
                                preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
                                log_info(f"Skipped preset '{preset.name}', passed assigned-time (status={preset.schedule_status})")
                    else:  # Nothing overdue today, schedule the last from yesterday (assumed to be the last for today)
                        last_preset_yesterday = list(timetable_for_today.values())[-1]  # last for yesterday same as last for today
                        last_preset_yesterday.schedule(start_of_today, self.activate_scheduled_preset_in_gui, overdue=True)
                # set a timer to rerun this scheduler at the start of the next day.
                ScheduleWorker.dequeue_all(SchedulerJobType.SCHEDULE_PRESETS)
                tomorrow = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                # tomorrow = zoned_now().replace(second=0, microsecond=0) + timedelta(minutes=2) # testing
                daily_schedule_job = SchedulerJob(tomorrow, SchedulerJobType.SCHEDULE_PRESETS,
                                                  partial(self.main_window.run_in_gui_thread, self.schedule_presets))
                log_info(f"Will update schedule for Presets at {tomorrow} "
                         f"(in {round(daily_schedule_job.remaining_time() / 60)} minutes)")
            log_debug("schedule_presets: released application_lock") if log_debug_enabled else None
        else:
            log_info(f"Scheduling is disabled or no location ({location=})")
            ScheduleWorker.shutdown()
        PresetsDialog.reconfigure_instance()

    def schedule_alteration(self, preset: Preset) -> None:
        location = self.main_config.get_location()
        if location and self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log_debug("schedule_alteration: try to obtain application_lock") if log_debug_enabled else None
            with self.application_lock:
                log_debug("schedule_alteration: holding application_lock") if log_debug_enabled else None
                preset.remove_elevation_trigger(quietly=True)
                start_of_today = zoned_now(rounded_to_minute=True).replace(hour=0, minute=0)
                timetable_for_today = self.schedule_create_timetable(start_of_today, location)
                if when := next((t for t, p in timetable_for_today.items() if p == preset), None):
                    if when > zoned_now():  # if destined for the future, schedule it
                        preset.schedule(when, self.activate_scheduled_preset_in_gui, overdue=False)
            log_debug("schedule_alteration: released application_lock") if log_debug_enabled else None
        else:
            log_info(f"schedule_alteration: Scheduling is disabled or no location ({location=})")

    def activate_scheduled_preset_in_gui(self, preset):
        self.main_window.run_in_gui_thread(partial(self.activate_scheduled_preset, preset))

    def activate_scheduled_preset(self, preset: Preset, check_weather: bool = True, immediately: bool = False,
                                  activation_time: datetime | None = None) -> None:
        assert is_running_in_gui_thread()

        def _activation_feedback(msg: str):
            self.main_window.show_preset_status(f"{TIME_CLOCK_SYMBOL} " + tr("Preset {} activating at {}").format(
                preset.name, f"{activation_time:%H:%M}") + f" - {msg}")

        def _activation_finished(worker: BulkChangeWorker) -> None:
            assert preset.elevation_time_today is not None or preset.get_at_time() is not None
            attempts = preset.scheduler_job.attempts
            if worker.work_exception is not None:
                too_close = zoned_now() + timedelta(seconds=60)  # retry if more than a minute before any others
                for other in self.preset_controller.find_presets_map().values():  # Skip retry if another is due soon
                    if (other.name != preset.name
                            and preset.elevation_time_today is not None and other.elevation_time_today is not None
                            and preset.elevation_time_today < other.elevation_time_today <= too_close):
                        log_info(f"Schedule restoration skipped '{preset.name}', too close to {other.name}")
                        if not off_schedule:
                            preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
                        _activation_feedback(tr("Skipped, superseded"))
                        return
                _activation_feedback(tr("Error, trying again in {} seconds").format(60))
                if attempts == 1:
                    log_warning(f"Error during restoration of '{preset.name}', retrying every {60} seconds.")
                preset.scheduler_job.requeue()  # retry - retain old schedule time to maintain proper schedule order.
                return
            if not off_schedule:
                preset.schedule_status = PresetScheduleStatus.SUCCEEDED
            self.main_window.update_status_indicators(preset)
            _activation_feedback(tr("Restored {}").format(preset.name))
            log_info(f"Restored preset '{preset.name}' on try {attempts}") if attempts > 1 else None

        if not self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log_info(f"Schedule is disabled - not activating preset '{preset.name}'")
            return
        if activation_time is None:
            activation_time = zoned_now()
        if preset.elevation_time_today:
            off_schedule = activation_time < preset.elevation_time_today  # Too early, must be an off-schedule catchup from yesterday
        else:
            off_schedule = activation_time < preset.get_at_time()
        if preset.is_weather_dependent() and check_weather and self.main_config.is_set(ConfOpt.WEATHER_ENABLED):
            if not self.is_weather_satisfactory(preset):
                if not off_schedule:
                    preset.schedule_status = PresetScheduleStatus.WEATHER_CANCELLATION
                message = tr("Preset {} activation was cancelled due to weather at {}").format(
                    preset.name, activation_time.isoformat(' ', 'seconds'))
                self.main_window.show_preset_status(message)
                return
        if preset.scheduler_job.attempts == 1:
            log_info(f"Activating scheduled preset '{preset.name}' transition={immediately} {off_schedule=}")
        # Happens asynchronously in a thread
        self.restore_preset(preset, finished_func=_activation_finished,
                            immediately=immediately or PresetTransitionFlag.SCHEDULED not in preset.get_transition_type(),
                            background_activity=True)

    def skip_scheduled_preset(self, preset: Preset):
        assert is_running_in_gui_thread()
        preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
        self.main_window.update_status_indicators(preset)

    def is_weather_satisfactory(self, preset, use_cache: bool = False) -> bool:
        try:
            if not use_cache or self.weather_query is None:
                if location := self.main_config.get_location():
                    self.weather_query = WeatherQuery(location)
                    self.weather_query.run_query()
                    if not self.weather_query.proximity_ok:
                        log_error(f"Preset '{preset.name}' weather location is {self.weather_query.proximity_km} km from "
                                  f"Settings Location, check settings.")
                        weather_bad_location_dialog(self.weather_query)
            if not preset.check_weather(self.weather_query):
                return False
        except ValueError as e:
            MBox(MIcon.Warning, msg=tr("Ignoring weather requirements, unable to query local weather: {}").format(str(e.args[0])),
                 info=e.args[1]).exec()
        return True

    def find_preset_by_name(self, preset_name: str) -> Preset | None:
        return self.preset_controller.find_presets_map().get(preset_name)

    def restore_named_preset(self, preset_name: str) -> None:
        if preset := self.find_preset_by_name(preset_name):
            # Transition immediately unless the Preset is required to ALWAYS transition.
            self.restore_preset(preset, immediately=PresetTransitionFlag.MENU not in preset.get_transition_type())

    def save_preset(self, preset: Preset) -> None:
        self.preset_controller.save_preset(preset)
        if self.main_window.app_context_menu.get_preset_menu_action(preset.name) is None:
            self.main_window.app_context_menu.insert_preset_menu_action(preset)
        self.main_window.update_status_indicators()
        preset.remove_elevation_trigger()
        self.schedule_alteration(preset)

    def save_preset_order(self, name_order: List[str]):
        self.preset_controller.save_order(name_order)
        self.refresh_preset_menu(reorder=True)

    def populate_ini_from_vdus(self, preset_ini: ConfIni, update_only: bool = False) -> None:
        for control_panel in self.main_window.get_main_panel().vdu_control_panels.values():
            vdu_section_name = control_panel.controller.vdu_stable_id
            if not preset_ini.has_section(vdu_section_name):
                preset_ini.add_section(vdu_section_name)
            for control in control_panel.vcp_controls:  # Fill out value for any options present in the preset_ini.
                if not update_only or preset_ini.has_option(vdu_section_name, control.vcp_capability.property_name()):
                    if control.current_value is not None:
                        preset_ini[vdu_section_name][control.vcp_capability.property_name()] = control.get_current_text_value()

    def delete_preset(self, preset: Preset) -> None:
        self.preset_controller.delete_preset(preset)
        self.main_window.app_context_menu.remove_preset_menu_action(preset.name)
        self.main_window.update_status_indicators()

    def refresh_preset_menu(self, reorder: bool = False):
        self.main_window.refresh_preset_menu(reorder=reorder)

    def which_preset_is_active(self) -> Preset | None:
        # See if we have a record of which was last active, and see if it still is active
        main_panel = self.main_window.get_main_panel()
        if CURRENT_PRESET_NAME_FILE.exists():
            with open(CURRENT_PRESET_NAME_FILE, encoding="utf-8") as cps_file:
                if preset_name := cps_file.read().strip():
                    preset = self.preset_controller.find_presets_map().get(preset_name)  # will be None if it has been deleted
                    if preset is not None and main_panel.is_preset_active(preset):
                        return preset
        # Guess by testing each possible preset against the current VDU settings
        for preset in self.preset_controller.find_presets_map().values():
            if main_panel.is_preset_active(preset):
                return preset
        return None

    def find_presets_map(self) -> Dict[str, Preset]:
        return self.preset_controller.find_presets_map()

    def get_lux_auto_controller(self) -> LuxAutoController:
        assert self.lux_auto_controller is not None
        return self.lux_auto_controller

    def get_vdu_stable_id_list(self) -> List[VduStableId]:
        return [stable_id for stable_id, vdu_controller in self.vdu_controllers_map.items() if not vdu_controller.ignore_vdu]

    def get_vdu_values(self, vdu_stable_id: VduStableId, vcp_codes: List[str] | None) -> List[Tuple[str, VcpValue]]:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            if not vcp_codes:
                vcp_codes = [capability.vcp_code for capability in controller.enabled_capabilities]
            return [(code, value) for code, value in zip(vcp_codes, controller.get_vcp_values(vcp_codes))]
        return []

    def get_enabled_capabilities(self, vdu_stable_id: VduStableId) -> List[VcpCapability]:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.enabled_capabilities
        return []

    def get_range(self, vdu_stable_id: VduStableId, vcp_code: str,
                  fallback: Tuple[int, int] | None = None) -> Tuple[int, int] | None:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.get_range_restrictions(vcp_code, fallback)
        log_error(f"get_range: No controller for {vdu_stable_id}")
        return fallback

    def get_value(self, vdu_stable_id, vcp_code) -> int:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            value = controller.get_vcp_values([vcp_code])
            if len(value) == 1:  # This could probably be an assertion
                return value[0].current
        log_error(f"get_value: No controller for {vdu_stable_id}")
        return 0

    def set_value(self, vdu_stable_id: VduStableId, vcp_code: str, value: int, origin: VcpOrigin = VcpOrigin.NORMAL):
        if panel := self.main_window.get_main_panel().vdu_control_panels.get(vdu_stable_id):
            if control := panel.get_control(vcp_code):
                control.set_value(value, origin)  # Apply to physical VDU
                return
        log_error(f"set_value: No controller for {vdu_stable_id=} {vcp_code=}")

    def is_vcp_code_enabled(self, vdu_stable_id, vcp_code: str) -> bool:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            for capability in controller.enabled_capabilities:
                if capability.vcp_code == vcp_code:
                    return True
        return False

    def update_window_status_indicators(self, preset: Preset | None = None):
        if not is_running_in_gui_thread():
            self.main_window.run_in_gui_thread(partial(self.main_window.update_status_indicators, preset))

    def get_vdu_preferred_name(self, vdu_stable_id: VduStableId):
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.get_vdu_preferred_name()
        log_error(f"get_vdu_description: No controller for {vdu_stable_id}")
        return vdu_stable_id

    def busy_doing(self) -> str | None:
        return tr("Preset editing") if PresetsDialog.is_instance_editing() else None

    def find_vdu_config_files(self) -> List[Path]:
        found = []
        for conf_file in [f for f in sorted(CONFIG_DIR_PATH.glob('*_*_*.conf')) if f.is_file()]:
            conf = ConfIni()
            conf.read(conf_file.as_posix())
            if conf.has_section(ConfOpt.CAPABILITIES_OVERRIDE.conf_id[0]) and conf.get(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id):
                found.append(conf_file)
        log_debug(f"find_vdu_config_files {found}")
        return found

    def status_message(self, message: str, timeout: int, destination: MsgDestination = MsgDestination.DEFAULT):
        self.main_window.status_message(message, timeout, destination)

    def restart_application(self, reason: str):
        # Force a restart of the application.  Some settings changes need this (for example, run in the system tray).
        MBox(MIcon.Warning, msg=reason, info=tr('When this message is dismissed, vdu_controls will restart.')).exec()
        self.main_window.app_save_window_state()
        QCoreApplication.exit(EXIT_CODE_FOR_RESTART)

    def replace_toolbar(self, main_toolbar):
        target_window = self.main_window
        for old_toolbar in target_window.findChildren(QToolBar):  # Make sure there is only one toolbar
            target_window.removeToolBar(old_toolbar)
            old_toolbar.deleteLater()
        at_top = self.main_config.is_set(ConfOpt.TOOLBAR_AT_TOP)
        toolbar_area = Qt.ToolBarArea.TopToolBarArea if at_top else Qt.ToolBarArea.BottomToolBarArea
        target_window.addToolBar(toolbar_area, main_toolbar)


class VduAppWindow(QMainWindow):
    splash_message_qtsignal = pyqtSignal(str)
    _run_in_gui_thread_qtsignal = pyqtSignal(object)

    def __init__(self, main_config: VduControlsConfig, main_controller: VduAppController) -> None:
        super().__init__()
        global gui_thread
        app = QApplication.instance()
        assert app
        if os.getenv('VDU_CONTROLS_DEBUG_LAYOUT', default='no') == 'yes':
            app.setStyleSheet("QWidget { border: 1px solid red; margin: 1px; padding: 1px; }")
        gui_thread = app.thread()
        self.main_controller: VduAppController = main_controller
        self.setObjectName('main_window')
        self.qt_version_key = self.objectName() + "_qt_version"
        self.qt_geometry_key = self.objectName() + "_geometry"
        self.qt_state_key = self.objectName() + "_window_state"
        self.qt_settings = QSettings('vdu_controls.qt.state', 'vdu_controls')
        self.main_panel: VduControlsMainPanel | None = None
        self.scroll_area: QScrollArea | None = None
        self.main_config = main_config
        self.hide_shortcuts = True
        self.initial_theme_is_dark = is_dark_theme()
        log_info(f"Started with dark theme: {self.initial_theme_is_dark}")

        def _run_in_gui(task: Callable):
            log_debug(f"Running task in gui thread {repr(task)}") if log_debug_enabled else None
            task()  # Was using a partial, but it silently failed when task was a method with only self and no other arguments.

        self._run_in_gui_thread_qtsignal.connect(_run_in_gui)

        if log_debug_enabled:
            for screen in app.screens():
                log_info("Screen", screen.name())

        self.app_context_menu = ContextMenu(
            app_controller=main_controller,
            main_window_action=partial(self.show_main_window, True),  # Gnome tray doesn't provide a way to bring up the main app.
            about_action=partial(AboutDialog.invoke, self.main_controller),
            help_action=HelpDialog.invoke,
            gray_scale_action=GreyScaleDialog,
            lux_auto_action=self.main_controller.lux_auto_action if main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) else None,
            lux_check_action=self.main_controller.lux_check_action if main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) else None,
            lux_meter_action=partial(LuxDialog.invoke, self.main_controller) if main_config.is_set(
                ConfOpt.LUX_OPTIONS_ENABLED) else None,
            settings_action=self.main_controller.edit_config,
            presets_dialog_action=self.main_controller.show_presets_dialog,
            refresh_action=self.main_controller.start_refresh,
            quit_action=self.quit_app,
            hide_shortcuts=self.hide_shortcuts, parent=self)

        # Don't do this - it creates a titlebar inside the application
        #self.app_context_menu.setTitle("VDU Controls ")  # Populate titlebar-menu (if it's enabled for Plasma Titlebars).
        #self.menuBar().addMenu(self.app_context_menu)    # TODO - make a proper menu - this will be a submenu.

        splash_pixmap = get_splash_image()
        splash = QSplashScreen(
            splash_pixmap.scaledToWidth(native_font_height(scaled=26)).scaledToHeight(native_font_height(scaled=13)),
            Qt.WindowType.WindowStaysOnTopHint) if main_config.is_set(ConfOpt.SPLASH_SCREEN_ENABLED) else None
        if splash is not None:
            splash.show()
            splash.raise_()  # Attempt to force it to the top with raise and activate
            splash.activateWindow()
            QApplication.processEvents()
        self.app_icon: QIcon | None = None
        self.tray_icon: QIcon | None = None
        self.initialise_app_icon(splash_pixmap)

        def f10_func():
            self.app_context_menu.exec(QCursor.pos())

        f10_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F10), self)  # New Qt standard shortcut for context menu.
        f10_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        f10_shortcut.activated.connect(f10_func)

        self.tray = None
        if main_config.is_set(ConfOpt.SYSTEM_TRAY_ENABLED):
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log_warning("no system tray, waiting to see if one becomes available.")
                for _ in range(0, SYSTEM_TRAY_WAIT_SECONDS):
                    if QSystemTrayIcon.isSystemTrayAvailable():
                        break
                    time.sleep(0.25)  # TODO - at least use a constant
            if QSystemTrayIcon.isSystemTrayAvailable():
                log_info("Using system tray.")
                app.setQuitOnLastWindowClosed(False)  # This next call appears to be automatic on KDE, but not on gnome.
                self.tray = QSystemTrayIcon(parent=self)
                self.tray.setContextMenu(self.app_context_menu)
            else:
                log_error("no system tray - cannot run in system tray.")

        self.app_name = APPNAME
        app.setApplicationDisplayName(self.app_name)
        if QT5_USE_HIGH_DPI_PIXMAPS:
            app.setAttribute(QT5_USE_HIGH_DPI_PIXMAPS)  # Make sure all icons use HiDPI - toolbars don't by default, so force it.

        def _splash_message_action(message) -> None:
            if splash is not None:
                log_info(f"splash_message: {repr(message)}")
                splash.showMessage(f"\n\n{APPNAME} {VDU_CONTROLS_VERSION}\n{message}",
                                   Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                QApplication.processEvents()

        self.splash_message_qtsignal.connect(_splash_message_action)
        self.splash_message_qtsignal.emit(tr('Looking for DDC monitors...'))

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.main_controller.configure_application(self)

        self.inactive_pause_millis = int(os.environ.get('VDU_CONTROLS_INACTIVE_PAUSE_MILLIS', default='1200'))
        self.active_event_count = 0
        app.applicationStateChanged.connect(self.on_application_state_changed)
        self.installEventFilter(self)

        if self.tray is not None:
            self.hide()
            self.tray.activated.connect(partial(self.show_main_window, True))
            self.tray.show()
        else:
            self.show_main_window()

        if splash is not None:
            splash.finish(self)
            splash.deleteLater()
            splash = None

        if main_config.file_path is None or main_config.ini_content.get_version() < VDU_CONTROLS_VERSION_TUPLE:  # New version...
            release_notes()
            main_config.write_file(ConfIni.get_path('vdu_controls'), overwrite=True)  # Stops release notes from being repeated.


    def is_inactive(self):
        if QApplication.instance().applicationState() != Qt.ApplicationState.ApplicationInactive:
            return False
        for top_level_widget in QApplication.topLevelWidgets():  # Check if any dialogs are active
            if isinstance(top_level_widget, DialogSingletonMixin) or isinstance(top_level_widget, GreyScaleDialog):
                if top_level_widget.isVisible():
                    return False  # A dialog is showing - definitely active
        return True  # inactive and no dialogs are active

    def on_application_state_changed(self, _: Qt.ApplicationState):
        if self.main_config.is_set(ConfOpt.HIDE_ON_FOCUS_OUT):
            if self.is_inactive():
                # The user may be using the title-bar or window-edges to move/resize the window. Monitor for the lack of
                # move/resize events, treat that as a real focus out.  This is needed for gnome and xfce.
                self.active_event_count = 0  # Count the following move/resize events as evidence of titlebar edge-grab activity.

                def _hide_func():
                    if self.active_event_count == 0 and self.is_inactive():  # No moving/resizing activity and is_inactive().
                        self.hide() if self.tray else self.showMinimized()  # Probably safe to hide now

                QTimer.singleShot(self.inactive_pause_millis, _hide_func)  # wait N ms and see if any move/resize events occur.

    def eventFilter(self, target: QObject | None, event: QEvent | None) -> bool:
        # log_info(f"eventFilter {event.__class__.__name__} {event.type()}")
        if event and event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                      QEvent.Type.WindowActivate):  # Still active if being moved or resized
            self.active_event_count += 1
        return super().eventFilter(target, event)

    def show_main_window(self, toggle: bool = False) -> None:
        if toggle and self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()  # Attempt to force it to the top with raise and activate
            self.activateWindow()

    def show(self):
        if not self.app_restore_window_state():  # No previous state or invalid
            if self.main_config.is_set(ConfOpt.SMART_WINDOW):
                self.adjustSize()
                self.app_decide_window_position()  # decide initial position relative to cursor
                self.app_save_window_state()
        super().show()

    def hide(self):
        if self.isVisible():  # Only save position if really on screen
            self.app_save_window_state()
        super().hide()

    def quit_app(self) -> None:
        self.app_save_window_state()
        QApplication.instance().quit()
        sys.exit(0)  # Just in case self.app.quit() errors

    def initialise_app_icon(self, splash_pixmap: QPixmap | None = None):
        global mono_light_tray
        self.app_icon = QIcon()
        self.app_icon.addPixmap(get_splash_image() if splash_pixmap is None else splash_pixmap)
        tray_theme_type = self.get_tray_theme_type()
        if CUSTOM_TRAY_ICON_FILE.exists() and os.access(CUSTOM_TRAY_ICON_FILE.as_posix(), os.R_OK):
            log_info(f"Loading custom app_icon: {CUSTOM_TRAY_ICON_FILE} {tray_theme_type=}")
            self.tray_icon = create_icon_from_path(CUSTOM_TRAY_ICON_FILE, tray_theme_type)
        elif tray_theme_type in (ThemeType.MONOCHROME_LIGHT, ThemeType.MONOCHROME_DARK):  # Special tray monochrome version
            log_info(f"Using monochrome app_icon: {tray_theme_type=}")
            self.tray_icon = create_icon_from_svg_bytes(MONOCHROME_APP_ICON_SOURCE, tray_theme_type)
        else:  # non-themed color icon based on the splash screen image
            self.tray_icon = self.app_icon

    def create_main_control_panel(self) -> None:
        # Call on initialization and whenever the number of connected VDUs changes.
        if self.main_panel is not None:
            self.main_panel.deleteLater()
            self.main_panel = None
        if self.scroll_area is not None:
            self.scroll_area.deleteLater()
            self.scroll_area = None
        self.main_panel = VduControlsMainPanel()
        self.main_controller.initialize_vdu_controllers()
        refresh_button = ToolButton(REFRESH_ICON_SOURCE, tr("Refresh settings from monitors"))
        refresh_button.pressed.connect(self.main_controller.start_refresh)
        tool_buttons = [refresh_button]
        extra_controls = []
        if self.main_controller.lux_auto_controller is not None:
            self.main_controller.lux_auto_controller.lux_config.load()  # may have changed
            if lux_auto_button := self.main_controller.lux_auto_controller.create_tool_button():
                lux_auto_button.pressed.connect(self.main_controller.lux_auto_action)
                tool_buttons.append(lux_auto_button)
            if lux_check_button := self.main_controller.lux_auto_controller.create_lighting_check_button():
                lux_check_button.pressed.connect(self.main_controller.lux_check_action)
                tool_buttons.append(lux_check_button)
            if lux_manual_input := self.main_controller.lux_auto_controller.create_manual_input_control():
                extra_controls.append(lux_manual_input)
            if lux_ambient_slider := self.main_controller.lux_auto_controller.lux_slider:
                lux_ambient_slider.status_icon_changed_qtsignal.connect(self.update_status_indicators)
        self.refresh_preset_menu()
        self.main_panel.initialise_control_panels(self.main_controller, self.app_context_menu, self.main_config,
                                                  tool_buttons, extra_controls, self.splash_message_qtsignal)
        # Wire-up after successful init to avoid deadlocks
        self.main_panel.vdu_vcp_changed_qtsignal.connect(self.respond_to_changes_handler)
        self.indicate_busy(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.main_panel)
        self.setCentralWidget(self.scroll_area)
        available_height = self.screen().availableGeometry().height() - npx(200)  # Minus allowance for panel/tray
        hint_height = self.main_panel.sizeHint().height()  # The hint is the actual required layout space
        hint_width = self.main_panel.sizeHint().width()
        log_debug(f"create_main_control_panel: {hint_height=} {available_height=} {self.minimumHeight()=}")
        if hint_height > available_height:
            log_debug(f"Main panel too high, adding scroll-area {hint_height=} {available_height=}") if log_debug_enabled else None
            self.setMaximumHeight(available_height)
            self.setMinimumWidth(hint_width + npx(20))  # Allow extra space for disappearing scrollbars
        else:  # Don't mess with the size unnecessarily - let the user determine it?
            number_of_vdus = len(self.main_controller.get_vdu_stable_id_list())
            self.setMinimumHeight(hint_height + npx(30) * (number_of_vdus + 1))
            if hint_height != self.height():
                self.setMinimumWidth(self.width())
                self.adjustSize()
            self.setMinimumWidth(hint_width + npx(20))

        self.splash_message_qtsignal.emit(tr("Checking Presets"))

    def get_main_panel(self) -> VduControlsMainPanel:
        assert self.main_panel is not None
        return self.main_panel

    def indicate_busy(self, is_busy: bool, lock_controls: bool = True):
        if self.main_panel:
            self.main_panel.indicate_busy(is_busy, lock_controls)
        self.app_context_menu.indicate_busy(is_busy)

    def show_preset_status(self, message: str, timeout: int = 3000):
        PresetsDialog.show_status_message(message=message, timeout=timeout)
        self.status_message(message, timeout=timeout, destination=MsgDestination.DEFAULT)

    def get_tray_theme_type(self):  # Ugly because Qt has no way to access the tray theme
        theme = ThemeType.UNTHEMED  # Don't alter colors for overlay onto app icon in tray if unthemed
        if self.main_config.is_set(ConfOpt.MONOCHROME_TRAY_ENABLED):
            theme = ThemeType.MONOCHROME_DARK
        if self.main_config.is_set(ConfOpt.MONO_LIGHT_TRAY_ENABLED):
            theme = ThemeType.MONOCHROME_LIGHT
        if theme != ThemeType.UNTHEMED:
            theme_has_flipped = self.initial_theme_is_dark != is_dark_theme()
            if theme_has_flipped and self.main_config.is_set(ConfOpt.TRAY_FOLLOWS_THEME):
                log_info(f"Option {ConfOpt.TRAY_FOLLOWS_THEME.conf_id} is set: Desktop theme flipped - flipping tray theme")
                theme = ThemeType.MONOCHROME_LIGHT if theme == ThemeType.MONOCHROME_DARK else ThemeType.MONOCHROME_DARK
        return theme

    def update_status_indicators(self, preset: Preset | None = None, palette_change: bool = False) -> None:
        assert is_running_in_gui_thread()  # Boilerplate in case this is called from the wrong thread.
        if self.main_panel is None:  # On deepin 23, events can trigger this method before initialization is complete
            return
        title = self.app_name
        tray_embedded_icon = led1_color = led2_color = None
        if preset is None:  # Detects matching Preset based on current VDU control settings
            preset = self.main_controller.which_preset_is_active()
        if preset is None:  # Clears the indicators
            self.get_main_panel().show_active_preset(None)
            self.app_context_menu.indicate_preset_active(None)
            PresetsDialog.instance_indicate_active_preset(None)
        else:  # Set indicators to specific preset
            self.get_main_panel().show_active_preset(preset)
            self.app_context_menu.indicate_preset_active(preset)
            PresetsDialog.instance_indicate_active_preset(preset)
            title = f"{preset.get_title_name()} {PRESET_APP_SEPARATOR_SYMBOL} {title}"
            tray_embedded_icon = preset.create_icon(self.get_tray_theme_type())
            led1_color = PRESET_TRANSITIONING_LED_COLOR if preset.in_transition_step > 0 else None  # TODO transitioning indicator
        if self.main_controller.lux_auto_controller is not None:
            if self.main_controller.lux_auto_controller.is_auto_enabled():
                title = f"{tr('Auto')}/{title}"
                led2_color = AUTO_LUX_LED_COLOR
            menu_lux_icon = create_icon_from_svg_bytes(
                self.main_controller.lux_auto_controller.current_auto_svg())  # NB cache involved
            self.app_context_menu.update_lux_auto_icon(menu_lux_icon)  # Won't actually update if it hasn't changed
            if tray_embedded_icon is None and self.main_config.is_set(ConfOpt.LUX_TRAY_ICON):
                if zone := self.main_controller.lux_auto_controller.get_lux_zone():
                    tray_embedded_icon = create_icon_from_svg_bytes(zone.icon_svg, self.get_tray_theme_type())
                    title = title + '\n' + tr("Lighting: {}").format(zone.name.lower())

        if self.windowTitle() != title:  # Don't change if not needed - prevent flickering.
            self.setWindowTitle(title)
            QApplication.instance().setWindowIcon(
                create_decorated_app_icon(self.app_icon, tray_embedded_icon, led1_color, led2_color))
        if self.tray:
            self.tray.setToolTip(title)
            self.tray.setIcon(create_decorated_app_icon(self.tray_icon, tray_embedded_icon, led1_color, led2_color))
        if palette_change or preset is not None:
            self.refresh_preset_menu(palette_change=palette_change)

    def respond_to_changes_handler(self, vdu_stable_id: VduStableId, vcp_code: str, value: int, origin: VcpOrigin,
                                   causes_config_change: bool) -> None:
        # Update UI secondary displays
        AboutDialog.refresh()
        for panel in self.main_panel.vdu_control_panels.values():
            panel.update_stats()
        if causes_config_change and origin == VcpOrigin.NORMAL:  # only respond if this is an internally initiated change
            log_info(f"Must reconfigure due to change to: {vdu_stable_id=} {vcp_code=} {value=} {origin}")
            self.main_controller.configure_application()  # Special case, such as a power control causing the VDU to go offline.
            return
        log_debug(f"respond_to_changes_handler {vdu_stable_id=} {vcp_code=} {value=} {origin}") if log_debug_enabled else None
        if origin != VcpOrigin.TRANSIENT:  # Only want to indicate final status (not when just passing through a preset)
            self.update_status_indicators()
            if origin != VcpOrigin.EXTERNAL:
                self.status_message(SET_VCP_SYMBOL, timeout=500, destination=MsgDestination.DEFAULT)
        if self.main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) and self.main_controller.lux_auto_controller is not None:
            if vcp_code == BRIGHTNESS_VCP_CODE:
                LuxDialog.lux_dialog_show_brightness(vdu_stable_id, value)

    def refresh_tray_menu(self) -> None:
        assert is_running_in_gui_thread()
        self.app_context_menu.update()

    def closeEvent(self, event) -> None:
        self.app_save_window_state()

    def app_save_window_state(self) -> None:
        if self.isVisible():
            self.qt_settings.setValue(self.qt_version_key, QtCore.qVersion())
            log_debug(f"app_save_window_state: {self.pos()=} {self.geometry()=} {QtCore.qVersion()}") if log_debug_enabled else None
            self.qt_settings.setValue(self.qt_geometry_key, self.saveGeometry())
            self.qt_settings.setValue(self.qt_state_key, self.saveState())

    def app_restore_window_state(self) -> bool:
        log_debug(f"app_restore_window_state")
        if len(self.qt_settings.allKeys()) == 0:  # No previous state
            return False
        save_version_major = self.qt_settings.value(self.qt_version_key, '5').split('.', 1)[0]
        qt_version_major = QtCore.qVersion().split('.', 1)[0]
        if save_version_major != qt_version_major:
            log_warning(
                f"app_restore_window_state: restore: {save_version_major=} != {qt_version_major=}, this may cause window geometry glitches")
        if smart_window := self.main_config.is_set(ConfOpt.SMART_WINDOW, fallback=True):  # Restore pos and geometry
            if geometry := self.qt_settings.value(self.qt_geometry_key, None):
                self.restoreGeometry(geometry)
                log_debug(f"app_restore_window_state: restoring {self.pos()=} {self.geometry()=}") if log_debug_enabled else None
        if window_state := self.qt_settings.value(self.qt_state_key, None):
            self.restoreState(window_state)  # Restore component positions, such as toolbar location
            log_debug(f"app_restore_window_state: restoring internal layout state") if log_debug_enabled else None
        return smart_window

    def app_decide_window_position(self):
        # Guess a window position near the tray. Use the mouse/cursor-pos as a guess to where the
        # system tray is.  Under Linux Qt the position of the tray icon is reported as 0,0, so we can't use that.
        cursor_x, cursor_y = QCursor.pos().x(), QCursor.pos().y()
        app_width, app_height = self.geometry().width(), self.geometry().height()
        desktop_width, desktop_height = (self.screen().availableGeometry().width(),
                                         self.screen().availableGeometry().height())
        # The following calculations allow for the tray being on any edge of the desktop...
        margin = min(abs(desktop_height - cursor_y), abs(desktop_width - cursor_x), npx(100)) + npx(25) if self.tray else 0
        x = cursor_x - app_width - margin if cursor_x > app_width else cursor_x + margin
        y = cursor_y - app_height - margin if cursor_y > app_height else cursor_y + margin
        log_debug(f"decide_window_position: {x=} {y=} {app_width=} {app_height=} {cursor_x=} {cursor_y=} {margin=}")
        self.setGeometry(x, y, app_width, app_height)

    def status_message(self, message: str, timeout: int, destination: MsgDestination):
        assert (self.main_panel is not None)
        if not is_running_in_gui_thread():
            self.run_in_gui_thread(partial(self.status_message, message, timeout, destination))
        else:
            if destination == MsgDestination.DEFAULT:
                self.main_panel.status_message(message, timeout)
                QApplication.processEvents()  # Force the message out straight way.

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            log_info("PaletteChange event: New style sheet in use, update icons")
            self.initialise_app_icon()
            self.update_status_indicators(palette_change=True)
            if self.main_panel:
                self.main_panel.main_toolbar.refresh_buttons()
        return super().event(event)

    def refresh_preset_menu(self, palette_change: bool = False, reorder: bool = False):
        self.app_context_menu.refresh_preset_menu(palette_change=palette_change, reorder=reorder)

    def show_no_controllers_error_dialog(self, ddcutil_problem: Exception):
        log_error("No controllable monitors found.")
        if isinstance(ddcutil_problem, subprocess.SubprocessError):
            problem_text = ddcutil_problem.stderr.decode('utf-8', errors='surrogateescape') + '\n' + str(ddcutil_problem)
        else:
            problem_text = str(ddcutil_problem)
        log_error(f"Most recent error: {problem_text}".encode("unicode_escape").decode("utf-8"))
        MBox(MIcon.Critical, msg=tr('No controllable monitors found.'),
             info=tr("Is ddcutil or ddcutil-service installed and working?") + "\n\n" +
                  tr("Most recent error: {}").format(problem_text) + "\n" + '_' * 80).exec()

    def ask_for_vdu_controller_remedy(self, vdu_number: str, model_name: str, vdu_serial: str):
        msg = tr('Failed to obtain capabilities for monitor {} {} {}.').format(vdu_number, model_name, vdu_serial)
        info = tr('Cannot automatically configure this monitor.'
                  '\n You can choose to:'
                  '\n 1: Retry obtaining the capabilities.'
                  '\n 2: Temporarily ignore this monitor.'
                  '\n 3: Apply standard brightness and contrast controls.'
                  '\n 4: Permanently discard this monitor from use with vdu_controls.'
                  '\n\nPossibly just a timing error, maybe a retry will work\n(see Settings: sleep multiplier)\n\n')
        choice = MBox(MIcon.Critical, msg=msg, info=info, buttons=MBtn.Discard | MBtn.Ignore | MBtn.Apply | MBtn.Retry).exec()
        if choice == MBtn.Discard:
            MBox(MIcon.Information, msg=tr('Discarding {} monitor.').format(model_name),
                 info=tr('Remove "{}" from {} capabilities override to reverse this decision.').format(IGNORE_VDU_MARKER_STR,
                                                                                                       model_name)).exec()
            return VduController.DISCARD_VDU
        elif choice == MBtn.Ignore:
            MBox(MIcon.Information, msg=tr('Ignoring {} monitor for now.').format(model_name),
                 info=tr('Will retry when vdu_controls is next started')).exec()
            return VduController.IGNORE_VDU
        elif choice == MBtn.Apply:
            MBox(MIcon.Information, msg=tr('Assuming {} has brightness and contrast controls.').format(model_name),
                 info=tr('Wrote {} config files to {}.').format(model_name, CONFIG_DIR_PATH) +
                      tr('\nPlease check these files and edit or remove them if they '
                         'cause further issues.')).exec()
            return VduController.ASSUME_STANDARD_CONTROLS
        elif choice == MBtn.Retry:
            return VduController.NORMAL_VDU
        return VduController.IGNORE_VDU

    def run_in_gui_thread(self, task: Callable):
        self._run_in_gui_thread_qtsignal.emit(task)


class SignalWakeupHandler(QtNetwork.QAbstractSocket):
    # https://stackoverflow.com/a/37229299/609575
    # '''
    # Quoted here: The Qt event loop is implemented in C(++). That means, that while it runs and no Python code is
    # called (e.g. by a Qt signal connected to a Python slot), the signals are noted, but the Python signal handlers
    # aren't called.
    #
    # But, since Python 2.6 and in Python 3 you can cause Qt to run a Python function when a signal with a handler is
    # received using signal.set_wakeup_fd().
    #
    # This is possible because, contrary to the documentation, the low-level signal handler doesn't only set a flag
    # for the virtual machine, but it may also write a byte into the file descriptor set by set_wakeup_fd(). Python 2
    # writes a NUL byte, Python 3 writes the signal number.
    #
    # So by subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g.
    # QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler) is received
    # causing the signal handler to execute nearly instantaneously without the need for timers:
    # '''

    received_unix_signal_qtsignal = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(QtNetwork.QAbstractSocket.SocketType.UdpSocket, parent)
        self.old_fd = None
        self.wsock, self.rsock = socket.socketpair(type=socket.SOCK_DGRAM)  # Create a socket pair
        self.setSocketDescriptor(self.rsock.fileno())  # Let Qt listen on the one end
        self.wsock.setblocking(False)  # And let Python write on the other end
        self.old_fd = signal.set_wakeup_fd(self.wsock.fileno())
        # First Python code executed gets any exception from the signal handler, so add a do-nothing handler first
        self.readyRead.connect(lambda: None)
        self.readyRead.connect(self._readSignal)  # Second handler does the real handling

    def __del__(self) -> None:
        if self.old_fd is not None and signal is not None and signal.set_wakeup_fd is not None:
            signal.set_wakeup_fd(self.old_fd)  # Restore any old handler on deletion

    def _readSignal(self) -> None:
        # Read the written byte. Note: readyRead is blocked from occurring again until readData()
        # is called, so call it, even if you don't need the value.
        data = self.readData(1)
        signal_number = int(data[0])
        log_info("SignalWakeupHandler", signal_number)
        self.received_unix_signal_qtsignal.emit(signal_number)  # Emit a Qt signal for convenience




def main() -> None:
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)  # Force UTF-8, just in case it isn't

    def signal_handler(x, y) -> None:
        log_info("Signal received", x, y)

    signal.signal(signal.SIGHUP, signal_handler)
    for i in range(PRESET_SIGNAL_MIN, PRESET_SIGNAL_MAX):
        signal.signal(i, signal_handler)

    sys.excepthook = exception_handler

    # This is supposed to set the locale for all categories to the user’s default setting.
    # This can error on some distros when the required language isn't installed, or if LANG
    # is set without also specifying the UTF-8 encoding, so LANG=da_DK might fail,
    # but LANG=da_DK.UTF-8 should work. For our purposes, failure is not important.
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        log_warning(f"Could not set the default locale - may not be an issue...", trace=True)

    main_config = VduControlsConfig('vdu_controls', main_config=True)
    default_config_path = ConfIni.get_path('vdu_controls')
    log_info("Looking for config file '" + default_config_path.as_posix() + "'")
    if Path.is_file(default_config_path) and os.access(default_config_path, os.R_OK):
        main_config.parse_file(default_config_path)

    if os.environ.get('XDG_SESSION_TYPE') != 'x11':  # If Wayland we can't do smart window placement - use XWayland
        if main_config.is_set(ConfOpt.SMART_WINDOW) and main_config.is_set(ConfOpt.SMART_USES_XWAYLAND):
            log_warning(f"{ConfOpt.SMART_WINDOW.conf_id}: Wayland disallows app window placement. Switching to XWayland.")
            force_xwayland()

    QGuiApplication.setDesktopFileName("vdu_controls")  # Wayland needs this set to find/use the app's desktop icon.
    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)
    log_info(f"{app.applicationName()=} {QApplication.instance().applicationName()=}")
    global unix_signal_handler
    unix_signal_handler = SignalWakeupHandler(app)

    log_info(f"{APPNAME} {VDU_CONTROLS_VERSION} {sys.argv[0]}  ")
    log_info(f"python-locale: {locale.getlocale()} Qt-locale: {QLocale.system().name()}")
    log_info(f"desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')}; "
             f"session-type: {os.environ.get('XDG_SESSION_TYPE', default='unknown')}; "
             f"platform: {QApplication.platformName()}; Qt: {QtCore.qVersion()}")
    log_info(f"app-style: {app.style().objectName()} (detected a {'dark' if is_dark_theme() else 'light'} theme)")

    args = main_config.parse_global_args()
    log_info(f"Logging to {'syslog' if main_config.is_set(ConfOpt.SYSLOG_ENABLED) else 'stdout'}")
    log_set_syslog(main_config.is_set(ConfOpt.SYSLOG_ENABLED))
    log_set_debug(main_config.is_set(ConfOpt.DEBUG_ENABLED))
    if args.syslog:
        log_to_syslog = True
    if args.debug:
        main_config.debug_dump()
    if args.create_config_files:
        main_config.write_file(default_config_path)
    if args.install:
        install_as_desktop_application()
        sys.exit()
    if args.uninstall:
        install_as_desktop_application(uninstall=True)
        sys.exit()
    if args.detailed_help:
        print(__doc__)
        sys.exit()

    if main_config.is_set(ConfOpt.TRANSLATIONS_ENABLED):
        initialise_locale_translations(app)

    main_controller = VduAppController(main_config)
    VduAppWindow(main_config, main_controller)  # may need to assign this to a variable to prevent garbage collection?

    if args.about:
        AboutDialog.invoke(main_controller)
    if args.create_config_files:
        main_controller.create_config_files()

    rc = app.exec()
    log_info(f"App exit {rc=} {'EXIT_CODE_FOR_RESTART' if rc == EXIT_CODE_FOR_RESTART else ''}")
    if rc == EXIT_CODE_FOR_RESTART:
        reverse_force_xwayland()
        rc = 0
        log_info(f"Trying to restart - this only works if {app.arguments()[0]} is executable and on your PATH): ", )
        restart_status = QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
        if not restart_status:
            MBox(MIcon.Critical, msg=tr("Restart of {} failed.  Please restart manually.").format(app.arguments()[0]),
                 info=tr("This is probably because {} is not executable or is not on your PATH.").format(app.arguments()[0]),
                 buttons=MBtn.Close).exec()
    sys.exit(rc)


if __name__ == '__main__':
    main()
