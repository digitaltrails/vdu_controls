# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import functools
import json
import os
import threading
import time
import time as sys_time
from typing import Dict, Tuple, Callable, List, Any

# Only import when checking - if the user isn't use varlink, don't require it.
from typing import TYPE_CHECKING

import vdu_controls.app_logging as log
from vdu_controls.constants import getenv_logged, VARLINK_MAX_RETRIES, VARLINK_RETRY_DELAY_SECS
from vdu_controls.ddcutil_abstract import (
    DdcutilServiceNotFound, DdcutilDisplayNotFound, DdcutilInterface,
    DdcDetectedAttributes, VcpValue, DdcCapabilities, VcpTypeInfo
)

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


class VarlinkListener:
    def __init__(self, varlink_socket, service_name, callback: Callable):
        self._callback = callback
        self.varlink_socket = varlink_socket
        self.service_name = service_name
        self._event_service = None

        # Thread management
        self._stop_event = threading.Event()
        self._thread = None


    def start(self):
        """Starts the background listening thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signals the loop to stop and tears down the socket connection immediately."""
        self._stop_event.set()

        # Intercept the blocking socket read by closing it from this thread
        if self._event_service is not None:
            try:
                # Closing the service handle drops the blocking generator in the other thread
                self._event_service.close()
            except Exception as e:
                log.debug(f"Ignoring errors while closing event connection {e}")
                pass  # Ignore errors caused by double-closing or race conditions

        # Wait for the background thread to finish execution cleanly
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        log.debug("VarlinkListener stopped")

    def _run_loop(self):
        """The main loop executing in the background thread."""
        VarlinkError = _lazy_load_varlinkerror_class()
        log.debug("VarlinkListener started")
        # ddcutil-varlink now serializes requests - no locking required
        while not self._stop_event.is_set():
            try:
                Client = _lazy_load_client_class()
                with Client(self.varlink_socket) as connection:
                    with connection.open(self.service_name) as service:
                        # Save the event_service reference so the stop() method can access it
                        if self._stop_event.is_set():
                            break
                        self._event_service = service
                        event_stream = service.Subscribe(True, _more=True)

                        # This loop blocks until a new event arrives OR service.close() is called
                        for raw_event in event_stream:
                            log.debug(f"Varlink: received event {raw_event}") if log.debug_enabled else None
                            if self._stop_event.is_set():
                                break
                            self._handle_event(raw_event)

            except (VarlinkError, OSError, ConnectionError) as e:
                # If we are stopping, this exception is expected (caused by service.close())
                if self._stop_event.is_set():
                    break

                log.error(f"Event stream connection error: {e}")
                if not self._stop_event.wait(2.0):
                    continue

            except Exception as e:
                log.error(f"Varlink: unexpected error in event loop: {e}")
                if not self._stop_event.wait(2.0):
                    continue

            finally:
                # Always close the service connection when exiting the connection context
                self._event_service.close()
                self._event_service = None

        log.info("Varlink background thread has successfully exited.")

    def _handle_event(self, raw_event):
        self._callback(raw_event)


