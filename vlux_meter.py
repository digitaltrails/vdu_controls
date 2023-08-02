#!/usr/bin/python3
"""
vlux_meter.py - guess lux value based on a webcam image
=======================================================

WORK IN PROGRESS

The appropriate manual exposure option (if there is one) can be 
discovered by running

   v4l2-ctl -d /dev/video0 --list-ctrls-menus 

Copyright (C) 2023 Michael Hamilton

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
import configparser
import io
import locale
import math
import os
import pathlib
import signal
import socket
import sys
import syslog
import threading
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import List, Tuple, Mapping, Callable, Dict

import cv2  # type: ignore
from PyQt5 import QtNetwork
from PyQt5.QtCore import QSettings, pyqtSignal, QThread, QCoreApplication, QTranslator, QLocale, QPoint, QSize, QEvent, Qt, QObject
from PyQt5.QtGui import QGuiApplication, QPixmap, QIcon, QCursor, QImage, QPainter, QPalette, QResizeEvent, QMouseEvent, QPen, \
    QColor, QIntValidator
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QStyle, QWidget, QLabel, QVBoxLayout, QToolButton, \
    QStatusBar, QHBoxLayout, QSlider, QGridLayout, QLineEdit, QSpinBox, QPushButton, QFileDialog, QCheckBox, QComboBox

APPNAME = "Vlux Meter"
VLUX_METER_VERSION = '1.0.0'

IMAGE_LOCATION = Path('/tmp').joinpath('lux-from-webcam.jpg').as_posix()
SAVE_IMAGE = False

#: A high resolution image, will fall back to an internal SVG if this file isn't found on the local system
DEFAULT_SPLASH_PNG = "/usr/share/icons/hicolor/256x256/apps/vlux_meter.png"

# On Plasma Wayland the system tray may not be immediately available at login - so keep trying for...
SYSTEM_TRAY_WAIT_SECONDS = 20

SVG_LIGHT_THEME_COLOR = b"#232629"
SVG_DARK_THEME_COLOR = b"#f3f3f3"

MENU_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <defs id="defs3051">
    <style type="text/css" id="current-color-scheme">
      .ColorScheme-Text {
        color:#232629;
      }
      </style>
  </defs>
  <g transform="translate(1,1)">
    <path style="fill:currentColor;fill-opacity:1;stroke:none" d="m3 5v2h16v-2h-16m0 5v2h16v-2h-16m0 5v2h16v-2h-16" class="ColorScheme-Text"/>
  </g>
</svg>
"""

# Icon copyright libraoffice (Mozilla license)
VLUX_METER_ICON_SVG = b"""<svg height="22" viewBox="0 0 22 22" width="22" xmlns="http://www.w3.org/2000/svg"><g 
transform="matrix(1 0 0 -1 0 22)"><g fill="#ed8733"><rect height="3" ry=".5" width="1" x="11"/><rect height="4" ry=".5" 
transform="rotate(90)" width="1" x="9" y="-22"/><rect height="4" ry=".5" transform="rotate(90)" width="1" x="9" y="-4"/><path 
d="m11 4a6 6 0 0 0 -6 6 6 6 0 0 0 1.0136719 3.330078l-.0136719-.001953c.038162.051.064392.07662.1015625.125a6 6 0 0 0 
.5996094.732422c.8070529.928391 1.2762984 1.307393 1.2988281 
2.314453-.0007262.143435-.013795.286541-.039063.427734l.039063.072266h6l.03906-.07227c-.025257-.141189-.038334-.284295-.03906
-.42773.02298-1.027161.514082-1.408019 1.351562-2.378906a6 6 0 0 0 .59961-.732422 6 6 0 0 0 
.002-.0039c.01721-.02273.02946-.03336.04687-.05664l-.01172.002a6 6 0 0 0 1.011678-3.330132 6 6 0 0 0 -6-6z"/><rect height="4" 
ry=".5" transform="matrix(.70710678 .70710678 -.70710678 .70710678 0 0)" width="1" x="14.702796" y="-12.060659"/><rect height="4" 
ry=".5" transform="matrix(.70710678 .70710678 -.70710678 .70710678 0 0)" width="1" x="14.702796" y="5.93934"/><rect height="4" 
ry=".5" transform="matrix(-.70710678 .70710678 -.70710678 -.70710678 0 0)" width="1" x="-1.560661" y="-26.202797"/><rect 
height="4" ry=".5" transform="matrix(-.70710678 .70710678 -.70710678 -.70710678 0 0)" width="1" x="-1.560661" 
y="-8.202796"/></g><path d="m11 4.9980469c-1.3093089 0-2.6112882.5390225-3.5371094 1.4648437s-1.4648437 2.2278005-1.4648437 
3.5371094c.00154.980628.3002839 1.960433.8457031 2.775391a.99890838.99890838 0 0 1 
.017578.0293c.013764.01676.00842.0068.033203.03906a.99890838.99890838 0 0 1 
.027344.03906c.1501828.216231.3176799.421408.5.611329a.99890838.99890838 0 0 1 .033203.03516c.3847951.442648.7251044.778877 
1.0253907 1.236328.2167144.330139.2916527.790529.3730468 
1.236328h4.2949225c.08428-.458305.165828-.9309.390624-1.267578.309293-.463228.658781-.804387 1.056641-1.265625a.99890838.99890838 
0 0 1 .03516-.03906c.182321-.189922.349817-.395098.5-.611329a.99890838.99890838 0 0 1 
.02734-.04297c.545201-.815669.843072-1.794296.84375-2.775394 
0-1.3093089-.539022-2.6112882-1.464844-3.5371094-.925821-.9258212-2.2278-1.4648437-3.537109-1.4648437z" fill="#f8db8f"/><path 
d="m8 20.5h6l-.5 1h-5z" fill="#3a3a38"/><path d="m8 17v3h6v-3zm1 1h4v1h-4z" fill="#3a3a38"/></g></svg>"""

