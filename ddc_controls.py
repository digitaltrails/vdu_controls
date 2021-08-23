#!/usr/bin/python3
"""
#
# ddc_controls.py
# Display Data Channel (DDC) - Virtual Control Panel (VCP)
#
# A GUI for retrieving and altering settings of connected monitors (via
# ddcutil) by issuing DDC commands over HDMI/DVI/USB.
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
#
"""

import sys
import re
import subprocess
import os
import base64
import traceback
import argparse
import signal
#from enum import StrEnum

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, QSplashScreen, QPushButton, QProgressBar
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon
from PyQt5.QtSvg import QSvgWidget

def tr(source_text):
    return QCoreApplication.translate('ddc-control', source_text)

DEFAULT_SPLASH_PNG="/usr/share/icons/oxygen/base/256x256/apps/preferences-desktop-display.png"
FALLBACK_SPLASH_JPEG_BASE64=b"""
/9j/4AAQSkZJRgABAQIARgBGAAD/2wBDAFA3PEY8MlBGQUZaVVBfeMiCeG5uePWvuZHI////////
////////////////////////////////////////////2wBDAVVaWnhpeOuCguv/////////////
////////////////////////////////////////////////////////////wAARCABAAEADASIA
AhEBAxEB/8QAGAAAAwEBAAAAAAAAAAAAAAAAAAIDBAH/xAAsEAACAQIDBgUFAQAAAAAAAAABAgAD
ERJTcQQiM0Gx0SEyUZOiI2GRkuFD/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAEC/8QAGBEBAQEBAQAA
AAAAAAAAAAAAAAEREgL/2gAMAwEAAhEDEQA/AJolIUUZkLM1+do2GjlD94q8Gjqes00z9NdBLIlq
GGjlD3IYKOUPc/s03heMNZsFHKHuf2GGjlD3JpvC8Yms2GjlD94rpSNF2VCrLbneaKhujaTO3Bra
jrFmLLoHBo6nrNCHcXSZwfpUdT1lUO4NJfKVS8Lxbzl5rGT4py8W8Lxg6/kbSQPBrajrLN5G0kDw
q2o6zPpryBwaOp6yindGkkrUzSQM+ErfleNipZvxPeSXFs1S8LxMVLM+J7x0CuLq1xoe811GeXYT
jhUF2aw0PeJjp5vxPeOjk7eQ6SX+VbUdZ3FTzfie8Vmpik4V8Ra3K0zbrUmITqjEwUczachIremy
U1HjvH1MqFwiy2A9BMSbVUUWNmH3lBto50/wYGg0w3m8R95N9kpsPDdPqJM7aOVP8mTfaqjCwso+
0CLLhYr6G05CED//2Q=="""

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


DDCUTIL="/usr/bin/ddcutil"

#class VcpType(StrEnum):
#    CONTINUOUS = 'C'
#    SIMPLE_NON_CONTINUOUS = 'SNC'
#    COMPLEX_NON_CONTINUOUS = 'CNC'

class VcpCapability():
    """
    Virtual Control Panel Command for monitors
    """
    def __init__(self, code, name, icon=None, values={}):
        self.name = name
        self.vcp_code = code
        self.icon = icon
        self.values = values

    def arg_name(self):
        return self.name.replace(' ', '-').lower()

# VCP commands to be made available as Qt sliders
GUI_VCP_COMMANDS = [
    VcpCapability('10', 'Brightness',   icon=BRIGHTNESS_SVG),
    VcpCapability('12', 'Contrast',     icon=CONTRAST_SVG),
    VcpCapability('62', 'Audio volume', icon=VOLUME_SVG),
    ]

