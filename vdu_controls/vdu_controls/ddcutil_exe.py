# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import re
import subprocess
from collections import namedtuple
import time as sys_time
from threading import Lock
from typing import Dict, List, Tuple, Any

from vdu_controls.ddcutil_abstract import DDCUTIL_RETRIES, VcpValue, CONTINUOUS_TYPE, SIMPLE_NON_CONTINUOUS_TYPE, \
    COMPLEX_NON_CONTINUOUS_TYPE, DdcutilDisplayNotFound, DdcutilInterface
import vdu_controls.logging as log


class DdcutilExeImpl(DdcutilInterface):
    """
    Performs ddcutil requests by executing each request in a one-off ddcutil subprocess.
    Relatively slow due to ddcutil initialization overheads on each request.
    """
    _VCP_CODE_REGEXP = re.compile(r"^VCP ([0-9A-F]{2}) ")  # VCP 2-digit-hex
    _C_PATTERN = re.compile(r'([0-9]+) ([0-9]+)')  # Match Continuous-Type getvcp result
    _SNC_PATTERN = re.compile(r'x([0-9a-f]+)')  # Match Simple Non-Continuous-Type getvcp result
    _CNC_PATTERN = re.compile(r'x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+)')  # Match Complex Non-Continuous-Type result
    _SPECIFIC_VCP_VALUE_PATTERN_CACHE: Dict[int, re.Pattern] = {}
    DetectedAttributes = namedtuple("DetectedAttributes", ('display_number', 'usb_bus', 'usb_device',
                                                           'manufacturer_id', 'model_name', 'serial_number',
                                                           'product_code', 'edid_txt', 'binary_serial_number'))

    def __init__(self, common_args: List[str] | None):
        self.vdu_sleep_multiplier: Dict[str, float] = {}
        self.extra_args: Dict[str, List[str]] = {}
        self.common_args = [arg for arg in os.getenv('VDU_CONTROLS_DDCUTIL_ARGS', default='').split() if arg != '']
        if common_args:
            self.common_args += common_args
        self.ddcutil_access_lock = Lock()
        self.vcp_type_map: Dict[int, str] = {}
        self.ddcutil_version: Tuple[int, ...] = (0, 0, 0)
        self.ddcutil_version_string = "0.0.0"
        self.version_suffix = ''
        self.ddcutil_exe = 'ddcutil'
        self.vdu_map_by_edid: Dict[str, Tuple] = {}

    def refresh_connection(self):
        pass

    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float):
        self.vdu_sleep_multiplier[edid_txt] = sleep_multiplier

    def set_vdu_specific_args(self, edid_txt: str, extra_args: List[str]):
        self.extra_args[edid_txt] = extra_args

    def _get_vdu_human_name(self, edid_txt: str):
        if vdu := self.vdu_map_by_edid.get(edid_txt):
            return f"display-{vdu.display_number} {vdu.model_name}"
        return f"Unknown-display {edid_txt:.30}..."

    def _format_args_diagnostic(self, args: List[str]):
        return ' '.join([arg if len(arg) < 30 else arg[:30] + "..." for arg in args])

    def __run__(self, *args, edid_txt: str | None = None) -> subprocess.CompletedProcess:
        if edid_txt:
            edid_args = ["--edid", edid_txt] if edid_txt else []
            multiplier = self.vdu_sleep_multiplier.get(edid_txt, None)
            multiplier_args = ["--sleep-multiplier", f"{multiplier:4.2f}"] if multiplier else []
        else:
            edid_args = []
            multiplier_args = []
        extra_args = self.extra_args.get(edid_txt, []) if edid_txt else []
        log_id = self._get_vdu_human_name(edid_txt) if (edid_txt and log.debug_enabled) else ''
        syslog_args = []
        if self.ddcutil_version[0] >= 2:
            if log.to_syslog and '--syslog' not in args:
                syslog_args = ['--syslog', 'DEBUG' if log.debug_enabled else 'ERROR']
        process_args = [self.ddcutil_exe] + self.common_args + multiplier_args + syslog_args + extra_args + list(args) + edid_args
        try:
            with self.ddcutil_access_lock:
                now = sys_time.time()
                result = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                elapsed = sys_time.time() - now
                # Shorten EDID to 30 characters when logging it (it will be the only long argument)
                log.debug(f"subprocess result: success {log_id} [{self._format_args_diagnostic(result.args)}] "
                          # f"{process_args=} "
                          f"rc={result.returncode} elapsed={elapsed:.2f} "
                          f"stdout={result.stdout.decode('utf-8', errors='surrogateescape')}") if log.debug_enabled else None
        except subprocess.SubprocessError as spe:
            error_text = spe.stderr.decode('utf-8', errors='surrogateescape')
            if error_text.lower().find("display not found") >= 0:  # raise DdcutilDisplayNotFound and stay quiet
                log.debug("subprocess result: display-not-found ", log_id, self._format_args_diagnostic(process_args),
                          f"stderr='{error_text}', exception={str(spe)}", trace=True) if log.debug_enabled else None
                raise DdcutilDisplayNotFound(' '.join(args)) from spe
            log.debug("subprocess result: error ", log_id, self._format_args_diagnostic(process_args),
                      f"stderr='{error_text}', exception={str(spe)}", trace=True) if log.debug_enabled else None
            raise
        return result

    def vcp_info(self) -> str:
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return self.__run__('--verbose', 'vcpinfo').stdout.decode('utf-8', errors='surrogateescape')

    def get_ddcutil_version_string(self) -> str:
        version_info = self.__run__('--version').stdout.decode('utf-8', errors='surrogateescape')
        if version_match := re.match(r'[a-z]+ ([0-9]+).([0-9]+).([0-9]+)-?([^\n]*)', version_info):
            self.ddcutil_version = tuple(int(i) for i in version_match.groups()[0:3])
            self.version_suffix = version_match.groups()[3]
            self.ddcutil_version_string = \
                f"{self.ddcutil_version[0]}.{self.ddcutil_version[1]}.{self.ddcutil_version[2]} {self.version_suffix}"
        return self.ddcutil_version_string

    def get_interface_version_string(self) -> str:
        return "Command Line - ddcutil"

    def _parse_edid(self, display_str: str) -> str:
        if edid_match := re.search(r'EDID hex dump:\n[^\n]+(\n([ \t]*[+]0).+)+', display_str):
            edid = "".join(re.findall('((?: [0-9a-f][0-9a-f]){16})', edid_match.group(0))).replace(' ', '')
            log.debug(f"{edid=}") if log.debug_enabled else None
            return edid
        log.error(f"Failed to parse edid in {display_str=}")
        return ''

    def detect(self, flags: int) -> List[Tuple[Any, ...]]:
        args = ['detect', '--verbose', ]
        result_list: List[Tuple[Any, ...]] = []
        result = self.__run__(*args)
        # Going to get rid of anything that is not a-z A-Z 0-9 as potential rubbish
        rubbish = re.compile('[^a-zA-Z0-9]+')
        # This isn't efficient, it doesn't need to be, so I'm keeping re-defs close to where they are used.
        for display_str in re.split("\n\n", result.stdout.decode('utf-8', errors='surrogateescape')):
            if display_match := re.search(r'Display ([0-9]+)', display_str):
                vdu_number = display_match.group(1)
                log.debug(f"checking possible IDs for display {vdu_number}") if log.debug_enabled else None
                ds_parts = {fm.group(1).strip(): fm.group(2).strip()
                            for fm in re.finditer(r'[ \t]*([^:\n]+):[ \t]+([^\n]*)', display_str)}  # Create dict {name:value} pairs
                model_name = rubbish.sub('_', ds_parts.get('Model', 'unknown_model'))
                manufacturer = rubbish.sub('_', ds_parts.get('Mfg id', 'unknown_mfg'))
                serial_number = rubbish.sub('_', ds_parts.get('Serial number', ''))
                bin_serial_number = rubbish.sub('_', ds_parts.get('Binary serial number', '').split('(')[0].strip())
                man_date = rubbish.sub('_', ds_parts.get('Manufacture year', ''))
                i2c_bus_id = ds_parts.get('I2C bus', '').replace("/dev/", '').replace("-", "_")
                edid_txt = self._parse_edid(display_str)
                if not edid_txt:
                    log.warning(f"DdcutilExeImpl: failed to parse edid from '{display_str}'")
                vdu_attributes = DdcutilExeImpl.DetectedAttributes(vdu_number, '', '', manufacturer, model_name, serial_number, '',
                                                                   edid_txt, bin_serial_number)
                result_list.append(vdu_attributes)
                self.vdu_map_by_edid[edid_txt] = vdu_attributes
        return result_list

    def get_capabilities(self, edid_txt: str) -> Tuple[
        str, int, int, Dict[bytes, str], Dict[bytes, Tuple[bytes, str, Dict[bytes, str]]], str]:
        result = self.__run__('capabilities', edid_txt=edid_txt)
        capability_text = result.stdout.decode('utf-8', errors='surrogateescape')
        return '', 0, 0, {}, {}, capability_text

    def get_type(self, edid_txt: str, vcp_code_int: int) -> Tuple[bool, bool] | None:  # edid_txt isn't currently used/supported
        type_code = self.vcp_type_map.get(vcp_code_int)
        if type_code is None:
            return False, False
        is_complex = type_code == COMPLEX_NON_CONTINUOUS_TYPE
        is_continuous = type_code == CONTINUOUS_TYPE
        return is_complex, is_continuous

    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        vcp_code = f"{vcp_code_int:02X}"
        new_value = f"x{new_value_int:X}"
        self.__run__('setvcp', vcp_code, new_value, edid_txt=edid_txt)

    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[Tuple[int, int, int, str]]:
        if self.ddcutil_version > (1, 3, 0):
            return self._get_vcp_values_implementation(edid_txt, vcp_code_int_list)
        else:
            return [self._get_vcp_values_implementation(edid_txt, [cd])[0] for cd in vcp_code_int_list]

    def _get_vcp_values_implementation(self, edid_txt: str, vcp_code_list: List[int]) -> List[Tuple[int, int, int, str]]:
        # Try a few times in case there is a glitch due to a monitor being turned-off/on or slow to respond
        args = ['--brief', 'getvcp'] + [f"{c:02X}" for c in vcp_code_list]
        results_dict: Dict[int, VcpValue | None] = {vcp_code: None for vcp_code in vcp_code_list}  # Force vcp_code_list ordering
        for attempt_count in range(DDCUTIL_RETRIES):
            try:
                from_ddcutil = self.__run__(*args, edid_txt=edid_txt)
                for line in from_ddcutil.stdout.split(b"\n"):
                    line_utf8 = line.decode('utf-8', errors='surrogateescape') + '\n'
                    if vcp_code_match := DdcutilExeImpl._VCP_CODE_REGEXP.match(line_utf8):
                        vcp_code = int(vcp_code_match.group(1), 16)
                        results_dict[vcp_code] = self.__parse_vcp_value(vcp_code, line_utf8)
                for vcp_code, vcp_value in results_dict.items():
                    if vcp_value is None:
                        raise ValueError(f"getvcp: {self._get_vdu_human_name(edid_txt)}"
                                         f" - failed to obtain value for vcp_code {vcp_code:02X}")
                # If we reach here, all values v will be non-null
                return [(vcp_code, v.current, v.max, v.vcp_type) for vcp_code, v in results_dict.items()]
            except (subprocess.SubprocessError, ValueError, DdcutilDisplayNotFound):
                if attempt_count + 1 == DDCUTIL_RETRIES:  # Don't log here, it creates too much noise in the logs
                    raise  # Too many failures, pass the buck upstairs
            sys_time.sleep(attempt_count * 0.25)
        raise ValueError(f"Exceeded {DDCUTIL_RETRIES} attempts to get vcp values.")

    def __parse_vcp_value(self, vcp_code: int, result: str) -> VcpValue:
        if not (specific_vcp_value_pattern := DdcutilExeImpl._SPECIFIC_VCP_VALUE_PATTERN_CACHE.get(vcp_code, None)):
            specific_vcp_value_pattern = re.compile(r'VCP ' + f"{vcp_code:02X}" + r' ([A-Z]+) (.+)\n')
            DdcutilExeImpl._SPECIFIC_VCP_VALUE_PATTERN_CACHE[vcp_code] = specific_vcp_value_pattern
        if value_match := specific_vcp_value_pattern.match(result):
            type_indicator = value_match.group(1)
            self.vcp_type_map[vcp_code] = type_indicator
            if type_indicator == CONTINUOUS_TYPE:
                if c_match := DdcutilExeImpl._C_PATTERN.match(value_match.group(2)):
                    return VcpValue(int(c_match.group(1)), int(c_match.group(2)), CONTINUOUS_TYPE)
            elif type_indicator == SIMPLE_NON_CONTINUOUS_TYPE:
                if snc_match := DdcutilExeImpl._SNC_PATTERN.match(value_match.group(2)):
                    return VcpValue(int(snc_match.group(1), 16), 0, SIMPLE_NON_CONTINUOUS_TYPE)
            elif type_indicator == COMPLEX_NON_CONTINUOUS_TYPE:
                if cnc_match := DdcutilExeImpl._CNC_PATTERN.match(value_match.group(2)):
                    return VcpValue(int(cnc_match.group(3), 16) << 8 | int(cnc_match.group(4), 16), 0, COMPLEX_NON_CONTINUOUS_TYPE)
            else:
                raise TypeError(f'Unsupported VCP type {type_indicator} vcp_code {vcp_code}')
        raise ValueError(f"VDU vcp_code {vcp_code} failed to parse vcp value '{result}'")