signal_wakeup_handler: Callable[[int], None] | None = None


def brightness_lux_str(brightness: int, lux: int) -> str:
    return f"{brightness} {lux}"


# Customise these values to your desktop and webcam
# Logitech, Inc. Webcam C270 settings for my study
DEFAULT_SETTINGS = {
    'camera': {
        'device': '/dev/video0',
        'manual_exposure_option': 1,
        'manual_exposure_time': 64,
        'auto_exposure_option': 3,
        'crop': '0.0,0.0,100.0,100.0'
    },
    'brightness_to_lux': {
        'Sunlight': brightness_lux_str(250, 100000),
        'Daylight': brightness_lux_str(160, 10000),
        'Overcast': brightness_lux_str(110, 1000),
        'Rise/set': brightness_lux_str(50, 400),
        'Dusk': brightness_lux_str(20, 100),
        'Room': brightness_lux_str(5, 50),
        'Night': brightness_lux_str(0, 5),
    },
    'global': {
        'system_tray_enabled': 'yes',
        'fifo_path': '~/.cache/vlux_fifo',
        'display_frequency_millis': 1000,
        'dispatch_frequency_seconds': 60,
        'translations_enabled': 'no',
    },

}

CONFIG_DIR_PATH = Path.home().joinpath('.config', 'vlux_meter')
CONFIG_PATH = CONFIG_DIR_PATH.joinpath('vlux_meter.conf')
LOCALE_TRANSLATIONS_PATHS = [
    Path.cwd().joinpath('translations')] if os.getenv('VDU_CONTROLS_DEVELOPER', default="no") == 'yes' else [] + [
    Path(CONFIG_DIR_PATH).joinpath('translations'),
    Path("/usr/share/vlux_meter/translations"), ]

LOG_SYSLOG_CAT = {syslog.LOG_INFO: "INFO:", syslog.LOG_ERR: "ERROR:",
                  syslog.LOG_WARNING: "WARNING:", syslog.LOG_DEBUG: "DEBUG:"}
log_to_syslog = False
log_debug_enabled = False

translator: QTranslator | None = None
ts_translations: Dict[str, str] = {}


def log_wrapper(severity, *args) -> None:
    with io.StringIO() as output:
        print(*args, file=output, end='')
        message = output.getvalue()
        prefix = LOG_SYSLOG_CAT[severity]
        if log_to_syslog:
            syslog_message = prefix + " " + message if severity == syslog.LOG_DEBUG else message
            syslog.syslog(severity, syslog_message)
        else:
            print(datetime.now().strftime("%H:%M:%S"), prefix, message)


def log_debug(*args) -> None:
    if log_debug_enabled:
        log_wrapper(syslog.LOG_DEBUG, *args)


def log_info(*args) -> None:
    log_wrapper(syslog.LOG_INFO, *args)


def log_warning(*args) -> None:
    log_wrapper(syslog.LOG_WARNING, *args)


def log_error(*args) -> None:
    log_wrapper(syslog.LOG_ERR, *args)


def zoned_now() -> datetime:
    return datetime.now().astimezone()


def args_from_config():
    pass


def tr(source_text: str, disambiguation: str | None = None) -> str:
    # If the source .ts file is newer, we load messages from the XML into ts_translations
    # and use the most recent translations. Using the .ts files in production may be a good
    # way to allow the users to help themselves.
    if ts_translations:
        if source_text in ts_translations:
            return ts_translations[source_text]
    # the context @default is what is generated by pylupdate5 by default
    return QCoreApplication.translate('@default', source_text, disambiguation=disambiguation)


def is_running_in_gui_thread() -> bool:
    return QThread.currentThread() == gui_thread


def get_splash_image() -> QPixmap:
    """Get the splash pixmap from the installed png, failing that, the internal splash png."""

    if os.path.isfile(DEFAULT_SPLASH_PNG) and os.access(DEFAULT_SPLASH_PNG, os.R_OK):
        pixmap = QPixmap()
        pixmap.load(DEFAULT_SPLASH_PNG)
    else:
        pixmap = create_themed_pixmap_from_svg_bytes(VLUX_METER_ICON_SVG)
    return pixmap


def si(widget: QWidget, icon_number: QStyle.StandardPixmap) -> QIcon:
    return widget.style().standardIcon(icon_number)


