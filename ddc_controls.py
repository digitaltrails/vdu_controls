#!/usr/bin/python3
"""
#
# ddc_controls.py
# Display Data Channel (DDC) - Virtual Control Panel (VCP)
#
# A GUI for retrieving and altering settings of connected VDU's (via
# ddcutil) by issuing DDC commands over HDMI/DVI/USB.  This code
# refers sometimes refers to displays and monitors as VDU's in order
# to disambiguate the noun/verb duality of "display" and "monitor"
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
# m i c h a e l @ a c t r i x . g e n . n z
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
import signal
from typing import List, Tuple, Mapping

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar
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


# class VcpType(StrEnum):
#    CONTINUOUS = 'C'
#    SIMPLE_NON_CONTINUOUS = 'SNC'
#    COMPLEX_NON_CONTINUOUS = 'CNC'


class VcpCapability:
    """ Representation of a VCP (Virtual Control Panel) capability for a VDU. """
    def __init__(self, vcp_code: str, name: str, icon_source: bytes = None, values: List[str] = None):
        self.vcp_code = vcp_code
        self.name = name
        self.icon_source = icon_source
        # For future use if we want to implement non-continuous types of VCP (VCP types SNC or CNC)
        self.values = [] if values is None else values

    def arg_name(self) -> str:
        return self.name.replace(' ', '-').lower()


# VCP capabilities to be made available as Qt sliders.
# Any continuous (VCP type C) value can be supported.
SUPPORTED_VCP_CAPABILITIES = [
    VcpCapability('10', 'Brightness', icon_source=BRIGHTNESS_SVG),
    VcpCapability('12', 'Contrast', icon_source=CONTRAST_SVG),
    VcpCapability('62', 'Audio volume', icon_source=VOLUME_SVG),
]


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

    def detect_monitors(self) -> List[Tuple[str, str]]:
        """ Returns a list of (vdu_id, desc) tuples """
        display_list = []
        result = self.__run__('detect', '--terse')
        model_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for display_str in re.split("^Display |\nDisplay", result.stdout.decode('utf-8'))[1:]:
            ddc_id = display_str.split('\n')[0].strip()
            model_match = model_pattern.search(display_str)
            model_name = model_match.group(1) if model_match else 'Unknown model'
            display_list.append((ddc_id, model_name))
        return display_list

    def query_capabilities(self, ddc_id: str) -> Mapping[str, VcpCapability]:
        """Returns a map of vpc capabilities keyed by vcp code."""
        feature_pattern = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\n(Values:\n)?(.*)?', re.DOTALL)
        feature_map: Mapping[str, VcpCapability] = {}
        result = self.__run__('--display', ddc_id, 'capabilities')
        for feature_text in result.stdout.decode('utf-8').split(' Feature: '):
            feature_match = feature_pattern.match(feature_text)
            if feature_match:
                feature_id = feature_match.group(1)
                feature_name = feature_match.group(2)
                current_feature = VcpCapability(feature_id, feature_name)
                feature_map[feature_id] = current_feature
        if self.debug:
            print("DEBUG: capabilities", feature_map.keys())
        return feature_map

    def get_attribute(self, ddc_id: str, vcp_code: str) -> Tuple[int, int]:
        """ Given a VDU id and vcp_code, returns the attributes current and maximum value. """
        value_pattern = re.compile(r'VCP ' + vcp_code + r' [A-Z]+ ([0-9]+) ([0-9]+)\n')
        # Try a few times in case there is a glitch due to a monitor being turned off/on
        for i in range(3):
            result = self.__run__('--brief', '--display', ddc_id, 'getvcp', vcp_code)
            value_match = value_pattern.match(result.stdout.decode('utf-8'))
            if value_match is None:
                if self.debug:
                    print("DEBUG: get_attribute returned garbage, will try two more times.")
                time.sleep(2)
                continue
            else:
                return int(value_match.group(1)), int(value_match.group(2))
        return 0, 0

    def set_attribute(self, ddc_id: str, vcp_code: str, new_value: str):
        current, _ = self.get_attribute(ddc_id, vcp_code)
        if new_value != current:
            self.__run__('--display', ddc_id, 'setvcp', vcp_code, str(new_value))


class DdcSliderWidget(QWidget):
    """ GUI control for a DDC continuously variable attribute. Compound widget with icon, slider and text field."""
    def __init__(self, ddcutil: DdcUtil, monitor_id: str, vcp_capability: VcpCapability):
        super().__init__()

        self.ddcutil = ddcutil
        self.monitor_id = monitor_id
        self.vcp_capability = vcp_capability
        self.current_value, self.max_value = self.ddcutil.get_attribute(self.monitor_id, self.vcp_capability.vcp_code)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon = QSvgWidget()
        icon.load(vcp_capability.icon_source)
        icon.setFixedSize(50, 50)
        icon.setToolTip(translate(vcp_capability.name))
        layout.addWidget(icon)

        self.slider = slider = QSlider()
        slider.setMinimumWidth(200)
        slider.setValue(self.current_value)
        slider.setRange(0, self.max_value)
        slider.setMinimum(0)
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
        text_validator.setRange(0, self.max_value)
        text_input.setValidator(text_validator)
        text_input.setText(str(slider.value()))
        layout.addWidget(text_input)

        def slider_changed(value):
            self.current_value = value
            text_input.setText(str(value))
            self.ddcutil.set_attribute(self.monitor_id, self.vcp_capability.vcp_code, value)

        slider.valueChanged.connect(slider_changed)

        def slider_moved(value):
            text_input.setText(str(value))

        slider.sliderMoved.connect(slider_moved)

        def text_changed():
            slider.setValue(int(text_input.text()))

        text_input.editingFinished.connect(text_changed)

    def refresh_data(self):
        """Query the VDU for a new data value and cache it (may be called from a task thread, so no GUI op's here.)"""
        self.current_value, _ = self.ddcutil.get_attribute(self.monitor_id, self.vcp_capability.vcp_code)

    def refresh_view(self):
        """Copy the internally cached current value onto the GUI view."""
        self.slider.setValue(self.current_value)


class DdcVduWidget(QWidget):
    """ Widget that contains all the controls for a single VDU (monitor/display) """
    def __init__(self, ddcutil: DdcUtil, vdu_id: str, vdu_desc: str, enabled_capabilities: List[VcpCapability],
                 warnings: bool):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        # label.setStyleSheet("font-weight: bold");
        label.setText(translate('Monitor {}: {}').format(vdu_id, vdu_desc))
        layout.addWidget(label)
        self.vdu_id = vdu_id
        self.vdu_desc = vdu_desc
        self.capabilities = ddcutil.query_capabilities(vdu_id)
        self.vcp_controls = []
        for capability in enabled_capabilities:
            if capability.vcp_code in self.capabilities:
                control = DdcSliderWidget(ddcutil, vdu_id, capability)
                layout.addWidget(control)
                self.vcp_controls.append(control)
            elif warnings:
                alert = QMessageBox()
                alert.setText(
                    translate('Monitor {} lacks a VCP control for {}.').format(vdu_desc, translate(capability.name)))
                alert.setInformativeText(
                    translate('No read/write ability for vcp_code {}.').format(capability.vcp_code))
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
    def __init__(self, enabled_capabilities: List[VcpCapability], warnings: bool, debug: bool, sleep_multiplier: float,
                 detect_vdu_hook: callable):
        super().__init__()
        layout = QVBoxLayout()
        self.ddcutil = DdcUtil(debug=debug, common_args=['--sleep-multiplier', str(sleep_multiplier)])
        self.vdu_widgets = []
        self.enabled_capabilities = enabled_capabilities
        self.warnings = warnings
        self.detected_vdus = self.ddcutil.detect_monitors()
        for vdu_id, desc in self.detected_vdus:
            if detect_vdu_hook is not None:
                detect_vdu_hook(vdu_id, desc)
            vdu_widget = DdcVduWidget(self.ddcutil, vdu_id, desc, enabled_capabilities, warnings)
            if vdu_widget.number_of_controls() != 0:
                self.vdu_widgets.append(vdu_widget)
                layout.addWidget(vdu_widget)
            elif warnings:
                alert = QMessageBox()
                alert.setText(translate('Monitor {} {} lacks any accessible controls.').format(vdu_id, desc))
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
            if (vdu_widget.vdu_id, vdu_widget.vdu_desc) in self.detected_vdus:
                vdu_widget.refresh_data()

    def refresh_view(self):
        """Callback when the GUI worker thread completes, the GUI thread and can refresh the GUI views."""
        to_do = self.detected_vdus.copy()
        for vdu_widget in self.vdu_widgets:
            if (vdu_widget.vdu_id, vdu_widget.vdu_desc) in to_do:
                vdu_widget.refresh_view()
                to_do.remove((vdu_widget.vdu_id, vdu_widget.vdu_desc))
        if len(to_do) > 0:
            alert = QMessageBox()
            alert.setText(translate('The physical monitor configuration has changed. A restart is required.'))
            alert.setInformativeText(translate('Dismiss this message to automatically restart.'))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()
            QCoreApplication.exit(EXIT_CODE_FOR_RESTART)


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

    parser = argparse.ArgumentParser(description='Display Data Channel - Virtual Control Panel')
    parser.add_argument('--show',
                        default=[],
                        action='append', choices=[vcp.arg_name() for vcp in SUPPORTED_VCP_CAPABILITIES],
                        help='show specified control only  (defaults is all of them), may be specified multiple times')
    parser.add_argument('--hide', default=[], action='append',
                        choices=[vcp.arg_name() for vcp in SUPPORTED_VCP_CAPABILITIES],
                        help='hide/disable a control (selective exclusion), may be specified multiple times')
    # Python 3.9 parser.add_argument('--debug',  action=argparse.BooleanOptionalAction, help='enable debugging')
    parser.add_argument('--debug', default=False, action='store_true', help='enable debugging')
    parser.add_argument('--warnings', default=False, action='store_true', help='enable missing feature warnings')
    parser.add_argument('--no-splash', default=False, action='store_true', help="don't show the splash screen")
    parser.add_argument('--sleep-multiplier', type=float, default="0.5", help='ddcutil sleep multiplier (>0.0)')

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
    app.setApplicationDisplayName(translate('DDC Control'))

    if len(args.show) != 0:
        enabled_capabilities = [c for c in SUPPORTED_VCP_CAPABILITIES if c.arg_name() in args.show]
    else:
        enabled_capabilities = [c for c in SUPPORTED_VCP_CAPABILITIES if c.arg_name() not in args.hide]

    if splash is not None:
        splash.showMessage(translate('\n\nDDC Control\nLooking for DDC monitors...\n'), Qt.AlignTop | Qt.AlignHCenter)

    def detect_vdu_hook(vdu_id, desc):
        if splash is not None:
            splash.showMessage(translate('\n\nDDC Control\nDDC ID {}\n{}').format(vdu_id, desc),
                               Qt.AlignTop | Qt.AlignHCenter)

    main_window = DdcMainWidget(enabled_capabilities, args.warnings, args.debug, args.sleep_multiplier, detect_vdu_hook)
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
