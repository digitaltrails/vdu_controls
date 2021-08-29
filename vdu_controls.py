#!/usr/bin/python3
"""
#
# vdu_controls.py - Visual Display Unit Controls
# A GUI wrapper for ddcutil
#
# A GUI for retrieving and altering settings of connected VDU's (via
# ddcutil) by issuing DDC VCP commands over HDMI/DisplayPort/DVI/USB.
#
# This code often refers to displays and monitors as VDU's in order to
# disambiguate the noun/verb duality of "display" and "monitor"
#
# Copyright (C) 2021 Michael Hamilton
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.
#
# m i c h a e l   at   a c t r i x   dot   g e n   dot   n z
#
# Prerequisites - OpenSUSE (similar for other distros):
#    Software:
#        zypper install python38-QtPy
#        zypper install ddcutil
#    Kernel Modules:
#        lsmod | grep i2c_dev
#
# Read ddcutil readme concerning config of i2c_dev with nvidia GPU's.
# Detailed ddcutil info at https://www.ddcutil.com/
#
"""

import sys
import re
import subprocess
import os
import base64
import time
import traceback
import argparse
import textwrap
import signal
from pathlib import Path
from typing import List, Tuple, Mapping

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon
from PyQt5.QtSvg import QSvgWidget


def translate(source_text: str):
    """For future internationalization - recommended way to do this at this time."""
    return QCoreApplication.translate('ddc-control', source_text)


