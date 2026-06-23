# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict

from vdu_controls.constants import getenv_logged

# Number of times to retry getting/setting attributes - in case a monitor is slow after being powered up.
# Note retrying a set may not be wise, sets are not repeatable.
DDCUTIL_RETRIES = int(getenv_logged("VDU_CONTROLS_DDCUTIL_RETRIES", default='4'))

#: Could be a str enumeration of VCP types
CONTINUOUS_TYPE = 'C'
SIMPLE_NON_CONTINUOUS_TYPE = 'SNC'
COMPLEX_NON_CONTINUOUS_TYPE = 'CNC'
CON = CONTINUOUS_TYPE  # Shorter abbreviation
SNC = SIMPLE_NON_CONTINUOUS_TYPE
CNC = COMPLEX_NON_CONTINUOUS_TYPE


BRIGHTNESS_VCP_CODE = BRIT = 0x10  # Note ddcutil command line treats 10 as 0x10
CONTRAST_VCP_CODE = CONT = 0x12


@dataclass(frozen=True)
class DdcCapabilities:
    model: str
    mccs_major: int
    mccs_minor: int
    commands: Dict[bytes, str]
    features: Dict[bytes, Tuple[bytes, str, Dict[bytes, str]]]  # From ddcutil-service
    capabilities_str: str  # From everything else


@dataclass(frozen=True)
class DdcDetectedAttributes:
    display_number: str
    usb_bus: str
    usb_device: str
    manufacturer_id: str
    model_name: str
    serial_number: str
    product_code: str
    edid_txt: str
    binary_serial_number: str


@dataclass(frozen=True)
class VcpValue:
    vcp_code: int
    current: int
    max: int
    vcp_type: str | None


@dataclass(frozen=True)
class VcpTypeInfo:
    is_complex: bool
    is_continuous: bool


class DdcEventType(Enum):  # Has to correspond to what the service supports
    UNKNOWN = -2
    LAPTOP_BRIGHTNESS_CHANGE = -1
    DPMS_AWAKE = 0
    DPMS_ASLEEP = 1
    DISPLAY_CONNECTED = 2
    DISPLAY_DISCONNECTED = 3


class DdcutilServiceNotFound(Exception):
    pass


class DdcutilDisplayNotFound(Exception):
    pass



class DdcutilSetterRateExceeded(ValueError):
    pass


# Cannot make this ABC - will conflict with QObject in the dbus implementation
# Plain interface class
class DdcutilInterface:
    """
    Defines the interface for Ddcutil-like implementations.  Implementors
    may use real ddcutil implementations or emulate a ddcutil-like interface.
    """
    def refresh_connection(self):
        raise NotImplementedError

    
    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float):
        raise NotImplementedError

    
    def set_vdu_specific_args(self, edid_txt: str, extra_args):
        raise NotImplementedError

    
    def vcp_info(self):
        """Returns info about all codes known to ddcutil, whether supported or not."""
        raise NotImplementedError

    
    def get_ddcutil_version_string(self):
        raise NotImplementedError

    
    def get_interface_version_string(self):
        raise NotImplementedError

    
    def detect(self, flags: int):
        raise NotImplementedError

    
    def get_capabilities(self, edid_txt: str):
        raise NotImplementedError

    
    def get_type(self, edid_txt: str, vcp_code_int: int) -> VcpTypeInfo:
        raise NotImplementedError

    
    def set_vcp(self,  edid_txt: str, vcp_code_int: int, new_value_int: int):
        raise NotImplementedError

    
    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[VcpValue]:
        raise NotImplementedError
