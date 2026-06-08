# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import locale
import signal
import socket
import subprocess
import threading
import time as sys_time
import traceback
from contextlib import contextmanager
from datetime import timedelta, datetime
from functools import partial
from typing import List, Tuple, Dict, Callable, cast, Optional, Iterator

import vdu_controls.gui_misc as gui_misc
import vdu_controls.logging as log
import vdu_controls.svg as svg
import vdu_controls.weather_util as weather_util
from vdu_controls import weather_util as weather_utils, app_locale
from vdu_controls.about_dialog import AboutDialog
from vdu_controls.app_locale import tr, initialise_locale_translations
from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import *
from vdu_controls.context_menu import ContextMenu, FixedItemKey
from vdu_controls.ddcutil_abstract import VcpOrigin, VcpValue, DdcutilDisplayNotFound, CONTINUOUS_TYPE, \
    BRIGHTNESS_VCP_CODE, DdcEventType, \
    DdcutilServiceNotFound
from vdu_controls.ddcutil_aggregator import DdcutilAggregator, VduStableId
from vdu_controls.ddcutil_emulator import DdcutilEmulatorImpl
from vdu_controls.ddcutil_laptop_panel import DdcutilPanelImpl
from vdu_controls.greyscale import GreyScaleDialog
from vdu_controls.help_dialog import HelpDialog
from vdu_controls.icon_utils import ThemeType, get_splash_pixmap
from vdu_controls.icon_utils import create_icon_from_svg_bytes, create_icon_from_path, create_decorated_app_icon, StdPixmap, \
    is_dark_theme
from vdu_controls.installer import install_as_desktop_application
from vdu_controls.lux_auto import LuxAutoController
from vdu_controls.lux_dialog import LuxDialog
from vdu_controls.lux_meters import LuxMeterSemiAutoDevice
from vdu_controls.misc import zoned_now, proper_name, GeoLocation
from vdu_controls.preset import Preset, PresetScheduleStatus, PresetTransitionFlag
from vdu_controls.preset_controller import PresetController
from vdu_controls.preset_dialog import PresetsDialog
from vdu_controls.qt_imports import *
from vdu_controls.release import release_notes
from vdu_controls.scaling import desktop_font_height, dpx
from vdu_controls.settings_editor import SettingsDialog
from vdu_controls.solar_calc import create_elevation_map
from vdu_controls.unicode import *
from vdu_controls.vdu_bulk_change import BulkChangeWorker, BulkChangeItem
from vdu_controls.vdu_control_panel import VduControlPanel
from vdu_controls.vdu_controller import VduController
from vdu_controls.vdu_controls_config import ConfOpt, VduControlsConfig, VcpCapability
from vdu_controls.vdu_exceptions import VduException
from vdu_controls.widgets import MIcon, MBox, MBtn, \
    alter_margins, DialogSingletonMixin, ToolButton
from vdu_controls.work_scheduler import WorkerThread, ScheduleWorker, thread_pid, SchedulerJob, SchedulerJobType

# Use Linux/UNIX signals to trigger preset changes - 16 presets should be enough for anyone.

unix_signal_handler: SignalWakeupHandler | None = None


original_qt_qpa_platform: str | None = None


def force_xwayland():
    """
    Set the QT_QPA_PLATFORM environment variable to force Qt to use XWayland.
    Caches the previous value of the environment variable so it can be restored later.
    """
    # Force Qt to use XWayland, or reverse the previous force
    global original_qt_qpa_platform
    original_qt_qpa_platform = os.environ.get('QT_QPA_PLATFORM', '')  # save original value
    log.info("Forcing Xwayland, setting environment variable QT_QPA_PLATFORM=xcb")
    os.environ['QT_QPA_PLATFORM'] = 'xcb'


def reverse_force_xwayland():
    """
    Restore or unset QT_QPA_PLATFORM environment variable to match the situation
    before calling force_xwayland().
    """
    if original_qt_qpa_platform:
        log.info(f"Restoring environment variable QT_QPA_PLATFORM={original_qt_qpa_platform}")
        os.environ['QT_QPA_PLATFORM'] = original_qt_qpa_platform  # restore original value
    elif original_qt_qpa_platform == '':  # Will be '' if force_xwayland() has been called, otherwise it will be None
        log.info(f"Removing environment variable QT_QPA_PLATFORM")
        os.environ.pop('QT_QPA_PLATFORM')  # before the call to force_xwayland() it did not previously exist, remove it.


class VduMainToolBar(QToolBar):

    def __init__(self, tool_buttons: List[ToolButton], app_context_menu: ContextMenu, parent: VduControlsMainPanel) -> None:
        super().__init__(parent=parent)
        self.setObjectName('VduPanelToolBar')  # Internal name for persistence - do not change or persistence will be lost.
        self.preset_edit_target: Preset | None = None
        self.setMovable(False)
        self.tool_buttons = tool_buttons
        for button in self.tool_buttons:
            self.addWidget(button)
        self.setIconSize(QSize(desktop_font_height(), desktop_font_height()))
        self.status_area = QStatusBar()
        self.addWidget(self.status_area)
        self.menu_button = ToolButton(svg.MENU_ICON_SVG, tr("Context and Preset Menu"), self)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.preset_action = self.addAction(QIcon(), "")
        assert self.preset_action
        #self.preset_action.setVisible(False)

        if (toggle_view_action := self.toggleViewAction()) is not None:
            toggle_view_action.setEnabled(False)  # Stop users from accidentally hiding the toolbar
            toggle_view_action.setVisible(False)

        def edit_current_preset():
            assert parent.main_controller is not None   # will have a value by now
            parent.main_controller.show_presets_dialog(self.preset_edit_target)

        self.preset_action.triggered.connect(edit_current_preset)
        self.addWidget(self.menu_button)

    def refresh_buttons(self):
        for button in self.tool_buttons:
            button.refresh_icon()
        self.menu_button.refresh_icon()

    def indicate_busy(self, is_busy: bool = True) -> None:
        if is_busy:
            self.tool_buttons[0].setBusy(True)
        else:
            self.tool_buttons[0].setBusy(False)
        QApplication.sendPostedEvents(self, 0)  # Flush any change events before resetting the flag
        QApplication.processEvents()  # Force the flushed events to be processed now

    def show_active_preset(self, preset: Preset | None) -> None:
        assert self.preset_action
        if preset is not None:
            self.preset_action.setToolTip(tr("{} preset").format(preset.get_title_name()))
            self.preset_action.setIcon(preset.create_icon())
            self.preset_edit_target = preset
        else:
            self.preset_action.setToolTip(tr("Open Preset Dialog"))
            self.preset_action.setIcon(create_icon_from_svg_bytes(svg.VDU_PRESET_ICON_SVG))
            self.preset_edit_target = None
        self.layout().update()  # pyright:ignore


class VduControlsMainPanel(QWidget):
    """GUI for detected VDUs, it will construct and contain a control panel for each VDU."""

    vdu_vcp_changed_qtsignal = pyqtSignal(str, int, int, VcpOrigin, bool)

    def __init__(self) -> None:
        super().__init__()
        self.main_toolbar: VduMainToolBar | None = None
        self.refresh_data_task = None
        self.setObjectName("vdu_controls_main_panel")
        self.vdu_control_panels: Dict[str, VduControlPanel] = {}
        self.alert: QMessageBox | None = None
        self.main_controller: VduAppController | None = None
        self.message_history = []

    def initialise_control_panels(self, main_controller: VduAppController,
                                  app_context_menu: ContextMenu, main_config: VduControlsConfig,
                                  tool_buttons: List[ToolButton], extra_controls: List[QWidget],
                                  splash_message_qtsignal: pyqtBoundSignal) -> None:
        self.main_controller = main_controller

        if old_layout := cast(QVBoxLayout, self.layout()):  # Must be responding to a configuration change requiring re-layout.
            for i in range(0, old_layout.count()):  # Remove all existing widgets.
                item = old_layout.itemAt(i)
                if isinstance(item, QWidget):
                    old_layout.removeWidget(item)
                    item.deleteLater()
                elif isinstance(item, QWidgetItem):
                    old_layout.removeItem(item)
                    item.widget().deleteLater() # pyright: ignore
        controllers_layout = QVBoxLayout()
        controllers_layout.setSpacing(dpx(2))
        alter_margins(controllers_layout, top=dpx(2), bottom=dpx(2))
        self.setLayout(controllers_layout)

        warnings_enabled = main_config.is_set(ConfOpt.WARNINGS_ENABLED)
        self.vdu_control_panels.clear()
        for controller in self.main_controller.vdu_controllers_map.values():
            splash_message_qtsignal.emit(f"DDC ID {controller.vdu_number}\n{controller.get_vdu_preferred_name()}")  # pyright: ignore
            vdu_control_panel = VduControlPanel(controller, self.show_vdu_exception)
            controller.vcp_value_changed_qtsignal.connect(self.vdu_vcp_changed_qtsignal)
            if vdu_control_panel.number_of_controls() != 0:
                self.vdu_control_panels[controller.vdu_stable_id] = vdu_control_panel
                controllers_layout.addWidget(vdu_control_panel)
            elif warnings_enabled:
                MBox(MIcon.Warning,
                     msg=tr('Monitor {0} {1} lacks any accessible controls.').format(controller.vdu_number,
                                                                                   controller.get_vdu_preferred_name()),
                     info=tr('The monitor will be omitted from the control panel.')).exec()

        for control in extra_controls:
            controllers_layout.addWidget(control)
        controllers_layout.addStretch(0)

        if len(self.vdu_control_panels) == 0:
            no_vdu_widget = QWidget()
            no_vdu_layout = QHBoxLayout()
            no_vdu_widget.setLayout(no_vdu_layout)
            no_vdu_text = QLabel(tr('No controllable monitors found.\n'
                                    'Use the refresh button if any become available.\n'
                                    'Check that ddcutil and i2c are installed and configured.'))
            no_vdu_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
            no_vdu_image = QLabel()
            no_vdu_image.setPixmap(QApplication.style().standardIcon(StdPixmap.SP_MessageBoxWarning).pixmap(QSize(64, 64)))  # pyright: ignore
            no_vdu_image.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            no_vdu_layout.addSpacing(32)
            no_vdu_layout.addWidget(no_vdu_image)
            no_vdu_layout.addWidget(no_vdu_text)
            no_vdu_layout.addSpacing(32)
            controllers_layout.addWidget(no_vdu_widget)

        self.main_toolbar = VduMainToolBar(tool_buttons=tool_buttons, app_context_menu=app_context_menu, parent=self)
        main_controller.replace_toolbar(self.main_toolbar)

        def _open_context_menu(position: QPoint) -> None:
            assert app_context_menu is not None
            app_context_menu.exec(self.mapToGlobal(position))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(_open_context_menu)

    def indicate_busy(self, is_busy: bool = True, lock_controls: bool = True) -> None:
        if self.main_toolbar is not None:
            self.main_toolbar.indicate_busy(is_busy)
        if lock_controls:
            for control_panel in self.vdu_control_panels.values():
                control_panel.setDisabled(is_busy)

    def is_preset_active(self, preset: Preset) -> bool:
        for section in preset.preset_ini:
            if section not in ('metadata', 'preset') and (panel := self.vdu_control_panels.get(section, None)):
                if not panel.is_preset_active(preset):
                    return False
        return True

    def show_active_preset(self, preset: Preset | None) -> None:
        if self.main_toolbar:
            self.main_toolbar.show_active_preset(preset)

    def show_vdu_exception(self, exception: Exception, can_retry: bool = False) -> bool:
        if isinstance(exception, VduException):
            log.error(f"{exception.vdu_description} {exception.operation} {exception.attr_id} {exception.cause}")
            msg = tr("Set value: Failed to communicate with display {}").format(exception.vdu_description)
            if exception.is_display_not_found_error():
                info = tr('Monitor appears to be switched off or disconnected.')
            else:
                info = tr('Is the monitor switched off?') + '<br>' + tr('Is the sleep-multiplier setting too low?')
            if isinstance(exception.cause, subprocess.CalledProcessError):
                details = exception.cause.stderr.decode('utf-8', errors='surrogateescape') + '\n' + str(exception.cause)
            else:
                details = str(exception.cause)
        else:
            msg = str(exception)
            info = repr(exception)
            details = ''
        if self.alert is not None:  # Dismiss any existing alert
            self.alert.done(MBtn.Close)
        self.alert = MBox(MIcon.Critical, msg=msg, info=info, details=details,
                          buttons=MBtn.Close | MBtn.Retry if can_retry else MBtn.Close,
                          default=MBtn.Retry if can_retry else MBtn.Close)
        self.alert.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        answer = self.alert.exec()
        self.alert = None
        return answer == MBtn.Retry

    def status_message(self, message: str, timeout: int):
        if message.strip():  # Only non-empty messages, ignore blank messages, they're just clearing the status bar.
            self.message_history.append(f"\n{datetime.now().strftime('%H:%M:%S')}{MESSAGE_SYMBOL} {message}")
            self.message_history = self.message_history[-9:]
        assert self.main_controller is not None   # will exist by the time this is called.
        if self.main_controller.main_config.is_set(ConfOpt.SEPARATE_STATUS_BAR):
            status_bar = self.main_controller.main_window.statusBar()  # pyright:ignore
            assert status_bar is not None
            status_bar.showMessage(message, timeout)
            status_bar.setToolTip("".join([tr('Message history:')] + self.message_history))
        elif self.main_toolbar:
            self.main_toolbar.status_area.showMessage(message, timeout)
            self.main_toolbar.status_area.setToolTip("".join([tr('Message history:')] + self.message_history))


