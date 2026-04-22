# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from collections import namedtuple
from enum import Enum

# Number of times to retry getting/setting attributes - in case a monitor is slow after being powered up.
DDCUTIL_RETRIES = int(os.getenv("VDU_CONTROLS_DDCUTIL_RETRIES", default='4'))

VcpValue = namedtuple('VcpValue', ['current', 'max', 'vcp_type'])  # A getvcp command returns these three things

#: Could be a str enumeration of VCP types
CONTINUOUS_TYPE = 'C'
SIMPLE_NON_CONTINUOUS_TYPE = 'SNC'
COMPLEX_NON_CONTINUOUS_TYPE = 'CNC'
CON = CONTINUOUS_TYPE  # Shorter abbreviation
SNC = SIMPLE_NON_CONTINUOUS_TYPE
CNC = COMPLEX_NON_CONTINUOUS_TYPE


BRIGHTNESS_VCP_CODE = BRIT = '10'  # This is HEX
CONTRAST_VCP_CODE = CONT = '12'  # Also HEX




class DdcEventType(Enum):  # Has to correspond to what the service supports
    UNKNOWN = -2
    LAPTOP_BRIGHTNESS_CHANGE = -1
    DPMS_AWAKE = 0
    DPMS_ASLEEP = 1
    DISPLAY_CONNECTED = 2
    DISPLAY_DISCONNECTED = 3


class VcpOrigin(Enum):  # Cause of a VCP value change
    NORMAL = 0  # Change generated internally within vdu_controls.
    TRANSIENT = 1  # Intermediate VDU VCP change as a result of vdu_controls transitioning to a new value
    EXTERNAL = 2  # Detected a change of value that must have been done externally to this vdu_controls run.


class DdcutilServiceNotFound(Exception):
    pass


class DdcutilDisplayNotFound(Exception):
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

    
    def set_sleep_multiplier(self, edid_txt, sleep_multiplier):
        raise NotImplementedError

    
    def set_vdu_specific_args(self, edid_txt, extra_args):
        raise NotImplementedError

    
    def vcp_info(self):
        """Returns info about all codes known to ddcutil, whether supported or not."""
        raise NotImplementedError

    
    def get_ddcutil_version_string(self):
        raise NotImplementedError

    
    def get_interface_version_string(self):
        raise NotImplementedError

    
    def detect(self, flags):
        raise NotImplementedError

    
    def get_capabilities(self, edid_txt):
        raise NotImplementedError

    
    def get_type(self, edid_txt, vcp_code_int):
        raise NotImplementedError

    
    def set_vcp(self, edid_txt, vcp_code_int, new_value_int):
        raise NotImplementedError

    
    def get_vcp_values(self, edid_txt, vcp_code_int_list):
        raise NotImplementedError
