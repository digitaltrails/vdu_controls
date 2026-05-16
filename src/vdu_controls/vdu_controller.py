# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import queue
import re
import subprocess
from typing import Callable, Dict, Tuple, List

from vdu_controls.qt_imports import QObject, pyqtSignal

from vdu_controls.vdu_controls_config import VduControlsConfig, ConfOpt, SUPPORTED_VCP_BY_CODE, VcpCapability
from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import IGNORE_VDU_MARKER_STR, ASSUMED_CONTROLS_CONFIG_VCP_CODES, ASSUMED_CONTROLS_CONFIG_TEXT

from vdu_controls.ddcutil_abstract import VcpOrigin, VcpValue, DdcutilDisplayNotFound, CONTINUOUS_TYPE, COMPLEX_NON_CONTINUOUS_TYPE, \
    SIMPLE_NON_CONTINUOUS_TYPE, BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE
from vdu_controls.ddcutil_aggregator import DdcutilAggregator, VduStableId
import vdu_controls.logging as log
from vdu_controls.misc import proper_name
from vdu_controls.vdu_exceptions import VduException
from vdu_controls.work_scheduler import WorkerThread


class VduControllerAsyncSetter(WorkerThread):  # Used to decouple the set-vcp from the GUI

    def __init__(self):
        super().__init__(task_body=self._async_setvcp_task_body, task_finished=None, loop=True)
        self._async_setvcp_queue: queue.Queue = queue.Queue()
        # limit set_vcp to a sustainable interval - KDE powerdevil recommendation - 0.5s, ddcui 1.0 seconds
        self._idle_seconds = float(os.getenv("VDU_CONTROLS_UI_IDLE_SECS", '0.5'))
        log.info(f"env VDU_CONTROLS_UI_IDLE_SECS={self._idle_seconds}")

    def _async_setvcp_task_body(self, _: WorkerThread):
        latest_pending = {}  # Handle bursts of UI setvcp requests, filtering out repeats for the same feature.
        while not self._async_setvcp_queue.empty():  # Keep going while there is something in the queue
            try:
                # print(f"{self._async_setvcp_queue.qsize()=}")
                controller, vcp_code, value, origin = self._async_setvcp_queue.get_nowait()
                key = (controller, vcp_code)
                if log.debug_enabled:
                    log.debug(f"UI discard earlier op on {controller.vdu_number=} {vcp_code=:#02x}") if key in latest_pending else None
                latest_pending[key] = (value, origin)  # keep the latest for each controller+vcp_code.
                self._async_setvcp_queue.task_done()
            except queue.Empty:
                pass
            if latest_pending and self._async_setvcp_queue.empty():  # some setvcp requests are pending,
                self.doze(self._idle_seconds)  # wait a bit in case more arrive - might be dragging a slider or spinning a spinner
        if latest_pending:  # nothing more has arrived, if any setvcp requests are pending, set for real now
            for (controller, vcp_code), (value, origin) in latest_pending.items():
                if controller.values_cache.get(vcp_code, None) != value:
                    log.debug(f"UI set {controller.vdu_number=} {vcp_code=:#02x} {value=} {origin}") if log.debug_enabled else None
                    controller.set_vcp_value(vcp_code, value, origin, asynchronous_caller=True)
                else:
                    log.debug(f"UI nochange {controller.vdu_number=} {vcp_code=:#02x} {value=} {origin}") if log.debug_enabled else None
        else:
            self.doze(self._idle_seconds)

    def queue_setvcp(self, controller: VduController, vcp_code: int, value: int, origin: VcpOrigin):
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
    _RANGE_PATTERN = re.compile(r'Values:\s+([0-9]+)[.][.]([0-9]+)')
    _FEATURE_PATTERN = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\s(.*)', re.DOTALL | re.MULTILINE)
    _LIMITED_RANGE_KEY = "%%RANGE%%"  # A key internal to vdu_controls for storing Range n..m values.
    _FORCE_REFRESH_NAME_SUFFIX = "*refresh*"

    vcp_value_changed_qtsignal = pyqtSignal(str, int, int, VcpOrigin, bool)
    _async_setvcp_exception_qtsignal = pyqtSignal(int, int, VcpOrigin, Exception)

    _async_setvcp_task: VduControllerAsyncSetter | None = None

    def __init__(self, vdu_number: str, vdu_model_name: str, serial_number: str, manufacturer: str,
                 default_config: VduControlsConfig, ddcutil: DdcutilAggregator, edit_config: Callable,
                 vdu_exception_handler: Callable, remedy: int = 0) -> None:
        super().__init__()
        self.no_longer_in_use = False
        if vdu_model_name.strip() == '':  # laptop monitors can sneak through with no model_name
            vdu_model_name = "Unknown"
        self.vdu_stable_id = VduStableId(proper_name(vdu_model_name, serial_number))
        log.info(f"Initializing controls for {vdu_number=} {vdu_model_name=} {self.vdu_stable_id=}")
        self.vdu_number = vdu_number
        self.model_name = vdu_model_name
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.edit_config_callable = edit_config
        self.vdu_exception_handler = vdu_exception_handler

        def _handle_async_setvcp_exception(vcp_code: int, value: int, origin: VcpOrigin, e: VduException):
            if self.vdu_exception_handler(e, True):
                self.set_vcp_value_asynchronously(vcp_code, value, origin)

        self._async_setvcp_exception_qtsignal.connect(_handle_async_setvcp_exception)
        if VduController._async_setvcp_task is None or VduController._async_setvcp_task.isFinished():
            VduController._async_setvcp_task = VduControllerAsyncSetter()
            VduController._async_setvcp_task.start()

        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text: str | None = None
        self.config = None
        self.values_cache: Dict[int, int] = {}
        self.ignore_vdu = remedy == VduController.IGNORE_VDU
        default_sleep_multiplier: float | None = default_config.get_sleep_multiplier(fallback=None)
        enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        for config_name in (self.vdu_stable_id, self.vdu_model_id):  # Allow for shared single model file (not encouraged).
            config_path = ConfIni.get_path(config_name)
            log.debug("checking for config file '" + config_path.as_posix() + "'") if log.debug_enabled else None
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
                log.info(f"Capabilities override set to ignore VDU {vdu_number=} {vdu_model_name=} {self.vdu_stable_id=}")
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

    def get_vcp_values(self, vcp_codes: List[int]) -> List[VcpValue]:
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
                        if log.debug_enabled:
                            log.debug(
                                f"get_vcp signals vcp_value_changed: {self.vdu_stable_id} {vcp_code=:02x} {value} {VcpOrigin.EXTERNAL}")
                        self.vcp_value_changed_qtsignal.emit(self.vdu_stable_id, vcp_code, value, VcpOrigin.EXTERNAL,
                                                             self.capabilities_supported_by_this_vdu[vcp_code].causes_config_change)
            return values
        except (subprocess.SubprocessError, ValueError, TimeoutError, DdcutilDisplayNotFound) as e:
            codes_csv = ", ".join([f"{vcp_code:02x}" for vcp_code in vcp_codes])
            raise VduException(vdu_description=self.get_vdu_preferred_name(), vcp_code=codes_csv,
                               exception=e, operation="get_vcp_values") from e

    def set_vcp_value(self, vcp_code: int, value: int, origin: VcpOrigin = VcpOrigin.NORMAL,
                      asynchronous_caller: bool = False) -> None:
        if self.no_longer_in_use:
            log.info(f"Expired controller discards set_vcp_value({vcp_code=:#02x}, {value=}, {origin=}) {asynchronous_caller=}")
            return
        try:
            # raise subprocess.SubprocessError("set_attribute")  # for testing
            retry_on_error = vcp_code in SUPPORTED_VCP_BY_CODE and SUPPORTED_VCP_BY_CODE[vcp_code].retry_setvcp
            self.ddcutil.set_vcp(self.vdu_number, vcp_code, value, retry_on_error=retry_on_error)
            self.values_cache[vcp_code] = value
            if log.debug_enabled:
                log.debug(f"set_vcp signals vcp_value_changed: {self.vdu_stable_id} {vcp_code=:#02x} {value} {origin}")
            self.vcp_value_changed_qtsignal.emit(self.vdu_stable_id, vcp_code, value, origin,
                                                 self.capabilities_supported_by_this_vdu[vcp_code].causes_config_change)
        except (subprocess.SubprocessError, ValueError, TimeoutError, DdcutilDisplayNotFound) as e:
            vdu_exception = VduException(vdu_description=self.get_vdu_preferred_name(), vcp_code=vcp_code, exception=e,
                                         operation="set_vcp_value")
            if not asynchronous_caller:
                raise vdu_exception from e
            self._async_setvcp_exception_qtsignal.emit(vcp_code, value, origin, vdu_exception)

    def set_vcp_value_asynchronously(self, vcp_code: int, value: int, origin: VcpOrigin = VcpOrigin.NORMAL) -> None:
        # Queue the change for the queue processing thread - avoids blocking the GUI.
        VduController._async_setvcp_task.queue_setvcp(self, vcp_code, value, origin)

    def get_range_restrictions(self, vcp_code: int, fallback: Tuple[int, int] | None = None) -> Tuple[int, int] | None:
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
                vcp_code = int(feature_match.group(1), 16)
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
                elif (vcp_code in SUPPORTED_VCP_BY_CODE
                      and SUPPORTED_VCP_BY_CODE[vcp_code].vcp_type == CONTINUOUS_TYPE):
                    # Standard MCCS-Continuous VCP (e.g. brightness 10, contrast 12) appearing with a
                    # spurious Values: block.  Some VDUs (observed on Philips Evnia firmware) repeat a
                    # Feature: 10/12 line inside a manufacturer-specific section with discrete values,
                    # which the parser would otherwise mis-classify as non-continuous and overwrite the
                    # earlier correct definition.  Trust the MCCS-standard type and discard the values.
                    log.warning(f"Ignoring spurious Values: for known-continuous VCP-Code {vcp_code:#02x}: {values}")
                    vcp_type = CONTINUOUS_TYPE
                    values = []
                else:  # two-byte or one-byte continuous type - cannot always trust the VDU metadata on this.
                    try:  # See whether the max is really contained within one byte:
                        max_value = max([int(v, 16) for v, _ in values])
                        vcp_type = COMPLEX_NON_CONTINUOUS_TYPE if max_value > 0xff else SIMPLE_NON_CONTINUOUS_TYPE
                    except ValueError:
                        vcp_type = COMPLEX_NON_CONTINUOUS_TYPE  # Assume two byte

                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None,
                                           can_transition=vcp_type == CONTINUOUS_TYPE, causes_config_change=requires_refresh)
                if vcp_code in feature_map:
                    # The VDU's capability string declared the same Feature: code more than once.
                    # Keep the first occurrence (which the parser already processed) and log the duplicate
                    # for diagnostics.  Avoids manufacturer-specific section bleed-through silently
                    # overwriting standard VCP-code definitions.  Use warning for codes vdu_controls
                    # exposes as a control (user-visible impact), info otherwise (firmware metadata noise).
                    log_fn = log.warning if vcp_code in SUPPORTED_VCP_BY_CODE else log.info
                    log_fn(f"Duplicate Feature: {vcp_code=:#02x} in capability string; keeping first occurrence "
                           f"(ignored second: vcp_type={vcp_type}, values={values})")
                else:
                    feature_map[vcp_code] = capability
        return {**{k: feature_map[k] for k in (BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE) if k in feature_map},  # Put B&C first
                **{k: v for k, v in feature_map.items() if k not in (BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE)}}