class DdcUtil():
    """
    Display Data Channel Utility for interacting with monitors
    """
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug

    def __run__(self, args):
        if self.debug:
            print("DEBUG: subprocess run    - ", args)
        result = subprocess.run(args, stdout=subprocess.PIPE, check=True)
        if self.debug:
            print("DEBUG: subprocess result - ", result)
        return result

    def detect(self):
        display_list = []
        result = self.__run__([DDCUTIL, 'detect', '--terse'])
        model_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for monitor_str in re.split("^Display |\nDisplay", result.stdout.decode('utf-8'))[1:]:
            ddc_id = monitor_str.split('\n')[0].strip()
            model_match = model_pattern.search(monitor_str)
            model = model_match.group(1) if model_match else 'Unknown model'
            display_list.append((ddc_id, model))
        return display_list

    def query_capabilities(self, ddc_id):
        feature_pattern = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\n(Values:\n)?(.*)?', re.DOTALL)
        feature_map = {}
        result = self.__run__([DDCUTIL, '--display', ddc_id, 'capabilities'])
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

    def get_attribute(self, ddc_id, vcp_code):
        result = self.__run__([DDCUTIL, '--brief', '--display', ddc_id, 'getvcp', vcp_code ])
        items = result.stdout.decode('utf-8').split()
        return int(items[3]),int(items[4])

    def set_attribute(self, ddc_id, vcp_code, new_value):
        current, _ = self.get_attribute(ddc_id, vcp_code)
        if new_value != current:
            self.__run__([DDCUTIL, '--display', ddc_id, 'setvcp', vcp_code, str(new_value) ])


class DdcSliderWidget(QWidget):
    """
    Slider widget for DDC continuously variable attributes
    """
    def __init__(self, ddcutil, monitor_id, vcp_command):
        super().__init__()

        self.ddcutil = ddcutil
        self.monitor_id = monitor_id
        self.vcp_command = vcp_command
        self.current, self.maximum = ddcutil.get_attribute(monitor_id, vcp_command.vcp_code)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon = QSvgWidget()
        icon.load(vcp_command.icon)
        icon.setFixedSize(50, 50)
        icon.setToolTip(tr(vcp_command.name))
        layout.addWidget(icon)

        slider = QSlider()
        slider.setMinimumWidth(200)
        slider.setValue(self.current)
        slider.setRange(0, self.maximum)
        slider.setMinimum(0)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setOrientation(Qt.Horizontal)
        # Don't ewrite the ddc value too often - not sure of the implications
        slider.setTracking(False)
        layout.addWidget(slider)
        self.slider = slider

        textinput = QLineEdit()
        textinput.setMaximumWidth(50)
        textinput.setMaxLength(4)
        textvalidator = QIntValidator()
        textvalidator.setRange(0, self.maximum)
        textinput.setValidator(textvalidator)
        textinput.setText(str(slider.value()))
        layout.addWidget(textinput)

        def slider_changed(value):
            self.current = value
            textinput.setText(str(value))
            self.ddcutil.set_attribute(self.monitor_id, self.vcp_command.vcp_code, value)
        slider.valueChanged.connect(slider_changed)

        def slider_moved(value):
            textinput.setText(str(value))
        slider.sliderMoved.connect(slider_moved)

        def text_changed():
            slider.setValue(int(textinput.text()))
        textinput.editingFinished.connect(text_changed)

    def refresh_data(self):
        self.current, _ = self.ddcutil.get_attribute(self.monitor_id, self.vcp_command.vcp_code)

    def refresh_view(self):
        self.slider.setValue(self.current)


class DdcMonitorWidget(QWidget):
    """
    Widget to control one monitor.feature_match
    """
    def __init__(self, ddcutil, monitor_id, monitor_name, hide, warnings):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        #label.setStyleSheet("font-weight: bold");
        label.setText(tr('Monitor {}: {}').format(monitor_id, monitor_name))
        layout.addWidget(label)
        self.capabilities = ddcutil.query_capabilities(monitor_id)
        self.controls = []
        for vcp_command in GUI_VCP_COMMANDS:
            if vcp_command.arg_name() not in hide:
                if vcp_command.vcp_code in self.capabilities:
                    control = DdcSliderWidget(ddcutil, monitor_id, vcp_command)
                    layout.addWidget(control)
                    self.controls.append(control)
                elif warnings:
                    alert = QMessageBox()
                    alert.setText(tr('Monitor {} lacks a VCP control for {}.').format(monitor_name, tr(vcp_command.name)))
                    alert.setInformativeText(tr('No read/write ability for vcp_code {}.').format(vcp_command.vcp_code))
                    alert.setIcon(QMessageBox.Warning)
                    alert.exec()
        if len(self.controls) != 0:
            self.setLayout(layout)

    def refresh_data(self):
        for control in self.controls:
            control.refresh_data()

    def refresh_view(self):
        for control in self.controls:
            control.refresh_view()

    def number_of_controls(self):
        return len(self.controls)


