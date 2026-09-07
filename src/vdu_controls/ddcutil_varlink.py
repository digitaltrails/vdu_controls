# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import functools
import json
import os
import threading
import time
import time as sys_time
from contextlib import suppress

# Only import when checking - if the user isn't use varlink, don't require it.
from typing import TYPE_CHECKING, Any, Callable, ClassVar

import vdu_controls.app_logging as log
from vdu_controls.constants import (
    VARLINK_MAX_RETRIES,
    VARLINK_RETRY_DELAY_SECS,
    getenv_logged,
)
from vdu_controls.ddcutil_abstract import (
    DdcCapabilities,
    DdcDetectedAttributes,
    DdcEventType,
    DdcutilDisplayNotFound,
    DdcutilInterface,
    DdcutilServiceNotFound,
    VcpTypeInfo,
    VcpValue,
)

if TYPE_CHECKING:
    from varlink import Client

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

        # Thread management
        self._stop_event = threading.Event()
        self._thread = None

        # State tracking and synchronization
        self._event_service_lock = threading.Lock()
        self._event_service = None

    def start(self):
        """Starts the background listening thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signals the loop to stop and tears down the socket connection immediately."""
        self._stop_event.set()

        # Intercept the blocking socket read by closing it from this thread
        with self._event_service_lock:
            if self._event_service is not None:
                try:
                    # Closing the service handle drops the blocking generator in the other thread
                    self._event_service.close()
                except (OSError, AttributeError) as e:
                    log.debug(f"Forcing stop by closing event connection - ignoring close error {e!s}")
                    # Ignore errors caused by double-closing or race conditions

        # Wait for the background thread to finish execution cleanly
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        log.debug("VarlinkListener stopped")

    def _run_loop(self):
        """The main loop executing in the background thread."""
        VarlinkError = _lazy_load_varlinkerror_class()
        log.debug("VarlinkListener started")
        while not self._stop_event.is_set():
            try:
                Client = _lazy_load_client_class()
                with (Client(self.varlink_socket) as connection,
                      connection.open(self.service_name) as service):

                        # Cache the handle so the stop() method can access it
                        with self._event_service_lock:
                            if self._stop_event.is_set():
                                break
                            self._event_service = service
                            event_stream = service.Subscribe(_more=True)

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

                log.error(f"Event stream connection error: {e!r}")
                if not self._stop_event.wait(2.0):
                    continue

            except (RuntimeError, LookupError, ValueError, TypeError) as e:
                log.error(f"Varlink: unexpected error in event loop: {e!r}")
                if not self._stop_event.wait(2.0):
                    continue

            finally:
                # Always close the service connection when exiting the connection context
                with self._event_service_lock:
                    # Ignore errors caused by double-closing or race conditions
                    with suppress(OSError, AttributeError):
                        if self._event_service is not None:
                            self._event_service.close()
                    self._event_service = None

        log.info("Varlink background thread has successfully exited.")

    def _handle_event(self, raw_event):
        self._callback(raw_event)


