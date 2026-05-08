# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import argparse
import inspect
import math
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any

import vdu_controls.logging as log
from vdu_controls import app_locale
from vdu_controls.app_locale import tr
from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import APPNAME
from vdu_controls.ddcutil_abstract import CON, BRIT, CONT, SNC
from vdu_controls.ddcutil_aggregator import DdcutilAggregator
from vdu_controls.misc import LocalStrEnum, GeoLocation
from vdu_controls.qt_imports import QT_TR_NOOP
from vdu_controls.svg import BRIGHTNESS_SVG, CONTRAST_SVG, VOLUME_SVG, COLOR_TEMPERATURE_SVG


class ConfType(LocalStrEnum):
    BOOL = 'bool'
    FLOAT = 'float'
    CSV = 'csv'
    LONG_TEXT = 'long_text'
    TEXT = 'text'
    LOCATION = 'location'
    PATH = 'path'


class TitledStrEnum(LocalStrEnum):
    """
    String enum where each member stores a human presentable title that gets translated
    using tr(). The context is the enum class name.
    Define members as: NAME = ("value", "raw title")
    """

    # Note: __contains__ and _missing_ are inherited from BaseStrEnum.
    # They will work correctly because members are still strings.

    def __new__(cls, value: str, raw_title: str) -> TitledStrEnum:
        # Because we subclass BaseStrEnum, we must properly create the string and enum parts.
        # The easiest way: call str.__new__ then set _value_ and _raw_title_.
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._raw_title_ = raw_title
        return obj

    @property
    def localized_name(self) -> str:
        """Translated name using the enum class name as context."""
        return tr(self._raw_title_, self.__class__.__name__)

    def __str__(self) -> str:
        return self.value


class ConfSec(TitledStrEnum):
    '''
    These are the valid fixed-names.  The fixed names are used in metadata headings
    and vdu_controls.ini.  Preset .ini files may also have dynamically named
    'device-name' sections which are also valid, but not enumerated here.
    '''
    VDU_CONTROLS_GLOBALS    = ("vdu-controls-globals", QT_TR_NOOP("vdu controls globals"))
    VDU_CONTROLS_WIDGETS    = ("vdu-controls-widgets", QT_TR_NOOP("vdu controls widgets"))
    DDCUTIL_PARAMETERS      = ("ddcutil-parameters", QT_TR_NOOP("ddcutil parameters"))
    DDCUTIL_CAPABILITIES    = ("ddcutil-capabilities", QT_TR_NOOP("ddcutil capabilities"))


class SubGroup(Enum):
    WINDOWING =   (1, QT_TR_NOOP('Windowing'))
    FEATURES =    (3, QT_TR_NOOP('Features'))
    SYSTEM_TRAY = (2, QT_TR_NOOP('System Tray'))
    DDC =         (4, QT_TR_NOOP('DDC options'))
    LOGGING =     (5, QT_TR_NOOP('Logging'))
    NONE =        (6, '')

    @property
    def intval(self) -> int:
        return self.value[0]

    @property
    def localized_name(self) -> str:
        return tr(self.value[1], SubGroup.__name__)


@dataclass(frozen=True)
class ConfOptDef:
    conf_name: str
    conf_section: str = ConfSec.VDU_CONTROLS_GLOBALS
    conf_type: str = ConfType.BOOL
    default_value: str | None = None
    global_allowed: bool = True
    restart_required: bool = False
    cmdline_arg: str = 'DEFAULT'
    ui_label: str | None = None
    help: str = ''
    sub_group: SubGroup = SubGroup.NONE
    related: str = ''
    requires: str = ''
    warning: str = ''

    @property
    def conf_id(self) -> str:
        return self.conf_section, self.conf_name

    @property
    def cmdline_var(self) -> str:
        return None if self.cmdline_arg == "DISALLOWED" else self.conf_name.replace('-enabled', '').replace('-', '_')

    @property
    def localized_name(self) -> str:
        return tr(self.ui_label, ConfOpt.__name__)

    @property
    def localized_help(self) -> str:
        return tr(self.help, ConfOpt.__name__)

    @property
    def localized_warning(self) -> str:
        return tr(self.warning, ConfOpt.__name__)

    def __post_init__(self):
        # hack to fit in with old convention - bypass frozen during initialization.
        # TODO refactor out the need to do this -
        proper_arg = self.conf_name.replace("-enabled", "") if self.cmdline_arg == 'DEFAULT' else self.cmdline_arg
        # Bypass the frozen restriction to assign it
        object.__setattr__(self, "cmdline_arg", proper_arg)