BRIGHTNESS_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <style id="current-color-scheme" type="text/css">
        .ColorScheme-Text { color:#232629; }
    </style>
  </defs>
  <g transform="translate(1,1)">
    <g shape-rendering="auto">
      <path d="m11 7c-2.2032167 0-4 1.7967833-4 4 0 2.203217 1.7967833 4 4 4 2.203217 0 4-1.796783 4-4 0-2.2032167-1.796783-4-4-4zm0 1c1.662777 0 3 1.3372234 3 3 0 1.662777-1.337223 3-3 3-1.6627766 0-3-1.337223-3-3 0-1.6627766 1.3372234-3 3-3z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m10.5 3v3h1v-3h-1z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m10.5 16v3h1v-3h-1z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m3 10.5v1h3v-1h-3z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m16 10.5v1h3v-1h-3z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="m14.707031 14-0.707031 0.707031 2.121094 2.121094 0.707031-0.707031-2.121094-2.121094z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="M 5.7070312 5 L 5 5.7070312 L 7.1210938 7.828125 L 7.828125 7.1210938 L 5.7070312 5 z " class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="M 7.1210938 14 L 5 16.121094 L 5.7070312 16.828125 L 7.828125 14.707031 L 7.1210938 14 z " class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <path d="M 16.121094 5 L 14 7.1210938 L 14.707031 7.828125 L 16.828125 5.7070312 L 16.121094 5 z " class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      <g>
        <path d="m11.000001 7.7500005v6.4999985h2.166665l1.083333-2.166666v-2.1666663l-1.083333-2.1666662z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
        <path d="m10.984375 7.734375v0.015625 6.515625h2.191406l1.089844-2.177734v-2.1757816l-1.089844-2.1777344h-2.191406zm0.03125 0.03125h2.140625l1.078125 2.1542969v2.1601561l-1.078125 2.154297h-2.140625v-6.46875z" class="ColorScheme-Text" fill="currentColor" color-rendering="auto" dominant-baseline="auto" image-rendering="auto"/>
      </g>
    </g>
  </g>
</svg>
"""

CONTRAST_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <style type="text/css" id="current-color-scheme">
      .ColorScheme-Text { color:#232629; }
    </style>
  </defs>
  <g transform="translate(1,1)">
    <path style="fill:currentColor;fill-opacity:1;stroke:none" transform="translate(-1,-1)" d="m 12,7 c -2.761424,0 -5,2.2386 -5,5 0,2.7614 2.238576,5 5,5 2.761424,0 5,-2.2386 5,-5 0,-2.7614 -2.238576,-5 -5,-5 z m 0,1 v 8 C 9.790861,16 8,14.2091 8,12 8,9.7909 9.790861,8 12,8" class="ColorScheme-Text" id="path79" />
  </g>
</svg>
"""

VOLUME_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-7 -7 40 40" width="24" height="24">
  <style id="current-color-scheme" type="text/css">
        .ColorScheme-Text { color:#232629; }
    </style>
  <g transform="translate(1,1)">
    <g class="ColorScheme-Text" fill="currentColor">
      <path d="m14.324219 7.28125-.539063.8613281a4 4 0 0 1 1.214844 2.8574219 4 4 0 0 1 -1.210938 2.861328l.539063.863281a5 5 0 0 0 1.671875-3.724609 5 5 0 0 0 -1.675781-3.71875z"/>
      <path d="m13.865234 3.5371094-.24414.9765625a7 7 0 0 1 4.378906 6.4863281 7 7 0 0 1 -4.380859 6.478516l.24414.974609a8 8 0 0 0 5.136719-7.453125 8 8 0 0 0 -5.134766-7.4628906z"/>
      <path d="m3 8h2v6h-2z" fill-rule="evenodd"/>
      <path d="m6 14 5 5h1v-16h-1l-5 5z"/>
    </g>
  </g>
</svg>
"""

# Encode some default graphics to make the script self contained
DEFAULT_SPLASH_PNG = "/usr/share/icons/oxygen/base/256x256/apps/preferences-desktop-display.png"

DDCUTIL = "/usr/bin/ddcutil"

EXIT_CODE_FOR_RESTART = 1959


def get_splash_image() -> QPixmap:
    """Gets the splash pixmap from a KDE oxygen PNG file or, failing that, a small base64 encoded internal JPEG."""
    pixmap = QPixmap()
    if os.path.isfile(DEFAULT_SPLASH_PNG) and os.access(DEFAULT_SPLASH_PNG, os.R_OK):
        pixmap.load(DEFAULT_SPLASH_PNG)
    else:
        pixmap.loadFromData(base64.decodebytes(FALLBACK_SPLASH_JPEG_BASE64), 'JPEG')
    return pixmap


CONTINUOUS_TYPE = 'C'
SIMPLE_NON_CONTINUOUS_TYPE = 'SNC'
COMPLEX_NON_CONTINUOUS_TYPE = 'CNC'


class VcpCapability:
    """ Representation of a VCP (Virtual Control Panel) capability for a VDU. """

    def __init__(self, vcp_code: str, vcp_name: str, vcp_type: str, values: List = None, icon_source: bytes = None):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.vcp_type = vcp_type
        self.icon_source = icon_source
        # For future use if we want to implement non-continuous types of VCP (VCP types SNC or CNC)
        self.values = [] if values is None else values


# VCP capability to be made available as Qt widgets.
class VcpGuiControlDef:
    def __init__(self, vcp_code, vcp_name, causes_config_change: bool = False, icon_source: bytes = None):
        self.vcp_code = vcp_code
        self.name = vcp_name
        self.causes_config_change = causes_config_change
        self.icon_source = icon_source

    def arg_name(self) -> str:
        return self.name.replace(' ', '-').lower()


# Default VCP capabilities to be made available as Qt widgets.
SUPPORTED_VCP_CONTROLS = {
    '10': VcpGuiControlDef('10', 'Brightness', icon_source=BRIGHTNESS_SVG),
    '12': VcpGuiControlDef('12', 'Contrast', icon_source=CONTRAST_SVG),
    '62': VcpGuiControlDef('62', 'Audio volume', icon_source=VOLUME_SVG),
    '60': VcpGuiControlDef('60', 'Input Source', causes_config_change=True),
    'D6': VcpGuiControlDef('D6', 'Power mode', causes_config_change=True),
    'CC': VcpGuiControlDef('CC', 'OSD Language'),
}


class DdcUtil:
    """ Interface to the command line ddcutil Display Data Channel Utility for interacting with VDU's. """

    def __init__(self, debug: bool = False, common_args: List[str] = None):
        super().__init__()
        self.debug = debug
        self.common_args = [] if common_args is None else common_args

    def __run__(self, *args) -> subprocess.CompletedProcess:
        if self.debug:
            print("DEBUG: subprocess run    - ", DDCUTIL, args)
        result = subprocess.run([DDCUTIL, ] + self.common_args + list(args), stdout=subprocess.PIPE, check=True)
        if self.debug:
            print("DEBUG: subprocess result - ", result)
        return result

    def detect_monitors(self) -> List[Tuple[str, str, str, str]]:
        """ Returns a list of (vdu_id, desc) tuples """
        display_list = []
        result = self.__run__('detect', '--terse')
        monitor_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for display_str in re.split("^Display |\nDisplay", result.stdout.decode('utf-8'))[1:]:
            ddc_id = display_str.split('\n')[0].strip()
            monitor_match = monitor_pattern.search(display_str)
            manufacturer, model_name, serial_number = \
                monitor_match.group(1).split(':') if monitor_match else ['', 'Unknown Model', '']
            display_list.append((ddc_id, manufacturer, model_name, serial_number))
        return display_list

    def __parse_values__(self, values_str: str):
        stripped = values_str.strip()
        values_list = []
        if len(stripped) != 0:
            lines_list = stripped.split('\n')
            if len(lines_list) == 1:
                space_separated = lines_list[0].replace('(interpretation unavailable)', '').strip().split(' ')
                values_list = [("x" + v, 'unknown ' + v) for v in space_separated[1:]]
            else:
                values_list = [("x" + key, desc) for key, desc in (v.strip().split(": ", 1) for v in lines_list[1:])]
        return values_list

    def query_capabilities(self, ddc_id: str, alternate_text=None) -> Mapping[str, VcpCapability]:
        """Returns a map of vpc capabilities keyed by vcp code."""
        feature_pattern = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\s(.*)', re.DOTALL | re.MULTILINE)
        feature_map: Mapping[str, VcpCapability] = {}
        if alternate_text is None:
            result = self.__run__('--display', ddc_id, 'capabilities')
            capability_text = result.stdout.decode('utf-8')
        else:
            capability_text = alternate_text
        for feature_text in capability_text.split(' Feature: '):
            feature_match = feature_pattern.match(feature_text)
            if feature_match:
                vcp_code = feature_match.group(1)
                vcp_name = feature_match.group(2)
                values = self.__parse_values__(feature_match.group(3))
                # Guess type from existance or not of value list
                vcp_type = CONTINUOUS_TYPE if len(values) == 0 else SIMPLE_NON_CONTINUOUS_TYPE
                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None)
                feature_map[vcp_code] = capability
        if self.debug:
            print("DEBUG: capabilities", feature_map.keys())
        return feature_map

    def get_attribute(self, ddc_id: str, vcp_code: str) -> Tuple[str, str]:
        """ Given a VDU id and vcp_code, returns the attributes current and maximum value. """
        value_pattern = re.compile(r'VCP ' + vcp_code + r' ([A-Z]+) (.+)\n')
        c_pattern = re.compile(r'([0-9]+) ([0-9]+)')
        snc_pattern = re.compile(r'(x[0-9a-f]+)')
        # Try a few times in case there is a glitch due to a monitor being turned off/on
        for i in range(3):
            result = self.__run__('--brief', '--display', ddc_id, 'getvcp', vcp_code)
            value_match = value_pattern.match(result.stdout.decode('utf-8'))
            if value_match is not None:
                type_indicator = value_match.group(1)
                if type_indicator == CONTINUOUS_TYPE:
                    c_match = c_pattern.match(value_match.group(2))
                    if c_match is not None:
                        return c_match.group(1), c_match.group(2)
                elif type_indicator == SIMPLE_NON_CONTINUOUS_TYPE:
                    snc_match = snc_pattern.match(value_match.group(2))
                    if snc_match is not None:
                        return snc_match.group(1), '0'
                else:
                    raise TypeError('Unsupported VCP type {} for monitor {} vcp_code {}'.format(
                        type_indicator, ddc_id, vcp_code))
            print("WARNING: obtained garbage '" + result.stdout.decode('utf-8') + "' will try again.")
            print("WARNING: ddcutil maybe running too fast for monitor {}, try increasing --sleep-multiplier.".format(
                ddc_id))
            time.sleep(2)
        print("ERROR: ddcutil failed all attempts to get value for monitor {} vcp_code {}".format(ddc_id, vcp_code))
        raise ValueError(
            "ddcutil returned garbage for monitor {} vcp_code {}, try increasing --sleep-multiplier".format(
                ddc_id, vcp_code))

    def set_attribute(self, ddc_id: str, vcp_code: str, new_value: str):
        current, _ = self.get_attribute(ddc_id, vcp_code)
        if new_value != current:
            self.__run__('--display', ddc_id, 'setvcp', vcp_code, new_value)


class DdcVdu:
    def __init__(self, vdu_id, vdu_model, vdu_serial, manufacturer, ddcutil: DdcUtil):
        self.id = vdu_id
        self.model = vdu_model
        self.serial = vdu_serial
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        alt_capability_text = None
        unacceptable_char_pattern = re.compile('[^A-Za-z0-9_-]')
        serial_config = re.sub(unacceptable_char_pattern, '_', vdu_model.strip() + '_' + vdu_serial.strip() + '.conf')
        model_config = re.sub(unacceptable_char_pattern, '_', vdu_model.strip() + '.conf')
        for config_filename in (serial_config, model_config):
            config_path = Path.home().joinpath('.config').joinpath('vdu_controls').joinpath(config_filename)
            print("INFO: checking for config file '" + config_path.as_uri() + "'")
            if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
                alt_capability_text = Path(config_path).read_text()
                print("WARNING: using config file '" + config_path.as_uri() + "'")
                break
        self.capabilities = ddcutil.query_capabilities(vdu_id, alt_capability_text)

    def get_description(self) -> str:
        return self.model + ':' + (self.serial if len(self.serial) != 0 else self.id)

    def get_full_id(self) -> Tuple[str, str, str, str]:
        return self.id, self.manufacturer, self.model, self.serial


def restart_due_to_config_change():
    alert = QMessageBox()
    alert.setText(translate('The physical monitor configuration has changed. A restart is required.'))
    alert.setInformativeText(translate('Dismiss this message to automatically restart.'))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QCoreApplication.exit(EXIT_CODE_FOR_RESTART)


class DdcSliderWidget(QWidget):
    """ GUI control for a DDC continuously variable attribute. Compound widget with icon, slider and text field."""

    def __init__(self, vdu: DdcVdu, vcp_capability: VcpCapability):
        super().__init__()

        self.vdu = vdu
        self.vcp_capability = vcp_capability
        self.current_value, self.max_value = vdu.ddcutil.get_attribute(vdu.id, self.vcp_capability.vcp_code)

        layout = QHBoxLayout()
        self.setLayout(layout)

        if vcp_capability.vcp_code in SUPPORTED_VCP_CONTROLS:
            icon = QSvgWidget()
            icon.load(SUPPORTED_VCP_CONTROLS[vcp_capability.vcp_code].icon_source)
            icon.setFixedSize(50, 50)
            icon.setToolTip(translate(vcp_capability.name))
            layout.addWidget(icon)
        else:
            label = QLabel()
            label.setText(vcp_capability.name)
            layout.addWidget(label)

        self.slider = slider = QSlider()
        slider.setMinimumWidth(200)
        slider.setRange(0, int(self.max_value))
        slider.setValue(int(self.current_value))
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setOrientation(Qt.Horizontal)
        # Don't rewrite the ddc value too often - not sure of the implications
        slider.setTracking(False)
        layout.addWidget(slider)

        text_input = QLineEdit()
        text_input.setMaximumWidth(50)
        text_input.setMaxLength(4)
        text_validator = QIntValidator()
        text_validator.setRange(0, int(self.max_value))
        text_input.setValidator(text_validator)
        text_input.setText(str(slider.value()))
        layout.addWidget(text_input)

        def slider_changed(value):
            self.current_value = str(value)
            text_input.setText(self.current_value)
            self.vdu.ddcutil.set_attribute(self.vdu.id, self.vcp_capability.vcp_code, self.current_value)
            if self.vcp_capability.vcp_code in SUPPORTED_VCP_CONTROLS and\
                    SUPPORTED_VCP_CONTROLS[self.vcp_capability.vcp_code].causes_config_change:
                restart_due_to_config_change()

        slider.valueChanged.connect(slider_changed)

        def slider_moved(value):
            text_input.setText(str(value))

        slider.sliderMoved.connect(slider_moved)

        def text_changed():
            slider.setValue(int(text_input.text()))

        text_input.editingFinished.connect(text_changed)

    def refresh_data(self):
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here.)"""
        self.current_value, _ = self.vdu.ddcutil.get_attribute(self.vdu.id, self.vcp_capability.vcp_code)

    def refresh_view(self):
        """Copy the internally cached current value onto the GUI view."""
        self.slider.setValue(int(self.current_value))


class DdcComboBox(QWidget):
    """ GUI control for a DDC continuously variable attribute. Compound widget with icon, slider and text field."""

    def __init__(self, vdu: DdcVdu, vcp_capability: VcpCapability):
        super().__init__()

        self.vdu = vdu
        self.vcp_capability = vcp_capability
        self.current_value = vdu.ddcutil.get_attribute(vdu.id, vcp_capability.vcp_code)[0]

        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel()
        label.setText(vcp_capability.name)
        layout.addWidget(label)

        self.combo_box = combo_box = QComboBox()
        layout.addWidget(combo_box)

        self.keys = []
        for value, desc in self.vcp_capability.values:
            self.keys.append(value)
            combo_box.addItem(desc, value)

        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))

        def index_changed(index: int):
            self.current_value = self.combo_box.currentData
            self.vdu.ddcutil.set_attribute(self.vdu.id, self.vcp_capability.vcp_code, self.combo_box.currentData())
            if SUPPORTED_VCP_CONTROLS[self.vcp_capability.vcp_code].causes_config_change:
                restart_due_to_config_change()
        combo_box.currentIndexChanged.connect(index_changed)

    def refresh_data(self):
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here.)"""
        self.current_value, _ = self.vdu.ddcutil.get_attribute(self.vdu.id, self.vcp_capability.vcp_code)

    def refresh_view(self):
        """Copy the internally cached current value onto the GUI view."""
        self.combo_box.setCurrentIndex(self.keys.index(self.current_value))