def service_call(func):
    """
    Decorator to serialize synchronous Varlink calls using a lock and
    automatically reconnect/retry if the server restarts.
    Consistently applies global retry and delay constants.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        VarlinkError = _lazy_load_varlinkerror_class()

        try:
            # ddcutil-varlink internally serializes all requests - we used to lock here,
            # but it is no longer necessary.
            log.debug(f"Varlink: call {func.__name__}") if log.debug_enabled else None

            for attempt in range(VARLINK_MAX_RETRIES):
                try:
                    return func(self, *args, **kwargs)
                except BrokenPipeError as e:
                    # If it's the last attempt, bubble it up to the outer catch
                    if attempt == VARLINK_MAX_RETRIES - 1:
                        raise e
                    log.warning(
                        f"Varlink error: {func.__name__} connection lost. "
                        f"Refreshing and retrying in {VARLINK_RETRY_DELAY_SECS}s... Error: {e}"
                    )
                    time.sleep(VARLINK_RETRY_DELAY_SECS)
                    self.refresh_connection()

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
        except BrokenPipeError as e:
            log.error(f"Varlink error: {func.__name__} failed permanently after {VARLINK_MAX_RETRIES} retries.")
            raise RuntimeError(f"Varlink {func.__name__} connection failed permanently") from e
        except Exception as e:
            log.error(f"Varlink error: Error in {func.__name__}: {e}")
            raise

    return wrapper


class DdcutilVarlinkImpl(DdcutilInterface):
    """
    Implements DdcutilInterface using the varlink ddcutil-service.
    """

    _metadata_cache: Dict[Tuple[str, int], VcpTypeInfo] = {}
    _event_listener: VarlinkListener | None = None

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
        self.listener_callback: Callable | None = callback

        # Connection used by normal method calls
        Client = _lazy_load_client_class()
        self._connection: Client | None = None
        self._service: Any | None = None

        self._display_map: Dict[str, int] = {}  # edid_base64 -> display_number

        # Connect and sanity check
        for try_count in range(1, 5):
            try:
                self._reconnect_to_service()
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
            if DdcutilVarlinkImpl._event_listener is not None:
                # Replace the old listener with a new one.
                DdcutilVarlinkImpl._event_listener.stop()
            DdcutilVarlinkImpl._event_listener = VarlinkListener(self.varlink_socket, self.service_name, self._handle_event)
            DdcutilVarlinkImpl._event_listener.start()

    def _reconnect_to_service(self) -> None:
        try:
            if self._service is not None:
                self._service.close()
                log.debug("Varlink: closed normal connection")
        except Exception as e:
            log.warning(f"Varlink: Error closing existing normal connection: {e}")
        try:
            Client = _lazy_load_client_class()
            self._connection = Client(self.varlink_socket)
            self._service = self._connection.open(self.service_name)
        except (ConnectionRefusedError, FileNotFoundError) as e:
            raise DdcutilServiceNotFound(f"Cannot connect to varlink service: {e}")

    def _resolve_display_identifier(self, edid_txt: str) -> Tuple[int | None, str | None]:
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

    @service_call
    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._service.SetSleepMultiplier(display_num, edid_b64, sleep_multiplier, None)

    @service_call
    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]) -> None:
        log.debug("set_vdu_specific_args not implemented for varlink")

    @service_call
    def get_ddcutil_version_string(self) -> str:
        res = self._service.GetDdcutilVersion()
        return res['version']

    @service_call
    def get_interface_version_string(self) -> str:
        res = self._service.GetServiceInterfaceVersion()
        return f"{res['version']} (Varlink ddcutil-service)"

    @service_call
    def _get_status_values(self) -> Dict[int, str]:
        # Not exposed; return empty dict.
        return {}

    @service_call
    def detect(self, flags: int) -> List[DdcDetectedAttributes]:
        include_offline = bool(flags & 1)
        result_map = self._service.Detect(include_offline)
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

    @service_call
    def get_capabilities(self, edid_txt: str) -> DdcCapabilities:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetCapabilitiesMetadata(display_num, edid_txt, None)

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

    @service_call
    def get_type(self, edid_txt: str, vcp_code_int: int) -> VcpTypeInfo:
        key = (edid_txt, vcp_code_int)
        if key in self._metadata_cache:
            return self._metadata_cache[key]
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetVcpMetadata(display_num, edid_b64, vcp_code_int, None)
        info = VcpTypeInfo(res.is_complex, res.is_continuous)
        self._metadata_cache[key] = info
        return info

    @service_call
    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._service.SetVcp(display_num, edid_b64, vcp_code_int, new_value_int, None, None)

    @service_call
    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetMultipleVcp(display_num, edid_b64, vcp_code_int_list, None)
        #res = self._stub(GetMultipleVcp", display_num, edid_b64, vcp_code_int_list, None)
        result = []
        for v in res["values"]:
            result.append(VcpValue(v['vcp_code'], v['current'], v['maximum'], None))
        return result

    @service_call
    def vcp_info(self):
        pass

    @service_call
    def refresh_connection(self):
        try:
            self._service.GetServiceInterfaceVersion()
            log.debug("refresh_connection: existing varlink connection is still OK.") if log.debug_enabled else None
        except (Exception, BrokenPipeError):
            log.error("refresh_connection: varlink connection lost, reconnecting...")
            time.sleep(5)
            self._reconnect_to_service()

    @service_call
    def get_capabilities_string(self, edid_txt: str) -> str:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetCapabilitiesString(display_num, edid_b64, None)
        return res['capabilities_text']

    @service_call
    def get_ddcutil_dynamic_sleep(self) -> bool:
        res = self._service.GetDdcutilDynamicSleep()
        return res['enabled']

    @service_call
    def set_ddcutil_dynamic_sleep(self, enabled: bool) -> None:
        self._service.SetDdcutilDynamicSleep(enabled)

    @service_call
    def get_ddcutil_output_level(self) -> int:
        res = self._service.GetDdcutilOutputLevel()
        return res['level']

    @service_call
    def set_ddcutil_output_level(self, level: int) -> None:
        self._service.SetDdcutilOutputLevel(level)

    @service_call
    def get_service_poll_interval(self) -> int:
        res = self._service.GetServicePollInterval()
        return res['seconds']

    @service_call
    def set_service_poll_interval(self, seconds: int) -> None:
        self._service.SetServicePollInterval(seconds)

    @service_call
    def get_service_poll_cascade_interval(self) -> float:
        res = self._service.GetServicePollCascadeInterval()
        return res['seconds']

    @service_call
    def set_service_poll_cascade_interval(self, seconds: float) -> None:
        self._service.SetServicePollCascadeInterval(seconds)

    # ----------------------------------------------------------------------
    # Event subscription
    # ----------------------------------------------------------------------

    def _handle_event(self, event_wrapper) -> None:
        log.info(f"Varklink: handling event: {event_wrapper=}")

        event = event_wrapper["event"]
        kind = event["kind"]
        data = event["data"]

        if kind == 'service_initialized':
            log.info("Service initialized event")
            if self.listener_callback:
                self.listener_callback('', -1, 0)

        elif kind == 'connected_displays_changed':
            log.info("Connected displays changed event")
            try:
                details = json.loads(data)
                event_type = details['event_type']
                flags = details['flags']
                if self.listener_callback:
                    self.listener_callback(event_type, flags, 0)
            except Exception as e:
                log.error(f"Error parsing connected_displays_changed data: {e}")

        elif kind == 'vcp_changed':
            log.debug("VCP changed event (ignored)")


