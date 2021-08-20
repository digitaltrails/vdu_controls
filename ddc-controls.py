import sys
import re
import subprocess

from PyQt5.QtWidgets import QApplication, QWidget,QPushButton, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QPixmap

class DdcUtil():

    def detect(self):
        display_list = []
        result = subprocess.run(['ddcutil', 'detect', '--terse'], stdout=subprocess.PIPE)
        model_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for monitor_str in re.split("^Display |\nDisplay", result.stdout.decode('utf-8'))[1:]:
            ddc_id = monitor_str.split('\n')[0].strip()
            model_match = model_pattern.search(monitor_str)
            model = model_match.group(1) if model_match else 'Unknown model'
            display_list.append((ddc_id, model))


        return display_list

    def is_brightness_controllable(self, ddc_id):
        result = subprocess.run(
            ['ddcutil', '--display', ddc_id, 'vcpinfo', '10' ],
            stdout=subprocess.PIPE)
        attribute_pattern = re.compile("Attributes: Read Write, Continuous")
        return attribute_pattern.search(result.stdout.decode('utf-8')) != None

    def get_brightness(self, ddc_id):
        result = subprocess.run(['ddcutil', '--brief', '--display', ddc_id, 'getvcp', '10' ], stdout=subprocess.PIPE)
        items = result.stdout.decode('utf-8').split()
        return int(items[1]),int(items[4]),int(items[3])

    def set_brightness(self, ddc_id, new_value):
        low, high, current = self.get_brightness(ddc_id)
        if new_value != current:
            result = subprocess.run(['ddcutil', '--display', ddc_id, 'setvcp', '10', str(new_value) ], stdout=subprocess.PIPE)



class DdcSliderWidget(QWidget):

    def __init__(self, monitor_id, low, high, current):
        super().__init__()

        self.monitor_id = monitor_id
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
            v = slider.value()
            textinput.setText(str(value))
            ddcutil = DdcUtil()
            ddcutil.set_brightness(self.monitor_id, value)
            #alert = QMessageBox()
            #alert.setText('value=' + str(v))
            #alert.exec()

        slider.valueChanged.connect(slider_changed)


        def slider_moved(value):
            v = slider.value()
            textinput.setText(str(value))

        slider.sliderMoved.connect(slider_moved)


        def text_changed():
            slider.setValue(90 if textinput.text() == '' else int(textinput.text()))

        textinput.editingFinished.connect(text_changed)

        layout.addWidget(slider)
        layout.addWidget(textinput)
        self.setLayout(layout)

class DdcMonitorWidget(QWidget):

    def __init__(self, monitor_id, monitor_name, low_brightness, high_brightness, current_brightness):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        label.setText('DDC ' + monitor_id + ":" + monitor_name)
        layout.addWidget(label)
        layout.addWidget(DdcSliderWidget(monitor_id, low_brightness, high_brightness, current_brightness))
        self.setLayout(layout)


def main():


    app = QApplication(sys.argv)

    pixmap = QPixmap("/usr/share/icons/oxygen/base/256x256/apps/preferences-desktop-display-color.png");
    splash = QSplashScreen(pixmap.scaledToWidth(800).scaledToHeight(400))
    #splash.resize(800,400)
    splash.show()

    main_window = QWidget()
    main_window.setWindowTitle('Simple')

    layout = QVBoxLayout()

    splash.showMessage('DDC-Controls\nLooking for DDC monitors...', Qt.AlignVCenter|Qt.AlignHCenter)

    ddcutil = DdcUtil()
    for ddc_id, desc in ddcutil.detect():
        splash.showMessage('DDC ID ' + ddc_id + '\n' + desc, Qt.AlignVCenter|Qt.AlignHCenter)
        print(ddc_id + " " + desc)
        print(ddcutil.get_brightness(ddc_id))
        if ddcutil.is_brightness_controllable(ddc_id):
            minv, maxv, current = ddcutil.get_brightness(ddc_id)
            layout.addWidget(DdcMonitorWidget(ddc_id, desc, minv, maxv, current))
        else:
            alert = QMessageBox()
            #alert.setDetailedText('Ddcutil reports no vcp brightness read/write attribute for this monitor.')
            alert.setText('Ignoring monitor with DDC ID ' + ddc_id)
            alert.setInformativeText('Command line ddcutil vcpinfo reports no brightness read/write ability (attribute 10) for '  + desc)
            alert.setIcon(QMessageBox.Warning)
            alert.exec()

    #layout.addWidget(QPushButton('Dismiss'))
    main_window.setLayout(layout)
    main_window.show()
    splash.finish(main_window)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
