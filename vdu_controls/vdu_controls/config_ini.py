# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import argparse
import configparser
import inspect
import math
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Dict, Any

import vdu_controls.logging as log
from vdu_controls import app_locale
from vdu_controls.app_locale import tr
from vdu_controls.constants import CONFIG_DIR_PATH, VDU_CONTROLS_VERSION, APPNAME
from vdu_controls.ddcutil_abstract import CON, BRIT, CONT, SNC
from vdu_controls.ddcutil_aggregator import DdcutilAggregator
from vdu_controls.misc import zoned_now
from vdu_controls.qt_imports import QT_TR_NOOP, QCoreApplication
from vdu_controls.svg import BRIGHTNESS_SVG, CONTRAST_SVG, VOLUME_SVG, COLOR_TEMPERATURE_SVG


class ConfIni(configparser.ConfigParser):
    """ConfigParser is a little messy, and its class name is a bit misleading, wrap it and bend it to our needs."""

    def __init__(self) -> None:
        super().__init__(interpolation=None)
        if not self.has_section(ConfSec.METADATA_SECTION):
            self.add_section(ConfSec.METADATA_SECTION)

    def data_sections(self) -> List:  # Section other than metadata and DEFAULT - real data.
        return [s for s in self.sections() if s != configparser.DEFAULTSECT and s != ConfSec.METADATA_SECTION]

    def get_version(self) -> Tuple:
        if version := self.get(*ConfOpt.METADATA_VERSION_OPTION.conf_id, fallback=None):
            try:
                return tuple(int(i) for i in version.split('.'))
            except ValueError:
                log.error(f"Illegal version number {version} should be i.j.k where i, j and k are integers.", trace=True)
        return 1, 6, 0

    def save(self, config_path) -> None:
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        with open(config_path, 'w', encoding="utf-8") as config_file:
            self[ConfOpt.METADATA_VERSION_OPTION.conf_section][ConfOpt.METADATA_VERSION_OPTION.conf_name] = VDU_CONTROLS_VERSION
            self[ConfOpt.METADATA_TIMESTAMP_OPTION.conf_section][ConfOpt.METADATA_TIMESTAMP_OPTION.conf_name] = str(zoned_now())
            self.write(config_file)
        log.info(f"Wrote config to {config_path.as_posix()}")

    def duplicate(self, new_ini=None) -> ConfIni:
        if new_ini is None:
            new_ini = ConfIni()
        for section in self.sections():
            if section != configparser.DEFAULTSECT and section != ConfSec.METADATA_SECTION:
                new_ini.add_section(section)
            for option in self[section]:
                new_ini[section][option] = self[section][option]
        return new_ini

    def diff(self, other: ConfIni, vdu_settings_only: bool = False) -> Dict[Tuple[str, str], str]:
        values = []
        for subject in (self, other):
            sections = set(subject.sections()) - {configparser.DEFAULTSECT, ConfSec.METADATA_SECTION}
            if vdu_settings_only:
                sections -= {'preset'}
            values.append([(section, option, value) for section in sections for option, value in subject[section].items()])
        differences = list(set(values[0]) ^ set(values[1]))
        return {(section, option): value for section, option, value in differences}

    @staticmethod
    def get_path(config_name: str) -> Path:
        return CONFIG_DIR_PATH.joinpath(config_name + '.conf')


class ConfType:  # Supported types constants (in Python 3.11 this could be a StrEnum)
    BOOL = 'bool'
    FLOAT = 'float'
    CSV = 'csv'
    LONG_TEXT = 'long_text'
    TEXT = 'text'
    LOCATION = 'location'
    PATH = 'path'


