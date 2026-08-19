# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import json
import os
import time as sys_time
import threading
from types import SimpleNamespace
from typing import Dict, Tuple, Callable, List, Optional, Any
from threading import Lock

# TODO make these imports conditional on using varlink
from varlink import Client, VarlinkError

import vdu_controls.app_logging as log
from vdu_controls.constants import getenv_logged
from vdu_controls.ddcutil_abstract import (
    DdcutilServiceNotFound, DdcutilDisplayNotFound, DdcutilInterface,
    DdcDetectedAttributes, VcpValue, DdcCapabilities, VcpTypeInfo
)
from vdu_controls.misc import intV  # may be unused


def to_namespace(data):
    """Recursively converts Varlink objects, dictionaries, and lists into SimpleNamespaces."""
    if hasattr(data, "as_dict") and callable(getattr(data, "as_dict")):
        data = data.as_dict()
    if isinstance(data, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in data.items()})
    elif isinstance(data, list):
        return [to_namespace(i) for i in data]
    return data


class DdcutilVarlinkImpl(DdcutilInterface):
    """
    Implements DdcutilInterface using the varlink ddcutil-service.
    """

    _metadata_cache: Dict[Tuple[str, int], VcpTypeInfo] = {}
    _current_connected_displays_changed_handler: Optional[Callable] = None
    _current_service_initialization_handler: Optional[Callable] = None
    _service_lock = Lock()
    _event_thread: Optional[threading.Thread] = None
    _stop_event = threading.Event()

    def __init__(self, common_args: List[str] | None = None, callback: Callable | None = None):
        super().__init__()
        self.varlink_socket = getenv_logged(
            'DDCUTIL_VARLINK_SOCKET',
            default=f"unix:/run/user/{os.getuid()}/ddcutil-varlink.socket"
        )
        self.service_name = getenv_logged(
            'DDCUTIL_VARLINK_INTERFACE',
            default="com.ddcutil.DdcutilInterface"
        )
        env_args = [arg for arg in getenv_logged('VDU_CONTROLS_DDCUTIL_ARGS', default='').split() if arg != '']
        self.common_args = env_args + (common_args if common_args else [])
        self.listener_callback: Optional[Callable] = callback
        self._connection: Optional[Client] = None
        self._stub: Optional[Any] = None
        self._display_map: Dict[str, int] = {}  # edid_base64 -> display_number

        # Connect and sanity check
        for try_count in range(1, 5):
            try:
                self._connect_to_service()
                # Lightweight call: GetServiceInterfaceVersion
                self.get_interface_version_string()
                break
            except Exception as e:
                log.error(f"Varlink sanity check try {try_count}: {e}")
                if try_count >= 4:
                    raise DdcutilServiceNotFound(f"Error contacting varlink service: {e}")
                sys_time.sleep(2)

        # Restart with common_args (unlikely to be supported, but kept for compatibility)
        if self.common_args:
            log.warning("Varlink service does not support Restart; common_args ignored.")

        # Start event subscription if callback provided
        if self.listener_callback is not None:
            self._start_event_subscription()

    def _connect_to_service(self) -> None:
        try:
            self._connection = Client(self.varlink_socket)
            self._stub = self._connection.open(self.service_name)
        except (ConnectionRefusedError, FileNotFoundError) as e:
            raise DdcutilServiceNotFound(f"Cannot connect to varlink service: {e}")

    def _call(self, method: str, *args, **kwargs) -> Any:
        """
        Low‑level varlink call with error conversion.
        Returns the result as a SimpleNamespace (via to_namespace).
        """
        with self._service_lock:
            try:
                func = getattr(self._stub, method)
                result = func(*args, **kwargs)
                return to_namespace(result)
            except VarlinkError as e:
                error_name = e.error()
                log.error(f"Varlink error: {error_name}, params: {to_namespace(e.parameters())}")
                if error_name == 'com.ddcutil.DdcutilInterface.DisplayNotFound':
                    raise DdcutilDisplayNotFound(str(e))
                elif error_name in ('com.ddcutil.DdcutilInterface.DdcError',
                                    'com.ddcutil.DdcutilInterface.DetectError'):
                    raise ValueError(str(e))
                elif error_name == 'com.ddcutil.DdcutilInterface.ConfigurationLocked':
                    raise RuntimeError("Configuration locked")
                else:
                    raise ValueError(f"Varlink error: {e}")

    def _resolve_display_identifier(self, edid_txt: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Convert the public EDID string (assumed to be base64) or a numeric display number
        into (display_number, edid_base64) for varlink methods.
        """
        if edid_txt.isdigit():
            return int(edid_txt), None
        # Assume it's base64 EDID; look up display number if available
        display_num = self._display_map.get(edid_txt)
        return (display_num, edid_txt) if display_num is not None else (None, edid_txt)

    # ----------------------------------------------------------------------
    # Public API (matching DdcutilInterface)
    # ----------------------------------------------------------------------

    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._call("SetSleepMultiplier", display_num, edid_b64, sleep_multiplier, None)

    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]) -> None:
        log.debug("set_vdu_specific_args not implemented for varlink")

    def get_ddcutil_version_string(self) -> str:
        res = self._call("GetDdcutilVersion")
        return res.version

    def get_interface_version_string(self) -> str:
        res = self._call("GetServiceInterfaceVersion")
        return f"{res.version} (Varlink ddcutil-service)"

    def _get_status_values(self) -> Dict[int, str]:
        # Not exposed; return empty dict.
        return {}

    def detect(self, flags: int) -> List[DdcDetectedAttributes]:
        include_offline = bool(flags & 1)
        res = self._call("Detect", include_offline)
        result_list = []
        for d in res.displays:
            attrs = DdcDetectedAttributes(
                display_number=str(d.display_number),
                usb_bus=str(d.usb_bus),
                usb_device=str(d.usb_device),
                manufacturer_id=str(d.mfg_id),
                model_name=str(d.model_name),
                serial_number=str(d.serial_number),
                product_code=str(d.product_code),
                edid_txt=str(d.edid_base64),
                binary_serial_number=str(d.edid_serial_number)
            )
            result_list.append(attrs)
            self._display_map[attrs.edid_txt] = d.display_number
        return result_list

    def get_capabilities(self, edid_txt: str) -> DdcCapabilities:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._call("GetCapabilitiesMetadata", display_num, edid_b64, None)
        # Convert commands and capabilities arrays to strings for compatibility
        commands_str = ', '.join(f"{item.key}:{item.value}" for item in res.commands)
        capabilities_str = ', '.join(f"{item.key}:{item.value.feature_name}" for item in res.capabilities)
        return DdcCapabilities(
            res.model_name,
            res.mccs_major,
            res.mccs_minor,
            commands_str,
            capabilities_str,
            ''   # extra field not used
        )

    def get_type(self, edid_txt: str, vcp_code_int: int) -> VcpTypeInfo:
        key = (edid_txt, vcp_code_int)
        if key in self._metadata_cache:
            return self._metadata_cache[key]
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._call("GetVcpMetadata", display_num, edid_b64, vcp_code_int, None)
        info = VcpTypeInfo(res.is_complex, res.is_continuous)
        self._metadata_cache[key] = info
        return info

    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._call("SetVcp", display_num, edid_b64, vcp_code_int, new_value_int, None, None)

    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._call("GetMultipleVcp", display_num, edid_b64, vcp_code_int_list, None)
        result = []
        for v in res.values:
            result.append(VcpValue(v.vcp_code, v.current, v.maximum, None))
        return result

    def vcp_info(self):
        pass

    def refresh_connection(self):
        try:
            self._call("GetServiceInterfaceVersion")
        except Exception:
            log.error("Varlink connection lost, reconnecting...")
            self._connect_to_service()
            if self.listener_callback is not None:
                self._start_event_subscription()

    # ----------------------------------------------------------------------
    # Event subscription
    # ----------------------------------------------------------------------

    def _start_event_subscription(self) -> None:
        if self._event_thread is not None and self._event_thread.is_alive():
            self._stop_event.set()
            self._event_thread.join(timeout=1.0)
        self._stop_event.clear()
        self._event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._event_thread.start()

    def _event_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self._stub is None:
                    self._connect_to_service()
                # Subscribe with use_polling=False (event-driven)
                event_stream = self._stub.Subscribe(False, _more=True)
                for raw_event in event_stream:
                    if self._stop_event.is_set():
                        break
                    self._handle_event(raw_event)
            except VarlinkError as e:
                log.error(f"Event stream error: {e}")
                if not self._stop_event.wait(2.0):
                    continue
            except Exception as e:
                log.error(f"Unexpected error in event loop: {e}")
                if not self._stop_event.wait(2.0):
                    continue

    def _handle_event(self, raw_event) -> None:
        ev = to_namespace(raw_event)
        event_obj = ev.event
        kind = event_obj.kind
        data = event_obj.data

        if kind == 'service_initialized':
            log.info("Service initialized event")
            if DdcutilVarlinkImpl._current_service_initialization_handler:
                DdcutilVarlinkImpl._current_service_initialization_handler('', -1, 0)
            if self.listener_callback:
                self.listener_callback('', -1, 0)

        elif kind == 'connected_displays_changed':
            log.info("Connected displays changed event")
            try:
                details = json.loads(data)
                event_type = details['event_type']
                flags = details['flags']
                if DdcutilVarlinkImpl._current_connected_displays_changed_handler:
                    DdcutilVarlinkImpl._current_connected_displays_changed_handler(event_type, flags, 0)
                if self.listener_callback:
                    self.listener_callback(event_type, flags, 0)
            except Exception as e:
                log.error(f"Error parsing connected_displays_changed data: {e}")

        elif kind == 'vcp_changed':
            log.debug("VCP changed event (ignored)")

        elif kind == 'stream_closed':
            log.info("Stream closed by server")
            self._stop_event.set()

    # ----------------------------------------------------------------------
    # Additional varlink methods (not in abstract, but available)
    # ----------------------------------------------------------------------

    def get_capabilities_string(self, edid_txt: str) -> str:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._call("GetCapabilitiesString", display_num, edid_b64, None)
        return res.capabilities_text

    def get_ddcutil_dynamic_sleep(self) -> bool:
        res = self._call("GetDdcutilDynamicSleep")
        return res.enabled

    def set_ddcutil_dynamic_sleep(self, enabled: bool) -> None:
        self._call("SetDdcutilDynamicSleep", enabled)

    def get_ddcutil_output_level(self) -> int:
        res = self._call("GetDdcutilOutputLevel")
        return res.level

    def set_ddcutil_output_level(self, level: int) -> None:
        self._call("SetDdcutilOutputLevel", level)

    def get_service_poll_interval(self) -> int:
        res = self._call("GetServicePollInterval")
        return res.seconds

    def set_service_poll_interval(self, seconds: int) -> None:
        self._call("SetServicePollInterval", seconds)

    def get_service_poll_cascade_interval(self) -> float:
        res = self._call("GetServicePollCascadeInterval")
        return res.seconds

    def set_service_poll_cascade_interval(self, seconds: float) -> None:
        self._call("SetServicePollCascadeInterval", seconds)