def is_dark_theme() -> bool:
    # Heuristic for checking for a dark theme.
    # Is the sample text lighter than the background?
    label = QLabel("am I in the dark?")
    text_hsv_value = label.palette().color(QPalette.WindowText).value()
    bg_hsv_value = label.palette().color(QPalette.Background).value()
    dark_theme_found = text_hsv_value > bg_hsv_value
    # debug(f"is_dark_them text={text_hsv_value} bg={bg_hsv_value} is_dark={dark_theme_found}") if debugging else None
    return dark_theme_found


def handle_theme(svg_str: bytes) -> bytes:
    if is_dark_theme():
        svg_str = svg_str.replace(SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR)
    return svg_str


def create_themed_pixmap_from_svg_bytes(svg_bytes: bytes) -> QPixmap:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    image = create_themed_image_from_svg_bytes(svg_bytes)
    return QPixmap.fromImage(image)


def create_themed_image_from_svg_bytes(svg_bytes) -> QImage:
    renderer = QSvgRenderer(handle_theme(svg_bytes))
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def create_themed_icon_from_svg_bytes(svg_bytes: bytes) -> QIcon:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    return QIcon(create_themed_pixmap_from_svg_bytes(svg_bytes))


def find_locale_specific_file(filename_template: str) -> Path | None:
    locale_name = QLocale.system().name()
    filename = filename_template.format(locale_name)
    for path in LOCALE_TRANSLATIONS_PATHS:
        full_path = path.joinpath(filename)
        log_debug(f"Checking for {locale_name} translation: {full_path}") if log_debug_enabled else None
        if full_path.exists():
            log_info(f"Found {locale_name} translation: {full_path}")
            return full_path
    return None


def initialise_locale_translations(app: QApplication) -> None:
    # Has to be put somewhere it won't be garbage collected when this function goes out of scope.
    global translator
    translator = QTranslator()
    log_info("Qt locale", QLocale.system().name())
    locale_name = QLocale.system().name()
    ts_path = find_locale_specific_file("{}.ts")
    qm_path = find_locale_specific_file("{}.qm")

    # If there is a .ts XML file in the path newer than the associated .qm binary file, load the messages
    # from the XML into a map and use them directly.  This is useful while developing and possibly useful
    # for users that want to do their own localisation.
    if ts_path is not None and (qm_path is None or os.path.getmtime(ts_path) > os.path.getmtime(qm_path)):
        log_info(tr("Using newer .ts file {} translations from {}").format(locale_name, ts_path.as_posix()))
        import xml.etree.ElementTree as XmlElementTree
        global ts_translations
        context = XmlElementTree.parse(ts_path).find('context')
        if context is not None:
            for message in context.findall('message'):
                translation = message.find('translation')
                source = message.find('source')
                if translation is not None and source is not None and translation.text is not None and source.text is not None:
                    ts_translations[source.text] = translation.text
        log_info(tr("Loaded {} translations from {}").format(locale_name, ts_path.as_posix()))
        return

    if qm_path is not None:
        log_info(tr("Loading {} translations from {}").format(locale_name, qm_path.as_posix()))
        if translator.load(qm_path.name, qm_path.parent.as_posix()):
            app.installTranslator(translator)
            log_info(tr("Using {} translations from {}").format(locale_name, qm_path.as_posix()))


class SignalWakeupHandler(QtNetwork.QAbstractSocket):
    # https://stackoverflow.com/a/37229299/609575
    # '''
    # Quoted here: The Qt event loop is implemented in C(++). That means, that while it runs and no Python code is
    # called (e.g. by a Qt signal connected to a Python slot), the signals are noted, but the Python signal handlers
    # aren't called.
    #
    # But, since Python 2.6 and in Python 3 you can cause Qt to run a Python function when a signal with a handler is
    # received using signal.set_wakeup_fd().
    #
    # This is possible, because, contrary to the documentation, the low-level signal handler doesn't only set a flag
    # for the virtual machine, but it may also write a byte into the file descriptor set by set_wakeup_fd(). Python 2
    # writes a NUL byte, Python 3 writes the signal number.
    #
    # So by subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g.
    # QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler) is received
    # causing the signal handler to execute nearly instantaneous without need for timers:
    # '''

    signalReceived = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(QtNetwork.QAbstractSocket.UdpSocket, parent)
        self.old_fd = None
        # Create a socket pair
        self.wsock, self.rsock = socket.socketpair(type=socket.SOCK_DGRAM)
        # Let Qt listen on the one end
        self.setSocketDescriptor(self.rsock.fileno())
        # And let Python write on the other end
        self.wsock.setblocking(False)
        self.old_fd = signal.set_wakeup_fd(self.wsock.fileno())
        # First Python code executed gets any exception from
        # the signal handler, so add a dummy handler first
        self.readyRead.connect(lambda: None)
        # Second handler does the real handling
        self.readyRead.connect(self._readSignal)

    def __del__(self) -> None:
        # Restore any old handler on deletion
        if self.old_fd is not None and signal is not None and signal.set_wakeup_fd is not None:
            signal.set_wakeup_fd(self.old_fd)

    def _readSignal(self) -> None:
        # Read the written byte.
        # Note: readyRead is blocked from occurring again until readData()
        # was called, so call it, even if you don't need the value.
        data = self.readData(1)
        # Emit a Qt signal for convenience
        signal_number = int(data[0])
        log_info("SignalWakeupHandler", signal_number)
        self.signalReceived.emit(signal_number)