class ConfSec:  # Data section constants (in Python 3.11 this could be a StrEnum)
    METADATA_SECTION = QT_TR_NOOP("metadata")  # INI version tracking section
    VDU_CONTROLS_GLOBALS = QT_TR_NOOP('vdu-controls-globals')
    VDU_CONTROLS_WIDGETS = QT_TR_NOOP('vdu-controls-widgets')
    DDCUTIL_PARAMETERS = QT_TR_NOOP('ddcutil-parameters')
    DDCUTIL_CAPABILITIES = QT_TR_NOOP('ddcutil-capabilities')
    UNKNOWN_SECTION = QT_TR_NOOP('unknown')

class ConfGroup(Enum):
    WINDOWING =   (1, QT_TR_NOOP('Windowing'))
    FEATURES =    (3, QT_TR_NOOP('Features'))
    SYSTEM_TRAY = (2, QT_TR_NOOP('System Tray'))
    DDC =         (4, QT_TR_NOOP('DDC'))
    LOGGING =     (5, QT_TR_NOOP('Logging'))
    NONE =        (6, '')

    @property
    def intval(self) -> int:
        return self.value[0]

    @property
    def title(self) -> str:
        return app_locale.translate_option(self.value[1])

class ConfOpt(Enum):  # An Enum with tuples for values is used for convenience for scope/iteration

    @staticmethod  # Tricky way of creating a tuple with default values for some tuple members.
    def _def(cname: str, section: str = ConfSec.VDU_CONTROLS_GLOBALS, conf_type: str = ConfType.BOOL, default: str | None = None,
             global_allowed: bool = True, restart: bool = False, cmdline_arg: str = 'DEFAULT', tip: str = '',
             group: ConfGroup = ConfGroup.NONE,
             related: str = '', requires: str = '') -> Tuple[str, str, str, str, str | None, bool, str, ConfGroup, str, str, bool]:
        return cname, section, cmdline_arg, conf_type, default, restart, tip, group, related, requires, global_allowed

    SPLASH_SCREEN_ENABLED = _def(cname=QT_TR_NOOP('splash-screen-enabled'), default='yes', cmdline_arg='splash',
                                 group=ConfGroup.FEATURES,
                                 tip=QT_TR_NOOP('enable the startup splash screen'))
    SYSTEM_TRAY_ENABLED = _def(cname=QT_TR_NOOP('system-tray-enabled'), default="no", restart=True,
                               group=ConfGroup.SYSTEM_TRAY,
                               tip=QT_TR_NOOP('start up in the system tray'), related='hide-on-focus-out')
    HIDE_ON_FOCUS_OUT = _def(cname=QT_TR_NOOP('hide-on-focus-out'), default="no", restart=False,
                             group=ConfGroup.WINDOWING,
                             tip=QT_TR_NOOP('minimize the main window automatically on focus out'))
    SMART_WINDOW = _def(cname=QT_TR_NOOP('smart-window'), default="yes",
                        group=ConfGroup.WINDOWING,
                        tip=QT_TR_NOOP('smart main window placement and geometry (X11 and XWayland)'), restart=True)
    SMART_USES_XWAYLAND = _def(cname=QT_TR_NOOP('smart-uses-xwayland'), default="yes", restart=True,
                               group=ConfGroup.WINDOWING,
                               tip=QT_TR_NOOP('if smart-window is enabled, use Xwayland in Wayland'))
    PREFER_QT6 = _def(cname=QT_TR_NOOP('prefer-qt6'), default="true", cmdline_arg='DISALLOWED',
                      group=ConfGroup.WINDOWING,
                      tip=QT_TR_NOOP('Prefer Qt6 over Qt5 (if both are installed)'), restart=True)
    MONOCHROME_TRAY_ENABLED = _def(cname=QT_TR_NOOP('monochrome-tray-enabled'), default="no", restart=False,
                                   group=ConfGroup.SYSTEM_TRAY,
                                   tip=QT_TR_NOOP('monochrome dark themed system tray'))
    MONO_LIGHT_TRAY_ENABLED = _def(cname=QT_TR_NOOP('mono-light-tray-enabled'), default="no", restart=False,
                                   group=ConfGroup.SYSTEM_TRAY,
                                   tip=QT_TR_NOOP('monochrome light themed system tray'))
    TRAY_FOLLOWS_THEME = _def(cname=QT_TR_NOOP('tray-follows-theme'), default="yes", restart=False,
                              group=ConfGroup.SYSTEM_TRAY,
                              tip=QT_TR_NOOP('tray dark/light theming follows desktop-theme changes'))
    TOOLBAR_AT_TOP = _def(cname=QT_TR_NOOP('toolbar-at-top'), default="no", restart=False,
                          group=ConfGroup.WINDOWING,
                          tip=QT_TR_NOOP('toolbar resides at top of main window'))
    SEPARATE_STATUS_BAR = _def(cname=QT_TR_NOOP('separate-status-bar'), default="no", restart=True,
                               group=ConfGroup.WINDOWING,
                               tip=QT_TR_NOOP('seperate the status-bar from the tool-bar'))
    PROTECT_NVRAM_ENABLED = _def(cname=QT_TR_NOOP('protect-nvram'), default="yes", restart=True,
                                 group=ConfGroup.DDC,
                                 tip=QT_TR_NOOP('alter options and defaults to minimize VDU NVRAM writes'))
    ORDER_BY_NAME = _def(cname=QT_TR_NOOP('order-by-name'), default="no",
                         group=ConfGroup.WINDOWING,
                         tip=QT_TR_NOOP('order lists and tabs by vdu-name'))
    LUX_OPTIONS_ENABLED = _def(cname=QT_TR_NOOP('lux-options-enabled'), default="yes", restart=True,
                               group=ConfGroup.FEATURES,
                               tip=QT_TR_NOOP('enable light metering options'))
    LUX_TRAY_ICON = _def(cname=QT_TR_NOOP('lux-tray-icon'), default="yes", restart=False,
                         group=ConfGroup.SYSTEM_TRAY,
                         tip=QT_TR_NOOP('enable lux light-level system-tray icon'))
    SCHEDULE_ENABLED = _def(cname=QT_TR_NOOP('schedule-enabled'), default='yes',
                            group=ConfGroup.FEATURES,
                            tip=QT_TR_NOOP('enable preset schedule'))
    WEATHER_ENABLED = _def(cname=QT_TR_NOOP('weather-enabled'), default='yes',
                           group=ConfGroup.FEATURES,
                           tip=QT_TR_NOOP('enable weather lookups'))
    DBUS_CLIENT_ENABLED = _def(cname=QT_TR_NOOP('dbus-client-enabled'), default="yes",
                               group=ConfGroup.DDC,
                               tip=QT_TR_NOOP('use the D-Bus ddcutil-server if available'))
    DBUS_EVENTS_ENABLED = _def(cname=QT_TR_NOOP('dbus-events-enabled'), default="yes",
                               group=ConfGroup.DDC,
                               tip=QT_TR_NOOP('enable D-Bus ddcutil-server events'), requires='dbus-client-enabled')
    LAPTOP_PANEL_ENABLED = _def(cname=QT_TR_NOOP('laptop-panel-enabled'), default="no",
                                group=ConfGroup.DDC,
                                tip=QT_TR_NOOP('use brightnessctl utility for laptop panel control'))
    SYSLOG_ENABLED = _def(cname=QT_TR_NOOP('syslog-enabled'), default="no",
                          group=ConfGroup.FEATURES,
                          tip=QT_TR_NOOP('divert diagnostic output to the syslog'))
    DEBUG_ENABLED = _def(cname=QT_TR_NOOP('debug-enabled'), default="no",
                         group=ConfGroup.FEATURES,
                         tip=QT_TR_NOOP('output extra debug information'))
    WARNINGS_ENABLED = _def(cname=QT_TR_NOOP('warnings-enabled'), default="no",
                            group=ConfGroup.DDC,
                            tip=QT_TR_NOOP('popup warnings if a VDU lacks an enabled control'))
    TRANSLATIONS_ENABLED = _def(cname=QT_TR_NOOP('translations-enabled'), default="no", restart=True,
                                group=ConfGroup.FEATURES,
                                tip=QT_TR_NOOP('enable language translations, currently not updated (no known users)'))
    LOCATION = _def(cname=QT_TR_NOOP('location'), conf_type=ConfType.LOCATION, tip=QT_TR_NOOP('latitude,longitude'))
    DDCUTIL_EMULATOR = _def(cname=QT_TR_NOOP('ddcutil-emulator'), conf_type=ConfType.PATH,
                            tip=QT_TR_NOOP('additional command-line ddcutil emulator for a laptop panel'))
    SLEEP_MULTIPLIER = _def(cname=QT_TR_NOOP('sleep-multiplier'), section=ConfSec.DDCUTIL_PARAMETERS, conf_type=ConfType.FLOAT,
                            tip=QT_TR_NOOP('ddcutil --sleep-multiplier (0.1 .. 2.0, default none)'))
    DDCUTIL_EXTRA_ARGS = _def(cname=QT_TR_NOOP('ddcutil-extra-args'), section=ConfSec.DDCUTIL_PARAMETERS, conf_type=ConfType.TEXT,
                              tip=QT_TR_NOOP('ddcutil extra arguments (default none)'))
    VDU_NAME = _def(cname=QT_TR_NOOP('vdu-name'), section=ConfSec.VDU_CONTROLS_WIDGETS, conf_type=ConfType.TEXT,
                    global_allowed=False, cmdline_arg='DISALLOWED', tip=QT_TR_NOOP('Name to display for this VDU'))
    ENABLE_VCP_CODES = _def(cname=QT_TR_NOOP('enable-vcp-codes'), section=ConfSec.VDU_CONTROLS_WIDGETS, conf_type=ConfType.CSV,
                            cmdline_arg='DISALLOWED', tip=QT_TR_NOOP('CSV list of VCP Hex-code capabilities to enable'))
    CAPABILITIES_OVERRIDE = _def(cname=QT_TR_NOOP('capabilities-override'), section=ConfSec.DDCUTIL_CAPABILITIES,
                                 conf_type=ConfType.LONG_TEXT, cmdline_arg='DISALLOWED')
    METADATA_VERSION_OPTION = _def(cname=QT_TR_NOOP('version'), section=ConfSec.METADATA_SECTION,
                                   conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED')
    METADATA_TIMESTAMP_OPTION = _def(cname=QT_TR_NOOP('timestamp'), section=ConfSec.METADATA_SECTION,
                                     conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED')
    UNKNOWN = _def(cname="UNKNOWN", section=ConfSec.UNKNOWN_SECTION, conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED', tip='')

    def __init__(self, conf_name: str, section: str, cmdline_arg: str, conf_type: str, default: str | None,
                 restart_required: bool, help_text: str, group: ConfGroup, related: str, requires: str, global_allowed):
        self.conf_name = conf_name
        self.conf_section = section
        self.conf_type = conf_type
        self.conf_id = self.conf_section, self.conf_name
        self.restart_required = restart_required
        self.help = help_text
        self.cmdline_arg = self.conf_name.replace("-enabled", "") if cmdline_arg == 'DEFAULT' else cmdline_arg
        self.cmdline_var = None if self.cmdline_arg == "DISALLOWED" else self.conf_name.replace('-enabled', '').replace('-', '_')
        self.default_value = default
        self.related = related
        self.requires = requires
        self.global_allowed = global_allowed
        self.group = group

    def add_cmdline_arg(self, parser: argparse.ArgumentParser) -> None:
        if self.cmdline_arg != "DISALLOWED":
            if self.conf_type == ConfType.BOOL:  # Store strings for bools, allows us to differentiate yes/no and not supplied.
                parser.add_argument(f"--{self.cmdline_arg}", dest=self.cmdline_var, action='store_const', const='yes',
                                    help=self.help + ' ' + (tr('(default)') if self.default_value == 'yes' else ''))
                parser.add_argument(f"--no-{self.cmdline_arg}", dest=self.cmdline_var, action='store_const', const='no',
                                    help=tr('(default)') if self.default_value == 'no' else '')
            elif self.conf_type == ConfType.FLOAT:
                parser.add_argument(f"--{self.cmdline_arg}", type=float, default=self.default_value, help=self.help)
            else:
                parser.add_argument(f"--{self.cmdline_arg}", type=str, default=self.default_value, help=self.help)

@dataclass
class VcpCapability:
    """Representation of a VCP (Virtual Control Panel) capability for a VDU."""
    vcp_code: str
    name: str
    vcp_type: str | None = None
    values: List | None = None
    causes_config_change: bool = False
    icon_source: bytes | None = None
    enabled: bool = False
    can_transition: bool = False
    retry_setvcp: bool = True

    def __post_init__(self):
        self.retry_setvcp = self.retry_setvcp and not self.causes_config_change  # Safe to repeat set on error
        # For non-continuous types of VCP (VCP types SNC or CNC). Also for special cases, such as restricted brightness ranges.
        self.values = [] if self.values is None else self.values

    def property_name(self) -> str:
        return re.sub('[^A-Za-z0-9_-]', '-', self.name).lower()

    def translated_name(self):  # deal with ddcutil returning mixed caps without losing the caps if possible
        tr_key = self.name.lower()
        tr_result = tr(tr_key)  # translations are keyed on lowercase
        return tr_result if tr_key != tr_result else self.name  # Use original name if not translated


# Enabling this would enable anything supported by ddcutil - but that isn't safe for the hardware
# given the undocumented settings that appear to be available and the sometimes dodgy VDU-vendor DDC
# implementations.  Plus, the user might not be able to reset to factory for some of them?
SUPPORT_ALL_VCP = False


# Maps of controls supported by name on the command line and in config files.
SUPPORTED_VCP_BY_CODE: Dict[str, VcpCapability] = {
    **{code: VcpCapability(code, name, retry_setvcp=False)
       for code, name in (DdcutilAggregator().get_supported_vcp_codes_map().items() if SUPPORT_ALL_VCP else [])},
    **{
        BRIT: VcpCapability(BRIT, QT_TR_NOOP('brightness'), CON, icon_source=BRIGHTNESS_SVG, enabled=True, can_transition=True),
        CONT: VcpCapability(CONT, QT_TR_NOOP('contrast'), CON, icon_source=CONTRAST_SVG, enabled=True, can_transition=True),
        '62': VcpCapability('62', QT_TR_NOOP('audio volume'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '8D': VcpCapability('8D', QT_TR_NOOP('audio mute'), SNC, icon_source=VOLUME_SVG),
        '8F': VcpCapability('8F', QT_TR_NOOP('audio treble'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '91': VcpCapability('91', QT_TR_NOOP('audio bass'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '64': VcpCapability('91', QT_TR_NOOP('audio mic volume'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '60': VcpCapability('60', QT_TR_NOOP('input source'), SNC, causes_config_change=True),
        'D6': VcpCapability('D6', QT_TR_NOOP('power mode'), SNC, causes_config_change=True),
        'CC': VcpCapability('CC', QT_TR_NOOP('OSD language'), SNC),
        '14': VcpCapability('14', QT_TR_NOOP('color preset'), SNC),
        '0C': VcpCapability('0C', QT_TR_NOOP('color temperature'), CON, icon_source=COLOR_TEMPERATURE_SVG, enabled=True),
    }}

SUPPORTED_VCP_BY_PROPERTY_NAME = {c.property_name(): c for c in SUPPORTED_VCP_BY_CODE.values()}

@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    place_name: str | None

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if not isinstance(other, GeoLocation):
            return NotImplemented  # don't attempt to compare against unrelated types
        return self.latitude == other.latitude and self.longitude == other.longitude and \
            self.place_name == other.place_name



class VduControlsConfig:
    """
    A vdu_controls config that can be read or written from INI style files by the standard configparser package.
    Includes a method that can fold in values from command line arguments parsed by the standard argparse package.
    """

    def __init__(self, config_name: str, default_enabled_vcp_codes: List | None = None, main_config: bool = False) -> None:
        self.config_name = config_name
        self.ini_content = ConfIni()

        if main_config:
            self.ini_content[ConfSec.VDU_CONTROLS_GLOBALS] = {}
            for option in ConfOpt:  # Add in options for all supported controls
                if option.conf_section == ConfSec.VDU_CONTROLS_GLOBALS:
                    default_str = str(option.default_value) if option.default_value is not None else ''
                    self.ini_content.set(*option.conf_id, default_str)

        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS] = {}
        self.ini_content[ConfSec.DDCUTIL_PARAMETERS] = {}
        self.ini_content[ConfSec.DDCUTIL_CAPABILITIES] = {}

        for item in SUPPORTED_VCP_BY_CODE.values():
            self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][item.property_name()] = 'yes' if item.enabled else 'no'

        self.ini_content.set(*ConfOpt.ENABLE_VCP_CODES.conf_id, '')
        if not main_config:
            self.ini_content.set(*ConfOpt.VDU_NAME.conf_id, '')
        self.ini_content.set(*ConfOpt.SLEEP_MULTIPLIER.conf_id, str('0.0'))
        self.ini_content.set(*ConfOpt.DDCUTIL_EXTRA_ARGS.conf_id, '')
        self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, '')

        if default_enabled_vcp_codes is not None:
            for code in default_enabled_vcp_codes:
                if code in SUPPORTED_VCP_BY_CODE:
                    self.enable_supported_vcp_code(code)
                else:
                    self.enable_unsupported_vcp_code(code)
        self.file_path: Path | None = None

    def get_conf_option(self, section_name: str, option_name: str) -> ConfOpt:
        for option in ConfOpt:  # Inefficient, but a small number of iterations
            if option.conf_section == section_name and option.conf_name == option_name:
                return option
        return ConfOpt.UNKNOWN

    def restrict_to_actual_capabilities(self, supported_by_this_vdu: Dict[str, VcpCapability]) -> None:
        for option_name in self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS]:
            if self.get_conf_option(ConfSec.VDU_CONTROLS_WIDGETS, option_name).conf_type == ConfType.BOOL:
                if option_name in SUPPORTED_VCP_BY_PROPERTY_NAME and \
                        SUPPORTED_VCP_BY_PROPERTY_NAME[option_name].vcp_code not in supported_by_this_vdu:
                    del self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][option_name]
                    log.debug(f"Removed {self.config_name} {option_name} - not supported by VDU") if log.debug_enabled else None
                elif option_name.startswith('unsupported-') and option_name[len('unsupported-'):] not in supported_by_this_vdu:
                    del self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][option_name]
                    log.debug(f"Removed {self.config_name} {option_name} - not supported by VDU") if log.debug_enabled else None

    def get_vdu_preferred_name(self):
        custom_name = self.ini_content.get(*ConfOpt.VDU_NAME.conf_id, fallback=None)
        return custom_name if custom_name is not None and custom_name.strip() != '' else self.config_name

    def is_set(self, option: ConfOpt, fallback=False) -> bool:
        return self.ini_content.getboolean(option.conf_section, option.conf_name, fallback=fallback)

    def set_option_from_args(self, option: ConfOpt, arg_values: Dict[str, Any]):
        if option.cmdline_var is not None and option.cmdline_var in arg_values and arg_values[option.cmdline_var] is not None:
            str_value = str(arg_values[option.cmdline_var])
            if str_value != self.ini_content[option.conf_section][option.conf_name]:
                log.warning(f"command-line {option.cmdline_arg}={str_value} overrides {option.conf_section}.{option.conf_name}="
                            f"{self.ini_content[option.conf_section][option.conf_name]} (in {self.file_path})")
                self.ini_content[option.conf_section][option.conf_name] = str_value

    def get_sleep_multiplier(self, fallback: float | None = None) -> float | None:
        value = self.ini_content.getfloat(*ConfOpt.SLEEP_MULTIPLIER.conf_id, fallback=0.0)
        return fallback if math.isclose(value, 0.0) else value

    def get_ddcutil_extra_args(self, fallback: List[str] | None = None) -> List[str]:
        fallback = [] if fallback is None else fallback
        value = self.ini_content.get(*ConfOpt.DDCUTIL_EXTRA_ARGS.conf_id, fallback=None)
        return fallback if value is None or value.strip() == '' else value.split()

    def get_capabilities_alt_text(self) -> str:
        return self.ini_content.get(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id)

    def set_capabilities_alt_text(self, alt_text: str) -> None:
        self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, alt_text)

    def enable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][SUPPORTED_VCP_BY_CODE[vcp_code].property_name()] = 'yes'

    def enable_unsupported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][f'unsupported-{vcp_code}'] = 'yes'

    def disable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][SUPPORTED_VCP_BY_CODE[vcp_code].property_name()] = 'no'

    def get_all_enabled_vcp_codes(self) -> List[str]:  # Not very efficient
        enabled_vcp_codes = []
        for control_name, control_def in SUPPORTED_VCP_BY_PROPERTY_NAME.items():
            if self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS].getboolean(control_name, fallback=False):
                enabled_vcp_codes.append(control_def.vcp_code)
        enable_codes_str = self.ini_content.get(*ConfOpt.ENABLE_VCP_CODES.conf_id, fallback='')
        for vcp_code in enable_codes_str.split(","):
            if code := vcp_code.strip().upper():
                if code not in enabled_vcp_codes:
                    enabled_vcp_codes.append(code)
                else:
                    log.warning(f"supported enabled vcp_code {code} is redundantly listed "
                                f"in enabled_vcp_codes ({enable_codes_str})")
        return enabled_vcp_codes

    def get_location(self) -> GeoLocation | None:
        try:
            spec = self.ini_content.get(*ConfOpt.LOCATION.conf_id, fallback=None)
            if spec is None or spec.strip() == '':
                return None
            parts = spec.split(',')
            return GeoLocation(float(parts[0]), float(parts[1]), None if len(parts) < 3 else parts[2])
        except ValueError as ve:
            log.error("Problem with geolocation:", ve)
            return None

    def parse_file(self, config_path: Path) -> None:
        """Parse config values from file"""
        self.file_path = config_path
        basename = os.path.basename(config_path)
        config_text = Path(config_path).read_text()
        log.info("Using config file '" + config_path.as_posix() + "'")
        if re.search(r'(\[ddcutil-capabilities])|(\[ddcutil-parameters])|(\[vdu-controls-\w])', config_text) is None:
            log.info(f"Old style config file {basename} overrides ddcutils capabilities")
            self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, config_text)
            return
        self.ini_content.read_string(config_text)
        # Manually extract the text preserving meaningful indentation
        preserve_indents_match = re.search(
            r'\[ddcutil-capabilities](?:.|\n)*\ncapabilities-override[ \t]*[:=]((.*)(\n[ \t].+)*)', config_text)
        alt_text = preserve_indents_match.group(1) if preserve_indents_match is not None else ''
        # Remove excess indentation while preserving the minimum existing indentation.
        alt_text = inspect.cleandoc(alt_text)
        self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, alt_text)

    def reload(self) -> None:
        log.info(f"Reloading config: {self.file_path}")
        if self.file_path:
            for section in list(self.ini_content.data_sections()):
                self.ini_content.remove_section(section)
            self.parse_file(self.file_path)

    def debug_dump(self) -> None:
        origin = 'configuration' if self.file_path is None else os.path.basename(self.file_path)
        for section in self.ini_content.sections():
            for option in self.ini_content[section]:
                log.debug(f"config: {origin} [{section}] {option} = {self.ini_content[section][option]}")

    def write_file(self, config_path: Path, overwrite: bool = False) -> None:
        """Write the config to a file.  Used for creating initial template config files."""
        self.file_path = config_path
        if config_path.exists():
            if not config_path.is_file() or not overwrite:
                log.error(f"{config_path.as_posix()} exists, remove the file if you really want to replace it.")
                return
        log.info(f"Creating new config file {config_path.as_posix()}")
        self.ini_content.save(config_path)

    def parse_global_args(self, args=None) -> argparse.Namespace:
        """Parse command line arguments and integrate the results into this config"""
        if args is None:
            args = sys.argv[1:]
        parser = argparse.ArgumentParser(
            description=textwrap.dedent(f"""
            {APPNAME}
              Uses ddcutil to issue Display Data Channel (DDC) Virtual Control Panel (VCP) commands.
              Controls DVI/DP/HDMI/USB connected monitors (but not builtin laptop displays)."""),
            formatter_class=argparse.RawTextHelpFormatter)
        parser.epilog = textwrap.dedent("""
            As well as command line arguments, individual VDU controls and optimizations may be
            specified in monitor specific configuration files, see --detailed-help for details.

            See the --detailed-help for important licencing information.
            """)
        parser.add_argument('--detailed-help', default=False, action='store_true', help='Detailed help (in markdown format).')
        parser.add_argument('--about', default=False, action='store_true', help='info about vdu_controls')
        parser.add_argument('--show', default=[], action='append',
                            choices=[vcp.property_name() for vcp in SUPPORTED_VCP_BY_CODE.values()],
                            help='show specified control only (--show may be specified multiple times)')
        parser.add_argument('--hide', default=[], action='append',
                            choices=[vcp.property_name() for vcp in SUPPORTED_VCP_BY_CODE.values()],
                            help='hide/disable a control (--hide may be specified multiple times)')
        parser.add_argument('--enable-vcp-code', type=str, action='append',
                            help='enable controls for an unsupported vcp-code hex value (maybe specified multiple times)')
        for option in ConfOpt:
            if option.cmdline_arg is not None:
                option.add_cmdline_arg(parser)
        parser.add_argument('--create-config-files', action='store_true',
                            help="create template config files, one global file and one for each detected VDU.")
        parser.add_argument('--install', action='store_true',
                            help="installs the vdu_controls in the current user's path and desktop application menu.")
        parser.add_argument('--uninstall', action='store_true',
                            help='uninstalls the vdu_controls application menu file and script for the current user.')
        parsed_args = parser.parse_args(args=args)

        arg_values = vars(parsed_args)
        for option in ConfOpt:
            if option.cmdline_arg is not None:
                self.set_option_from_args(option, arg_values)
        if len(parsed_args.show) != 0:
            for control_def in SUPPORTED_VCP_BY_CODE.values():
                if control_def.property_name() in parsed_args.show:
                    self.enable_supported_vcp_code(control_def.vcp_code)
                else:
                    self.disable_supported_vcp_code(control_def.vcp_code)
        if len(parsed_args.hide) != 0:
            for control_def in SUPPORTED_VCP_BY_CODE.values():
                if control_def.property_name() in parsed_args.hide:
                    self.disable_supported_vcp_code(control_def.vcp_code)
        if parsed_args.enable_vcp_code is not None:
            for code in parsed_args.enable_vcp_code:
                self.enable_unsupported_vcp_code(code)

        return parsed_args

