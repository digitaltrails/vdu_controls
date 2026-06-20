# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
import shutil
import subprocess
import time as sys_time
from datetime import datetime, timedelta
from threading import Lock
from typing import List, Callable, Dict

import vdu_controls.logging as log
from vdu_controls.constants import VDU_CONTROLS_DEVELOPER
from vdu_controls.ddcutil_abstract import BRIGHTNESS_VCP_CODE, DdcutilInterface, DdcDetectedAttributes, VcpValue, DdcCapabilities, \
    VcpTypeInfo
from vdu_controls.ddcutil_abstract import DDCUTIL_RETRIES, CONTINUOUS_TYPE, DdcEventType, DdcutilDisplayNotFound
from vdu_controls.qt_imports import QTimer, QSocketNotifier


class DdcutilPanelImpl(DdcutilInterface):  # Laptop/builtin panel
    """
    Emulates DDC for a laptop-panel by wrapping brightnessctl.
    Also monitors udev for laptop "brightness" events caused by
    screen-saving dimming or brightness up/down keys.
    """

    BRIGHTNESSCTL_EXE = 'brightnessctl'

    @staticmethod
    def is_available() -> bool:
        return shutil.which(DdcutilPanelImpl.BRIGHTNESSCTL_EXE) is not None

    def __init__(self, _: List[str] | None = None, callback: Callable | None = None):
        self.include_leds = VDU_CONTROLS_DEVELOPER  # Test using desktop controllable LEDs
        self.brightness_vcp_code_int = BRIGHTNESS_VCP_CODE
        self.ddcutil_access_lock = Lock()
        self.max_brightness: Dict[str, int] = {}
        if log.debug_enabled:
            version_check = self.__run__('-V').stdout.decode('utf-8')
            log.debug(f"{DdcutilPanelImpl.BRIGHTNESSCTL_EXE} version {version_check}")
        self.set_vcp_time: datetime = datetime.now() - timedelta(seconds=60)  # Last time set_vcp was called
        self.callback = callback
        if self.callback:  # --- udev setup ---
            import pyudev  # Don't make non-laptop users import this.
            self.context = pyudev.Context()
            self.monitor = pyudev.Monitor.from_netlink(self.context)
            self.monitor.filter_by(subsystem='backlight')
            self.monitor.start()  # Start receiving events

            def _on_udev_event(event):
                while True:
                    try:
                        dev = self.monitor.poll(0.1)
                        if dev is None:
                            break
                    except (BlockingIOError, pyudev.DeviceNotFoundError):
                        break
                self.debounce_timer.start(50)  # Debounce: restart timer

            def _invoke_callback():
                if self.callback is not None:
                    if datetime.now() - self.set_vcp_time > timedelta(seconds=1):
                        for edid_txt in self.max_brightness.keys():
                            self.callback(edid_txt, DdcEventType.LAPTOP_BRIGHTNESS_CHANGE.value, 0)

            fd = self.monitor.fileno()  # Get the file descriptor and create a QSocketNotifier
            self.notifier = QSocketNotifier(fd, QSocketNotifier.Type.Read, None)
            self.notifier.activated.connect(_on_udev_event)
            self.debounce_timer = QTimer()
            self.debounce_timer.setSingleShot(True)
            self.debounce_timer.timeout.connect(_invoke_callback)

    def refresh_connection(self):
        pass

    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float):
        pass

    def set_vdu_specific_args(self, edid_txt: str, extra_args: List[str]):
        pass

    def _get_max_brightness(self, edid_txt: str) -> int:
        if not edid_txt in self.max_brightness:
            self.max_brightness[edid_txt] = int(self.__run__("max").stdout)
        return self.max_brightness[edid_txt]

    def __run__(self, *args) -> subprocess.CompletedProcess:
        log_id = DdcutilPanelImpl.BRIGHTNESSCTL_EXE
        process_args = [DdcutilPanelImpl.BRIGHTNESSCTL_EXE] + list(args)
        try:
            with self.ddcutil_access_lock:
                now = sys_time.perf_counter()
                result = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                elapsed = sys_time.perf_counter() - now
                log.debug(f"subprocess result: success {log_id} [{result.args}] "
                          f"rc={result.returncode} elapsed={elapsed:.2f} "
                          f"stdout={result.stdout.decode('utf-8', errors='surrogateescape')}") if log.debug_enabled else None
        except subprocess.CalledProcessError as spe:
            error_text = spe.stderr.decode('utf-8', errors='surrogateescape')
            log.debug("subprocess result: error ", log_id, process_args,
                      f"stderr='{error_text}', exception={str(spe)}", trace=True) if log.debug_enabled else None
            raise
        return result

    def vcp_info(self) -> str:
        return ''

    def get_ddcutil_version_string(self) -> str:
        return '2.2.5'

    def get_interface_version_string(self) -> str:
        return f"Command Line - {DdcutilPanelImpl.BRIGHTNESSCTL_EXE}"

    def detect(self, _: int) -> List[DdcDetectedAttributes]:
        results = []
        cmd_result = self.__run__('-m', 'i')
        for item_number, line in enumerate(cmd_result.stdout.splitlines(), start=1):
            parts = str(line, 'utf-8').split(',')
            if len(parts) > 1 and (parts[1] == 'backlight') or (self.include_leds and parts[1] == 'leds'):
                display_number = str(-item_number)
                usb_bus, usb_device = '', ''
                manufacturer_id, model_name, product_code = 'Unknown', 'Panel', 'Unknown'
                edid_txt = parts[0]
                binary_sn_str = f"BSN#{edid_txt}"
                serial_number = re.sub(r'[^A-Za-z0-9]', '_', parts[0]).title()
                log.info(f"Detected panel {model_name=} {edid_txt=} detected")
                vdu_attributes = DdcDetectedAttributes(
                    display_number, usb_bus, usb_device,
                    manufacturer_id, model_name, serial_number, product_code, edid_txt, binary_sn_str)
                results.append(vdu_attributes)
        return results

    def get_capabilities(self, _: str) -> DdcCapabilities:
        capability_text = ('Model: AB_12345\n'
                           'MCCS version: 2.2\n'
                           'Commands:\n'
                           '   Op Code: 01 (VCP Request)\n'
                           '   Op Code: 02 (VCP Response)\n'
                           '   Op Code: 03 (VCP Set)\n'
                           '   Op Code: 07 (Timing Request)\n'
                           '   Op Code: 0C (Save Settings)\n'
                           '   Op Code: F3 (Capabilities Request)\n'
                           'VCP Features:\n'
                           '   Feature: 10 (Brightness)\n'
                           '   Feature: FF (Dummy to finish)\n')
        return DdcCapabilities('', 0, 0, {}, {}, capability_text)
        #return '', 0, 0, {}, {}, capability_text

    def get_type(self, _: str, vcp_code_int: int) -> VcpTypeInfo:  # edid_txt isn't currently used/supported
        assert vcp_code_int == self.brightness_vcp_code_int  # nothing else supported
        return VcpTypeInfo(False, True)

    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        assert vcp_code_int == self.brightness_vcp_code_int  # nothing else supported
        try:
            physical_value = f"{round(new_value_int * self._get_max_brightness(edid_txt) / 100)}"
            log.info(f"set_vcp: Panel set {new_value_int=} {physical_value=}")
            self.__run__('set', '-d', edid_txt, physical_value)
        finally:
            self.set_vcp_time = datetime.now()

    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        assert vcp_code_int_list[0] == self.brightness_vcp_code_int and len(vcp_code_int_list) == 1
        for attempt_count in range(DDCUTIL_RETRIES):
            try:
                brightness = int(self.__run__('get', '-d', edid_txt).stdout)
                max_brightness = self._get_max_brightness(edid_txt)
                percent = round((100.0 * brightness) / max_brightness)
                log.info(f"get_vcp_values: Panel {brightness=} {max_brightness=} {percent=}")
                return [VcpValue(self.brightness_vcp_code_int, percent, 100, CONTINUOUS_TYPE)]
            except (subprocess.SubprocessError, ValueError, DdcutilDisplayNotFound):
                if attempt_count + 1 == DDCUTIL_RETRIES:  # Don't log here, it creates too much noise in the logs
                    raise  # Too many failures, pass the buck upstairs
            sys_time.sleep(attempt_count * 0.25)
        raise ValueError(f"Exceeded {DDCUTIL_RETRIES} attempts to get vcp values.")
