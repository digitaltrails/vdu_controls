import sys
import re
import subprocess

from PyQt5.QtWidgets import QApplication, QWidget,QPushButton, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator

class DdcUtil():

    def detect(self):
        display_list = []
        result = subprocess.run(['ddcutil', 'detect', '--terse'], stdout=subprocess.PIPE)
        result.stdout.decode('utf-8')
        model_pattern = re.compile('Monitor:[ \t]+([^\n]*)')
        for monitor_str in re.split("^Display |\nDisplay", result.stdout.decode('utf-8'))[1:]:
            display_id = monitor_str.split('\n')[0].strip()
            model_match = model_pattern.search(monitor_str)
            model = model_match.group(1) if model_match else 'Unknown model'
            display_list.append((display_id, model))
        return display_list

    def get_brightness(self, display_id):
        result = subprocess.run(['ddcutil', '--brief', '--display', display_id, 'getvcp', '10' ], stdout=subprocess.PIPE)
        items = result.stdout.decode('utf-8').split()
        return int(items[1]),int(items[4]),int(items[3])

    def set_brightness(self, display_id, new_value):
        low, high, current = self.get_brightness(display_id)
        if new_value != current:
            result = subprocess.run(['ddcutil', '--display', display_id, 'setvcp', '10', str(new_value) ], stdout=subprocess.PIPE)



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

    w = QWidget()
    #w.resize(250, 150)
    #w.move(300, 300)
    w.setWindowTitle('Simple')

    layout = QVBoxLayout()

    ddcutil = DdcUtil()

    for mid, desc in ddcutil.detect():
        print(mid + " " + desc)
        print(ddcutil.get_brightness(mid))
        minv, maxv, current = ddcutil.get_brightness(mid)
        layout.addWidget(DdcMonitorWidget(mid, desc, minv, maxv, current))

    #layout.addWidget(DdcMonitorWidget('LG 4K', 10, 90))
    #layout.addWidget(DdcMonitorWidget('HP ZR24w', 10, 90))

    layout.addWidget(QPushButton('Dismiss'))
    w.setLayout(layout)
    w.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