class ConfigIni(configparser.ConfigParser):
    """ConfigParser is a little messy and its classname is a bit misleading, wrap it and bend it to our needs."""

    METADATA_SECTION = "metadata"
    METADATA_VERSION_OPTION = "version"
    METADATA_TIMESTAMP_OPTION = "timestamp"

    def __init__(self) -> None:
        super().__init__()
        self.optionxform = partial(str)  # Retain case in property names
        if not self.has_section(ConfigIni.METADATA_SECTION):
            self.add_section(ConfigIni.METADATA_SECTION)
        self.read_dict(DEFAULT_SETTINGS)

    def data_sections(self) -> List:
        """Section other than metadata and DEFAULT - real data."""
        return [s for s in self.sections() if s != configparser.DEFAULTSECT and s != ConfigIni.METADATA_SECTION]

    def get_version(self) -> Tuple:
        if self.has_option(ConfigIni.METADATA_SECTION, ConfigIni.METADATA_VERSION_OPTION):
            version = self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_VERSION_OPTION]
            try:
                return tuple([int(i) for i in version.split('.')])
            except ValueError:
                log_error(f"Illegal version number {version} should be i.j.k where i, j and k are integers.")
        return 1, 0, 0

    def get_brightness_map(self):
        brightness_map: Mapping[int: Tuple[int, str]] = {}
        for name, brightness_lux in self["brightness_to_lux"].items():
            brightness, lux = brightness_lux.split(' ')
            brightness_map[int(brightness)] = name, int(lux)
        sorted_map = {brightness: brightness_map[brightness] for brightness in sorted(brightness_map, reverse=True)}
        return sorted_map

    def set_brightness_map(self, brightness_map: Mapping[int, Tuple[str, int]]):
        sorted_map = {brightness: brightness_map[brightness] for brightness in sorted(brightness_map)}
        for name, brightness, lux in sorted_map:
            self.set("brightness_to_lux", name, brightness_lux_str(brightness, lux))

    def save(self, config_path) -> None:
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        with open(config_path, 'w', encoding="utf-8") as config_file:
            self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_VERSION_OPTION] = VLUX_METER_VERSION
            self[ConfigIni.METADATA_SECTION][ConfigIni.METADATA_TIMESTAMP_OPTION] = str(zoned_now())
            self.write(config_file)
        log_debug(f"Wrote config to {config_path.as_posix()}")


global_config: ConfigIni = ConfigIni()


class ContextMenu(QMenu):

    def __init__(self,
                 main_window,
                 main_window_action,
                 about_action, help_action, chart_action, settings_action, quit_action) -> None:
        super().__init__()
        self.main_window = main_window
        if main_window_action is not None:
            self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Control Panel'), main_window_action)
            self.addSeparator()
        self.busy_disable_prop = "busy_disable"
        self.preset_prop = "is_preset"
        # self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Grey Scale'), chart_action)
        # self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Settings'), settings_action)
        # self.addAction(si(self, QStyle.SP_MessageBoxInformation), tr('About'), about_action)
        # self.addAction(si(self, QStyle.SP_DialogHelpButton), tr('Help'), help_action)
        # self.addSeparator()
        self.addAction(si(self, QStyle.SP_DialogCloseButton), tr('Quit'), quit_action)


