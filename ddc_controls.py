#!/usr/bin/python3
#
# ddc_controls.py
#
# Copyright (C) 2021 Michael Hamilton michael@actrix.gen.nz
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
#

# Prerequisites - OpenSUSE (similar for other distros)
#
# Software:
#    zypper install python38-QtPy
#    zypper install ddcutil
#
# Kernel Modules:
#    lsmod | grep i2c_dev
#
# Read ddcutil readme concerning config of i2c_dev with nvidia GPU's.
#

import sys
import re
import subprocess
import os
import base64
import traceback

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, QSplashScreen
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon

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


class DdcUtil():

    def __init__(self, debug=False):
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
        result = self.__run__(['ddcutil', 'detect', '--terse'])
        model_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for monitor_str in re.split("^Display |\nDisplay", result.stdout.decode('utf-8'))[1:]:
            ddc_id = monitor_str.split('\n')[0].strip()
            model_match = model_pattern.search(monitor_str)
            model = model_match.group(1) if model_match else 'Unknown model'
            display_list.append((ddc_id, model))
        return display_list

    def is_brightness_controllable(self, ddc_id):
        result = self.__run__(['ddcutil', '--display', ddc_id, 'vcpinfo', '10' ])
        attribute_pattern = re.compile("Attributes: Read Write, Continuous")
        return attribute_pattern.search(result.stdout.decode('utf-8')) is not None

    def get_brightness(self, ddc_id):
        result = self.__run__(['ddcutil', '--brief', '--display', ddc_id, 'getvcp', '10' ])
        items = result.stdout.decode('utf-8').split()
        return int(items[1]),int(items[4]),int(items[3])

    def set_brightness(self, ddc_id, new_value):
        _, _, current = self.get_brightness(ddc_id)
        if new_value != current:
            self.__run__(['ddcutil', '--display', ddc_id, 'setvcp', '10', str(new_value) ])


class DdcSliderWidget(QWidget):

    def __init__(self, ddcutil, monitor_id):
        super().__init__()

        self.ddcutil = ddcutil
        self.monitor_id = monitor_id
        low, high, current = ddcutil.get_brightness(monitor_id)

        layout = QHBoxLayout()

        slider = QSlider()
        textinput = QLineEdit()

        slider.setMinimumWidth(200)
        slider.setValue(current)
        slider.setRange(low, high)
        slider.setMinimum(low)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setOrientation(Qt.Horizontal)
        #slider.setToolTip(str(slider.value()))
        textinput.setText(str(slider.value()))
        # Don't want to rewrite the ddc value too often - not sure of the implications
        slider.setTracking(False)

        textinput.setMaximumWidth(50)
        textinput.setMaxLength(4)
        textvalidator = QIntValidator()
        textvalidator.setRange(low,high)
        textinput.setValidator(textvalidator)

        def slider_changed(value):
            textinput.setText(str(value))
            self.ddcutil.set_brightness(self.monitor_id, value)

        slider.valueChanged.connect(slider_changed)

        def slider_moved(value):
            textinput.setText(str(value))

        slider.sliderMoved.connect(slider_moved)

        def text_changed():
            slider.setValue(90 if textinput.text() == '' else int(textinput.text()))

        textinput.editingFinished.connect(text_changed)

        layout.addWidget(slider)
        layout.addWidget(textinput)
        self.setLayout(layout)

class DdcMonitorWidget(QWidget):

    def __init__(self, ddcutil, monitor_id, monitor_name):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        label.setText(tr('Monitor {}: {}').format(monitor_id, monitor_name))
        layout.addWidget(label)
        layout.addWidget(DdcSliderWidget(ddcutil, monitor_id))
        self.setLayout(layout)

def exception_handler(etype, evalue, etraceback):
    print("ERROR:\n", ''.join(traceback.format_exception(etype, evalue, etraceback)))
    alert = QMessageBox()
    alert.setText(tr('Error: {}').format(''.join(traceback.format_exception_only(etype, evalue))))
    alert.setInformativeText(tr('Details: {}').format(''.join(traceback.format_exception(etype, evalue, etraceback))))
    alert.setIcon(QMessageBox.Critical)
    alert.exec()
    QApplication.quit()

def main():

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

    main_window = QWidget()

    layout = QVBoxLayout()

    splash.showMessage(tr('DDC Control\nLooking for DDC monitors...\n'), Qt.AlignVCenter|Qt.AlignHCenter)

    ddcutil = DdcUtil(debug=True)
    number_found = 0
    for ddc_id, desc in ddcutil.detect():
        splash.showMessage(tr('DDC Control\nDDC ID {}\n{}').format(ddc_id, desc), Qt.AlignVCenter|Qt.AlignHCenter)
        print(ddc_id + " " + desc)
        print(ddcutil.get_brightness(ddc_id))
        if ddcutil.is_brightness_controllable(ddc_id):
            layout.addWidget(DdcMonitorWidget(ddcutil, ddc_id, desc))
            number_found += 1
        else:
            alert = QMessageBox()
            #alert.setDetailedText('Ddcutil reports no vcp brightness read/write attribute for this monitor.')
            alert.setText(tr('Ignoring monitor with DDC ID {}').format(ddc_id))
            alert.setInformativeText(tr('No brightness read/write ability (attribute 10) for {}').format(desc))
            alert.setIcon(QMessageBox.Warning)
            alert.exec()

    if number_found == 0:
        alert = QMessageBox()
        #alert.setDetailedText('Ddcutil reports no vcp brightness read/write attribute for this monitor.')
        alert.setText(tr('No controllable monitors found, exiting.'))
        alert.setInformativeText(tr('Run ddc_control in a console and check for additional messages. Check the requirements for the ddcutil command.'))
        alert.setIcon(QMessageBox.Critical)
        alert.exec()
        sys.exit()

    #layout.addWidget(QPushButton('Dismiss'))
    main_window.setLayout(layout)
    main_window.show()
    splash.finish(main_window)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
