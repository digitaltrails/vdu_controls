# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
import threading
from collections import defaultdict, deque
from typing import List, Dict, Callable, Tuple, NewType, DefaultDict
import time as sys_time

import vdu_controls.logging as log
from vdu_controls.constants import getenv_logged
from vdu_controls.ddcutil_abstract import VcpValue, DdcutilServiceNotFound, DdcutilInterface, VcpTypeInfo, DdcutilSetterRateExceeded
from vdu_controls.ddcutil_emulator import DdcutilEmulatorImpl
from vdu_controls.ddcutil_exe import DdcutilExeImpl
from vdu_controls.ddcutil_laptop_panel import DdcutilPanelImpl
from vdu_controls.ddcutil_qdbus import DdcutilDBusImpl


VduStableId = NewType('VduStableId', str)


class DdcutilAggregator(DdcutilInterface):
    """
    Routes operations to relevant DdcutilInterface instances and aggregates the results.
    For example, a "detect" might be routed to all instances, such as DdcutilDbusImpl and
    DdcutilPanelImpl, with the results aggregated together.
    """
    vcp_write_counters: DefaultDict[str, int] = defaultdict(int)

    _setter_history: dict[tuple[str, int], deque] = {}
    _setter_history_lock = threading.Lock()
    _setter_cascade_detected = False
    _RATE_WINDOW_SECONDS = int(getenv_logged("VDU_CONTROLS_SETTER_RATE_SECS", '65'))  # Set either to zero to disable checks.
    _RATE_MAX_CALLS = int(getenv_logged("VDU_CONTROLS_SETTER_RATE_CALLS", '20'))

    def __init__(self, common_args: List[str] | None = None, prefer_dbus_client: bool = True,
                 connected_vdus_changed_callback: Callable | None = None) -> None:
        super().__init__()
        self.common_args = common_args
        self.ddcutil_emulators_by_edid: Dict[str, DdcutilInterface] = {}
        self.ddcutil_impl: DdcutilDBusImpl | DdcutilExeImpl  # The service-interface implementations are duck-typed.
        if prefer_dbus_client:
            try:
                self.ddcutil_impl = DdcutilDBusImpl(self.common_args, callback=connected_vdus_changed_callback)
            except DdcutilServiceNotFound:
                log.warning("Failed to detect D-Bus ddcutil-service, falling back to the ddcutil command.")
                prefer_dbus_client = False

        if not prefer_dbus_client:  # dbus not preferred or dbus failed to initialize
            self.ddcutil_impl = DdcutilExeImpl(self.common_args)

        self.supported_codes: Dict[int, str] = {}
        self.vcp_type_map: Dict[Tuple[str, int], VcpTypeInfo] = {}
        self.edid_txt_map: Dict[str, str] = {}
        self.ddcutil_version: Tuple[int, ...] = (0, 0, 0)  # Initial version for bootstrapping
        self.version_suffix = ''
        version_info = self.ddcutil_impl.get_ddcutil_version_string()
        if version_match := re.match(r'[a-z]* ?([0-9]+).([0-9]+).([0-9]+)-?([^\n]*)', version_info):
            self.ddcutil_version = tuple(int(i) for i in version_match.groups()[0:3])
            self.version_suffix = version_match.groups()[3]
        # self.version = (1, 2, 2)  # for testing for 1.2.2 compatibility
        log.info(f"ddcutil version {self.ddcutil_version} "
                 f"{self.version_suffix}(dynamic-sleep={self.ddcutil_version >= (2, 0, 0)}) "
                 f"- interface {self.ddcutil_impl.get_interface_version_string()}")

    def ddcutil_version_info(self) -> Tuple[str, str]:
        return self.ddcutil_impl.get_interface_version_string(), self.ddcutil_impl.get_ddcutil_version_string()

    def add_ddcutil_emulator(self, emulator: DdcutilPanelImpl | DdcutilEmulatorImpl):
        try:
            for attr in emulator.detect(1):
                log.info(f"add_ddcutil_emulator: VDU edid={attr.edid_txt}")
                self.ddcutil_emulators_by_edid[attr.edid_txt] = emulator
        except Exception as e:
            log.error(f"add_ddcutil_emulator exception: {e}")

    def _impl(self, edid: str) -> DdcutilInterface:
        if emulator_impl := self.ddcutil_emulators_by_edid.get(edid):  # edid is for a virtual implementation
            return emulator_impl  # A virtual ddcutil implementation - probably a laptop panel
        return self.ddcutil_impl  # Use real implementation

    def refresh_connection(self):
        self.ddcutil_impl.refresh_connection()
        for emulator_impl in self.ddcutil_emulators_by_edid.values():
            emulator_impl.refresh_connection()

    def set_sleep_multiplier(self, vdu_number: str, sleep_multiplier: float):
        try:
            edid = self.get_edid_txt(vdu_number)
            self._impl(edid).set_sleep_multiplier(edid, sleep_multiplier)
        except ValueError as e:
            if str(e).find('com.ddcutil.DdcutilService.Error.MultiplierLocked') > 0:
                log.warning(f"Ignoring: {e}")
            else:
                raise

    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]):
        edid = self.get_edid_txt(vdu_number)
        self._impl(edid).set_vdu_specific_args(edid, extra_args)

    def get_edid_txt(self, vdu_number: str) -> str:
        return self.edid_txt_map.get(vdu_number, vdu_number)  # no edid probably means a simulated VDU

    def get_write_count(self, vdu_number: str) -> int:
        if edid_txt := self.get_edid_txt(vdu_number):
            return DdcutilAggregator.vcp_write_counters[edid_txt]
        return 0

    def detect_vdus(self) -> List[Tuple[str, str, str, str]]:
        """Return a list of (vdu_number, desc) tuples."""
        result_list = []
        vdu_list = self.ddcutil_impl.detect(0)
        log.info(f"detecting using {len(self.ddcutil_emulators_by_edid)} emulators")
        for emulator_impl in set(self.ddcutil_emulators_by_edid.values()):  # Use set() to only use each emulator once.
            vdu_list += emulator_impl.detect(0)
        # Going to get rid of anything that is not a-z A-Z 0-9 as potential rubbish
        rubbish = re.compile('[^a-zA-Z0-9]+')
        # This isn't efficient, it doesn't need to be, so I'm keeping re-defs close to where they are used.
        key_prospects: Dict[Tuple[str, str], Tuple[str, str]] = {}
        for vdu in vdu_list:
            vdu_number = str(vdu.display_number)
            log.debug(f"checking possible IDs for display {vdu_number}") if log.debug_enabled else None
            model_name = rubbish.sub('_', vdu.model_name)
            manufacturer = rubbish.sub('_', vdu.manufacturer_id)
            serial_number = rubbish.sub('_', vdu.serial_number)
            bin_serial_number = str(vdu.binary_serial_number)
            man_date = ''  # TODO rubbish.sub('_', ds_parts.get('Manufacture year', ''))
            i2c_bus_id = ''  # TODO ds_parts.get('I2C bus', '').replace("/dev/", '').replace("-", "_")
            edid = vdu.edid_txt
            # check for duplicate edid, any duplicate will use the display Num
            if edid is not None and edid not in self.edid_txt_map.values():
                self.edid_txt_map[vdu_number] = edid
            for candidate in serial_number, bin_serial_number, man_date, i2c_bus_id, f"DisplayNum{vdu_number}":
                if candidate.strip() != '':
                    possibly_unique = (model_name, candidate)
                    if possibly_unique in key_prospects:  # Not unique - it has already been encountered.
                        log.info(f"Ignoring non-unique key {possibly_unique=}"
                                 f" - it matches display {vdu_number=} already in {possibly_unique}")
                        del key_prospects[possibly_unique]
                    else:
                        key_prospects[possibly_unique] = vdu_number, manufacturer
        # Try and pin down a unique id that won't change even if other monitors are turned off. Ideally, this should
        # yield the same result for the same monitor - DisplayNum is the worst for that, so it's the fallback.
        key_already_assigned = {}
        for model_and_main_id, vdu_number_and_manufacturer in key_prospects.items():
            vdu_number, manufacturer = vdu_number_and_manufacturer
            if vdu_number not in key_already_assigned:
                model_name, main_id = model_and_main_id
                log.debug(
                    f"Unique key for {vdu_number=} {manufacturer=} is ({model_name=} {main_id=})") if log.debug_enabled else None
                result_list.append((vdu_number, manufacturer, model_name, main_id))
                key_already_assigned[vdu_number] = 1
        # result_list.append(("3", "maker_y", "model_z", "1234")) # For testing bad VDUs:
        return result_list

    def query_capabilities(self, vdu_number: str) -> str:
        edid_txt = self.get_edid_txt(vdu_number)
        capabilities = self._impl(edid_txt).get_capabilities(edid_txt)
        if capabilities.capabilities_str:  # The service supplies pre-assembled capabilities text.
            return capabilities.capabilities_str
        model = capabilities.model
        mccs_major = capabilities.mccs_major
        mccs_minor = capabilities.mccs_minor
        capability_text = f"Model: {model}\nMCCS version: {mccs_major}.{mccs_minor}\nVCP Features:\n"
        for feature_id, feature in capabilities.features.items():
            feature_code = f"{int.from_bytes(feature_id, 'big'):02X}"
            feature_name = feature[0]
            feature_values = feature[2]
            capability_text += f"   Feature: {feature_code} ({feature_name})\n"
            if len(feature_values) != 0:
                if all(value == '' for value in feature_values.values()):
                    capability_text += "      Values:"
                    for value_id in feature_values.keys():
                        capability_text += f" {int.from_bytes(value_id, 'big'):02X}"
                    capability_text += " (interpretation unavailable)\n"
                else:
                    capability_text += "      Values:\n"
                    for value_id, value_name in feature_values.items():
                        value_code = f"{int.from_bytes(value_id, 'big'):02X}"
                        capability_text += f"         {value_code}: {value_name}\n"
        return capability_text

    def get_type(self, vdu_number: str, vcp_code: int) -> VcpTypeInfo:  # may not be needed with a dbus implementation
        # TODO I don't think anything uses this - maybe it should be removed.
        edid_txt = self.get_edid_txt(vdu_number)
        vcp_type_key = (edid_txt, vcp_code)
        if info := self.vcp_type_map.get(vcp_type_key):
            return info
        info = self._impl(edid_txt).get_type(edid_txt, vcp_code)
        self.vcp_type_map[vcp_type_key] = info
        return info

    @classmethod
    def clear_setter_cascade_blocking(cls):
        with cls._setter_history_lock:
            cls._setter_cascade_detected = False
            cls._setter_history.clear()

    @classmethod
    def _check_setter_rate_limit(cls, key: tuple[str, int]) -> bool:
        """
        Enforce sliding‑window rate limit for a given (vdu_number, vcp_code).
        Raises DdcutilRateLimitExceeded if too many calls are made in the time window.
        Boilerplate.

        Once too many calls are made block further writes until reset

        Returns True if all is OK, False if rate has been exceeded.
        """
        if cls._RATE_MAX_CALLS == 0 or cls._RATE_WINDOW_SECONDS == 0:
            return True

        with cls._setter_history_lock:

            if cls._setter_cascade_detected:
                log.debug("Rate limit currently exceeded - waiting for it to be reset.") if log.debug_enabled else None
                return False

            now = sys_time.monotonic()
            vdu_vcp_history = cls._setter_history.setdefault(key, deque())
            log.debug(f"{key=} {len(vdu_vcp_history)=}") if log.debug_enabled else None

            while vdu_vcp_history and (now - vdu_vcp_history[0]) > cls._RATE_WINDOW_SECONDS:  # Prune expired entries
                vdu_vcp_history.popleft()

            vdu_vcp_history.append(now)
            if len(vdu_vcp_history) > cls._RATE_MAX_CALLS: # Check if a cascade might be occurring
                cls._setter_cascade_detected = True   # stop all setting
                vdu_number, vcp_code = key
                log.error(msg := f"Cascade detected for {vdu_number=} {vcp_code=:#02x} : {len(vdu_vcp_history)} calls in last "
                                 f"{cls._RATE_WINDOW_SECONDS}s (limit {cls._RATE_MAX_CALLS})")
                raise DdcutilSetterRateExceeded(msg)
            return True

    def set_vcp(self, vdu_number: str, vcp_code: int, new_value: int) -> None:
        key = (vdu_number, vcp_code)
        if not self._check_setter_rate_limit(key):  # check if rate limit is exceeded, raises if exceeded
            return   # When the limit is reached, stop writing until reset is called.
        edid_txt = self.get_edid_txt(vdu_number)
        impl = self._impl(edid_txt)
        impl.set_vcp(edid_txt, vcp_code, new_value)
        DdcutilAggregator.vcp_write_counters[edid_txt] += 1
        log.debug(f"set_vcp: {vdu_number=} {vcp_code=:#02x} {new_value=}") if log.debug_enabled else None

    def vcp_info(self) -> str:
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return DdcutilExeImpl([]).vcp_info()

    def get_supported_vcp_codes_map(self) -> Dict[int, str]:
        """Returns a map of descriptions keyed by vcp_code, the codes that ddcutil appears to support."""
        if len(self.supported_codes) == 0:  # Initialize on demand
            info = self.vcp_info()
            code_definitions = info.split("\nVCP code ")
            for code_def in code_definitions[1:]:
                lines = code_def.split('\n')
                vcp_code_str, vcp_name = lines[0].split(': ', 1)
                vcp_code = int(vcp_code_str, 16)
                ddcutil_feature_subsets = None
                for line in lines[2:]:
                    line = line.strip()
                    if line.startswith('ddcutil feature subsets:'):
                        ddcutil_feature_subsets = line.split(": ", 1)
                if ddcutil_feature_subsets is not None:
                    if vcp_code not in self.supported_codes:
                        self.supported_codes[vcp_code] = vcp_name
        return self.supported_codes

    def get_vcp_values(self, vdu_number: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        values_dict: Dict[int, VcpValue | None] = {vcp_code: None for vcp_code in vcp_code_int_list}
        edid_txt = self.get_edid_txt(vdu_number)
        impl = self._impl(edid_txt)
        values_list = impl.get_vcp_values(edid_txt, vcp_code_int_list)
        for vcp_value in values_list:
            values_dict[vcp_value.vcp_code] = vcp_value
        results = []
        for vcp_code, value in values_dict.items():
            if value is None:  # If all attempts failed, the values_dict will be missing one or more values.
                raise ValueError(f"getvcp: display-{vdu_number} - failed to obtain value for {vcp_code=:#02x}")
            results.append(value)  # if we reach here all values will be present (none are None).
        log.debug(f"DdcutilAggregator {results=}") if log.debug_enabled else None
        return results