class ToolButton(QToolButton):

    def __init__(self, svg_source: bytes, tip: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if tip is not None:
            self.setToolTip(tip)
        self.svg_source = svg_source
        self.refresh_icon()

    def refresh_icon(self, svg_source: bytes | None = None) -> None:  # may refresh the theme (coloring light/dark) of the icon
        if svg_source is not None:
            self.svg_source = svg_source
        self.setIcon(create_themed_icon_from_svg_bytes(self.svg_source))  # this may alter the SVG for light/dark theme


class StatusBar(QStatusBar):

    def __init__(self, app_context_menu: QMenu, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.menu_button = ToolButton(MENU_ICON_SOURCE, tr("Context and Preset Menu"), self)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setAutoRaise(True)
        self.menu_button.setIconSize(QSize(32, 32))
        self.addPermanentWidget(self.menu_button, stretch=1)
        self.installEventFilter(self)


class CameraDisplay(QLabel):
    def __init__(self, parent):
        super().__init__("", parent=parent)
        self.painter = None
        self.current_image: QImage | None = None
        self.setPixmap(QPixmap(800,600))  # Initial "null value"
        self.drawing_with_mouse = False
        self.x_start = 0
        self.y_start = 0
        self.x_end = 0
        self.y_end = 0
        self.selected_relative_all = self.mouse_relative_rectangle = (0.0, 0.0, 100.0, 100.0)
        self.setToolTip(tr("Click and drag to define the brightness sampling area."))
        self.setMouseTracking(True)  # Enable mouse move events
        self.setMinimumSize(800, 600)  # Must set, otherwise cannot be shrunk via resize.

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.display_image(self.current_image)

    def display_image(self, image: QImage):
        if image is not None and self.isVisible():
            self.current_image = image
            self.display_refresh()

    def display_refresh(self):
        if self.current_image is not None:
            scaled = self.current_image.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio)
            pixmap = QPixmap.fromImage(scaled)
            self.painter = QPainter(pixmap)
            self.painter.drawTiledPixmap(0, 0, self.width(), self.height(), pixmap)
            # Existing selection from config file:
            existing_relative_selection = (float(v) for v in global_config['camera']['crop'].split(','))
            existing_absolute_selection = self.calc_absolute_rectangle(*existing_relative_selection)
            self.painter.setPen(QPen(QColor(0x000000), 1))
            self.painter.drawRect(*existing_absolute_selection)
            self.painter.setPen(QPen(QColor(0xff0000), 1))
            # New selection from mouse:
            absolute_mouse_selection = self.calc_absolute_rectangle(*self.mouse_relative_rectangle)
            if existing_absolute_selection != absolute_mouse_selection:
                self.painter.drawRect(*absolute_mouse_selection)
            self.setPixmap(pixmap)
            self.painter.end()

    def calc_relative_rectangle(self, x_start: int, y_start: int, x_end: int, y_end: int) -> Tuple[float, float, float, float]:
        x = min(x_start, x_end)
        y = min(y_start, y_end)
        w = abs(x_start - x_end)
        h = abs(y_start - y_end)
        x_percent = 100 * x / self.pixmap().width()
        y_percent = 100 * y / self.pixmap().height()
        h_percent = 100 * h / self.pixmap().height()
        w_percent = 100 * w / self.pixmap().width()
        return x_percent, y_percent, w_percent, h_percent

    def calc_absolute_rectangle(self, x_percent: float, y_percent: float, w_percent: float, h_percent: float) -> Tuple[int, int, int, int]:
        x = int(int(x_percent/100 * self.pixmap().width()))
        y = int(int(y_percent/100 * self.pixmap().height()))
        w = int(w_percent/100 * self.pixmap().width())
        h = int(h_percent/100 * self.pixmap().height())
        return x, y, w, h

    def mousePressEvent(self, event: QMouseEvent) -> None:
        changed = False
        local_pos = self.mapFromGlobal(event.globalPos())
        self.x_start = local_pos.x()
        self.y_start = local_pos.y()
        if event.button() == Qt.LeftButton:
            self.drawing_with_mouse = True
        if changed:
            self.show_changes()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drawing_with_mouse and self.pixmap() is not None:
            local_pos = self.mapFromGlobal(event.globalPos())
            self.x_end = local_pos.x()
            self.y_end = local_pos.y()
            self.display_refresh()
            self.mouse_relative_rectangle = self.calc_relative_rectangle(self.x_start, self.y_start, self.x_end, self.y_end)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.set_measurement_relative_rectangle()
        if event.button() == Qt.LeftButton:
            self.drawing_with_mouse = False
        event.accept()

    def set_measurement_relative_rectangle(self):
        if self.pixmap() is not None:
            x, y, w, h = self.calc_relative_rectangle(self.x_start, self.y_start, self.x_end, self.y_end)
            global_config['camera']['crop'] = f"{x:0.4f},{y:0.4f},{w:0.4f},{h:0.4f}"
            global_config.save(CONFIG_PATH)


def make_heading(heading_text: str, parent: QWidget = None):
    heading = QLabel(parent=parent)
    big_font = heading.font()
    big_font.setPointSize(big_font.pointSize() + 4)
    heading.setFont(big_font)
    heading.setText(heading_text)
    return heading


class BrightnessMappingDisplay(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.setLayout(layout)
        heading = make_heading(tr("Brightness-to-Lux Mapping"), self)
        layout.addWidget(heading, 0, 0, 1, -1, Qt.AlignTop)

        self.input_widgets: Dict[QWidget, QSpinBox] = {}
        for col, (brightness, (name, lux)) in enumerate(reversed(global_config.get_brightness_map().items())):
            lux_label = QLabel(f"{lux:n}\n{name}")
            layout.addWidget(lux_label, 1, col, 1, 1)
            brightness_input = QSpinBox()
            self.input_widgets[name] = brightness_input
            brightness_input.setRange(0, 255)
            brightness_input.setValue(brightness)
            layout.addWidget(brightness_input, 2, col, 1, 1)
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setToolTip(f"{name} ({lux})")
            slider.setRange(0, 255)
            slider.setValue(brightness)
            slider.sliderMoved.connect(brightness_input.setValue)
            brightness_input.valueChanged.connect(slider.setValue)
            brightness_input.valueChanged.connect(partial(self.save_value, name, lux))
            # slider.setTickInterval(20)
            slider.setTickPosition(QSlider.TicksLeft)
            layout.addWidget(slider, 3, col, -1, 1, Qt.AlignRight)
        self.show()

    def save_value(self, name: str, lux: int, brightness: int):
        global_config['brightness_to_lux'][name] = f"{brightness} {lux}"
        global_config.save(CONFIG_PATH)

class PushButtonLeftJustified(QPushButton):
    def __init__(self, text: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.label = QLabel()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.layout().addWidget(self.label)
        # Not sure if this helps:
        self.setContentsMargins(0, 0, 0, 0)
        # Seems to fix top/bottom clipping on openbox and xfce:
        layout.setContentsMargins(0, 0, 0, 0)
        if text is not None:
            self.setText(text)

    def setText(self, text: str) -> None:
        self.label.setText(text)
class CameraControls(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.camera_device_selector = PushButtonLeftJustified()
        self.camera_device_selector.setText(global_config.get('camera', 'device', fallback=''))
        layout.addWidget(self.camera_device_selector)
        self.toggle_manual_control = QComboBox()
        self.toggle_manual_control.addItem("Manual Exposure")
        self.toggle_manual_control.addItem("Auto Exposure")
        self.toggle_manual_control.setDisabled(True)
        layout.addWidget(self.toggle_manual_control)

        def choose_device() -> None:
            device_name = QFileDialog.getOpenFileName(self, tr("Select a camera device"), "/dev/video0")[0]
            if device_name != '':
                path = pathlib.Path(device_name)
                if path.is_char_device():
                    global_config['camera']['device'] = device_name
                    global_config.save(CONFIG_PATH)

        self.camera_device_selector.pressed.connect(choose_device)


class VluxMeterWindow(QMainWindow):

    def __init__(self, config: ConfigIni, app: QApplication, meter_thread: 'CameraMeterThread') -> None:
        super().__init__()
        global gui_thread
        gui_thread = app.thread()
        self.app = app
        self.app_icon = create_themed_icon_from_svg_bytes(VLUX_METER_ICON_SVG)
        splash_pixmap = get_splash_image()
        self.lux_dispatcher = None if config.getboolean("global", "fifo_disabled", fallback=True) else LuxFifoDispatcher()
        self.app_icon.addPixmap(splash_pixmap)
        self.setObjectName('main_window')
        self.geometry_key = self.objectName() + "_geometry"
        self.state_key = self.objectName() + "_window_state"
        self.settings = QSettings('vlux_meter.qt.state', 'vlux_meter')
        self.config = config
        self.tray = None
        self.meter_thread = meter_thread
        app.installEventFilter(self)

        gnome_tray_behaviour = config.getboolean("global", "system_tray_enabled") and 'gnome' in os.environ.get(
            'XDG_CURRENT_DESKTOP', default='unknown').lower()

        main_window_action: Callable[[], None] | None = None

        if gnome_tray_behaviour:
            # Gnome tray doesn't normally provide a way to bring up the main app.
            def main_window_action_implemenation() -> None:
                self.show()
                self.raise_()
                self.activateWindow()

            main_window_action = main_window_action_implemenation

        def quit_app() -> None:
            self.app_save_state()
            app.quit()

        self.context_menu = ContextMenu(self, main_window_action=main_window_action, settings_action=None, help_action=None,
                                        quit_action=quit_app, chart_action=None, about_action=None)
        self.app_name = "Vlux Meter"
        self.set_app_icon_and_title()
        app.setApplicationDisplayName(self.app_name)

        def open_context_menu(position: QPoint) -> None:
            assert self.context_menu is not None
            self.context_menu.exec(self.mapToGlobal(position))

        self.customContextMenuRequested.connect(open_context_menu)

        def respond_to_unix_signal(signal_number: int) -> None:
            if signal_number == signal.SIGHUP:
                self.start_refresh()

        global signal_wakeup_handler
        signal_wakeup_handler.signalReceived.connect(respond_to_unix_signal)

        if config.getboolean('global', 'system_tray_enabled'):
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log_warning("no system tray, waiting to see if one becomes available.")
                for _ in range(0, SYSTEM_TRAY_WAIT_SECONDS):
                    if QSystemTrayIcon.isSystemTrayAvailable():
                        break
                    time.sleep(0.25)  # TODO - at least use a constant
            if QSystemTrayIcon.isSystemTrayAvailable():
                log_info("Using system tray.")
                # This next call appears to be automatic on KDE, but not on gnome.
                app.setQuitOnLastWindowClosed(False)
                self.tray = QSystemTrayIcon(parent=self)
                self.tray.setContextMenu(self.context_menu)
                self.tray.setIcon(create_themed_icon_from_svg_bytes(VLUX_METER_ICON_SVG))
            else:
                log_error("no system tray - cannot run in system tray.")

        main_widget = QWidget()
        layout = QGridLayout()
        self.setContentsMargins(8, 0, 0, 0)
        main_widget.setLayout(layout)

        self.lux_display = make_heading(tr('Lux:'), parent=self)
        layout.addWidget(self.lux_display, 0, 0, 1, 2)

        self.camera_display = CameraDisplay(parent=self)
        layout.addWidget(self.camera_display, 1, 0, 1, 2, Qt.AlignTop|Qt.AlignLeft)

        self.brightness_lux_mapping_display = BrightnessMappingDisplay()
        #self.brightness_lux_mapping_display.setDisabled(True)
        layout.addWidget(self.brightness_lux_mapping_display, 0, 2, -1, 1)

        self.camera_controls = CameraControls()
        layout.addWidget(self.camera_controls, 2, 0, 1, 2)

        self.setCentralWidget(main_widget)
        self.setStatusBar(StatusBar(app_context_menu=self.context_menu, parent=self))
        self.status_message("Waiting for FIFO consumer", 0)
        self.setBaseSize(200, 600)
        self.app_restore_state()

        if self.tray is not None:
            def show_window() -> None:
                if self.isVisible():
                    self.hide()
                else:
                    if len(self.settings.allKeys()) == 0:
                        # No previous state - guess a position near the tray. Use the mouse pos as a guess to where the
                        # system tray is.  The Linux Qt x,y geometry returned by the tray icon is 0,0, so we can't use that.
                        p = QCursor.pos()
                        wg = self.geometry()
                        # Also try to cope with the tray not being at the bottom right of the screen.
                        x = p.x() - wg.width() if p.x() > wg.width() else p.x()
                        y = p.y() - wg.height() if p.y() > wg.height() else p.y()
                        self.setGeometry(x, y, wg.width(), wg.height())
                    self.show()
                    # Attempt to force it to the top with raise and activate
                    self.raise_()
                    self.activateWindow()
            self.hide()
            self.tray.activated.connect(show_window)
            self.tray.setVisible(True)
        else:
            self.show()

    def display_lux_value(self, lux: int, brightness: int):
        self.status_message('', 0)
        if self.lux_dispatcher is not None:
            self.lux_dispatcher.dispatch_lux_value(lux)
        self.lux_display.setText(f"Lux: {lux:n} (brightness={brightness}) {datetime.now().strftime('%X')}")

    def display_camera_image(self, image: QImage):
        self.camera_display.display_image(image)

    def eventFilter(self, obj: QObject, event: QEvent):
        if obj == self.app:
            if event.type() == QEvent.ApplicationActivate:
                log_info(f"GUI Visible: Switch image refresh rate to fast")
                self.meter_thread.fast_fresh = True
            elif event.type() == QEvent.ApplicationDeactivate:  # Minimised or not focused
                log_info(f"Minimised or not focused: Switch image refresh rate to slow")
                self.meter_thread.fast_fresh = False
        return super().eventFilter(obj, event)

    def closeEvent(self, event) -> None:
        self.app_save_state()

    def set_app_icon_and_title(self) -> None:
        assert is_running_in_gui_thread()
        title = self.app_name
        if self.windowTitle() != title:
            self.setWindowTitle(title)
        icon = self.app_icon
        self.app.setWindowIcon(icon)
        if self.tray:
            self.tray.setToolTip(title)
            self.tray.setIcon(icon)

    def app_save_state(self) -> None:
        self.settings.setValue(self.geometry_key, self.saveGeometry())
        self.settings.setValue(self.state_key, self.saveState())

    def app_restore_state(self) -> None:
        geometry = self.settings.value(self.geometry_key, None)
        if geometry is not None:
            self.restoreGeometry(geometry)
            window_state = self.settings.value(self.state_key, None)
            self.restoreState(window_state)

    def status_message(self, message: str, timeout: int):
        self.statusBar().showMessage(message, timeout)


class CameraMeterThread(QThread):
    new_lux_value_signal = pyqtSignal(int, int)
    new_image_signal = pyqtSignal(QImage)

    def __init__(self) -> None:

        """Init should always be called from the GUI thread - for easy access to the GUI thread"""
        super().__init__()
        log_info(f"MeterThread: going to start from thread = {threading.get_ident()}")
        # Background is always initiated from the GUI thread to grant the worker's __init__ easy access to the GUI thread.
        self.fast_fresh = False

    def run(self) -> None:
        """Long-running task, runs in a separate non-GUI thread"""
        try:
            log_info(f"MeterThread: thread = {threading.get_ident()} {is_running_in_gui_thread()}")
            self.measure_lux()
        finally:
            pass

    def measure_lux(self):
        while True:
            camera = cv2.VideoCapture(global_config['camera']['device'], cv2.CAP_V4L2)
            original_auto_exposure_option = camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            original_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
            log_debug(f"existing values: auto-exposure={original_auto_exposure_option} exposure={original_exposure}") if log_debug_enabled else None
            auto_exposure_option = global_config.getint("camera", "auto_exposure_option")
            manual_exposure_time = global_config.getint("camera", "manual_exposure_time")
            try:
                camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure_option)
                camera.set(cv2.CAP_PROP_EXPOSURE, manual_exposure_time)
                new_auto_exposure = camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                new_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
                log_debug(f"new values: auto-exposure={new_auto_exposure} exposure={new_exposure}") if log_debug_enabled else None
                result, image = camera.read()
                self.signal_new_image(image)
                xp, yp, wp, hp = (float(v) for v in global_config['camera']['crop'].split(','))
                ih, iw = image.shape[0:2]
                crop_x, crop_y, crop_w, crop_h = round(xp/100.0 * iw), round(yp/100.0 * ih), round(wp/100.0 * iw), round(hp/100.0 * ih)
                grey_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                cv2.imshow('grey', grey_image) if log_debug_enabled else None
                cropped_image = grey_image[crop_y:crop_y+crop_h,crop_x:crop_x+crop_w]
                cv2.imshow('crop', cropped_image) if log_debug_enabled else None
                brightness = cv2.mean(cropped_image)[0]
                previous_lux, previous_value = None, None
                for value, (name, lux) in global_config.get_brightness_map().items():
                    if brightness >= value:
                        if previous_lux:
                            # Interpolate on a log10 scale - at least that's what I think this is (idea from chatgpt)
                            lux = lux + 10 ** (
                                    (brightness - value) / (previous_value - value) * math.log10((previous_lux - lux)))
                        log_debug(f"brightness={brightness}, value={value}, lux={lux}, name={name}") if log_debug_enabled else None
                        int_lux = round(lux)
                        self.new_lux_value_signal.emit(int_lux, round(brightness))
                        break
                    previous_lux, previous_value = lux, value
            finally:
                log_debug(f"Restoring auto-exposure={original_auto_exposure_option} exposure={original_exposure}"
                          )  if log_debug_enabled else None
                camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, original_auto_exposure_option)
                if original_auto_exposure_option != auto_exposure_option:  # Can only set exposure if not on auto_exposure
                    camera.set(cv2.CAP_PROP_EXPOSURE, original_exposure)
                camera.release()
                camera = None
            sleep_seconds = 1 if self.fast_fresh else global_config.getint('global', 'dispatch_frequency_seconds')
            log_debug(f"Meter Sleeping {sleep_seconds} seconds") if log_debug_enabled else None
            for _ in range(0, sleep_seconds):
                time.sleep(1)
                if self.fast_fresh:
                    break

    def signal_new_image(self, image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.new_image_signal.emit(q_img)


class LuxFifoDispatcher(QThread):

    def __init__(self):
        super().__init__()
        self.fifo = None
        self.last_time = 0
        self.lux_value = -1

    def run(self) -> None:
        """Long-running task, runs in a separate non-GUI thread"""
        try:
            log_info(f"LuxFifoDispatcher: thread = {threading.get_ident()} {is_running_in_gui_thread()}")
            while self.lux_value == -1:  # Initialising, wait for a value
                time.sleep(1)
            while True:
                if self.lux_value > -1:
                    if self.fifo is None:
                        fifo_path = Path(os.path.expanduser(global_config.get('global', 'fifo_path')))
                        if not fifo_path.exists():
                            os.mkfifo(fifo_path)
                        self.fifo = open(fifo_path, 'w')
                    log_info(f"Dispatcher writing {self.lux_value} to FIFO")
                    self.fifo.write(f"{self.lux_value}\n")
                    self.fifo.flush()
                dispatch_frequency_seconds = global_config.getint('global', 'dispatch_frequency_seconds', fallback=60)
                log_debug(f"Dispatcher sleeping {dispatch_frequency_seconds} seconds") if log_debug_enabled else None
                time.sleep(dispatch_frequency_seconds)

        finally:
            self.fifo.close()
            self.fifo = None

    def dispatch_lux_value(self, lux: int, _: int):
        log_debug(f"Dispatcher received new value {lux}") if log_debug_enabled else None
        self.lux_value = lux


def main():
    global global_config
    """vdu_controls application main."""
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)  # Force UTF-8, just in case it isn't

    # This is supposed to set the locale for all categories to the user’s default setting.
    # This can error on some distros when the required language isn't installed, or if LANG
    # is set without also specifying the UTF-8 encoding, so LANG=da_DK might fail,
    # but LANG=da_DK.UTF-8 should work. For our purposes failure is not important.
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        log_warning("Could not set the default locale - may not be an issue...")
    log_info("Python locale", locale.getlocale())

    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)

    # Wayland needs this set in order to find/use the app's desktop icon.
    QGuiApplication.setDesktopFileName("vlux_meter")

    global signal_wakeup_handler
    signal_wakeup_handler = SignalWakeupHandler(app)

    log_info("Looking for config file '" + CONFIG_PATH.as_posix() + "'")
    # global_config = ConfigIni()
    if Path.is_file(CONFIG_PATH) and os.access(CONFIG_PATH, os.R_OK):
        if not global_config.read(CONFIG_PATH):
            log_error(f"Error loading {CONFIG_PATH}")
    log_info(f"{global_config['camera']=} {global_config['camera']['crop']=}")

    # Assign to variable to stop it being reclaimed as garbage
    if global_config.getboolean('global', 'translations_enabled'):
        initialise_locale_translations(app)

    meter_thread = CameraMeterThread()
    main_window = VluxMeterWindow(global_config, app, meter_thread)

    meter_thread.new_lux_value_signal.connect(main_window.display_lux_value)
    meter_thread.new_image_signal.connect(main_window.display_camera_image)
    meter_thread.start()

    fifo_thread = LuxFifoDispatcher()
    meter_thread.new_lux_value_signal.connect(fifo_thread.dispatch_lux_value)
    fifo_thread.start()

    rc = app.exec_()
    log_info(f"App exit {rc=}")
    sys.exit(rc)


if __name__ == '__main__':
    main()
