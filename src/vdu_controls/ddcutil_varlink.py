# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import functools
import json
import os
import time
import time as sys_time
import threading

from typing import Dict, Tuple, Callable, List, Optional, Any
from threading import Lock

import vdu_controls.app_logging as log
from vdu_controls.constants import getenv_logged
from vdu_controls.ddcutil_abstract import (
    DdcutilServiceNotFound, DdcutilDisplayNotFound, DdcutilInterface,
    DdcDetectedAttributes, VcpValue, DdcCapabilities, VcpTypeInfo
)

# Only import when checking - if the user isn't use varlink, don't require it.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from varlink import Client, VarlinkError

_Client = None
_VarlinkError = None


def _lazy_load_client_class():
    global _Client
    if _Client is None:
        from varlink import Client
        _Client = Client
    return _Client


def _lazy_load_varlinkerror_class():
    global _VarlinkError
    if _VarlinkError is None:
        from varlink import VarlinkError
        _VarlinkError = VarlinkError
    return _VarlinkError


def locked_and_handled(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        VarlinkError = _lazy_load_varlinkerror_class()
        try:
            log.debug(f"Varlink: {func.__name__}")
            for attempt in range(0, 2):
                try:
                    with self._service_lock:
                        log.debug(f"Varlink: {func.__name__} obtained lock")
                        return func(self, *args, **kwargs)
                except BrokenPipeError as e:
                    log.warning(f"Varlink error: {func.__name__} connection lost, refreshing connection, {str(e)}")
                    time.sleep(2)
                    self.refresh_connection()
            raise RuntimeError(f"Varlink {func.__name__} Configuration locked")
        except VarlinkError as e:
            error_name = e.error()
            log.error(f"Varlink error: {func.__name__} {error_name}, params: {e.parameters()}")
            if error_name == 'com.ddcutil.DdcutilInterface.DisplayNotFound':
                raise DdcutilDisplayNotFound(f"Varlink error: {func.__name__} {str(e)}")
            elif error_name in ('com.ddcutil.DdcutilInterface.DdcError',
                                'com.ddcutil.DdcutilInterface.DetectError'):
                raise ValueError(f"Varlink error: {func.__name__} {str(e)}")
            elif error_name == 'com.ddcutil.DdcutilInterface.ConfigurationLocked':
                raise RuntimeError(f"Varlink error: {func.__name__} Configuration locked")
            else:
                raise ValueError(f"Varlink error: {func.__name__} Varlink error: {e}")
        except Exception as e:
            # --- your error handling here ---
            log.error(f"Varlink error: Error in {func.__name__}: {e}")
            raise
    return wrapper



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

        # Connection used by normal method calls
        Client = _lazy_load_client_class()
        self._connection: Optional[Client] = None
        self._stub: Optional[Any] = None

        # Event‐specific connection and stub
        self._event_connection: Optional[Client] = None
        self._event_stub: Optional[Any] = None

        self._display_map: Dict[str, int] = {}  # edid_base64 -> display_number

        # Connect and sanity check
        for try_count in range(1, 5):
            try:
                self._reconnect_to_service()
                # Lightweight call: GetServiceInterfaceVersion
                self.get_interface_version_string()
                # Start event subscription if callback provided
                if self.listener_callback is not None:
                    self._start_event_subscription()
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

    def _reconnect_to_service(self) -> None:
        try:
            if self._connection:
                self._connection.close()
        except:
            pass
        try:
            Client = _lazy_load_client_class()
            self._connection = Client(self.varlink_socket)
            self._stub = self._connection.open(self.service_name)
        except (ConnectionRefusedError, FileNotFoundError) as e:
            raise DdcutilServiceNotFound(f"Cannot connect to varlink service: {e}")

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

    @locked_and_handled
    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._stub.SetSleepMultiplier( display_num, edid_b64, sleep_multiplier, None)

    @locked_and_handled
    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]) -> None:
        log.debug("set_vdu_specific_args not implemented for varlink")

    @locked_and_handled
    def get_ddcutil_version_string(self) -> str:
        res = self._stub.GetDdcutilVersion()
        return res['version']

    @locked_and_handled
    def get_interface_version_string(self) -> str:
        res = self._stub.GetServiceInterfaceVersion()
        return f"{res['version']} (Varlink ddcutil-service)"

    @locked_and_handled
    def _get_status_values(self) -> Dict[int, str]:
        # Not exposed; return empty dict.
        return {}

    @locked_and_handled
    def detect(self, flags: int) -> List[DdcDetectedAttributes]:
        include_offline = bool(flags & 1)
        result_map = self._stub.Detect(include_offline)
        result_list = []
        for disp_map in result_map['displays']:
            attrs = DdcDetectedAttributes(
                display_number=str(disp_map['display_number']),
                usb_bus=str(disp_map['usb_bus']),
                usb_device=str(disp_map['usb_device']),
                manufacturer_id=str(disp_map['mfg_id']),
                model_name=str(disp_map['model_name']),
                serial_number=str(disp_map['serial_number']),
                product_code=str(disp_map['product_code']),
                edid_txt=str(disp_map['edid_base64']),
                binary_serial_number=str(disp_map['edid_serial_number'])
            )
            result_list.append(attrs)
            self._display_map[attrs.edid_txt] = disp_map['display_number']
        return result_list

    @locked_and_handled
    def get_capabilities(self, edid_txt: str) -> DdcCapabilities:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._stub.GetCapabilitiesMetadata(display_num, edid_txt, None)

        def convert_feature_values(values):
            if values:
                return {feature_value: value_name for feature_value, value_name in values.items() }
            return values

        capabilities = {feature_code:
                            (feature['feature_name'],
                             feature['feature_description'],
                             convert_feature_values(feature['values'])) for feature_code, feature in res['capabilities'].items()}
        return DdcCapabilities(
            res['model_name'],
            res['mccs_major'],
            res['mccs_minor'],
            res['commands'],
            capabilities,
            ''   # extra field not used
        )

    @locked_and_handled
    def get_type(self, edid_txt: str, vcp_code_int: int) -> VcpTypeInfo:
        key = (edid_txt, vcp_code_int)
        if key in self._metadata_cache:
            return self._metadata_cache[key]
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._stub.GetVcpMetadata(display_num, edid_b64, vcp_code_int, None)
        info = VcpTypeInfo(res.is_complex, res.is_continuous)
        self._metadata_cache[key] = info
        return info

    @locked_and_handled
    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._stub.SetVcp(display_num, edid_b64, vcp_code_int, new_value_int, None, None)

    @locked_and_handled
    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._stub.GetMultipleVcp(display_num, edid_b64, vcp_code_int_list, None)
        #res = self._stub(GetMultipleVcp", display_num, edid_b64, vcp_code_int_list, None)
        result = []
        for v in res["values"]:
            result.append(VcpValue(v['vcp_code'], v['current'], v['maximum'], None))
        return result

    @locked_and_handled
    def vcp_info(self):
        pass

    @locked_and_handled
    def refresh_connection(self):
        try:
            self._stub.GetServiceInterfaceVersion()
            log.debug("refresh_connection: existing varlink connection is still OK.") if log.debug_enabled else None
        except Exception:
            log.error("refresh_connection: varlink connection lost, reconnecting...")
            self._connect_to_service()
            if self.listener_callback is not None:
                self._start_event_subscription()

    # ----------------------------------------------------------------------
    # Event subscription
    # ----------------------------------------------------------------------

    def _start_event_subscription(self) -> None:
        log.info("Varlink: _start_event_subscription")
        if self._event_thread is not None and self._event_thread.is_alive():
            self._stop_event.set()
            self._event_thread.join(timeout=1.0)
        self._stop_event.clear()
        self._event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._event_thread.start()

    def _event_loop(self) -> None:
        log.debug("Varlink: event loop started")
        VarlinkError = _lazy_load_varlinkerror_class()
        while not self._stop_event.is_set():
            try:
                self._reconnect_event_connection()

                # Subscribe with use_polling=False (event-driven)
                with self._service_lock:
                    event_stream = self._event_stub.Subscribe(True, _more=True)
                for raw_event in event_stream:
                    log.debug(f"Varlink: received event {raw_event}") if log.debug_enabled else None
                    if self._stop_event.is_set():
                        break
                    self._handle_event(raw_event)
            except VarlinkError as e:
                log.error(f"Event stream error: {e}")
                if not self._stop_event.wait(2.0):
                    continue
            except Exception as e:
                log.error(f"Varlink: unexpected error in event loop: {e}")
                if not self._stop_event.wait(2.0):
                    continue

    def _reconnect_event_connection(self) -> None:
        log.info("Varlink: reconnecting event-connection")
        try:
            if self._event_connection:
                self._event_connection.close()
        except:
            pass
        Client = _lazy_load_client_class()
        self._event_connection = Client(self.varlink_socket)
        self._event_stub = self._event_connection.open(self.service_name)

    def _handle_event(self, event_wrapper) -> None:
        log.info(f"Varklink: handling event: {event_wrapper=}")

        event = event_wrapper["event"]
        kind = event["kind"]
        data = event["data"]

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

    @locked_and_handled
    def get_capabilities_string(self, edid_txt: str) -> str:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._stub.GetCapabilitiesString(display_num, edid_b64, None)
        return res['capabilities_text']

    @locked_and_handled
    def get_ddcutil_dynamic_sleep(self) -> bool:
        res = self._stub.GetDdcutilDynamicSleep()
        return res['enabled']

    @locked_and_handled
    def set_ddcutil_dynamic_sleep(self, enabled: bool) -> None:
        self._stub.SetDdcutilDynamicSleep(enabled)

    @locked_and_handled
    def get_ddcutil_output_level(self) -> int:
        res = self._stub.GetDdcutilOutputLevel()
        return res['level']

    @locked_and_handled
    def set_ddcutil_output_level(self, level: int) -> None:
        self._stub.SetDdcutilOutputLevel( level)

    @locked_and_handled
    def get_service_poll_interval(self) -> int:
        res = self._stub.GetServicePollInterval()
        return res['seconds']

    @locked_and_handled
    def set_service_poll_interval(self, seconds: int) -> None:
        self._stub.SetServicePollInterval( seconds)

    @locked_and_handled
    def get_service_poll_cascade_interval(self) -> float:
        res = self._stub.GetServicePollCascadeInterval()
        return res['seconds']

    @locked_and_handled
    def set_service_poll_cascade_interval(self, seconds: float) -> None:
        self._stub.SetServicePollCascadeInterval( seconds)