"""
GNU License
===========

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/.
"""
# vdu_lux_chart Copyright (C) 2021 Michael Hamilton
import math
import sys

from PyQt5.QtGui import QGuiApplication, QPixmap, QPainter, QPen, QColor, QMouseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel


class VduLuxChart(QLabel):

    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.data = []
        self.plot_height = 600
        self.plot_width = 600
        self.y_origin = self.plot_height + 50
        self.x_origin = 120
        self.setFixedHeight(self.plot_height + 150)
        self.setFixedWidth(self.plot_width + 200)
        self.create_plot()

    def create_plot(self):
        width, height = self.width(), self.height()
        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, width, height, QColor(0x5b93c5))
        painter.setPen(QPen(QColor(0xffffff), 4))
        painter.drawText(width//4, 30, "Click plot to draw brightness/lux response curve.")

        # Draw x-axis
        painter.drawLine(self.x_origin, self.y_origin, self.x_origin + self.plot_width, self.y_origin)
        for lux in [0, 10, 100, 1_000, 10_000, 100_000]:  # Draw x-axis ticks
            x = self.x_from_lux(lux)
            painter.drawLine(self.x_origin + x, self.y_origin + 5, self.x_origin + x, self.y_origin - 5)
            painter.drawText(self.x_origin + x - 8 * len(str(lux)), self.y_origin + 35, str(lux))
        painter.drawText(self.x_origin + self.plot_width // 2 - len(str("Lux")), self.y_origin + 65, str("Lux"))

        # Draw y-axis
        painter.drawLine(self.x_origin, self.y_origin, self.x_origin, self.y_origin - self.plot_height)
        for percent in range(0, 101, 10):  # Draw y-axis ticks
            y = self.y_from_percent(percent)
            painter.drawLine(self.x_origin - 5, self.y_origin - y, self.x_origin + 5, self.y_origin - y)
            painter.drawText(self.x_origin - 50, self.y_origin - y + 5, str(percent))
        painter.save()
        painter.translate(self.x_origin - 70, self.y_origin - self.plot_height // 2 + 6 * len("Brightness %"))
        painter.rotate(-90)
        painter.drawText(0, 0, "Brightness %")
        painter.restore()
        painter.setPen(QPen(QColor(0xff965b), 6))

        # for vdu in vdu_list:  # draw curve per vdu
        last_x = 0
        last_y = 0
        for lux, percent in self.data:
            x = self.x_origin + self.x_from_lux(lux)
            y = self.y_origin - self.y_from_percent(percent)
            painter.drawEllipse(x - 10, y - 10, 20, 20)
            if last_x and last_y:
                painter.drawLine(last_x, last_y, x, y)
            last_x = x
            last_y = y

        painter.end()
        self.setPixmap(pixmap)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        local_pos = self.mapFromGlobal(event.globalPos())
        x = local_pos.x() - self.x_origin
        y = self.y_origin - local_pos.y()
        percent = self.percent_from_y(y)
        lux = self.lux_from_x(x)
        if percent < 0 or lux < 0 or percent > 100 or lux > 100000:
            return
        print(f"percent={percent}, lux={lux}")
        deleted = False
        for existing_lux, existing_percent in self.data:
            existing_x = self.x_from_lux(existing_lux)
            existing_y = self.y_from_percent(existing_percent)
            if existing_x - 10 <= x <= existing_x + 10 and existing_y - 10 <= y <= existing_y + 10:
                self.data.remove((existing_lux, existing_percent))
                deleted = True
        if not deleted:
            self.data.append((lux, percent))
            self.data.sort()
        self.create_plot()
        self.update()
        event.ignore()

    def percent_from_y(self, y):
        return round(100.0 * abs(y) / self.plot_height)

    def y_from_percent(self, percent):
        return round(self.plot_height * percent / 100)

    def lux_from_x(self, x):
        return round(10.0 ** (math.log10(1) + (x / self.plot_width) * (math.log10(100000) - math.log10(1))))

    def x_from_lux(self, lux: int) -> int:
        return round((math.log10(lux) - math.log10(1)) / ((math.log10(100000) - math.log10(1)) / self.plot_width)) if lux > 0 else 0


class ChartWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.tray = None
        self.app_name = "VDU Lux Chart"
        app.setApplicationDisplayName(self.app_name)
        self.chart_panel = QWidget()
        self.chart_panel.setLayout(QHBoxLayout())
        self.chart_panel.layout().addWidget(VduLuxChart())
        self.chart_panel.setMinimumWidth(900)
        self.chart_panel.setMinimumHeight(900)
        self.setCentralWidget(self.chart_panel)


def main():
    app = QApplication(sys.argv)

    # Wayland needs this set in order to find/use the app's desktop icon.
    QGuiApplication.setDesktopFileName("vdu_lux_chart")

    main_window = ChartWindow(app)
    main_window.show()
    rc = app.exec_()

    sys.exit(rc)


if __name__ == '__main__':
    main()