def exception_handler(e_type, e_value, e_traceback) -> None:
    """Overarching error handler in case something unexpected happens."""
    log.error("\n" + ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    MBox(MIcon.Critical, msg=tr('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))),
         details=tr('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback)))).exec()


@contextmanager  # https://stackoverflow.com/questions/31501487/non-blocking-lock-with-with-statement
def non_blocking_lock(lock: threading.RLock) -> Iterator[Optional[threading.RLock]]:  # Provide a way to use a with-statement with non-blocking locks
    acquire_succeeded = lock.acquire(False)  # acquire_succeeded will be False if the lock is already locked.
    try:
        yield lock if acquire_succeeded else None  # return None to the with if the lock was not acquired
    finally:
        if acquire_succeeded:
            lock.release()


class VduAppController(QObject):  # Main controller containing methods for high level operations

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.find_vdu_config_files()
        self.application_lock = threading.RLock()  # thread level, thread-safe, access lock
        self.main_config = main_config
        self.ddcutil: DdcutilAggregator | None = None
        self.main_window: VduAppWindow | None = None
        self.vdu_controllers_map: Dict[VduStableId, VduController] = {}
        self.preset_controller = PresetController()
        self.detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.previously_detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.refresh_data_task: WorkerThread | None = None
        self.weather_query: weather_util.WeatherQuery | None = None
        self.preset_transition_workers: List[BulkChangeWorker] = []  # Not sure if this actually needs to be a list.
        self.lux_auto_controller: LuxAutoController | None = LuxAutoController(self) if self.main_config.is_set(
            ConfOpt.LUX_OPTIONS_ENABLED) else None

        def respond_to_unix_signal(signal_number: int) -> None:
            if signal_number == signal.SIGHUP:
                self.start_refresh(external_event=True)
            elif PRESET_SIGNAL_MIN <= signal_number <= PRESET_SIGNAL_MAX:
                if preset := self.preset_controller.get_preset(signal_number - PRESET_SIGNAL_MIN):
                    immediately = PresetTransitionFlag.SIGNAL not in preset.get_transition_type()
                    log.info(f"Signaled for {preset.name=} {preset.get_transition_type()=} {immediately=} {thread_pid()=}")
                    # Signals occur outside the GUI thread - initiate the restore in the GUI thread
                    self.restore_preset(preset=preset, immediately=immediately, background_activity=True)
                else:
                    # Cannot raise a Qt alert inside the signal handler in case another signal comes in.
                    log.warning(f"ignoring {signal_number=}, no preset associated with that signal number.")

        global unix_signal_handler
        assert unix_signal_handler is not None   # should not be None at this point
        unix_signal_handler.received_unix_signal_qtsignal.connect(respond_to_unix_signal)

    def get_main_window(self) -> VduAppWindow:
        assert self.main_window is not None
        return self.main_window

    def configure_application(self, main_window: VduAppWindow | None = None, check_schedule: bool = True):
        try:
            log.info(f"Configuring application (reconfiguring={main_window is None})...")
            for controller in self.vdu_controllers_map.values():
                controller.no_longer_in_use = True
            if main_window is not None:  # First time through
                self.main_window = main_window
            if self.get_main_window().main_panel is not None:
                self.get_main_window().indicate_busy(True)
                QApplication.processEvents()
            log.debug("configure: try to obtain application_lock", trace=False) if log.debug_enabled else None
            with self.application_lock:
                log.debug("configure: holding application_lock") if log.debug_enabled else None
                ScheduleWorker.dequeue_all()
                if self.lux_auto_controller is not None:
                    self.lux_auto_controller.stop_worker()
                    self.lux_auto_controller.lux_slider = None
                self.stop_any_transitioning_presets()
                log.set_syslog(self.main_config.is_set(ConfOpt.SYSLOG_ENABLED))
                self.create_ddcutil()
                self.preset_controller.reinitialize()
                self.get_main_window().initialise_app_icon()
                self.get_main_window().create_main_control_panel()
                SettingsDialog.reconfigure_instance(self.get_vdu_configs())
                self.restore_vdu_initialization_presets()
                self.schedule_presets()
                ScheduleWorker.check() if check_schedule else None
            log.debug("configure: released application_lock") if log.debug_enabled else None
            if self.main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED):
                if self.lux_auto_controller is not None:
                    self.lux_auto_controller.initialize_from_config()
                    LuxDialog.reconfigure_instance()
            self.get_main_window().update_status_indicators()
        finally:
            if self.main_window is not None:
                self.get_main_window().indicate_busy(False)
        log.info("Completed configuring application")

    def stop_any_transitioning_presets(self):
        for running_worker in [worker for worker in self.preset_transition_workers if worker.isRunning()]:
            running_worker.stop()
            log.debug(f"Stop requested for {running_worker.name=} {running_worker.start_time=!s}")
        self.preset_transition_workers.clear()

    def create_ddcutil(self):

        if self.main_config.is_set(ConfOpt.DBUS_CLIENT_ENABLED) and self.main_config.is_set(ConfOpt.DBUS_EVENTS_ENABLED):

            def _vdu_connectivity_changed_callback(edid_encoded: str, event_type: int, flags: int):
                values_only = False
                if not DdcEventType.UNKNOWN.value <= event_type <= DdcEventType.DISPLAY_DISCONNECTED.value:
                    log.warning(f"Connected VDUs event - unknown {event_type=} treating as DPMS_UNKNOWN.")
                    event_type = DdcEventType.UNKNOWN.value
                if event_type == DdcEventType.DPMS_ASLEEP.value:
                    log.info(f"Connected VDUs event {DdcEventType(event_type)} {flags=} {edid_encoded:.30}...")
                    return  # Don't do anything, the VDUs are just asleep.
                elif event_type == DdcEventType.LAPTOP_BRIGHTNESS_CHANGE.value:
                    log.info(f"Laptop event {edid_encoded:.30}...")
                    values_only = True
                    # self.lux_auto_controller.set_auto(False) - we don't do this for any other manual change - so do nothing?
                    # could do something specific here - but the following refresh will cover it.
                self.start_refresh(external_event=True, values_only=values_only)

            change_handler = _vdu_connectivity_changed_callback
            log.debug("Enabled callback for VDU-connectivity-change D-Bus signals")
        else:
            change_handler = None  # This will force disabling the eventing/polling inside the server, not just the client.

        try:
            self.ddcutil = DdcutilAggregator(common_args=self.main_config.get_ddcutil_extra_args(),
                                             prefer_dbus_client=self.main_config.is_set(ConfOpt.DBUS_CLIENT_ENABLED),
                                             connected_vdus_changed_callback=change_handler)
            if self.main_config.is_set(ConfOpt.LAPTOP_PANEL_ENABLED):
                try:
                    self.ddcutil.add_ddcutil_emulator(DdcutilPanelImpl(callback=change_handler))
                except Exception as e:
                    MBox(MIcon.Critical, msg=tr('Laptop Support: brightessctrl command failed'),
                         info='Check that brightessctrl is installed and is working.', details=str(e)).exec()
            if emulator := self.main_config.ini_content.get(ConfOpt.DDCUTIL_EMULATOR.conf_section,
                                                            ConfOpt.DDCUTIL_EMULATOR.conf_name, fallback=None):
                common_args = self.main_config.get_ddcutil_extra_args()
                log.info(f"add_ddcutil_emulator: {emulator} {common_args}")
                self.ddcutil.add_ddcutil_emulator(DdcutilEmulatorImpl(emulator, common_args))
        except (subprocess.SubprocessError, ValueError, re.error, OSError, DdcutilServiceNotFound) as e:
            self.get_main_window().show_no_controllers_error_dialog(e)

    def detect_vdus(self) -> Tuple[List[Tuple[str, str, str, str]], Exception | None]:
        if self.ddcutil is None:
            return [], None
        ddcutil_problem = None
        try:
            self.detected_vdu_list = []
            log.debug("Detecting connected monitors, looping detection until it stabilizes.") if log.debug_enabled else None
            # Loop in case the session is initializing/restoring which can make detection unreliable.
            # Limit to a reasonable number of iterations.
            for i in range(1, 11):
                prev_num = len(self.detected_vdu_list)
                self.detected_vdu_list = self.ddcutil.detect_vdus()
                if prev_num == len(self.detected_vdu_list):
                    log.info(f"Number of detected monitors is stable at {len(self.detected_vdu_list)} (loop={i})")
                    break
                elif prev_num > 0:
                    log.info(f"Number of detected monitors changed from {prev_num} to {len(self.detected_vdu_list)} (loop={i})")
                sys_time.sleep(1.5)
        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
            log.error(e)
            ddcutil_problem = e
        self.previously_detected_vdu_list = self.detected_vdu_list
        return self.detected_vdu_list, ddcutil_problem

    def initialize_vdu_controllers(self) -> None:
        assert gui_misc.is_running_in_gui_thread()
        if self.ddcutil is None:
            return
        detected_vdu_list, ddcutil_problem = self.detect_vdus()
        self.vdu_controllers_map = {}
        main_panel_error_handler = self.get_main_window().get_main_panel().show_vdu_exception
        for vdu_number, manufacturer, model_name, vdu_serial in detected_vdu_list:
            controller = None
            while True:
                try:
                    controller = VduController(vdu_number, model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, self.edit_config, main_panel_error_handler, VduController.NORMAL_VDU)
                except (subprocess.SubprocessError, ValueError, re.error, OSError, DdcutilDisplayNotFound) as e:
                    log.error(f"Problem creating controller for {vdu_number=} {model_name=} {vdu_serial=} exception={e}",
                              trace=True)
                    remedy = self.get_main_window().ask_for_vdu_controller_remedy(vdu_number, model_name, vdu_serial)
                    if remedy == VduController.NORMAL_VDU:
                        sys_time.sleep(1.0)  # Slow things down in case something is wrong with the GUI or VDU interactions.
                        continue  # Loop and retry as a normal VDU
                    controller = VduController(vdu_number, model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, self.edit_config, main_panel_error_handler, remedy)
                    controller.write_template_config_files()
                break  # Normally expect to just pass through the loop once
            if controller is not None:
                self.vdu_controllers_map[controller.vdu_stable_id] = controller
        if len(self.vdu_controllers_map) == 0:
            if self.main_config.is_set(ConfOpt.WARNINGS_ENABLED):
                self.get_main_window().show_no_controllers_error_dialog(ddcutil_problem)
        if self.main_config.is_set(ConfOpt.ORDER_BY_NAME):
            self.vdu_controllers_map = {
                c.vdu_stable_id: c for c in sorted(self.vdu_controllers_map.values(), key=VduController.get_vdu_preferred_name)}

    def settings_changed(self, changed_settings: List) -> None:
        if changed_settings is None:  # Special value - means settings have been reset/removed - needs restart.
            self.restart_application(tr("A settings reset requires vdu_controls to restart."))
            return
        for setting in ConfOpt:
            if setting.restart_required and (setting.conf_section, setting.conf_name) in changed_settings:
                self.restart_application(
                    tr("The change to the {} option requires vdu_controls to restart.").format(tr(setting.conf_name)))
                return
        self.main_config.reload()
        log.set_syslog(self.main_config.is_set(ConfOpt.SYSLOG_ENABLED))
        log.set_debug(self.main_config.is_set(ConfOpt.DEBUG_ENABLED))
        log.info("Reconfiguring due to settings change.")
        self.configure_application()

    def edit_config(self, config_name: str | None = None) -> None:
        SettingsDialog.show_dialog(self.main_config, self.get_vdu_configs(), self.settings_changed)
        SettingsDialog.edit_config(config_name if config_name else self.main_config.config_name)

    def show_presets_dialog(self, preset: Preset | None = None) -> None:
        PresetsDialog.show_dialog(self, self.main_config)
        if preset is not None:
            PresetsDialog.get_instance().edit_preset(preset)

    def get_vdu_configs(self) -> List[VduControlsConfig]:
        return [vdu.config for vdu in self.vdu_controllers_map.values() if vdu.config is not None]

    def create_config_files(self) -> None:
        for controller in self.vdu_controllers_map.values():
            controller.write_template_config_files()

    def lux_auto_action(self) -> None:
        if self.lux_auto_controller:
            try:
                self.get_main_window().setDisabled(True)
                self.lux_auto_controller.toggle_auto()
                self.get_main_window().update_status_indicators()
            finally:
                self.get_main_window().setDisabled(False)

    def lux_check_action(self) -> None:
        if self.lux_auto_controller and self.lux_auto_controller.is_auto_enabled():
            self.lux_auto_controller.adjust_brightness_now()

    def start_refresh(self, external_event: bool = False, values_only: bool = False) -> None:

        def _update_from_vdu(worker: WorkerThread) -> None:
            assert self.refresh_data_task is not None
            if self.ddcutil is not None:
                with non_blocking_lock(self.application_lock) as acquired_lock:
                    if acquired_lock:  # If acquired_lock is not None, then we have successfully acquired the lock.
                        log.debug(f"_update_from_vdu: holding application_lock") if log.debug_enabled else None
                        try:
                            log.info(f"Refresh commences: {external_event=} {values_only=}") if log.debug_enabled else None
                            if values_only:
                                self.detected_vdu_list = self.ddcutil.detect_vdus()  # TODO Not sure why this is necessary.
                            else:
                                self.ddcutil.refresh_connection()
                                self.detected_vdu_list = self.ddcutil.detect_vdus()
                                self.restore_vdu_initialization_presets()
                            for control_panel in self.get_main_window().get_main_panel().vdu_control_panels.values():
                                if control_panel.controller.get_full_id() in self.detected_vdu_list:
                                    control_panel.refresh_from_vdu()
                        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
                            if self.refresh_data_task.work_exception is None:
                                self.refresh_data_task.work_exception = VduException(vdu_description="unknown", operation="unknown",
                                                                                     exception=e)
                    else:
                        log.info(f"Application is already busy, can't do a refresh ({external_event=})")
                        worker.stop()  # Stop the thread - which also indicates we did not acquire the lock.
                        return  # Prevents logging unlock (because we don't have the lock if we reach here).
                log.debug(f"_update_from_vdu: released application_lock") if log.debug_enabled else None

        def _update_ui_view(worker: WorkerThread) -> None:
            assert self.refresh_data_task is not None
            # Invoke when the worker thread completes. Runs in the GUI thread and can refresh remaining UI views.
            if worker.stop_requested:
                return  # in this case, this means the worker never started anything
            try:  # No need for locking in here - running in the GUI thread effectively single threads the operation.
                assert self.refresh_data_task is not None and gui_misc.is_running_in_gui_thread()
                log.debug(f"Refresh - update UI view {external_event=} {values_only=}") if log.debug_enabled else None
                main_panel = self.get_main_window().get_main_panel()
                if self.refresh_data_task.work_exception is not None:
                    log.debug(f"Refresh - update UI view - exception {self.refresh_data_task.work_exception} {external_event=}")
                    if not external_event:
                        main_panel.show_vdu_exception(self.refresh_data_task.work_exception, can_retry=False)
                if not values_only:
                    if len(self.detected_vdu_list) == 0 or self.detected_vdu_list != self.previously_detected_vdu_list or (
                            external_event and False):
                        log.info(f"Reconfiguring: detected={self.detected_vdu_list} previously={self.previously_detected_vdu_list}")
                        self.configure_application(check_schedule=False)  # May cause a further refresh?
                        self.previously_detected_vdu_list = self.detected_vdu_list
                    ScheduleWorker.check()  # immediately active the currently applicable preset
                    if self.lux_auto_controller:
                        if LuxDialog.exists():
                            LuxDialog.get_instance().reconfigure()  # Incase the number of connected monitors has changed.
                        if self.lux_auto_controller.is_auto_enabled():
                            self.lux_auto_controller.adjust_brightness_now()
            finally:
                self.get_main_window().indicate_busy(False)

        if not gui_misc.is_running_in_gui_thread():  # TODO this appears to never be true - remove???
            log.debug(f"Re-invoke start_refresh() in GUI thread {external_event=}") if log.debug_enabled else None
            self.get_main_window().run_in_gui_thread(partial(self.start_refresh, external_event))
            return
        self.refresh_data_task = WorkerThread(task_body=_update_from_vdu, task_finished=_update_ui_view)
        self.refresh_data_task.start()
        sys_time.sleep(0.1)  # Sleep a bit to see if we acquire the application lock
        if not self.refresh_data_task.stop_requested:  # if the thread has already stopped, it never acquired the application_lock
            self.get_main_window().indicate_busy(True)  # Refresh has probably commenced, give the user some feedback

    def restore_preset(self, preset: Preset, finished_func: Callable[[BulkChangeWorker], None] | None = None,
                       immediately: bool = False, background_activity: bool = False, initialization_preset: bool = False) -> None:
        if initialization_preset:
            background_activity = True
            immediately = True
        elif self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED):
            immediately = True
        # Starts the restore, but it will complete in the worker thread
        if not gui_misc.is_running_in_gui_thread():  # Transfer this request into the GUI thread
            log.debug(f"restore_preset: '{preset.name}' transferring task to GUI thread") if log.debug_enabled else None
            self.get_main_window().run_in_gui_thread(partial(self.restore_preset, preset, finished_func,
                                                       immediately, background_activity, initialization_preset))
            return

        log.debug(f"restore_preset: '{preset.name}' try to obtain application_lock", trace=False) if log.debug_enabled else None
        with self.application_lock:  # The lock prevents a transition firing when the GUI/app is reconfiguring

            def _update_progress(worker_thread: BulkChangeWorker) -> None:
                preset.in_transition_step += 1
                self.get_main_window().show_preset_status(
                    tr("Transitioning to preset {0} (elapsed time {1} seconds)...").format(
                        preset.name, f"{worker_thread.total_elapsed_seconds:.2f}"))
                #self.transitioning_dummy_preset.update_progress() if self.transitioning_dummy_preset else None
                self.get_main_window().update_status_indicators(preset)

            def _restore_finished_callback(worker_thread: BulkChangeWorker) -> None:
                # self.transitioning_dummy_preset = None
                if worker_thread.work_exception is not None and not background_activity:  # if it's a GUI request, ask about retry
                    if self.get_main_window().get_main_panel().show_vdu_exception(worker_thread.work_exception, can_retry=True):
                        self.restore_preset(preset, finished_func=finished_func, immediately=immediately)  # Try again, new thread
                        return  # Don't do anything more, the new thread will take over from here
                preset.in_transition_step = 0
                self.get_main_window().indicate_busy(False)
                if not initialization_preset:
                    if self.get_main_window().tray is not None:
                        self.get_main_window().refresh_tray_menu()
                    if worker_thread.completed:
                        with open(CURRENT_PRESET_NAME_FILE, 'w', encoding="utf-8") as cps_file:
                            cps_file.write(preset.name)
                        self.get_main_window().update_status_indicators(preset)
                        if worker_thread.change_count != 0:
                            self.get_main_window().show_preset_status(tr("Restored {0} (elapsed time {1} seconds)").format(
                                preset.name, f"{worker_thread.total_elapsed_seconds:.2f}"))
                            if (self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED)
                                    and preset.get_transition_type() != PresetTransitionFlag.NONE):
                                log.warning(
                                    f"restore-preset: protect-nvram prevents '{preset.name}' from stepping, changes are immediate.")
                        else:
                            self.get_main_window().show_preset_status(tr("Already on Preset {} (no changes)").format(preset.name))
                        if df := preset.get_daylight_factor():
                            log.info(f"Daylight-Factor {df:.4f} read from Preset {preset.name}")
                            LuxMeterSemiAutoDevice.set_daylight_factor(df, persist=True)
                            LuxDialog.reconfigure_instance()
                    else:  # Interrupted or exception:
                        self.get_main_window().update_status_indicators()
                        self.get_main_window().show_preset_status(tr("Interrupted restoration of {}").format(preset.name))
                if finished_func is not None:
                    finished_func(worker_thread)

            log.debug(f"restore_preset: '{preset.name}' holding application_lock", trace=False) if log.debug_enabled else None
            if not immediately:
                self.get_main_window().show_preset_status(tr("Transitioning to preset {}").format(preset.name))
                self.get_main_window().update_status_indicators(preset)  # TODO - create a transitioning indicator
            self.get_main_window().indicate_busy(True, lock_controls=immediately)
            preset.load()
            bulk_changer = BulkChangeWorker('RestorePreset', self, _update_progress, _restore_finished_callback,
                                            step_interval=0.0 if immediately else 5.0,
                                            ignore_others=initialization_preset, context=preset)
            for vdu_stable_id in self.get_vdu_stable_id_list():
                if vdu_stable_id in preset.preset_ini:
                    for vcp_capability in self.get_enabled_capabilities(vdu_stable_id):
                        property_name = vcp_capability.property_name()
                        if property_name in preset.preset_ini[vdu_stable_id]:
                            if vcp_capability.vcp_type == CONTINUOUS_TYPE:
                                final_value = preset.preset_ini.getint(vdu_stable_id, property_name)
                            else:
                                final_value = int(preset.preset_ini[vdu_stable_id][property_name], 16)
                            bulk_changer.add_item(BulkChangeItem(vdu_stable_id, vcp_capability.vcp_code, final_value,
                                                                 transition=vcp_capability.can_transition))
            self.preset_transition_workers.append(bulk_changer)
            log.debug(f"restore_preset: '{preset.name}' handover to WorkerThread") if log.debug_enabled else None
            bulk_changer.start()
            if initialization_preset:  # Don't allow anything else until it's finished
                bulk_changer.wait()
        log.debug(f"restore_preset: '{preset.name}' released application_lock") if log.debug_enabled else None

    def restore_vdu_initialization_presets(self):
        # Find presets that match the name of each VDU name+serial and restore them...
        for stable_id in self.vdu_controllers_map.keys():
            for preset in self.preset_controller.find_presets_map().values():
                preset_proper_name = proper_name(preset.name)
                if stable_id == preset_proper_name:
                    log.info(f"Found initialization-preset for {stable_id}")

                    def _restored_initialization_preset(worker: BulkChangeWorker) -> None:
                        if worker.work_exception is not None:
                            log.error(f"Error during restoration of '{preset.name}'")
                            self.status_message(tr("Error during restoration preset {}").format(preset.name), timeout=5)
                            return
                        log.info(f"Restored initialization-preset '{worker.context.name}'")
                        message = tr("Restored I-Preset {}").format(worker.context.name)
                        self.status_message(message, timeout=5)
                        self.get_main_window().splash_message_qtsignal.emit(message)
                        sys_time.sleep(1.0)  # Pause to give the message time to display - TODO find non-delaying solution
                        self.get_main_window().update_status_indicators()  # Refresh to restore other non-init preset icons

                    self.restore_preset(preset, finished_func=_restored_initialization_preset, initialization_preset=True)

    def schedule_create_timetable(self, start_of_day: datetime, location: GeoLocation) -> Dict[datetime, Preset]:
        log.debug(f"Create preset timetable for {start_of_day}") if log.debug_enabled else None
        timetable_for_day: Dict[datetime, Preset] = {}  # Create a timetable for the entire day from 00:00:00 to 23:59:59
        time_elevation_map = create_elevation_map(start_of_day, latitude=location.latitude, longitude=location.longitude)
        for preset in self.preset_controller.find_presets_map().values():
            if elevation_key := preset.get_solar_elevation():
                if elevation_data := time_elevation_map.get(elevation_key):
                    preset.elevation_time_today = elevation_data.when
                    timetable_for_day[elevation_data.when] = preset
                else:
                    log.debug(f"schedule_create_timetable: Skipped preset '{preset.name}' {elevation_key} degrees,"
                              " the sun does not reach that elevation today.")
            if at_time := preset.get_at_time():
                timetable_for_day[at_time] = preset
        return {when: preset for when, preset in sorted(list(timetable_for_day.items()))}

    def schedule_presets(self) -> None:
        assert gui_misc.is_running_in_gui_thread()
        location = self.main_config.get_location()
        if location and self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log.debug("schedule_presets: try to obtain application_lock") if log.debug_enabled else None
            with self.application_lock:
                log.debug("schedule_presets: holding application_lock") if log.debug_enabled else None
                ScheduleWorker.dequeue_all(SchedulerJobType.RESTORE_PRESET)
                start_of_today = zoned_now(rounded_to_minute=True).replace(hour=0, minute=0)
                timetable_for_today = self.schedule_create_timetable(start_of_today, location)
                if len(timetable_for_today) > 0:  # Use the timetable to schedule jobs
                    now = zoned_now()
                    if future_presets := [(when, preset) for when, preset in timetable_for_today.items() if when > now]:
                        for when, preset in future_presets:  # Schedule future part of day
                            preset.schedule(when, self.activate_scheduled_preset_in_gui, self.skip_scheduled_preset)
                    # Schedule the preset that might apply right now, either the first overdue, or last from yesterday
                    if overdue_presets := [(when, preset) for when, preset in timetable_for_today.items() if when <= now]:
                        when_overdue, most_recent_overdue_preset = overdue_presets[-1]  # first is the most recently applicable
                        if most_recent_overdue_preset.schedule_status != PresetScheduleStatus.SUCCEEDED:  # not already run
                            most_recent_overdue_preset.schedule(when_overdue, self.activate_scheduled_preset_in_gui, overdue=True)
                        for when, preset in overdue_presets[:-1]:  # The rest have been superseded (if not already succeeded)
                            if preset.schedule_status != PresetScheduleStatus.SUCCEEDED:  # not already run
                                preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
                                log.info(f"Skipped preset '{preset.name}', passed assigned-time (status={preset.schedule_status})")
                    else:  # Nothing overdue today, schedule the last from yesterday (assumed to be the last for today)
                        last_preset_yesterday = list(timetable_for_today.values())[-1]  # last for yesterday same as last for today
                        last_preset_yesterday.schedule(start_of_today, self.activate_scheduled_preset_in_gui, overdue=True)
                # set a timer to rerun this scheduler at the start of the next day.
                ScheduleWorker.dequeue_all(SchedulerJobType.SCHEDULE_PRESETS)
                tomorrow = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                # tomorrow = zoned_now().replace(second=0, microsecond=0) + timedelta(minutes=2) # testing
                daily_schedule_job = SchedulerJob(tomorrow, SchedulerJobType.SCHEDULE_PRESETS,
                                                  partial(self.get_main_window().run_in_gui_thread, self.schedule_presets))
                log.info(f"Will update schedule for Presets at {tomorrow} "
                         f"(in {round(daily_schedule_job.remaining_time() / 60)} minutes)")
            log.debug("schedule_presets: released application_lock") if log.debug_enabled else None
        else:
            log.info(f"Scheduling is disabled or no location ({location=})")
            ScheduleWorker.shutdown()
        PresetsDialog.reconfigure_instance()

    def schedule_alteration(self, preset: Preset) -> None:
        location = self.main_config.get_location()
        if location and self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log.debug("schedule_alteration: try to obtain application_lock") if log.debug_enabled else None
            with self.application_lock:
                log.debug("schedule_alteration: holding application_lock") if log.debug_enabled else None
                preset.remove_elevation_trigger(quietly=True)
                start_of_today = zoned_now(rounded_to_minute=True).replace(hour=0, minute=0)
                timetable_for_today = self.schedule_create_timetable(start_of_today, location)
                if when := next((t for t, p in timetable_for_today.items() if p == preset), None):
                    if when > zoned_now():  # if destined for the future, schedule it
                        preset.schedule(when, self.activate_scheduled_preset_in_gui, overdue=False)
            log.debug("schedule_alteration: released application_lock") if log.debug_enabled else None
        else:
            log.info(f"schedule_alteration: Scheduling is disabled or no location ({location=})")

    def activate_scheduled_preset_in_gui(self, preset):
        self.get_main_window().run_in_gui_thread(partial(self.activate_scheduled_preset, preset))

    def activate_scheduled_preset(self, preset: Preset, check_weather: bool = True, immediately: bool = False,
                                  activation_time: datetime | None = None) -> None:
        assert gui_misc.is_running_in_gui_thread()

        def _activation_feedback(msg: str):
            self.get_main_window().show_preset_status(f"{TIME_CLOCK_SYMBOL} " + tr("Preset {0} activating at {1}").format(
                preset.name, f"{activation_time:%H:%M}") + f" - {msg}")

        def _activation_finished(worker: BulkChangeWorker) -> None:
            preset_at_time = preset.get_at_time()
            assert preset.elevation_time_today is not None or preset_at_time is not None  # must be one or the other
            assert preset.scheduler_job is not None
            attempts = preset.scheduler_job.attempts
            if worker.work_exception is not None:
                too_close = zoned_now() + timedelta(seconds=60)  # retry if more than a minute before any others
                for other in self.preset_controller.find_presets_map().values():  # Skip retry if another is due soon
                    if (other.name != preset.name
                            and preset.elevation_time_today is not None and other.elevation_time_today is not None
                            and preset.elevation_time_today < other.elevation_time_today <= too_close):
                        log.info(f"Schedule restoration skipped '{preset.name}', too close to {other.name}")
                        if not off_schedule:
                            preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
                        _activation_feedback(tr("Skipped, superseded"))
                        return
                _activation_feedback(tr("Error, trying again in {} seconds").format(60))
                if attempts == 1:
                    log.warning(f"Error during restoration of '{preset.name}', retrying every {60} seconds.")
                preset.scheduler_job.requeue()  # retry - retain old schedule time to maintain proper schedule order.
                return
            if not off_schedule:
                preset.schedule_status = PresetScheduleStatus.SUCCEEDED
            self.get_main_window().update_status_indicators(preset)
            _activation_feedback(tr("Restored {}").format(preset.name))
            log.info(f"Restored preset '{preset.name}' on try {attempts}") if attempts > 1 else None

        if not self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log.info(f"Schedule is disabled - not activating preset '{preset.name}'")
            return
        if activation_time is None:
            activation_time = zoned_now()
        if preset.elevation_time_today is not None:
            off_schedule = activation_time < preset.elevation_time_today  # Too early, must be an off-schedule catchup from yesterday
        else:
            preset_at_time = preset.get_at_time()
            assert preset_at_time is not None   # Has to be because of the assertion on entry
            off_schedule = activation_time < preset_at_time
        if preset.is_weather_dependent() and check_weather and self.main_config.is_set(ConfOpt.WEATHER_ENABLED):
            if not self.is_weather_satisfactory(preset):
                if not off_schedule:
                    preset.schedule_status = PresetScheduleStatus.WEATHER_CANCELLATION
                message = tr("Preset {0} activation was cancelled due to weather at {1}").format(
                    preset.name, activation_time.isoformat(' ', 'seconds'))
                self.get_main_window().show_preset_status(message)
                return
        assert preset.scheduler_job is not None  # Given this is job activation, it has to have one
        if preset.scheduler_job.attempts == 1:
            log.info(f"Activating scheduled preset '{preset.name}' transition={immediately} {off_schedule=}")
        # Happens asynchronously in a thread
        self.restore_preset(preset, finished_func=_activation_finished,
                            immediately=immediately or PresetTransitionFlag.SCHEDULED not in preset.get_transition_type(),
                            background_activity=True)

    def skip_scheduled_preset(self, preset: Preset):
        assert gui_misc.is_running_in_gui_thread()
        preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
        self.get_main_window().update_status_indicators(preset)

    def is_weather_satisfactory(self, preset, use_cache: bool = False) -> bool:
        try:
            if not use_cache or self.weather_query is None:
                if location := self.main_config.get_location():
                    self.weather_query = weather_utils.WeatherQuery(location)
                    self.weather_query.run_query()
                    if not self.weather_query.proximity_ok:
                        log.error(f"Preset '{preset.name}' weather location is {self.weather_query.proximity_km} km from "
                                  f"Settings Location, check settings.")
                        weather_util.weather_bad_location_dialog(self.weather_query)
            if not preset.check_weather(self.weather_query):
                return False
        except ValueError as e:
            MBox(MIcon.Warning, msg=tr("Ignoring weather requirements, unable to query local weather: {}").format(str(e.args[0])),
                 info=e.args[1]).exec()
        return True

    def find_preset_by_name(self, preset_name: str) -> Preset | None:
        return self.preset_controller.find_presets_map().get(preset_name)

    def restore_named_preset(self, preset_name: str) -> None:
        if preset := self.find_preset_by_name(preset_name):
            # Transition immediately unless the Preset is required to ALWAYS transition.
            self.restore_preset(preset, immediately=PresetTransitionFlag.MENU not in preset.get_transition_type())

    def save_preset(self, preset: Preset) -> None:
        self.preset_controller.save_preset(preset)
        if self.get_main_window().app_context_menu.get_preset_menu_action(preset.name) is None:
            self.get_main_window().app_context_menu.insert_preset_menu_action(preset)
        self.get_main_window().update_status_indicators()
        preset.remove_elevation_trigger()
        self.schedule_alteration(preset)

    def save_preset_order(self, name_order: List[str]):
        self.preset_controller.save_order(name_order)
        self.refresh_preset_menu(reorder=True)

    def populate_ini_from_vdus(self, preset_ini: ConfIni, update_only: bool = False) -> None:
        for control_panel in self.get_main_window().get_main_panel().vdu_control_panels.values():
            vdu_section_name = control_panel.controller.vdu_stable_id
            if not preset_ini.has_section(vdu_section_name):
                preset_ini.add_section(vdu_section_name)
            for control in control_panel.vcp_controls:  # Fill out value for any options present in the preset_ini.
                if not update_only or preset_ini.has_option(vdu_section_name, control.vcp_capability.property_name()):
                    if control.current_value is not None:
                        text_val = control.get_current_text_value()
                        assert text_val is not None   # Given control.current_value has a value.
                        preset_ini[vdu_section_name][control.vcp_capability.property_name()] = text_val

    def delete_preset(self, preset: Preset) -> None:
        self.preset_controller.delete_preset(preset)
        self.get_main_window().app_context_menu.remove_preset_menu_action(preset.name)
        self.get_main_window().update_status_indicators()

    def refresh_preset_menu(self, reorder: bool = False):
        self.get_main_window().refresh_preset_menu(reorder=reorder)

    def which_preset_is_active(self) -> Preset | None:
        # See if we have a record of which was last active, and see if it still is active
        main_panel = self.get_main_window().get_main_panel()
        if CURRENT_PRESET_NAME_FILE.exists():
            with open(CURRENT_PRESET_NAME_FILE, encoding="utf-8") as cps_file:
                if preset_name := cps_file.read().strip():
                    preset = self.preset_controller.find_presets_map().get(preset_name)  # will be None if it has been deleted
                    if preset is not None and main_panel.is_preset_active(preset):
                        return preset
        # Guess by testing each possible preset against the current VDU settings
        for preset in self.preset_controller.find_presets_map().values():
            if main_panel.is_preset_active(preset):
                return preset
        return None

    def find_presets_map(self) -> Dict[str, Preset]:
        return self.preset_controller.find_presets_map()

    def get_lux_auto_controller(self) -> LuxAutoController:
        assert self.lux_auto_controller is not None
        return self.lux_auto_controller

    def get_vdu_stable_id_list(self) -> List[VduStableId]:
        return [stable_id for stable_id, vdu_controller in self.vdu_controllers_map.items() if not vdu_controller.ignore_vdu]

    def get_vdu_values(self, vdu_stable_id: VduStableId, vcp_codes: List[int] | None) -> List[Tuple[int, VcpValue]]:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            if not vcp_codes:
                vcp_codes = [capability.vcp_code for capability in controller.enabled_capabilities]
            return [(code, value) for code, value in zip(vcp_codes, controller.get_vcp_values(vcp_codes))]
        return []

    def get_enabled_capabilities(self, vdu_stable_id: VduStableId) -> List[VcpCapability]:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.enabled_capabilities
        return []

    def get_range(self, vdu_stable_id: VduStableId, vcp_code: int,
                  fallback: Tuple[int, int] | None = None) -> Tuple[int, int] | None:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.get_range_restrictions(vcp_code, fallback)
        log.error(f"get_range: No controller for {vdu_stable_id}")
        return fallback

    def get_value(self, vdu_stable_id, vcp_code) -> int:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            value = controller.get_vcp_values([vcp_code])
            if len(value) == 1:  # This could probably be an assertion
                return value[0].current
        log.error(f"get_value: No controller for {vdu_stable_id}")
        return 0

    def set_value(self, vdu_stable_id: VduStableId, vcp_code: int, value: int, origin: VcpOrigin = VcpOrigin.NORMAL):
        if panel := self.get_main_window().get_main_panel().vdu_control_panels.get(vdu_stable_id):
            if control := panel.get_control(vcp_code):
                control.set_value(value, origin)  # Apply to physical VDU
                return
        log.error(f"set_value: No controller for {vdu_stable_id=} {vcp_code=:#02x}")

    def is_vcp_code_enabled(self, vdu_stable_id, vcp_code: int) -> bool:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            for capability in controller.enabled_capabilities:
                if capability.vcp_code == vcp_code:
                    return True
        return False

    def update_window_status_indicators(self, preset: Preset | None = None):
        if not gui_misc.is_running_in_gui_thread():
            self.get_main_window().run_in_gui_thread(partial(self.get_main_window().update_status_indicators, preset))

    def get_vdu_preferred_name(self, vdu_stable_id: VduStableId) -> str:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.get_vdu_preferred_name()
        log.error(f"get_vdu_description: No controller for {vdu_stable_id}")
        return vdu_stable_id

    def busy_doing(self) -> str | None:
        return tr("Preset editing") if PresetsDialog.is_instance_editing() else None

    def find_vdu_config_files(self) -> List[Path]:
        found = []
        for conf_file in [f for f in sorted(CONFIG_DIR_PATH.glob('*_*_*.conf')) if f.is_file()]:
            conf = ConfIni()
            conf.read(conf_file.as_posix())
            if (conf.has_section(ConfOpt.CAPABILITIES_OVERRIDE.conf_section) and
                    conf.get(ConfOpt.CAPABILITIES_OVERRIDE.conf_section, ConfOpt.CAPABILITIES_OVERRIDE.conf_name)):
                found.append(conf_file)   # Seems to be sane
        log.debug(f"find_vdu_config_files {found}")
        return found

    def status_message(self, message: str, timeout: int, destination: MsgDestination = MsgDestination.DEFAULT):
        self.get_main_window().status_message(message, timeout, destination)

    def restart_application(self, reason: str):
        # Force a restart of the application.  Some settings changes need this (for example, run in the system tray).
        MBox(MIcon.Warning, msg=reason, info=tr('When this message is dismissed, vdu_controls will restart.')).exec()
        self.get_main_window().app_save_window_state()
        QCoreApplication.exit(EXIT_CODE_FOR_RESTART)

    def replace_toolbar(self, main_toolbar):
        target_window = self.get_main_window()
        for old_toolbar in target_window.findChildren(QToolBar):  # Make sure there is only one toolbar
            target_window.removeToolBar(old_toolbar)
            old_toolbar.deleteLater()
        at_top = self.main_config.is_set(ConfOpt.TOOLBAR_AT_TOP)
        toolbar_area = Qt.ToolBarArea.TopToolBarArea if at_top else Qt.ToolBarArea.BottomToolBarArea
        target_window.addToolBar(toolbar_area, main_toolbar)


class VduAppWindow(QMainWindow):
    splash_message_qtsignal = pyqtSignal(str)
    _run_in_gui_thread_qtsignal = pyqtSignal(object)

    def __init__(self, main_config: VduControlsConfig, main_controller: VduAppController) -> None:
        super().__init__()
        app_instance = get_app_instance()
        if os.getenv('VDU_CONTROLS_DEBUG_LAYOUT', default='no') == 'yes':
            app_instance.setStyleSheet("QWidget { border: 1px solid red; margin: 1px; padding: 1px; }")
        #set_gui_thread(app.thread())
        self.main_controller: VduAppController = main_controller
        self.setObjectName('main_window')
        self.qt_version_key = self.objectName() + "_qt_version"
        self.qt_geometry_key = self.objectName() + "_geometry"
        self.qt_state_key = self.objectName() + "_window_state"
        self.qt_settings = QSettings('vdu_controls.qt.state', 'vdu_controls')
        self.main_panel: VduControlsMainPanel | None = None
        self.scroll_area: QScrollArea | None = None
        self.main_config = main_config
        self.hide_shortcuts = True
        self.initial_theme_is_dark = is_dark_theme()
        log.info(f"Started with dark theme: {self.initial_theme_is_dark}")

        def _run_in_gui(task: Callable):
            log.debug(f"Running task in gui thread {repr(task)}") if log.debug_enabled else None
            task()  # Was using a partial, but it silently failed when task was a method with only self and no other arguments.

        self._run_in_gui_thread_qtsignal.connect(_run_in_gui)

        if log.debug_enabled:
            for screen in app_instance.screens():
                log.info("Screen", screen.name())

        menu_callables = {
            FixedItemKey.CONTROL_PANEL: partial(self.show_main_window, True),
            FixedItemKey.PRESETS: self.main_controller.show_presets_dialog,  # Gnome tray doesn't provide a way to bring up the main app.
            FixedItemKey.GREY_SCALE: GreyScaleDialog,
            FixedItemKey.SETTINGS_DIALOG: self.main_controller.edit_config,
            FixedItemKey.REFRESH: self.main_controller.start_refresh,
            FixedItemKey.ABOUT_DIALOG: partial(AboutDialog.show_dialog, self.main_controller),
            FixedItemKey.HELP: HelpDialog.show_dialog,
            FixedItemKey.QUIT: self.quit_app,}

        if main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED):
            menu_callables.update({
                FixedItemKey.LUX_AUTO_MANUAL: self.main_controller.lux_auto_action,
                FixedItemKey.LIGHTING_CHECK_NOW: self.main_controller.lux_check_action,
                FixedItemKey.LIGHT_METERING_DIALOG: partial(LuxDialog.show_dialog, self.main_controller),
            })

        self.app_context_menu = ContextMenu(app_controller=main_controller, fixed_item_callables=menu_callables,
                                            hide_shortcuts=self.hide_shortcuts, parent=self)

        # Don't do this - it creates a titlebar inside the application
        #self.app_context_menu.setTitle("VDU Controls ")  # Populate titlebar-menu (if it's enabled for Plasma Titlebars).
        #self.menuBar().addMenu(self.app_context_menu)    # TODO - make a proper menu - this will be a submenu.

        splash_pixmap = get_splash_pixmap()
        splash = QSplashScreen(
            splash_pixmap.scaledToWidth(desktop_font_height(scaled=26)).scaledToHeight(desktop_font_height(scaled=13)),
            Qt.WindowType.WindowStaysOnTopHint) if main_config.is_set(ConfOpt.SPLASH_SCREEN_ENABLED) else None
        if splash is not None:
            splash.show()
            splash.raise_()  # Attempt to force it to the top with raise and activate
            splash.activateWindow()
            QApplication.processEvents()
        self.app_icon: QIcon | None = None
        self.tray_icon: QIcon | None = None
        self.initialise_app_icon(splash_pixmap)

        def f10_func():
            self.app_context_menu.exec(QCursor.pos())

        f10_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F10), self)  # New Qt standard shortcut for context menu.
        f10_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        f10_shortcut.activated.connect(f10_func)

        self.tray = None
        if main_config.is_set(ConfOpt.SYSTEM_TRAY_ENABLED):
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log.warning("no system tray, waiting to see if one becomes available.")
                for _ in range(0, SYSTEM_TRAY_WAIT_SECONDS):
                    if QSystemTrayIcon.isSystemTrayAvailable():
                        break
                    sys_time.sleep(0.25)  # TODO - at least use a constant
            if QSystemTrayIcon.isSystemTrayAvailable():
                log.info("Using system tray.")
                app_instance.setQuitOnLastWindowClosed(False)  # This next call appears to be automatic on KDE, but not on gnome.
                self.tray = QSystemTrayIcon(parent=self)
                self.tray.setContextMenu(self.app_context_menu)
            else:
                log.error("no system tray - cannot run in system tray.")

        self.app_name = APPNAME
        app_instance.setApplicationDisplayName(self.app_name)
        if QT5_USE_HIGH_DPI_PIXMAPS:
            app_instance.setAttribute(QT5_USE_HIGH_DPI_PIXMAPS)  # Make sure all icons use HiDPI - toolbars don't by default, so force it.

        def _splash_message_action(message) -> None:
            if splash is not None:
                log.info(f"splash_message: {repr(message)}")
                splash.showMessage(f"\n\n{APPNAME} {VDU_CONTROLS_VERSION}\n{message}",
                                   Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                QApplication.processEvents()

        self.splash_message_qtsignal.connect(_splash_message_action)
        self.splash_message_qtsignal.emit(tr('Looking for DDC monitors...'))

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.main_controller.configure_application(self)

        self.inactive_pause_millis = int(os.environ.get('VDU_CONTROLS_INACTIVE_PAUSE_MILLIS', default='1200'))
        self.active_event_count = 0
        app_instance.applicationStateChanged.connect(self.on_application_state_changed)
        self.installEventFilter(self)

        if self.tray is not None:
            self.hide()
            self.tray.activated.connect(partial(self.show_main_window, True))
            self.tray.show()
        else:
            self.show_main_window()

        if splash is not None:
            splash.finish(self)
            splash.deleteLater()
            splash = None

        if main_config.file_path is None or main_config.ini_content.get_version() < VDU_CONTROLS_VERSION_TUPLE:  # New version...
            release_notes()
            main_config.write_file(ConfIni.get_path('vdu_controls'), overwrite=True)  # Stops release notes from being repeated.


    def is_inactive(self):
        if get_app_instance().applicationState() != Qt.ApplicationState.ApplicationInactive:
            return False
        for top_level_widget in QApplication.topLevelWidgets():  # Check if any dialogs are active
            if isinstance(top_level_widget, DialogSingletonMixin) or isinstance(top_level_widget, GreyScaleDialog):
                if top_level_widget.isVisible():
                    return False  # A dialog is showing - definitely active
        return True  # inactive and no dialogs are active

    def on_application_state_changed(self, _: Qt.ApplicationState):
        if self.main_config.is_set(ConfOpt.HIDE_ON_FOCUS_OUT):
            if self.is_inactive():
                # The user may be using the title-bar or window-edges to move/resize the window. Monitor for the lack of
                # move/resize events, treat that as a real focus out.  This is needed for gnome and xfce.
                self.active_event_count = 0  # Count the following move/resize events as evidence of titlebar edge-grab activity.

                def _hide_func():
                    if self.active_event_count == 0 and self.is_inactive():  # No moving/resizing activity and is_inactive().
                        self.hide() if self.tray else self.showMinimized()  # Probably safe to hide now

                QTimer.singleShot(self.inactive_pause_millis, _hide_func)  # wait N ms and see if any move/resize events occur.

    def eventFilter(self, target: QObject | None, event: QEvent | None) -> bool:
        # log.info(f"eventFilter {event.__class__.__name__} {event.type()}")
        if event and event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                      QEvent.Type.WindowActivate):  # Still active if being moved or resized
            self.active_event_count += 1
        return super().eventFilter(target, event)

    def show_main_window(self, toggle: bool = False) -> None:
        if toggle and self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()  # Attempt to force it to the top with raise and activate
            self.activateWindow()

    def show(self):
        if not self.app_restore_window_state():  # No previous state or invalid
            if self.main_config.is_set(ConfOpt.SMART_WINDOW):
                self.adjustSize()
                self.app_decide_window_position()  # decide initial position relative to cursor
                self.app_save_window_state()
        super().show()

    def hide(self):
        if self.isVisible():  # Only save position if really on screen
            self.app_save_window_state()
        super().hide()

    def quit_app(self) -> None:
        self.app_save_window_state()
        get_app_instance().quit()
        sys.exit(0)  # Just in case self.app.quit() errors

    def initialise_app_icon(self, splash_pixmap: QPixmap | None = None):
        self.app_icon = QIcon()
        self.app_icon.addPixmap(get_splash_pixmap() if splash_pixmap is None else splash_pixmap)
        tray_theme_type = self.get_tray_theme_type()
        if CUSTOM_TRAY_ICON_FILE.exists() and os.access(CUSTOM_TRAY_ICON_FILE.as_posix(), os.R_OK):
            log.info(f"Loading custom app_icon: {CUSTOM_TRAY_ICON_FILE} {tray_theme_type=}")
            self.tray_icon = create_icon_from_path(CUSTOM_TRAY_ICON_FILE, tray_theme_type)
        elif tray_theme_type in (ThemeType.MONOCHROME_LIGHT, ThemeType.MONOCHROME_DARK):  # Special tray monochrome version
            log.info(f"Using monochrome app_icon: {tray_theme_type=}")
            self.tray_icon = create_icon_from_svg_bytes(svg.TRAY_MONOCHROME_ICON_SVG, tray_theme_type)
        else:  # non-themed color icon based on the splash screen image
            self.tray_icon = create_icon_from_svg_bytes(svg.TRAY_COLOR_ICON_SVG, tray_theme_type)

    def create_main_control_panel(self) -> None:
        # Call on initialization and whenever the number of connected VDUs changes.
        if self.main_panel is not None:
            self.main_panel.deleteLater()
            self.main_panel = None
        if self.scroll_area is not None:
            self.scroll_area.deleteLater()
            self.scroll_area = None
        self.main_panel = VduControlsMainPanel()
        self.main_controller.initialize_vdu_controllers()
        refresh_button = ToolButton(svg.REFRESH_ICON_SVG, tr("Refresh settings from monitors"))
        refresh_button.pressed.connect(self.main_controller.start_refresh)
        tool_buttons = [refresh_button]
        extra_controls = []
        if self.main_controller.lux_auto_controller is not None:
            self.main_controller.lux_auto_controller.lux_config.load()  # may have changed
            if lux_auto_button := self.main_controller.lux_auto_controller.create_tool_button():
                lux_auto_button.pressed.connect(self.main_controller.lux_auto_action)
                tool_buttons.append(lux_auto_button)
            if lux_check_button := self.main_controller.lux_auto_controller.create_lighting_check_button():
                lux_check_button.pressed.connect(self.main_controller.lux_check_action)
                tool_buttons.append(lux_check_button)
            if lux_ambient_slider := self.main_controller.lux_auto_controller.create_manual_input_control():
                extra_controls.append(lux_ambient_slider)
                lux_ambient_slider.status_icon_changed_qtsignal.connect(self.update_status_indicators)
        self.refresh_preset_menu()
        self.main_panel.initialise_control_panels(self.main_controller, self.app_context_menu, self.main_config,
                                                  tool_buttons, extra_controls, self.splash_message_qtsignal)
        # Wire-up after successful init to avoid deadlocks
        self.main_panel.vdu_vcp_changed_qtsignal.connect(self.respond_to_changes_handler)
        self.indicate_busy(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.main_panel)
        self.setCentralWidget(self.scroll_area)
        my_screen = self.screen()
        assert my_screen is not None
        available_height = my_screen.availableGeometry().height() - dpx(100)  # Minus allowance for panel/tray
        hint_height = self.main_panel.sizeHint().height()  # The hint is the actual required layout space
        hint_width = self.main_panel.sizeHint().width()
        log.debug(f"create_main_control_panel: {hint_height=} {available_height=} {self.minimumHeight()=}")
        if hint_height > available_height:
            log.debug(f"Main panel too high, adding scroll-area {hint_height=} {available_height=}") if log.debug_enabled else None
            self.setMaximumHeight(available_height)
            self.setMinimumWidth(hint_width + dpx(10))  # Allow extra space for disappearing scrollbars
        else:  # Don't mess with the size unnecessarily - let the user determine it?
            number_of_vdus = len(self.main_controller.get_vdu_stable_id_list())
            self.setMinimumHeight(hint_height + dpx(15) * (number_of_vdus + 1))
            if hint_height != self.height():
                self.setMinimumWidth(self.width())
                self.adjustSize()
            self.setMinimumWidth(hint_width + dpx(10))

        self.splash_message_qtsignal.emit(tr("Checking Presets"))

    def get_main_panel(self) -> VduControlsMainPanel:
        assert self.main_panel is not None
        return self.main_panel

    def indicate_busy(self, is_busy: bool, lock_controls: bool = True):
        if self.main_panel:
            self.main_panel.indicate_busy(is_busy, lock_controls)
        self.app_context_menu.indicate_busy(is_busy)

    def show_preset_status(self, message: str, timeout: int = 3000):
        PresetsDialog.show_status_message(message=message, timeout=timeout)
        self.status_message(message, timeout=timeout, destination=MsgDestination.DEFAULT)

    def get_tray_theme_type(self):  # Ugly because Qt has no way to access the tray theme
        theme = ThemeType.UNTHEMED  # Don't alter colors for overlay onto app icon in tray if unthemed
        if self.main_config.is_set(ConfOpt.MONOCHROME_TRAY_ENABLED):
            theme = ThemeType.MONOCHROME_DARK
        if self.main_config.is_set(ConfOpt.MONO_LIGHT_TRAY_ENABLED):
            theme = ThemeType.MONOCHROME_LIGHT
        if theme != ThemeType.UNTHEMED:
            theme_has_flipped = self.initial_theme_is_dark != is_dark_theme()
            if theme_has_flipped and self.main_config.is_set(ConfOpt.TRAY_FOLLOWS_THEME):
                log.info(f"Option {ConfOpt.TRAY_FOLLOWS_THEME.conf_id} is set: Desktop theme flipped - flipping tray theme")
                theme = ThemeType.MONOCHROME_LIGHT if theme == ThemeType.MONOCHROME_DARK else ThemeType.MONOCHROME_DARK
        return theme

    def update_status_indicators(self, preset: Preset | None = None, palette_change: bool = False) -> None:
        assert gui_misc.is_running_in_gui_thread()  # Boilerplate in case this is called from the wrong thread.
        if self.main_panel is None:  # On deepin 23, events can trigger this method before initialization is complete
            return
        title = self.app_name
        tray_embedded_icon = led1_color = led2_color = None
        if preset is None:  # Detects matching Preset based on current VDU control settings
            preset = self.main_controller.which_preset_is_active()
        if preset is None:  # Clears the indicators
            self.get_main_panel().show_active_preset(None)
            self.app_context_menu.indicate_preset_active(None)
            PresetsDialog.instance_indicate_active_preset(None)
        else:  # Set indicators to specific preset
            self.get_main_panel().show_active_preset(preset)
            self.app_context_menu.indicate_preset_active(preset)
            PresetsDialog.instance_indicate_active_preset(preset)
            title = f"{preset.get_title_name()} {PRESET_APP_SEPARATOR_SYMBOL} {title}"
            tray_embedded_icon = preset.create_icon(self.get_tray_theme_type())
            led1_color = svg.PRESET_TRANSITIONING_LED_QCOLOR if preset.in_transition_step > 0 else None  # TODO transitioning indicator
        if self.main_controller.lux_auto_controller is not None:
            if self.main_controller.lux_auto_controller.is_auto_enabled():
                title = f"{tr('Auto')}/{title}"
                led2_color = svg.AUTO_LUX_LED_QCOLOR
            menu_lux_icon = create_icon_from_svg_bytes(
                self.main_controller.lux_auto_controller.current_auto_svg())  # NB cache involved
            self.app_context_menu.update_lux_auto_icon(menu_lux_icon)  # Won't actually update if it hasn't changed
            if tray_embedded_icon is None and self.main_config.is_set(ConfOpt.LUX_TRAY_ICON):
                if zone := self.main_controller.lux_auto_controller.get_lux_zone():
                    tray_embedded_icon = create_icon_from_svg_bytes(zone.icon_svg, self.get_tray_theme_type())
                    title = title + '\n' + tr("Lighting: {}").format(zone.name.lower())

        if self.windowTitle() != title:  # Don't change if not needed - prevent flickering.
            self.setWindowTitle(title)
            assert self.app_icon is not None  # Should be initialized by now
            get_app_instance().setWindowIcon(
                create_decorated_app_icon(self.app_icon, tray_embedded_icon, led1_color, led2_color))
        if self.tray:
            self.tray.setToolTip(title)
            assert self.tray_icon is not None   # Should be initialized by now
            self.tray.setIcon(create_decorated_app_icon(self.tray_icon, tray_embedded_icon, led1_color, led2_color))
        if palette_change or preset is not None:
            self.refresh_preset_menu(palette_change=palette_change)

    def respond_to_changes_handler(self, vdu_stable_id: VduStableId, vcp_code: int, value: int, origin: VcpOrigin,
                                   causes_config_change: bool) -> None:
        # Update UI secondary displays
        AboutDialog.refresh()
        for panel in self.get_main_panel().vdu_control_panels.values():
            panel.update_stats()
        if causes_config_change and origin == VcpOrigin.NORMAL:  # only respond if this is an internally initiated change
            log.info(f"Must reconfigure due to change to: {vdu_stable_id=} {vcp_code=:#02x} {value=} {origin}")
            self.main_controller.configure_application()  # Special case, such as a power control causing the VDU to go offline.
            return
        log.debug(f"respond_to_changes_handler {vdu_stable_id=} {vcp_code=:#02x} {value=} {origin}") if log.debug_enabled else None
        if origin != VcpOrigin.TRANSIENT:  # Only want to indicate final status (not when just passing through a preset)
            self.update_status_indicators()
            if origin != VcpOrigin.EXTERNAL:
                self.status_message(SET_VCP_SYMBOL, timeout=500, destination=MsgDestination.DEFAULT)
        if self.main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) and self.main_controller.lux_auto_controller is not None:
            if vcp_code == BRIGHTNESS_VCP_CODE:
                LuxDialog.lux_dialog_show_brightness(vdu_stable_id, value)

    def refresh_tray_menu(self) -> None:
        assert gui_misc.is_running_in_gui_thread()
        self.app_context_menu.update()

    def closeEvent(self, event) -> None:
        self.app_save_window_state()

    def app_save_window_state(self) -> None:
        if self.isVisible():
            self.qt_settings.setValue(self.qt_version_key, QtCore.qVersion())
            log.debug(f"app_save_window_state: {self.pos()=} {self.geometry()=} {QtCore.qVersion()}") if log.debug_enabled else None
            self.qt_settings.setValue(self.qt_geometry_key, self.saveGeometry())
            self.qt_settings.setValue(self.qt_state_key, self.saveState())

    def app_restore_window_state(self) -> bool:
        try:
            log.debug(f"app_restore_window_state")
            if len(self.qt_settings.allKeys()) == 0:  # No previous state
                return False
            save_version_major = self.qt_settings.value(self.qt_version_key, '5').split('.', 1)[0]
            qcore_version = QtCore.qVersion()
            qt_version_major = qcore_version.split('.', 1)[0] if qcore_version is not None else '5'
            if save_version_major != qt_version_major:
                log.warning(
                    f"app_restore_window_state: restore: {save_version_major=} != {qt_version_major=}, this may cause window geometry glitches")
            if smart_window := self.main_config.is_set(ConfOpt.SMART_WINDOW, fallback=True):  # Restore pos and geometry
                if geometry := self.qt_settings.value(self.qt_geometry_key, None):
                    self.restoreGeometry(geometry)
                    log.debug(f"app_restore_window_state: restoring {self.pos()=} {self.geometry()=}") if log.debug_enabled else None
            if window_state := self.qt_settings.value(self.qt_state_key, None):
                self.restoreState(window_state)  # Restore component positions, such as toolbar location
                log.debug(f"app_restore_window_state: restoring internal layout state") if log.debug_enabled else None
            return smart_window
        finally:
            if self.main_panel and self.main_panel.main_toolbar:
                self.main_panel.main_toolbar.setVisible(True)   # just in case it was hidden accidentally

    def app_decide_window_position(self):
        # Guess a window position near the tray. Use the mouse/cursor-pos as a guess to where the
        # system tray is.  Under Linux Qt the position of the tray icon is reported as 0,0, so we can't use that.
        cursor_x, cursor_y = QCursor.pos().x(), QCursor.pos().y()
        my_geometry = self.geometry()
        my_screen = self.screen()
        assert my_geometry is not None and my_screen is not None
        app_width, app_height = my_geometry.width(), my_geometry.height()
        desktop_width, desktop_height = (my_screen.availableGeometry().width(),
                                         my_screen.availableGeometry().height())
        # The following calculations allow for the tray being on any edge of the desktop...
        margin = min(abs(desktop_height - cursor_y), abs(desktop_width - cursor_x), dpx(50)) + dpx(12) if self.tray else 0
        x = cursor_x - app_width - margin if cursor_x > app_width else cursor_x + margin
        y = cursor_y - app_height - margin if cursor_y > app_height else cursor_y + margin
        log.debug(f"decide_window_position: {x=} {y=} {app_width=} {app_height=} {cursor_x=} {cursor_y=} {margin=}")
        self.setGeometry(x, y, app_width, app_height)

    def status_message(self, message: str, timeout: int, destination: MsgDestination):
        assert (self.main_panel is not None)
        if not gui_misc.is_running_in_gui_thread():
            self.run_in_gui_thread(partial(self.status_message, message, timeout, destination))
        else:
            if destination == MsgDestination.DEFAULT:
                self.main_panel.status_message(message, timeout)
                QApplication.processEvents()  # Force the message out straight way.

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            log.info("PaletteChange event: New style sheet in use, update icons")
            self.initialise_app_icon()
            self.update_status_indicators(palette_change=True)
            if self.main_panel is not None and self.main_panel.main_toolbar is not None:
                self.main_panel.main_toolbar.refresh_buttons()
        return super().event(event)

    def refresh_preset_menu(self, palette_change: bool = False, reorder: bool = False):
        self.app_context_menu.refresh_preset_menu(palette_change=palette_change, reorder=reorder)

    def show_no_controllers_error_dialog(self, ddcutil_problem: Exception | None):
        log.error("No controllable monitors found.")
        if ddcutil_problem is None:
            problem_text = "No exceptions, but no monitors anyway."
        elif isinstance(ddcutil_problem, subprocess.CalledProcessError):
            problem_text = ddcutil_problem.stderr.decode('utf-8', errors='surrogateescape') + '\n' + str(ddcutil_problem)
        else:
            problem_text = str(ddcutil_problem)

        log.error(f"Most recent error: {problem_text}".encode("unicode_escape").decode("utf-8"))
        MBox(MIcon.Critical, msg=tr('No controllable monitors found.'),
             info=tr("Is ddcutil or ddcutil-service installed and working?") + "\n\n" +
                  tr("Most recent error: {}").format(problem_text) + "\n" + '_' * 80).exec()

    def ask_for_vdu_controller_remedy(self, vdu_number: str, model_name: str, vdu_serial: str):
        msg = tr('Failed to obtain capabilities for monitor {0} {1} {2}.').format(vdu_number, model_name, vdu_serial)
        info = tr('Cannot automatically configure this monitor.'
                  '\n You can choose to:'
                  '\n 1: Retry obtaining the capabilities.'
                  '\n 2: Temporarily ignore this monitor.'
                  '\n 3: Apply standard brightness and contrast controls.'
                  '\n 4: Permanently discard this monitor from use with vdu_controls.'
                  '\n\nPossibly just a timing error, maybe a retry will work\n(see Settings: sleep multiplier)\n\n')
        choice = MBox(MIcon.Critical, msg=msg, info=info, buttons=MBtn.Discard | MBtn.Ignore | MBtn.Apply | MBtn.Retry).exec()
        if choice == MBtn.Discard:
            MBox(MIcon.Information, msg=tr('Discarding {} monitor.').format(model_name),
                 info=tr('Remove "{0}" from {1} capabilities override to reverse this decision.').format(IGNORE_VDU_MARKER_STR,
                                                                                                       model_name)).exec()
            return VduController.DISCARD_VDU
        elif choice == MBtn.Ignore:
            MBox(MIcon.Information, msg=tr('Ignoring {} monitor for now.').format(model_name),
                 info=tr('Will retry when vdu_controls is next started')).exec()
            return VduController.IGNORE_VDU
        elif choice == MBtn.Apply:
            MBox(MIcon.Information, msg=tr('Assuming {} has brightness and contrast controls.').format(model_name),
                 info=tr('Wrote {0} config files to {1}.').format(model_name, CONFIG_DIR_PATH) +
                      tr('\nPlease check these files and edit or remove them if they '
                         'cause further issues.')).exec()
            return VduController.ASSUME_STANDARD_CONTROLS
        elif choice == MBtn.Retry:
            return VduController.NORMAL_VDU
        return VduController.IGNORE_VDU

    def run_in_gui_thread(self, task: Callable):
        self._run_in_gui_thread_qtsignal.emit(task)


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
    # This is possible because, contrary to the documentation, the low-level signal handler doesn't only set a flag
    # for the virtual machine, but it may also write a byte into the file descriptor set by set_wakeup_fd(). Python 2
    # writes a NUL byte, Python 3 writes the signal number.
    #
    # So by subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g.
    # QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler) is received
    # causing the signal handler to execute nearly instantaneously without the need for timers:
    # '''

    received_unix_signal_qtsignal = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(QtNetwork.QAbstractSocket.SocketType.UdpSocket, parent)
        self.old_fd = None
        self.wsock, self.rsock = socket.socketpair(type=socket.SOCK_DGRAM)  # Create a socket pair
        self.setSocketDescriptor(sip.voidptr(self.rsock.fileno()))  # Let Qt listen on the one end
        self.wsock.setblocking(False)  # And let Python write on the other end
        self.old_fd = signal.set_wakeup_fd(self.wsock.fileno())
        # First Python code executed gets any exception from the signal handler, so add a do-nothing handler first
        self.readyRead.connect(lambda: None)
        self.readyRead.connect(self._readSignal)  # Second handler does the real handling

    def __del__(self) -> None:
        if self.old_fd is not None and signal is not None and signal.set_wakeup_fd is not None:
            signal.set_wakeup_fd(self.old_fd)  # Restore any old handler on deletion

    def _readSignal(self) -> None:
        # Read the written byte. Note: readyRead is blocked from occurring again until readData()
        # is called, so call it, even if you don't need the value.
        data = self.readData(1)
        signal_number = int(data[0])
        log.info("SignalWakeupHandler", signal_number)
        self.received_unix_signal_qtsignal.emit(signal_number)  # Emit a Qt signal for convenience


