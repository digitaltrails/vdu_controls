# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import time as sys_time
from threading import Lock
from typing import Dict, Tuple, Callable, List

import vdu_controls.logging as log
from vdu_controls.constants import getenv_logged
from vdu_controls.ddcutil_abstract import DdcutilServiceNotFound, DdcutilDisplayNotFound, DdcutilInterface, DdcDetectedAttributes, \
    VcpValue, DdcCapabilities, VcpTypeInfo
from vdu_controls.misc import intV
from vdu_controls.qt_imports import (QDBusArgument, QDBusInterface, QMetaType, QDBusConnection,
                                     QDBusVariant, QDBusMessage, pyqtSlot)
from vdu_controls.qt_imports import QObject


class DdcutilDBusImpl(QObject, DdcutilInterface):
    """
    Uses the DBus ddcutil-service as a fast interface to libddcutil.
    Fast: service calls have a low overheads because the backing service
    does the expensive initialization once at startup.
    """
    RETURN_RAW_VALUES = 2
    _metadata_cache: Dict[Tuple[str, int], VcpTypeInfo] = {}
    _current_connected_displays_changed_handler: Callable | None = None  # Only one instance and listener should exist at a time
    _current_service_initialization_handler: Callable | None = None  # Only one instance and listener should exist at a time

    def __init__(self, common_args: List[str] | None = None, callback: Callable | None = None):
        super().__init__()
        self.dbus_interface_name = getenv_logged('DDCUTIL_SERVICE_INTERFACE_NAME', default="com.ddcutil.DdcutilInterface")
        env_args = [arg for arg in getenv_logged('VDU_CONTROLS_DDCUTIL_ARGS', default='').split() if arg != '']
        self.common_args = env_args + common_args if common_args else []
        self.service_access_lock = Lock()
        self.listener_callback: Callable | None = callback
        self.dbus_timeout_millis = int(getenv_logged("VDU_CONTROLS_DBUS_TIMEOUT_MILLIS", default='10000'))
        self._status_values: Dict[int, str] = {}
        self.dbus_service_name = getenv_logged('DDCUTIL_SERVICE_NAME', default="com.ddcutil.DdcutilService")
        self.dbus_object_path = getenv_logged('DDCUTIL_SERVICE_OBJECT_PATH', default="/com/ddcutil/DdcutilObject")
        for try_count in range(1, 5):  # Approximating an infinite loop
            self.ddcutil_proxy, self.ddcutil_props_proxy = self._connect_to_service()
            if len(self.common_args) != 0:  # have to restart with the common_args, wait and connect again
                try:
                    log.info(f"Restarting dbus service with common args {self.common_args}")
                    self._validate(self.ddcutil_proxy.call("Restart", " ".join(self.common_args),
                                                           QDBusArgument(0, intV(QMetaType.Type.UInt)),
                                                           QDBusArgument(0, intV(QMetaType.Type.UInt))))
                    sys_time.sleep(2)  # Should be enough time
                    log.info("Reconnecting after dbus service restart.")
                    self.ddcutil_proxy, self.ddcutil_props_proxy = self._connect_to_service()  # connect again
                except (ValueError, DdcutilDisplayNotFound):
                    log.warning(f"Failed to restart with common_args {self.common_args} on try {try_count}")
            # Retrieve the attributes returned by detect and also use the retrieval as a self check
            self_check_op = self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "AttributesReturnedByDetect")
            if not self_check_op.errorName():
                break  # Stop looping
            log.error(f'Sanity check try {try_count}: {self.dbus_interface_name} failed: {self_check_op.errorMessage()}')
            if try_count >= 4:  # Give up
                self._connection_reset()  # disconnect handler references to facilitate garbage collection
                raise DdcutilServiceNotFound(
                    f"Error contacting D-Bus service {self.dbus_interface_name} {self_check_op.errorMessage()}")
            sys_time.sleep(2)  # Try again

    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float):
        with self.service_access_lock:
            self._validate(self.ddcutil_proxy.call("SetSleepMultiplier", -1, edid_txt,
                                                   QDBusArgument(sleep_multiplier, intV(QMetaType.Type.Double)),
                                                   QDBusArgument(0, intV(QMetaType.Type.UInt))))

    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]):
        pass  # TODO not implemented

    def _connection_reset(self) -> Tuple[QDBusConnection, QDBusInterface, QDBusInterface]:
        session_bus = QDBusConnection.connectToBus(QDBusConnection.BusType.SessionBus, "session")
        ddcutil_dbus_iface = QDBusInterface(
            self.dbus_service_name, self.dbus_object_path, self.dbus_interface_name, connection=session_bus)
        # Properties are available via a separate interface with "Get" and "Set" methods
        ddcutil_dbus_props = QDBusInterface(
            self.dbus_service_name, self.dbus_object_path, "org.freedesktop.DBus.Properties", connection=session_bus)
        session_bus.registerObject("/", self)
        # Clear handlers belonging to old instance
        if DdcutilDBusImpl._current_connected_displays_changed_handler:  # clear previous handler that belonged to old instance.
            session_bus.disconnect(self.dbus_service_name, self.dbus_object_path, self.dbus_interface_name,
                                   "ConnectedDisplaysChanged", DdcutilDBusImpl._current_connected_displays_changed_handler)
        DdcutilDBusImpl._current_connected_displays_changed_handler = None
        if DdcutilDBusImpl._current_service_initialization_handler:  # clear previous handler that belonged to old instance.
            session_bus.disconnect(self.dbus_service_name, self.dbus_object_path, self.dbus_interface_name,
                                   "ServiceInitialized", DdcutilDBusImpl._current_service_initialization_handler)
            DdcutilDBusImpl._current_service_initialization_handler = None
        return session_bus, ddcutil_dbus_iface, ddcutil_dbus_props

    def _connect_to_service(self) -> Tuple[QDBusInterface, QDBusInterface]:
        session_bus, ddcutil_dbus_iface, ddcutil_dbus_props = self._connection_reset()
        # Connect new handlers - bind receiving slots to our new handlers
        DdcutilDBusImpl._current_service_initialization_handler = self._service_initialization_handler
        session_bus.connect(self.dbus_service_name, self.dbus_object_path, self.dbus_interface_name,
                            "ServiceInitialized", DdcutilDBusImpl._current_service_initialization_handler)
        session_bus.connect(self.dbus_service_name, self.dbus_object_path, self.dbus_interface_name,
                            "ConnectedDisplaysChanged", self._connected_displays_changed_handler)
        DdcutilDBusImpl._current_connected_displays_changed_handler = self._connected_displays_changed_handler
        ddcutil_dbus_iface.setTimeout(self.dbus_timeout_millis)
        # This is intended to provide the user with an easy way enable or disable events in the server.
        log.info(f"Remotely configuring ddcutil-service ServiceEmitSignals={self.listener_callback is not None}")
        ddcutil_dbus_props.call("Set",
                                "com.ddcutil.DdcutilInterface",
                                "ServiceEmitSignals",
                                QDBusVariant(QDBusArgument(self.listener_callback is not None, intV(QMetaType.Type.Bool))))
        return ddcutil_dbus_iface, ddcutil_dbus_props

    def refresh_connection(self):
        self_check_op = self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "ServiceInterfaceVersion")
        if self_check_op.errorName():  # Only reconnect if something appears to be wrong
            log.error(f'refresh_connection: check of {self.dbus_interface_name} failed: {self_check_op.errorMessage()}')
            self.ddcutil_proxy, self.ddcutil_props_proxy = self._connect_to_service()

    @pyqtSlot(QDBusMessage)
    def _service_initialization_handler(self, message: QDBusMessage):
        log.info(f"Received service_initialized D-Bus signal {message.arguments()=} {id(self)=}")  # check old instances... id()
        with self.service_access_lock:
            if self.listener_callback:  # In case the service has restarted
                self.ddcutil_props_proxy.call("Set",
                                              "com.ddcutil.DdcutilInterface",
                                              "ServiceEmitSignals",
                                              QDBusVariant(QDBusArgument(True, intV(QMetaType.Type.Bool))))
                self.listener_callback('', -1, 0)

    @pyqtSlot(QDBusMessage)
    def _connected_displays_changed_handler(self, message: QDBusMessage):
        log.info(f"Received display_change D-Bus signal {message.arguments()=} {id(self)=}")  # check old instances id()
        if self.listener_callback:
            self.listener_callback(*message.arguments())

    def get_ddcutil_version_string(self) -> str:
        return self._validate(self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "DdcutilVersion"))[0]

    def get_interface_version_string(self) -> str:
        return self._validate(self.ddcutil_props_proxy.call(
            "Get", self.dbus_interface_name, "ServiceInterfaceVersion"))[0] + " (D-Bus ddcutil-service - libddcutil)"

    def _get_status_values(self) -> Dict[int, str]:
        if len(self._status_values) == 0:
            self._status_values = self._validate(self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "StatusValues"))[0]
        return self._status_values

    def detect(self, flags: int) -> List[DdcDetectedAttributes]:
        with self.service_access_lock:
            vdu_list: List[DdcDetectedAttributes] = []
            result = self.ddcutil_proxy.call("Detect", QDBusArgument(flags, intV(QMetaType.Type.UInt)))
            for vdu in self._validate(result)[1]:
                vdu_prop_values = [str(property) for property in vdu]
                vdu_list.append(DdcDetectedAttributes(*vdu_prop_values))  # Note: depends on result ordering of properties
            return vdu_list

    def get_capabilities(self, edid_txt: str) -> DdcCapabilities:
        with self.service_access_lock:
            model, mccs_major, mccs_minor, commands, capabilities = \
                self._validate(self.ddcutil_proxy.call(
                    "GetCapabilitiesMetadata", -1, edid_txt, QDBusArgument(0, intV(QMetaType.Type.UInt))))
            return DdcCapabilities(model, int.from_bytes(mccs_major, 'big'), int.from_bytes(mccs_minor, 'big'),
                                   commands, capabilities, '')
            #return model, int.from_bytes(mccs_major, 'big'), int.from_bytes(mccs_minor, 'big'), commands, capabilities, ''

    def get_type(self, edid_txt: str, vcp_code_int: int) -> VcpTypeInfo:
        key = (edid_txt, vcp_code_int)
        if key in DdcutilDBusImpl._metadata_cache:
            return DdcutilDBusImpl._metadata_cache[key]
        with self.service_access_lock:
            _, _, _, _, _, is_complex, is_continuous = self._validate(self.ddcutil_proxy.call(
                "GetVcpMetadata", -1, edid_txt, QDBusArgument(vcp_code_int, intV(QMetaType.Type.UChar)),
                QDBusArgument(0, intV(QMetaType.Type.UInt))))
            info = VcpTypeInfo(is_complex, is_continuous)
            DdcutilDBusImpl._metadata_cache[key] = info
            return info

    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        with self.service_access_lock:
            self._validate(self.ddcutil_proxy.call("SetVcp", -1, edid_txt,
                                                   QDBusArgument(vcp_code_int, intV(QMetaType.Type.UChar)),
                                                   QDBusArgument(new_value_int, intV(QMetaType.Type.UShort)),
                                                   QDBusArgument(0, intV(QMetaType.Type.UInt))))

    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        vcp_code_array = QDBusArgument()
        vcp_code_array.beginArray(intV(QMetaType.Type.UChar))
        for vcp_code_int in vcp_code_int_list:
            vcp_code_array.add(QDBusArgument(vcp_code_int, intV(QMetaType.Type.UChar)))
        vcp_code_array.endArray()
        with self.service_access_lock:
            raw = self._validate(self.ddcutil_proxy.call(
                "GetMultipleVcp", -1, edid_txt, vcp_code_array, QDBusArgument(DdcutilDBusImpl.RETURN_RAW_VALUES,
                                                                              intV(QMetaType.Type.UInt))))[0]
            results = []
            for vcp, value, maximum, text_val in raw:
                vcp_code_int = int.from_bytes(vcp, 'big')
                results.append(VcpValue(vcp_code_int, value, maximum, None))  # TODO is None for type really OK?
            #print(f"results {len(results)=} {results=}")
            return results

    def vcp_info(self):
        pass

    def _validate(self, result: QDBusMessage) -> List:
        if result.errorName():
            raise ValueError(f"D-Bus error {result.errorName()}: {result.errorMessage()}")
        result_arg_list = result.arguments()
        if len(result_arg_list) >= 2:  # Normal retrieval calls return at least three items
            status, message = result.arguments()[-2:]  # last two are always DDC status and message
            if status != 0:
                formatted_message = f"D-Bus  {status=}: {message}"
                log.debug(formatted_message) if log.debug_enabled else None
                if self._get_status_values().get(status, "DDCRC_INVALID_DISPLAY") == "DDCRC_INVALID_DISPLAY":
                    raise DdcutilDisplayNotFound(formatted_message)
                raise ValueError(formatted_message)
            return result_arg_list[:-2]  # results with status and message stripped out.
        return result_arg_list  # Must be something like a property retrieval, just return as is

