#!/usr/bin/python3
"""
lux-from-brightness.py - guess lux value based on a webcam image
================================================================

This script will read lux/brightness values from ~/.config/lux-from-webcam.data
Add as many discrete values as you require: name lux value. The name is
simple a comment and should have no spaces.

A default config file is created when the script is first run, please alter
it to match your own ambient lighting conditions.

Exposure time is 1/s seconds, so 64 is 1/64 of a second.
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
import base64
import configparser
import io
import locale
import math
import os
import socket
import syslog
import threading
import time
from ast import literal_eval
from datetime import datetime
from pathlib import Path
import signal
import sys
from typing import List, Tuple, Mapping, Callable, Dict

import cv2  # type: ignore
from PyQt5 import QtNetwork
from PyQt5.QtCore import QSettings, pyqtSignal, QThread, QCoreApplication, QTranslator, QLocale, QPoint, QSize
from PyQt5.QtGui import QGuiApplication, QPixmap, QIcon, QCursor, QImage, QPainter, QPalette
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QStyle, QWidget, QLabel, QVBoxLayout, QToolButton, \
    QToolBar, QStatusBar

APPNAME = "Vlux Meter"
VLUX_METER_VERSION = '1.0.0'

IMAGE_LOCATION = Path('/tmp').joinpath('lux-from-webcam.jpg').as_posix()
SAVE_IMAGE = False
VERBOSE = False

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

BRIGHTNESS_ICON_SVG = b"""<svg height="22" viewBox="0 0 22 22" width="22" xmlns="http://www.w3.org/2000/svg"><g 
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
        'crop_at_x': 0,
        'crop_at_y': 0,
        'crop_height': 0,
        'crop_width': 0,
    },
    'brightness_to_lux': {
        'sunlight': brightness_lux_str(250, 100000),
        'daylight': brightness_lux_str(160, 10000),
        'overcast': brightness_lux_str(110, 1000),
        'sunrise_sunset': brightness_lux_str(50, 400),
        'dark_overcast': brightness_lux_str(20, 100),
        'living_room': brightness_lux_str(5, 50),
        'night': brightness_lux_str(0, 5),
    },
    'global': {
        'system_tray_enabled': 'yes',
        'fifo_path': '~/.cache/vlux_fifo',
        'update_frequency_seconds': 60,
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
    pixmap = QPixmap()
    if os.path.isfile(DEFAULT_SPLASH_PNG) and os.access(DEFAULT_SPLASH_PNG, os.R_OK):
        pixmap.load(DEFAULT_SPLASH_PNG)
    else:
        pixmap.loadFromData(base64.decodebytes(FALLBACK_SPLASH_PNG_BASE64), 'PNG')
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
        log_info(f"Wrote config to {config_path.as_posix()}")


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


class VduPanelBottomToolBar(QStatusBar):

    def __init__(self, app_context_menu: QMenu, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.menu_button = ToolButton(MENU_ICON_SOURCE, tr("Context and Preset Menu"), self)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setAutoRaise(True)
        self.menu_button.setIconSize(QSize(32, 32))
        self.addPermanentWidget(self.menu_button, stretch=0)
        self.installEventFilter(self)


class VluxMeterWindow(QMainWindow):

    def __init__(self, config: ConfigIni, app: QApplication) -> None:
        super().__init__()
        global gui_thread
        gui_thread = app.thread()
        self.app = app
        self.app_icon = create_themed_icon_from_svg_bytes(BRIGHTNESS_ICON_SVG)
        splash_pixmap = get_splash_image()
        self.app_icon.addPixmap(splash_pixmap)
        self.setObjectName('main_window')
        self.geometry_key = self.objectName() + "_geometry"
        self.state_key = self.objectName() + "_window_state"
        self.settings = QSettings('vlux_meter.qt.state', 'vlux_meter')
        self.config = config
        self.tray = None

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
                self.tray.setIcon(create_themed_icon_from_svg_bytes(BRIGHTNESS_ICON_SVG))
            else:
                log_error("no system tray - cannot run in system tray.")

        main_widget = QWidget()
        main_widget.setLayout(QVBoxLayout())
        self.lux_display = QLabel("0")
        main_widget.layout().addWidget(self.lux_display)

        # main_widget.setMinimumWidth(1024)

        self.setCentralWidget(main_widget)
        self.setStatusBar(VduPanelBottomToolBar(app_context_menu=self.context_menu, parent=self))
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
        assert (self.main_panel is not None)
        self.main_panel.status_message(message, timeout)


class MeterThread(QThread):
    new_lux_value_signal = pyqtSignal(int)

    def __init__(self) -> None:

        """Init should always be called from the GUI thread - for easy access to the GUI thread"""
        super().__init__()
        log_info(f"MeterThread: going to start from thread = {threading.get_ident()}")
        # Background is always initiated from the GUI thread to grant the worker's __init__ easy access to the GUI thread.
        assert is_running_in_gui_thread()

    def run(self) -> None:
        """Long-running task, runs in a separate non-GUI thread"""
        try:
            log_info(f"MeterThread: thread = {threading.get_ident()} {is_running_in_gui_thread()}")
            self.measure_lux()
        finally:
            pass

    def measure_lux(self):
        fifo_path = Path(os.path.expanduser(global_config.get('global', 'fifo_path')))
        if not fifo_path.exists():
            os.mkfifo(fifo_path)
        with open(fifo_path, 'w') as fifo:
            while True:
                camera = cv2.VideoCapture(global_config['camera']['device'])
                original_auto_exposure_option = camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                original_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
                print(f"INFO: existing values: auto-exposure={original_auto_exposure_option} exposure={original_exposure}",
                      file=sys.stderr) if VERBOSE else None
                auto_exposure_option = global_config.getint("camera", "auto_exposure_option")
                manual_exposure_time = global_config.getint("camera", "manual_exposure_time")
                try:
                    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure_option)
                    camera.set(cv2.CAP_PROP_EXPOSURE, manual_exposure_time)
                    new_auto_exposure = camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                    new_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
                    log_info(f"new values: auto-exposure={new_auto_exposure} exposure={new_exposure}",
                             file=sys.stderr) if VERBOSE else None

                    result, image = camera.read()
                    cv2.imwrite(IMAGE_LOCATION, image) if SAVE_IMAGE else None  # uncomment to check the image exposure etc.
                    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    cv2.imwrite(IMAGE_LOCATION + "-gray", gray_image) if SAVE_IMAGE else None

                    brightness = cv2.mean(gray_image)[0]

                    previous_lux, previous_value = None, None
                    for value, (name, lux) in global_config.get_brightness_map().items():
                        if brightness >= value:
                            if previous_lux:
                                # Interpolate on a log10 scale - at least that's what I think this is (idea from chatgpt)
                                print(
                                    f"INFO: log10 interpolating {brightness} over {value}..{previous_value} to lux {lux}..{previous_lux}") if VERBOSE else None
                                lux = lux + 10 ** (
                                        (brightness - value) / (previous_value - value) * math.log10((previous_lux - lux)))
                            log_info(f"brightness={brightness}, value={value}, lux={lux}, name={name}")
                            int_lux = round(lux)
                            fifo.write(f"{int_lux}\n")
                            fifo.flush()
                            self.new_lux_value_signal.emit(int_lux)
                            break
                        previous_lux, previous_value = lux, value
                finally:
                    log_info(
                        f"Restoring auto-exposure={original_auto_exposure_option} exposure={original_exposure}") if VERBOSE else None
                    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, original_auto_exposure_option)
                    if original_auto_exposure_option != auto_exposure_option:  # Can only set exposure if not on auto_exposure
                        camera.set(cv2.CAP_PROP_EXPOSURE, original_exposure)
                    camera.release()
                    camera = None
                sleep_seconds = global_config.getint('global', 'update_frequency_seconds')
                log_info(f"Sleeping {sleep_seconds}")
                time.sleep(sleep_seconds)


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
    print(global_config['camera'])

    # Assign to variable to stop it being reclaimed as garbage
    if global_config.getboolean('global', 'translations_enabled'):
        initialise_locale_translations(app)

    main_window = VluxMeterWindow(global_config, app)
    worker = MeterThread()

    def show_lux(value: int):
        log_info(f"value={value}")
        main_window.lux_display.setText(str(value))

    worker.new_lux_value_signal.connect(show_lux)
    worker.start()

    rc = app.exec_()
    log_info(f"App exit {rc=}")
    sys.exit(rc)


# A fallback in case the hard coded splash screen PNG doesn't exist (which probably means KDE is not installed).
FALLBACK_SPLASH_PNG_BASE64 = b"""
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
"""

if __name__ == '__main__':
    main()