class DdcVduWidget(QWidget):
    """ Widget that contains all the controls for a single VDU (monitor/display) """

    def __init__(self, vdu: DdcVdu, enabled_vcp_codes: List[str], warnings: bool):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        # label.setStyleSheet("font-weight: bold");
        label.setText(translate('Monitor {}: {}').format(vdu.id, vdu.get_description()))
        layout.addWidget(label)
        self.vdu = vdu
        self.vcp_controls = []
        for vcp_code in enabled_vcp_codes:
            if vcp_code in vdu.capabilities:
                capability = vdu.capabilities[vcp_code]
                if capability.vcp_type == CONTINUOUS_TYPE:
                    control = DdcSliderWidget(vdu, capability)
                elif capability.vcp_type == SIMPLE_NON_CONTINUOUS_TYPE:
                    control = DdcComboBox(vdu, capability)
                else:
                    raise TypeError(
                        'No GUI support for VCP type {} for vcp_code {}'.format(capability.vcp_type, vcp_code))
                layout.addWidget(control)
                self.vcp_controls.append(control)
            elif warnings:
                missing_vcp = SUPPORTED_VCP_CONTROLS[vcp_code].name if vcp_code in SUPPORTED_VCP_CONTROLS else vcp_code
                alert = QMessageBox()
                alert.setText(
                    translate('Monitor {} lacks a VCP control for {}.').format(
                        vdu.get_description(), translate(missing_vcp)))
                alert.setInformativeText(translate('No read/write ability for vcp_code {}.').format(vcp_code))
                alert.setIcon(QMessageBox.Warning)
                alert.exec()
        if len(self.vcp_controls) != 0:
            self.setLayout(layout)

    def refresh_data(self):
        """Tell the control widgets to get fresh VDU data (may be called from a task thread, so no GUI op's here.)"""
        for control in self.vcp_controls:
            control.refresh_data()

    def refresh_view(self):
        """Tell the control widgets to refresh their views from their internally cached values."""
        for control in self.vcp_controls:
            control.refresh_view()

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)