class SingleInstanceServer(QObject):
    # Listens on a per-user QLocalServer socket so a second vdu_controls launch can ask the
    # running instance to surface its main window instead of starting a duplicate process.
    # Two startup channels routinely coexist on KDE (XDG autostart + ksmserver session-restore),
    # plus manual menu clicks; without this guard each becomes its own independent process.

    activate_requested = pyqtSignal()

    def __init__(self, server_name: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._server = QtNetwork.QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        if not self._server.listen(server_name):
            # listen() failed - typically a stale socket from a crashed prior run.  Remove and retry.
            # (A true race with a concurrent launch is handled by the caller's pre-check via
            # _activate_running_instance, which runs before constructing this server.)
            QtNetwork.QLocalServer.removeServer(server_name)
            if not self._server.listen(server_name):
                log.warning(f"Single-instance guard could not bind {server_name}: {self._server.errorString()}")

    def _on_new_connection(self) -> None:
        while self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            if sock is not None:
                sock.readAll()
                sock.disconnectFromServer()
        self.activate_requested.emit()


def _activate_running_instance(server_name: str, timeout_ms: int = 500) -> bool:
    # Try to contact a running vdu_controls and ask it to raise its main window.
    # Returns True if a peer accepted the request (caller should exit), False if no peer was reachable.
    sock = QtNetwork.QLocalSocket()
    sock.connectToServer(server_name)
    if not sock.waitForConnected(timeout_ms):
        return False
    sock.write(b"activate\n")
    sock.flush()
    sock.waitForBytesWritten(timeout_ms)
    sock.disconnectFromServer()
    return True


def get_app_instance() -> QApplication:
    app_instance = cast(QApplication, QApplication.instance())
    assert app_instance is not None
    return app_instance


def main() -> None:
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)  # Force UTF-8, just in case it isn't

    def signal_handler(x, y) -> None:
        log.info("Signal received", x, y)

    signal.signal(signal.SIGHUP, signal_handler)
    for i in range(PRESET_SIGNAL_MIN, PRESET_SIGNAL_MAX):
        signal.signal(i, signal_handler)

    sys.excepthook = exception_handler

    # This is supposed to set the locale for all categories to the user’s default setting.
    # This can error on some distros when the required language isn't installed, or if LANG
    # is set without also specifying the UTF-8 encoding, so LANG=da_DK might fail,
    # but LANG=da_DK.UTF-8 should work. For our purposes, failure is not important.
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        log.warning(f"Could not set the default locale - may not be an issue...", trace=True)

    main_config = VduControlsConfig('vdu_controls', main_config=True)
    default_config_path = ConfIni.get_path('vdu_controls')
    log.info("Looking for config file '" + default_config_path.as_posix() + "'")
    if Path.is_file(default_config_path) and os.access(default_config_path, os.R_OK):
        main_config.parse_file(default_config_path)

    if os.environ.get('XDG_SESSION_TYPE') != 'x11':  # If Wayland we can't do smart window placement - use XWayland
        if main_config.is_set(ConfOpt.SMART_WINDOW) and main_config.is_set(ConfOpt.SMART_USES_XWAYLAND):
            log.warning(f"{ConfOpt.SMART_WINDOW.conf_id}: Wayland disallows app window placement. Switching to XWayland.")
            force_xwayland()

    QGuiApplication.setDesktopFileName("vdu_controls")  # Wayland needs this set to find/use the app's desktop icon.
    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)
    assert app is not None
    app_thread = app.thread()
    assert app_thread is not None
    gui_misc.set_gui_thread(app_thread)
    assert gui_misc.is_running_in_gui_thread()
    log.info(f"{app.applicationName()=} {get_app_instance().applicationName()=}")
    global unix_signal_handler
    unix_signal_handler = SignalWakeupHandler(app)

    log.info(f"{APPNAME} {VDU_CONTROLS_VERSION} {sys.argv[0]}  ")
    log.info(f"python-locale: {locale.getlocale()} Qt-locale: {QLocale.system().name()}")
    log.info(f"desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')}; "
             f"session-type: {os.environ.get('XDG_SESSION_TYPE', default='unknown')}; "
             f"platform: {QApplication.platformName()}; Qt: {QtCore.qVersion()}")
    app_style = app.style()
    if app_style is not None:
        log.info(f"app-style: {app_style.objectName()} (detected a {'dark' if is_dark_theme() else 'light'} theme)")
    else:
        log.warning("app-style: unknown, may not be able to respond to theme changes")
    args = main_config.parse_global_args()
    log.info(f"Logging to {'syslog' if main_config.is_set(ConfOpt.SYSLOG_ENABLED) else 'stdout'}")
    log.set_syslog(main_config.is_set(ConfOpt.SYSLOG_ENABLED))
    log.set_debug(main_config.is_set(ConfOpt.DEBUG_ENABLED))
    if args.syslog:
        log.set_syslog(True)
    if args.debug:
        main_config.debug_dump()
    if args.create_config_files:
        main_config.write_file(default_config_path)
    if args.install:
        install_as_desktop_application()
        sys.exit()
    if args.uninstall:
        install_as_desktop_application(uninstall=True)
        sys.exit()
    if args.detailed_help:
        print(app_locale.load_docs_text(HELP_FILENAME))
        sys.exit()

    # Single-instance guard: if another vdu_controls is already running, ask it to surface its
    # main window and exit.  Placed after the one-shot CLI ops (--install, --uninstall,
    # --detailed-help) so those still work regardless.
    single_instance_only = main_config.is_set(ConfOpt.SINGLE_INSTANCE)
    log.info(f"{single_instance_only=}")
    if single_instance_only:
        single_instance_name = f"vdu_controls-{os.geteuid()}"
        if _activate_running_instance(single_instance_name):
            log.info(f"Another {APPNAME} instance is already running; activated it and exiting.")
            sys.exit(0)
        single_instance_server = SingleInstanceServer(single_instance_name, parent=app)

    if main_config.is_set(ConfOpt.TRANSLATIONS_ENABLED):
        initialise_locale_translations(app)
    else:
        log.info(f"Language translations disabled by setting: {ConfOpt.TRANSLATIONS_ENABLED.conf_id}")

    main_controller = VduAppController(main_config)
    assert gui_misc.is_running_in_gui_thread()
    main_window = VduAppWindow(main_config, main_controller)  # may need to assign this to a variable to prevent garbage collection?
    if single_instance_only:
        single_instance_server.activate_requested.connect(partial(main_window.show_main_window, False))

    if args.about:
        AboutDialog.show_dialog(main_controller)
    if args.create_config_files:
        main_controller.create_config_files()

    rc = app.exec()
    log.info(f"App exit {rc=} {'EXIT_CODE_FOR_RESTART' if rc == EXIT_CODE_FOR_RESTART else ''}")
    if rc == EXIT_CODE_FOR_RESTART:
        reverse_force_xwayland()
        rc = 0
        log.info(f"Trying to restart - this only works if {app.arguments()[0]} is executable and on your PATH): ", )
        restart_status = QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
        if not restart_status:
            MBox(MIcon.Critical, msg=tr("Restart of {} failed.  Please restart manually.").format(app.arguments()[0]),
                 info=tr("This is probably because {} is not executable or is not on your PATH.").format(app.arguments()[0]),
                 buttons=MBtn.Close).exec()
    sys.exit(rc)


if __name__ == '__main__':
    main()