def exception_handler(etype, evalue, etraceback):
    print("ERROR:\n", ''.join(traceback.format_exception(etype, evalue, etraceback)))
    alert = QMessageBox()
    alert.setText(tr('Error: {}').format(''.join(traceback.format_exception_only(etype, evalue))))
    alert.setInformativeText(tr('Details: {}').format(''.join(traceback.format_exception(etype, evalue, etraceback))))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QApplication.quit()

class DdcControlWidget(QWidget):

    def __init__(self, args, splash):
        super().__init__()
        layout = QVBoxLayout()

        ddcutil = DdcUtil(debug=args.debug)
        self.monitor_widgets = []
        for monitor_id, desc in ddcutil.detect():
            splash.showMessage(tr('DDC Control\nDDC ID {}\n{}').format(monitor_id, desc), Qt.AlignVCenter|Qt.AlignHCenter)
            monitor_widget = DdcMonitorWidget(ddcutil, monitor_id, desc, args.hide, args.warnings)
            if monitor_widget.number_of_controls() != 0:
                self.monitor_widgets.append(monitor_widget)
                layout.addWidget(monitor_widget)

        if len(self.monitor_widgets) == 0:
            alert = QMessageBox()
            alert.setText(tr('No controllable monitors found, exiting.'))
            alert.setInformativeText(tr(
                '''Run ddc_control in a console and check for additional messages.\
                Check the requirements for the ddcutil command.'''))
            alert.setIcon(QMessageBox.Critical)
            alert.exec()
            sys.exit()

        self.refreshTask = RefreshTaskThread(self)
        self.refreshTask.taskFinished.connect(self.onFinished)

        self.progressBar = QProgressBar(self)
        self.progressBar.setTextVisible(False)
        self.progressBar.setRange(0,1)
        self.progressBar.setDisabled(True)
        layout.addWidget(self.progressBar, Qt.AlignVCenter|Qt.AlignHCenter)

        self.refresh_button = QPushButton(tr("Refresh settings from monitors"))
        self.refresh_button.clicked.connect(self.onStart)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def onStart(self):
        self.refresh_button.setDisabled(True)
        self.progressBar.setDisabled(False)
        self.progressBar.setRange(0,0)
        self.refreshTask.start()

    def onFinished(self):
        # Stop the pulsation
        self.progressBar.setRange(0,1)
        self.progressBar.setDisabled(True)
        self.refresh_button.setDisabled(False)
        for widget in self.monitor_widgets:
            widget.refresh_view()

class RefreshTaskThread(QThread):

    taskFinished = pyqtSignal()

    def __init__(self, ddc_widget):
        super().__init__()
        self.ddc_widget = ddc_widget

    def run(self):
        for widget in self.ddc_widget.monitor_widgets:
            widget.refresh_data()
        self.taskFinished.emit()



def main():
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(description='Display Data Channel - Virtual Control Panel')
    parser.add_argument('--hide', default=[], action='append', choices=[ vcp.arg_name() for vcp in GUI_VCP_COMMANDS ], help='hide/disable a control')
    # Python 3.9 parser.add_argument('--debug',  action=argparse.BooleanOptionalAction, help='enable debugging')
    parser.add_argument('--debug', default=False, action='store_true', help='enable debugging')
    parser.add_argument('--warnings', default=False, action='store_true', help='enable missing feature warnings')
    args = parser.parse_args()

    sys.excepthook = exception_handler

    app = QApplication(sys.argv)

    pixmap = QPixmap()
    if os.path.isfile(DEFAULT_SPLASH_PNG) and os.access(DEFAULT_SPLASH_PNG, os.R_OK):
        pixmap.load(DEFAULT_SPLASH_PNG)
    else:
        pixmap.loadFromData(base64.decodebytes(FALLBACK_SPLASH_JPEG_BASE64), 'JPEG')

    splash = QSplashScreen(pixmap.scaledToWidth(800).scaledToHeight(400))

    splash.show()

    app_icon = QIcon()
    app_icon.addPixmap(pixmap)
    app.setWindowIcon(app_icon)
    app.setApplicationDisplayName(tr('DDC Control'))

    splash.showMessage(tr('DDC Control\nLooking for DDC monitors...\n'), Qt.AlignVCenter|Qt.AlignHCenter)
    main_window = DdcControlWidget(args, splash)
    main_window.show()
    splash.finish(main_window)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