class DdcMainWidget(QWidget):
    """ Detects connected VDU's and constructs a window containing a control panel each that is found. """

    def __init__(self, enabled_vcp_codes: List[str], warnings: bool, debug: bool, sleep_multiplier: float,
                 detect_vdu_hook: callable):
        super().__init__()
        layout = QVBoxLayout()
        self.ddcutil = DdcUtil(debug=debug, common_args=['--sleep-multiplier', str(sleep_multiplier)])
        self.vdu_widgets = []
        self.enabled_capabilities = enabled_vcp_codes
        self.warnings = warnings
        self.detected_vdus = self.ddcutil.detect_monitors()
        for vdu_id, manufacturer, vdu_model, vdu_serial in self.detected_vdus:
            vdu = DdcVdu(vdu_id, vdu_model, vdu_serial, manufacturer, self.ddcutil)
            if detect_vdu_hook is not None:
                detect_vdu_hook(vdu)
            vdu_widget = DdcVduWidget(vdu, enabled_vcp_codes, warnings)
            if vdu_widget.number_of_controls() != 0:
                self.vdu_widgets.append(vdu_widget)
                layout.addWidget(vdu_widget)
            elif warnings:
                alert = QMessageBox()
                alert.setText(
                    translate('Monitor {} {} lacks any accessible controls.').format(vdu.id, vdu.get_description()))
                alert.setInformativeText(translate('The monitor will be omitted from the control panel.'))
                alert.setIcon(QMessageBox.Warning)
                alert.exec()

        if len(self.vdu_widgets) == 0:
            alert = QMessageBox()
            alert.setText(translate('No controllable monitors found, exiting.'))
            alert.setInformativeText(translate(
                '''Run ddc_control --debug in a console and check for additional messages.\
                Check the requirements for the ddcutil command.'''))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()
            sys.exit()

        def start_refresh():
            self.refresh_button.setDisabled(True)
            self.progressBar.setDisabled(False)
            # Setting range to 0,0 cause the progress bar to pulsate - used as a busy spinner.
            self.progressBar.setRange(0, 0)
            # Start a background task
            self.refreshDataTask.start()

        def finish_refresh():
            # GUI-thread QT signal handler for refresh task completion
            # Stop the busy-spinner progress bar pulsation
            self.progressBar.setRange(0, 1)
            self.progressBar.setDisabled(True)
            self.refresh_button.setDisabled(False)
            self.refresh_view()

        self.refreshDataTask = RefreshFromVduTask(self)
        self.refreshDataTask.task_finished.connect(finish_refresh)

        self.progressBar = QProgressBar(self)
        # Disable text percentage label on the spinner progress-bar
        self.progressBar.setTextVisible(False)
        self.progressBar.setRange(0, 1)
        self.progressBar.setDisabled(True)
        layout.addWidget(self.progressBar, Qt.AlignVCenter)

        self.refresh_button = QPushButton(translate("Refresh settings from monitors"))
        self.refresh_button.clicked.connect(start_refresh)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def refresh_data(self):
        """Called by a non-GUI task to obtain new data from all monitors.  The task thread cannot do any GUI op's"""
        self.detected_vdus = self.ddcutil.detect_monitors()
        for vdu_widget in self.vdu_widgets:
            if vdu_widget.vdu.get_full_id() in self.detected_vdus:
                vdu_widget.refresh_data()

    def refresh_view(self):
        """Callback when the GUI worker thread completes, the GUI thread and can refresh the GUI views."""
        if len(self.detected_vdus) != len(self.vdu_widgets):
            restart_due_to_config_change()
        for vdu_widget in self.vdu_widgets:
            vdu_widget.refresh_view()