def serialized_retry(func):
    """
    Decorator to serialize synchronous Varlink calls using a lock and
    automatically reconnect/retry if the server restarts.
    Consistently applies global retry and delay constants.
    The lock prevents overlapping varlink Client calls from one stream - which
    is not supported.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        VarlinkError = _lazy_load_varlinkerror_class()

        try:
            for attempt in range(VARLINK_MAX_RETRIES):
                try:
                    with self.service_lock:
                        log.debug(f"Varlink: {func.__name__} obtained lock")
                        return func(self, *args, **kwargs)
                except (OSError, BrokenPipeError) as e:
                    # If it's the last attempt, bubble it up to the outer catch
                    if attempt == VARLINK_MAX_RETRIES - 1:
                        raise
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
                raise DdcutilDisplayNotFound(f"Varlink error: {func.__name__} {e!s}")
            elif error_name in ('com.ddcutil.DdcutilInterface.DdcError',
                                'com.ddcutil.DdcutilInterface.DetectError'):
                raise ValueError(f"Varlink error: {func.__name__} {e!s}")
            elif error_name == 'com.ddcutil.DdcutilInterface.ConfigurationLocked':
                raise RuntimeError(f"Varlink error: {func.__name__} Configuration locked")
            else:
                raise ValueError(f"Varlink error: {func.__name__} Varlink error: {e!s}")
        except BrokenPipeError as e:
            log.error(f"Varlink error: {func.__name__} failed permanently after {VARLINK_MAX_RETRIES} retries.")
            raise RuntimeError(f"Varlink {func.__name__} connection failed permanently") from e
        except Exception as e:
            log.error(f"Varlink error: Error in {func.__name__}: {e!s}")
            raise

    return wrapper


class DdcutilVarlinkImpl(DdcutilInterface):
    """
    Implements DdcutilInterface using the varlink ddcutil-service.
    """

    _metadata_cache: ClassVar[dict[tuple[str, int], VcpTypeInfo]] = {}

    # Lock prevents overlapping varlink Client calls from one stream - which is not supported.
    _service_lock: ClassVar[threading.Lock]  = threading.Lock()

    _event_listener: ClassVar[VarlinkListener | None] = None

    def __init__(self, common_args: list[str] | None = None, callback: Callable | None = None):
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
        self._connection: Client | None = None
        self._service: Any | None = None

        self._display_map: dict[str, int] = {}  # edid_base64 -> display_number

        # Connect and sanity check
        VarlinkError = _lazy_load_varlinkerror_class()

        for try_count in range(1, 5):  # TODO fix hardcoded constant
            try:
                self._reconnect_to_service()
                # Lightweight call: GetServiceInterfaceVersion
                self.get_interface_version_string()
                break
            except (OSError, DdcutilServiceNotFound, VarlinkError, BrokenPipeError) as e:
                log.error(f"Varlink sanity check try {try_count}: {e!s}")
                if try_count >= 4:
                    raise DdcutilServiceNotFound(f"Error contacting varlink service: {e!s}")
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
        if self._service is not None:
            with suppress(OSError, AttributeError):
                self._service.close()
                log.debug("Varlink: closed normal connection")
        try:
            Client = _lazy_load_client_class()
            self._connection = Client(self.varlink_socket)
            self._service = self._connection.open(self.service_name)
        except (ConnectionRefusedError, FileNotFoundError) as e:
            raise DdcutilServiceNotFound(f"Cannot connect to varlink service: {e}")

    def _resolve_display_identifier(self, edid_txt: str) -> tuple[int | None, str | None]:
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

    @serialized_retry
    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._service.SetSleepMultiplier(display_num, edid_b64, sleep_multiplier, None)

    @serialized_retry
    def set_vdu_specific_args(self, vdu_number: str, extra_args: list[str]) -> None:
        log.debug("set_vdu_specific_args not implemented for varlink")

    @serialized_retry
    def get_ddcutil_version_string(self) -> str:
        res = self._service.GetDdcutilVersion()
        return res['version']

    @serialized_retry
    def get_interface_version_string(self) -> str:
        res = self._service.GetServiceInterfaceVersion()
        return f"{res['version']} (Varlink ddcutil-service)"

    @serialized_retry
    def _get_status_values(self) -> dict[int, str]:
        # Not exposed; return empty dict.
        return {}

    @serialized_retry
    def detect(self, flags: int) -> list[DdcDetectedAttributes]:
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

    @serialized_retry
    def get_capabilities(self, edid_txt: str) -> DdcCapabilities:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetCapabilitiesMetadata(display_num, edid_b64, None)

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

    @serialized_retry
    def get_type(self, edid_txt: str, vcp_code_int: int) -> VcpTypeInfo:
        key = (edid_txt, vcp_code_int)
        if key in DdcutilVarlinkImpl._metadata_cache:
            return DdcutilVarlinkImpl._metadata_cache[key]
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetVcpMetadata(display_num, edid_b64, vcp_code_int, None)
        info = VcpTypeInfo(res.is_complex, res.is_continuous)
        DdcutilVarlinkImpl._metadata_cache[key] = info
        return info

    @serialized_retry
    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        self._service.SetVcp(display_num, edid_b64, vcp_code_int, new_value_int, None, None)

    @serialized_retry
    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: list[int]) -> list[VcpValue]:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetMultipleVcp(display_num, edid_b64, vcp_code_int_list, None)
        result = []
        for v in res["values"]:
            result.append(VcpValue(v['vcp_code'], v['current'], v['maximum'], None))
        return result

    @serialized_retry
    def vcp_info(self):
        pass

    @serialized_retry
    def refresh_connection(self):
        VarlinkError = _lazy_load_varlinkerror_class()
        try:
            self._service.GetServiceInterfaceVersion()
            log.debug("refresh_connection: existing varlink connection is still OK.") if log.debug_enabled else None
        except (OSError, VarlinkError):
            log.error("refresh_connection: varlink connection lost, reconnecting...")
            time.sleep(5)
            self._reconnect_to_service()

    @serialized_retry
    def get_capabilities_string(self, edid_txt: str) -> str:
        display_num, edid_b64 = self._resolve_display_identifier(edid_txt)
        res = self._service.GetCapabilitiesString(display_num, edid_b64, None)
        return res['capabilities_text']

    @serialized_retry
    def get_ddcutil_dynamic_sleep(self) -> bool:
        res = self._service.GetDdcutilDynamicSleep()
        return res['enabled']

    @serialized_retry
    def set_ddcutil_dynamic_sleep(self, enabled: bool) -> None:
        self._service.SetDdcutilDynamicSleep(enabled)

    @serialized_retry
    def get_ddcutil_output_level(self) -> int:
        res = self._service.GetDdcutilOutputLevel()
        return res['level']

    @serialized_retry
    def set_ddcutil_output_level(self, level: int) -> None:
        self._service.SetDdcutilOutputLevel(level)

    @serialized_retry
    def get_service_poll_interval(self) -> int:
        res = self._service.GetServicePollInterval()
        return res['seconds']

    @serialized_retry
    def set_service_poll_interval(self, seconds: int) -> None:
        self._service.SetServicePollInterval(seconds)

    @serialized_retry
    def get_service_poll_cascade_interval(self) -> float:
        res = self._service.GetServicePollCascadeInterval()
        return res['seconds']

    @serialized_retry
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


        if kind == 'subscription_started':
            log.info(f"Varlink subscription event: {kind=}")   # not a real event, ignore it.
        elif kind == 'connected_displays_changed':
            try:
                details = json.loads(data)
                edid = details['edid_base64']
                varlink_event_type = details['event_type']
                flags = details['flags']
                log.info(f"Varlink subscription event: {kind=} {varlink_event_type=} {flags!r}")
                if self.listener_callback:
                    if varlink_event_type == "VcpChange":
                        event_type = DdcEventType.UNKNOWN
                    elif varlink_event_type == "DpmsAsleep":
                        event_type = DdcEventType.DPMS_ASLEEP
                    elif varlink_event_type == "DpmsAwake":
                        event_type = DdcEventType.DPMS_AWAKE
                    elif varlink_event_type == "DisplayConnected":
                        event_type = DdcEventType.DISPLAY_CONNECTED
                    elif varlink_event_type == "DisplayDisconnected":
                        event_type = DdcEventType.DISPLAY_DISCONNECTED
                    else:
                        event_type = DdcEventType.UNKNOWN
                    self.listener_callback(edid, event_type.value, 0)
            except (ValueError, TypeError) as e:
                log.error(f"Varlink subscription event: {kind=} {data!r} - error parsing connected_displays_changed data: {e}")

        elif kind == 'vcp_changed':
            log.debug("VCP changed event (ignored)")

    @property
    def service_lock(self):
        return DdcutilVarlinkImpl._service_lock