class ConfOpt(Enum):  # An Enum with frozen data items for values is used for convenience for scope/iteration

    SPLASH_SCREEN_ENABLED = ConfOptDef(
        conf_name='splash-screen-enabled', default_value='yes', cmdline_arg='splash',
        ui_label=QT_TR_NOOP('splash screen'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('enable the startup splash screen'))

    SYSTEM_TRAY_ENABLED = ConfOptDef(
        conf_name='system-tray-enabled', default_value="no", restart_required=True,
        ui_label=QT_TR_NOOP('system tray'),
        sub_group=SubGroup.SYSTEM_TRAY,
        help=QT_TR_NOOP('start up in the system tray'), related='hide-on-focus-out')

    HIDE_ON_FOCUS_OUT = ConfOptDef(
        conf_name='hide-on-focus-out', default_value="no", restart_required=False,
        ui_label=QT_TR_NOOP('hide on focus out'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('minimize the main window automatically on focus out'))

    SMART_WINDOW = ConfOptDef(
        conf_name='smart-window', default_value="yes",
        ui_label=QT_TR_NOOP('smart window'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('smart main window placement and geometry (X11 and XWayland)'), restart_required=True)

    SMART_USES_XWAYLAND = ConfOptDef(
        conf_name='smart-uses-xwayland', default_value="yes", restart_required=True,
        ui_label=QT_TR_NOOP('smart uses xwayland'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('if smart-window is enabled, use Xwayland in Wayland'))

    PREFER_QT6 = ConfOptDef(
        conf_name='prefer-qt6', default_value="true", cmdline_arg='DISALLOWED',
        ui_label=QT_TR_NOOP('prefer-qt6'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('Prefer Qt6 over Qt5 (if both are installed)'), restart_required=True)

    MONOCHROME_TRAY_ENABLED = ConfOptDef(
        conf_name='monochrome-tray-enabled', default_value="no", restart_required=False,
        ui_label=QT_TR_NOOP('monochrome tray'),
        sub_group=SubGroup.SYSTEM_TRAY,
        help=QT_TR_NOOP('monochrome dark themed system tray'))

    MONO_LIGHT_TRAY_ENABLED = ConfOptDef(
        conf_name='mono-light-tray-enabled', default_value="no", restart_required=False,
        ui_label=QT_TR_NOOP('mono light tray'),
        sub_group=SubGroup.SYSTEM_TRAY,
        help=QT_TR_NOOP('monochrome light themed system tray'))

    TRAY_FOLLOWS_THEME = ConfOptDef(
        conf_name='tray-follows-theme', default_value="yes", restart_required=False,
        ui_label=QT_TR_NOOP('tray follows theme'),
        sub_group=SubGroup.SYSTEM_TRAY,
        help=QT_TR_NOOP('tray dark/light theming follows desktop-theme changes'))

    TOOLBAR_AT_TOP = ConfOptDef(
        conf_name='toolbar-at-top', default_value="no", restart_required=False,
        ui_label=QT_TR_NOOP('toolbar at top'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('toolbar resides at top of main window'))

    SEPARATE_STATUS_BAR = ConfOptDef(
        conf_name='separate-status-bar', default_value="no", restart_required=True,
        ui_label=QT_TR_NOOP('separate status bar'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('seperate the status-bar from the tool-bar'))

    PROTECT_NVRAM_ENABLED = ConfOptDef(
        conf_name='protect-nvram', default_value="yes", restart_required=True,
        ui_label=QT_TR_NOOP('protect nvram'),
        sub_group=SubGroup.DDC,
        help=QT_TR_NOOP('alter options and defaults to minimize VDU NVRAM writes'))

    ORDER_BY_NAME = ConfOptDef(
        conf_name='order-by-name', default_value="no",
        ui_label=QT_TR_NOOP('order by name'),
        sub_group=SubGroup.WINDOWING,
        help=QT_TR_NOOP('order lists and tabs by vdu-name'))

    LUX_OPTIONS_ENABLED = ConfOptDef(
        conf_name='lux-options-enabled', default_value="yes", restart_required=True,
        ui_label=QT_TR_NOOP('lux options'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('enable light metering options'))

    LUX_TRAY_ICON = ConfOptDef(
        conf_name='lux-tray-icon', default_value="yes", restart_required=False,
        ui_label=QT_TR_NOOP('lux tray icon'),
        sub_group=SubGroup.SYSTEM_TRAY,
        help=QT_TR_NOOP('enable lux light-level system-tray icon'))

    SCHEDULE_ENABLED = ConfOptDef(
        conf_name='schedule-enabled', default_value='yes',
        ui_label=QT_TR_NOOP('schedule'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('enable preset schedule'))

    WEATHER_ENABLED = ConfOptDef(
        conf_name='weather-enabled', default_value='yes',
        ui_label=QT_TR_NOOP('weather'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('enable weather lookups'))

    DBUS_CLIENT_ENABLED = ConfOptDef(
        conf_name='dbus-client-enabled', default_value="yes",
        ui_label=QT_TR_NOOP('dbus client'),
        sub_group=SubGroup.DDC,
        help=QT_TR_NOOP('use the D-Bus ddcutil-server if available'))

    DBUS_EVENTS_ENABLED = ConfOptDef(
        conf_name='dbus-events-enabled', default_value="yes",
        ui_label=QT_TR_NOOP('dbus events'),
        sub_group=SubGroup.DDC,
        help=QT_TR_NOOP('enable D-Bus ddcutil-server events'), requires='dbus-client-enabled')

    LAPTOP_PANEL_ENABLED = ConfOptDef(
        conf_name='laptop-panel-enabled', default_value="no",
        ui_label=QT_TR_NOOP('laptop panel'),
        sub_group=SubGroup.DDC,
        help=QT_TR_NOOP('use brightnessctl utility for laptop panel control'))

    SYSLOG_ENABLED = ConfOptDef(
        conf_name='syslog-enabled', default_value="no",
        ui_label=QT_TR_NOOP('syslog'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('divert diagnostic output to the syslog'))

    DEBUG_ENABLED = ConfOptDef(
        conf_name='debug-enabled', default_value="no",
        ui_label=QT_TR_NOOP('debug'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('output extra debug information'))

    WARNINGS_ENABLED = ConfOptDef(
        conf_name='warnings-enabled', default_value="no",
        ui_label=QT_TR_NOOP('warnings'),
        sub_group=SubGroup.DDC,
        help=QT_TR_NOOP('popup warnings if a VDU lacks an enabled control'))

    TRANSLATIONS_ENABLED = ConfOptDef(
        conf_name='translations-enabled', default_value="no", restart_required=True,
        ui_label=QT_TR_NOOP('translations'),
        sub_group=SubGroup.FEATURES,
        help=QT_TR_NOOP('enable language translations, currently not updated (no known users)'),
        warning=('{}\n\n{}\n\n{}'.format(
            QT_TR_NOOP('Your locale {} will be translated.').format(app_locale.get_locale_name())
            if  app_locale.get_locale_name() in app_locale.available_translations() else
            QT_TR_NOOP('Your locale {} lacks a translation.').format(app_locale.get_locale_name()),
            QT_TR_NOOP('Installed translations: {}.').format(', '.join(app_locale.available_translations())),
            QT_TR_NOOP('These translations have not been validated by any native speakers.'))))

    LOCATION = ConfOptDef(
        conf_name='location', conf_type=ConfType.LOCATION,
        ui_label=QT_TR_NOOP('location'),
        help=QT_TR_NOOP('latitude,longitude'))

    DDCUTIL_EMULATOR = ConfOptDef(
        conf_name='ddcutil-emulator', conf_type=ConfType.PATH,
        ui_label=QT_TR_NOOP('ddcutil emulator'),
        help=QT_TR_NOOP('additional command-line ddcutil emulator for a laptop panel'))

    SLEEP_MULTIPLIER = ConfOptDef(
        conf_name='sleep-multiplier', conf_section=ConfSec.DDCUTIL_PARAMETERS,
        ui_label=QT_TR_NOOP('sleep multiplier'),
        conf_type=ConfType.FLOAT,
        help=QT_TR_NOOP('ddcutil --sleep-multiplier (0.1 .. 2.0, default none)'))

    DDCUTIL_EXTRA_ARGS = ConfOptDef(
        conf_name='ddcutil-extra-args', conf_section=ConfSec.DDCUTIL_PARAMETERS,
        ui_label=QT_TR_NOOP('ddcutil extra args'),
        conf_type=ConfType.TEXT,
        help=QT_TR_NOOP('ddcutil extra arguments (default none)'))

    VDU_NAME = ConfOptDef(
        conf_name='vdu-name', conf_section=ConfSec.VDU_CONTROLS_WIDGETS,
        ui_label=QT_TR_NOOP('vdu name'),
        conf_type=ConfType.TEXT,
        global_allowed=False, cmdline_arg='DISALLOWED', help=QT_TR_NOOP('Name to display for this VDU'))

    ENABLE_VCP_CODES = ConfOptDef(
        conf_name='enable-vcp-codes', conf_section=ConfSec.VDU_CONTROLS_WIDGETS,
        ui_label=QT_TR_NOOP('enable vcp codes'),
        conf_type=ConfType.CSV,
        cmdline_arg='DISALLOWED', help=QT_TR_NOOP('CSV list of VCP Hex-code capabilities to enable'))

    CAPABILITIES_OVERRIDE = ConfOptDef(
        conf_name='capabilities-override', conf_section=ConfSec.DDCUTIL_CAPABILITIES,
        ui_label=QT_TR_NOOP('capabilities override'),
        conf_type=ConfType.LONG_TEXT, cmdline_arg='DISALLOWED')

    UNKNOWN = ConfOptDef(
        conf_name="UNKNOWN", conf_section=ConfIni.UNKNOWN_SECTION,
        conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED', help='')

    def __getattr__(self, name):
        """
        Allow ConfOptEnum.BLAH.property to be directly referenced
        instead of having to do ConfOptEnum.BLAH.value.property
        For example, allow ConfOptEnum.LOCATION.conf_name instead
        of ConfOptEnum.LOCATION.value.conf_name
        """
        # Avoid delegating internal Python/Enum attributes (like __members__)
        if name.startswith('_'):
            raise AttributeError(name)

        # Use object.__getattribute__ to safely get 'value' without recursing
        inner_data = object.__getattribute__(self, 'value')
        return getattr(inner_data, name)

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
                print(option)
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