class RefreshFromVduTask(QThread):
    """
    Task to refresh VDU data from the physical VDU's.  Run as a task because
    it can be quite slow depending on the number of VDU's, number of controls,
    as well as ddcutil parameters such as the sleep-multiplier.
    """
    task_finished = pyqtSignal()

    def __init__(self, ddc_widget):
        super().__init__()
        self.ddc_widget = ddc_widget

    def run(self):
        # Running in a task thread, cannot interact with GUI thread, just update the data.
        self.ddc_widget.refresh_data()
        # Tell the GUI-thread the task has finished, the GUI thread will then update the view widgets.
        self.task_finished.emit()


def exception_handler(etype, evalue, etraceback):
    print("ERROR:\n", ''.join(traceback.format_exception(etype, evalue, etraceback)))
    alert = QMessageBox()
    alert.setText(translate('Error: {}').format(''.join(traceback.format_exception_only(etype, evalue))))
    alert.setInformativeText(
        translate('Details: {}').format(''.join(traceback.format_exception(etype, evalue, etraceback))))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QApplication.quit()


def main():
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
        VDU Controls 
          Uses ddcutil to issue Display Data Channel (DDC) Virtual Control Panel (VCP) commands. 
          Controls DVI/DP/HDMI/USB connected monitors (but not builtin laptop displays)."""),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--show',
                        default=[],
                        action='append', choices=[vcp.arg_name() for vcp in SUPPORTED_VCP_CONTROLS.values()],
                        help='show specified control only (--show may be specified multiple times)')
    parser.add_argument('--hide', default=[], action='append',
                        choices=[vcp.arg_name() for vcp in SUPPORTED_VCP_CONTROLS.values()],
                        help='hide/disable a control (--hide may be specified multiple times)')
    parser.add_argument('--enable-vcp-code', type=str, action='append',
                        help='enable controls for an unsupported vcp-code hex value (may be specified multiple times)')
    # Python 3.9 parser.add_argument('--debug',  action=argparse.BooleanOptionalAction, help='enable debugging')
    parser.add_argument('--debug', default=False, action='store_true', help='enable debug output to stdout')
    parser.add_argument('--warnings', default=False, action='store_true',
                        help='enable warnings when a VDU lacks a control')
    parser.add_argument('--no-splash', default=False, action='store_true', help="don't show the splash screen")
    parser.add_argument('--sleep-multiplier', type=float, default="0.5",
                        help='protocol reliability multiplier for ddcutil (typically 0.1 .. 2.0, default is 0.5)')

    args = parser.parse_args()

    sys.excepthook = exception_handler

    app = QApplication(sys.argv)

    pixmap = get_splash_image()

    splash = None if args.no_splash else QSplashScreen(pixmap.scaledToWidth(800).scaledToHeight(400),
                                                       Qt.WindowStaysOnTopHint)

    if splash is not None:
        splash.show()

    app_icon = QIcon()
    app_icon.addPixmap(pixmap)
    app.setWindowIcon(app_icon)
    app.setApplicationDisplayName(translate('VDU Control'))

    if len(args.show) != 0:
        enabled_vcp_codes = [x.vcp_code for x in SUPPORTED_VCP_CONTROLS.values() if x.arg_name() in args.show]
    else:
        enabled_vcp_codes = [x.vcp_code for x in SUPPORTED_VCP_CONTROLS.values() if x.arg_name() not in args.hide]
    if args.enable_vcp_code is not None:
        enabled_vcp_codes.extend(args.enable_vcp_code)

    if splash is not None:
        splash.showMessage(translate('\n\nVDU Control\nLooking for DDC monitors...\n'), Qt.AlignTop | Qt.AlignHCenter)

    def detect_vdu_hook(vdu: DdcVdu):
        if splash is not None:
            splash.showMessage(translate('\n\nVDU Control\nDDC ID {}\n{}').format(vdu.id, vdu.get_description()),
                               Qt.AlignTop | Qt.AlignHCenter)

    main_window = DdcMainWidget(enabled_vcp_codes, args.warnings, args.debug, args.sleep_multiplier, detect_vdu_hook)
    main_window.show()
    if splash is not None:
        splash.finish(main_window)

    rc = app.exec_()
    if rc == EXIT_CODE_FOR_RESTART:
        QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
    sys.exit(rc)


FALLBACK_SPLASH_JPEG_BASE64 = b"""
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
"""

if __name__ == '__main__':
    main()
