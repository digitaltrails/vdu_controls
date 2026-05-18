# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
from ast import literal_eval
from dataclasses import dataclass
from enum import Enum
from typing import List, TYPE_CHECKING

from vdu_controls.qt_imports import Qt, pyqtSignal

from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import MsgDestination
from vdu_controls.ddcutil_abstract import BRIGHTNESS_VCP_CODE

from vdu_controls.ddcutil_aggregator import VduStableId
from vdu_controls.app_locale import tr
import vdu_controls.logging as log
from vdu_controls.lux_ambient_slider import LuxZone, LuxAmbientSlider
from vdu_controls.lux_config import LuxConfig, LuxPoint
from vdu_controls.lux_dialog import LuxDialog
from vdu_controls.lux_meters import lux_create_device, LuxMeterDevice, LuxMeterSemiAutoDevice, LuxDeviceException
from vdu_controls.preset import PresetTransitionFlag
from vdu_controls.svg import AUTO_LUX_ON_SVG, LIGHTING_CHECK_SVG, AUTO_LUX_OFF_SVG, \
    LIGHTING_CHECK_OFF_SVG
from vdu_controls.unicode import TIMER_RUNNING_SYMBOL, SUN_SYMBOL, PROCESSING_LUX_SYMBOL, STEPPING_SYMBOL, ERROR_SYMBOL, \
    RAISED_HAND_SYMBOL, ALMOST_EQUAL_SYMBOL, SMOOTHING_SYMBOL
from vdu_controls.vdu_bulk_change import BulkChangeWorker, BulkChangeItem

from vdu_controls.vdu_exceptions import VduException
import vdu_controls.gui_misc as gui_misc
from vdu_controls.widgets import MBox, MIcon, ToolButton
from vdu_controls.work_scheduler import WorkerThread, thread_pid

if TYPE_CHECKING:
    from vdu_controls_application import VduAppController


class LuxSmooth:
    def __init__(self, n: int, alpha: float = 0.5) -> None:
        self.length: int = n
        self.input: List[float] = []
        self.output: List[float] = []
        self.alpha: float = alpha

    def smooth(self, v: float) -> int:  # A low pass filter
        # The smaller the alpha, the more each previous value affects the following value. Smaller alpha results => more smoothing.
        # https://stackoverflow.com/questions/4611599/smoothing-data-from-a-sensor
        # https://en.wikipedia.org/wiki/Low-pass_filter#Simple_infinite_impulse_response_filter
        if len(self.input) == self.length:
            self.input.pop(0)
            self.output.pop(0)
        self.input.append(v)
        self.output.append(v)  # extend to same length - value will be overwritten if there is more than one sample.
        for i in range(1, len(self.input)):
            self.output[i] = self.output[i - 1] + self.alpha * (self.input[i] - self.output[i - 1])
        return round(self.output[-1])


class LuxStepStatus(Enum):  # TODO unused?
    ENCOUNTERED_ERROR = -2
    UNEXPECTED_CHANGE = -1
    FINISHED = 0,
    MORE_TO_DO = 1,


@dataclass
class LuxToDo:
    vdu_sid: VduStableId
    brightness: int
    preset_name: str | None
    current_brightness: int


class LuxAutoWorker(WorkerThread):  # Why is this so complicated?

    _lux_dialog_message_qtsignal = pyqtSignal(str, int, MsgDestination)

    def __init__(self, auto_controller: LuxAutoController, single_shot: bool) -> None:
        super().__init__(task_body=self._adjust_for_lux, task_finished=self._adjust_for_lux_finished)
        self.single_shot = single_shot  # Called for an on-demand single time assessment with immediate effect.
        self.main_controller = auto_controller.main_controller
        self.adjust_now_requested = False
        lux_config = auto_controller.get_lux_config()
        log.info(f"LuxAuto: lux-meter.interval-minutes={lux_config.get_interval_minutes()} {single_shot=}")
        self.sleep_seconds = lux_config.get_interval_minutes() * 60
        self.consecutive_error_count = 0

        def _get_prop(prop: str, fallback: bool | int | float | str) -> bool | int | float:
            getters_by_type = {bool: lux_config.getboolean, int: lux_config.getint, float: lux_config.getfloat}
            value = getters_by_type[type(fallback)]('lux-meter', prop, fallback=fallback)
            log.info(f"LuxAuto: lux-meter.{prop}={value}")
            return value

        samples_per_minute = _get_prop('samples-per-minute', fallback=3)
        self.sampling_interval_seconds = 60 // samples_per_minute
        self.smoother = LuxSmooth(_get_prop('smoother-n', fallback=5), alpha=_get_prop('smoother-alpha', fallback=0.5))
        self.interpolation_enabled = _get_prop('interpolate-brightness', fallback=True)
        self.sensitivity_percent = _get_prop('interpolation-sensitivity-percent', fallback=10)
        self.step_pause_millis = _get_prop('step-pause-millis', fallback=1000)
        self._lux_dialog_message_qtsignal.connect(LuxDialog.lux_dialog_message)
        self._lux_dialog_message_qtsignal.connect(self.main_controller.main_window.status_message)
        self.status_message(f"{TIMER_RUNNING_SYMBOL} 00:00", 0, MsgDestination.COUNTDOWN)

    def status_message(self, message: str, timeout: int = 0, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        self._lux_dialog_message_qtsignal.emit(message, timeout, destination)

    def _adjust_for_lux(self, _: WorkerThread) -> None:
        try:
            lux_auto_controller = self.main_controller.get_lux_auto_controller()
            # Give any previous thread a chance to exit, plus let the GUI and presets settle down
            self.doze(2) if not self.single_shot else None
            log.info(f"LuxAuto: monitoring commences {thread_pid()=}")
            assert lux_auto_controller is not None
            while not self.stop_requested:
                error_count = self.consecutive_error_count
                busy_main_controller = self.main_controller.busy_doing()
                if lux_meter := lux_auto_controller.lux_meter:
                    if (status := lux_meter.get_status())[0]:
                        if metered_lux := lux_meter.get_value():
                            if not busy_main_controller:
                                if to_do_list := self.assemble_required_work(lux_auto_controller, metered_lux,
                                                                             not lux_meter.has_manual_capability):
                                    self.do_work(to_do_list)
                    elif status[1]:
                        self.status_message(status[1], timeout=5000)
                    if self.single_shot:
                        break
                else:  # In-app config change - things are in a state of flux
                    log.error("Exiting, no lux meter available.")
                    break
                if error_count == self.consecutive_error_count:  # no change - must be OK now
                    log.debug("LuxAuto: clearing consecutive_error_count") if log.debug_enabled else None
                    self.consecutive_error_count = 0
                self.idle_sampling(lux_meter, busy_main_controller)  # Sleep and sample for rest of cycle
        finally:
            log.info(f"LuxAuto: exiting (stop_requested={self.stop_requested}) {thread_pid()=}")

    def assemble_required_work(self, lux_auto_controller: LuxAutoController, metered_lux: float, requires_smoothing) -> List[
        LuxToDo]:
        lux = self.smoother.smooth(metered_lux) if requires_smoothing else round(metered_lux)
        summary_text = self.lux_summary(metered_lux, lux)
        self.status_message(f"{SUN_SYMBOL} {summary_text} {PROCESSING_LUX_SYMBOL}", timeout=3000)
        to_do_list: List[LuxToDo] = []
        for vdu_sid in self.main_controller.get_vdu_stable_id_list():  # For each VDU, do one step of its profile
            if self.stop_requested:
                return []
            value_range = self.main_controller.get_range(vdu_sid, BRIGHTNESS_VCP_CODE, fallback=(0, 100))
            lux_profile = lux_auto_controller.get_lux_profile(vdu_sid, value_range)
            if to_do := self.determine_changes(vdu_sid, lux, lux_profile):
                to_do_list.append(to_do)
        self.assess_presets_collectively(to_do_list)
        return to_do_list

    def assess_presets_collectively(self, to_do_list: List[LuxToDo]) -> None:
        if to_do_list:  # See if all items are in agreement on whether a preset should be used
            for preset_name in [x.preset_name for x in to_do_list if x.preset_name is not None]:
                if preset := self.main_controller.find_preset_by_name(preset_name):
                    sids_present = set(self.main_controller.get_vdu_stable_id_list())
                    sids_present_and_in_preset = sids_present.intersection(set(preset.get_vdu_sids()))
                    items_with_this_preset = [x for x in to_do_list if x.preset_name == preset_name]
                    sids_of_items_with_this_preset = set([x.vdu_sid for x in items_with_this_preset])
                    log.debug(f"LuxAuto: {sids_present_and_in_preset=} {sids_of_items_with_this_preset=}")
                    if sids_present_and_in_preset == sids_of_items_with_this_preset:
                        log.debug(f"LuxAuto: applying Preset {preset_name}")
                        for item in items_with_this_preset:
                            if (preset_brightness := preset.get_brightness(item.vdu_sid)) > 0:
                                item.brightness = preset_brightness
                    else:
                        log.debug(f"LuxAuto: ignoring Preset {preset_name} doesn't match for all VDUs present.")
                        for item in items_with_this_preset:
                            item.preset_name = None
                else:
                    log.debug(f"LuxAuto: ignoring Preset {preset_name} no longer exists.")

    def do_work(self, to_do_list: List[LuxToDo]):
        to_do_preset_names = []
        bulk_changer = BulkChangeWorker('LuxAutoBulk', main_controller=self.main_controller,
                                        progress_callable=self._to_do_progress, finished_callable=self._to_do_finished,
                                        step_interval=self.step_pause_millis / 1000.0, context=to_do_preset_names)
        for to_do in to_do_list:
            if to_do.brightness != -1:
                bulk_change_item = BulkChangeItem(to_do.vdu_sid, BRIGHTNESS_VCP_CODE, to_do.brightness,
                                                  current_value=to_do.current_brightness,
                                                  transition=True)  # only transitions if protect-nvram is False.
                bulk_changer.add_item(bulk_change_item)
            if to_do.preset_name and to_do.preset_name not in to_do_preset_names:
                to_do_preset_names.append(to_do.preset_name)
        bulk_changer.run()  # Call run instead of start; run in this thread instead of a new thread.

    def _to_do_progress(self, _: BulkChangeWorker):
        self.status_message(f"{SUN_SYMBOL} {STEPPING_SYMBOL}")

    def _to_do_finished(self, worker: BulkChangeWorker):
        if worker.completed:
            if to_do_preset_names := worker.context:
                self.doze(0.5)  # Give the user a chance to read messages
                for preset_name in to_do_preset_names:  # if a point had a Preset attached, activate it now
                    # Restoring the Preset's non-brightness settings. Invoke now, so it will happen in this thread's sleep period.
                    if preset := self.main_controller.find_preset_by_name(preset_name):  # Check that it still exists
                        log.debug(f"LuxAuto: restoring Preset {preset.name=}") if log.debug_enabled else None
                        self.main_controller.restore_preset(
                            preset, immediately=PresetTransitionFlag.SCHEDULED not in preset.get_transition_type(),
                            background_activity=True)
                    else:
                        log.debug("LuxAuto: Preset {preset.name} no longer exists - ignoring") if log.debug_enabled else None
                        self.main_controller.update_window_status_indicators()
        else:
            log.debug("LuxAuto: bulk worker failed to complete.") if log.debug_enabled else None
            self.status_message(f"{SUN_SYMBOL} {ERROR_SYMBOL} {RAISED_HAND_SYMBOL}")
            self.consecutive_error_count += 1

    def _adjust_for_lux_finished(self, _: WorkerThread) -> None:
        log.debug("LuxAuto: worker finished") if log.debug_enabled else None
        if self.work_exception:
            log.error(f"LuxAuto: exited with exception={self.work_exception}")

    def idle_sampling(self, lux_meter: LuxMeterDevice, busy_main_controller: str | None):
        seconds = 2 if self.consecutive_error_count == 1 else self.sleep_seconds
        log.debug(f"LuxAuto: sleeping {seconds=}") if log.debug_enabled else None
        if busy_main_controller:
            self.status_message(
                tr("Task waiting for {} to finish.").format(busy_main_controller), timeout=0, destination=MsgDestination.DEFAULT)
        for second in range(seconds, -1, -1):
            if busy_main_controller and not self.main_controller.busy_doing():
                break  # the main controller is no longer busy
            if self.stop_requested or self.adjust_now_requested:  # Respond to stop requests while sleeping
                self.adjust_now_requested = False
                break
            if not lux_meter.has_manual_capability:  # Update the smoother every n seconds, but not at the start or end of the period.
                if (0 < second < self.sleep_seconds) and second % self.sampling_interval_seconds == 0:
                    if metered_lux := lux_meter.get_value():  # Update the smoothing while sleeping
                        self.status_message(
                            f"{SUN_SYMBOL} {self.lux_summary(metered_lux, self.smoother.smooth(metered_lux))}", timeout=3000)
            self.status_message(f"{TIMER_RUNNING_SYMBOL} {second // 60:02d}:{second % 60:02d}", 0, MsgDestination.COUNTDOWN)
            self.doze(1)

    def determine_changes(self, vdu_sid: VduStableId, smoothed_lux: int, lux_profile: List[LuxPoint]) -> LuxToDo | None:
        previous_normal_point = matched_point = lower_point = LuxPoint(0, 0)
        proposed_brightness = 0
        # Update/bind the current Preset values onto the LuxPoints and wrap with min and max values.
        for profile_point in [LuxPoint(0, 0), *lux_profile, LuxPoint(100000, 100)]:
            # Moving up the lux steps, seeking the step below smoothed_lux
            if smoothed_lux > profile_point.lux:  # Possible result, there may be something higher, keep going...
                # if profile_point.brightness is -1, this is a Preset that doesn't change the VDU's brightness control
                if profile_point.brightness >= 0:  # else use existing result_brightness
                    proposed_brightness = profile_point.brightness
                matched_point = profile_point
            else:  # Step is too high, if interpolating check against the following point, if not, the previous match is the result.
                if self.interpolation_enabled:  # Only interpolate if lux is not an exact match and next_point has a brightness
                    if smoothed_lux != matched_point.lux and profile_point.brightness >= 0:
                        # if profile_point.brightness is -1, this is a Preset that doesn't change the VDU's brightness control
                        lower_point = matched_point if matched_point.brightness >= 0 else previous_normal_point
                        proposed_brightness = self.interpolate_brightness(smoothed_lux, lower_point, profile_point)
                break
            if profile_point.brightness > 0:
                previous_normal_point = profile_point
        try:
            preset_name = self.assess_preset_proximity(proposed_brightness, lower_point, matched_point, profile_point)
            current_brightness = self.main_controller.get_value(vdu_sid, BRIGHTNESS_VCP_CODE)
            diff = proposed_brightness - current_brightness
            if self.interpolation_enabled and preset_name is None and abs(diff) < self.sensitivity_percent:
                log.info(f"LuxAuto: {smoothed_lux=} {vdu_sid=} {current_brightness=} {proposed_brightness=} ignored, too small")
                self.status_message(f"{SUN_SYMBOL} {proposed_brightness}% {ALMOST_EQUAL_SYMBOL} {current_brightness}% {vdu_sid}",
                                    timeout=5000)
                return None
            if log.debug_enabled:
                log.debug(f"LuxAuto: {smoothed_lux=} {vdu_sid=} {current_brightness=}% {proposed_brightness=}% {preset_name=}")
            return LuxToDo(vdu_sid, proposed_brightness, preset_name, current_brightness)
        except VduException as e:
            self.consecutive_error_count += 1
            log.debug(f"LuxAuto: {self.consecutive_error_count=} error getting brightness: {e}") if log.debug_enabled else None
        return None

    def interpolate_brightness(self, smoothed_lux: int, current_point: LuxPoint, next_point: LuxPoint) -> int:

        def _x_from_lux(lux: int) -> float:
            return (math.log10(lux) / math.log10(100000)) if lux > 0 else 0

        interpolated_brightness = float(current_point.brightness)
        x_smoothed = _x_from_lux(smoothed_lux)
        x_current_point = _x_from_lux(current_point.lux)
        x_next_point = _x_from_lux(next_point.lux)
        x_diff = x_next_point - x_current_point
        if not math.isclose(x_diff, 0.0):
            interpolated_brightness += (next_point.brightness - current_point.brightness) * (
                    x_smoothed - x_current_point) / x_diff
        return round(interpolated_brightness)

    def assess_preset_proximity(self, proposed_brightness: float,
                                previous_normal_point: LuxPoint, matched_point: LuxPoint, next_point: LuxPoint) -> str | None:
        # Brightness is a better indicator of nearness for deciding whether to activate a preset
        ordered = sorted([(abs(proposed_brightness - matched_point.brightness), matched_point),
                          (abs(proposed_brightness - previous_normal_point.brightness), previous_normal_point),
                          (abs(proposed_brightness - next_point.brightness), next_point)], key=lambda x: x[0])
        for diff, item in ordered:
            if diff < self.sensitivity_percent and (pick := item.preset_name):
                log.debug(f"LuxAuto: assess_preset_proximity {pick=}") if log.debug_enabled else None
                return pick
        return None

    def lux_summary(self, metered_lux: float, smoothed_lux: int) -> str:
        lux_int = round(metered_lux)  # 256 bit char in lux_summary_text can cause issues if stdout not utf8 (force utf8 for stdout)
        return f"{lux_int} {SMOOTHING_SYMBOL} {smoothed_lux} lux {tr('(smoothed)')}" if lux_int != smoothed_lux else f"{lux_int} lux"

    def stop(self) -> None:
        super().stop()
        assert gui_misc.is_running_in_gui_thread()
        self._lux_dialog_message_qtsignal.disconnect()
        log.info("LuxAuto: stopped on request")


class LuxAutoController:

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.main_controller = main_controller
        self.lux_config = LuxConfig()
        self.lux_config.load()
        self.lux_meter: LuxMeterDevice | None = None
        self.lux_auto_brightness_worker: LuxAutoWorker | None = None
        self.lux_tool_button: ToolButton | None = None
        self.lux_lighting_check_button: ToolButton | None = None
        self.lux_slider: LuxAmbientSlider | None = None

    def create_tool_button(self) -> ToolButton:  # Used when the application UI has to reinitialize
        # Used when the application UI has to reinitialize
        self.lux_tool_button = ToolButton(AUTO_LUX_ON_SVG, tr("Toggle automatic light metered brightness adjustment"))
        return self.lux_tool_button

    def create_lighting_check_button(self) -> ToolButton:
        # Used when the application UI has to reinitialize
        self.lux_lighting_check_button = ToolButton(LIGHTING_CHECK_SVG, tr("Perform ambient lighting check now"))
        return self.lux_lighting_check_button

    def update_manual_meter(self, value: int):
        if self.is_auto_enabled() and not self.lux_meter.has_semi_auto_capability:  # goto manual unless on semi-auto
            self.set_auto(False)
        self.lux_meter.set_current_value(value)
        self.adjust_brightness_now()

    def update_manual_slider(self, value: int):
        if self.is_auto_enabled() and self.lux_slider:  # May not exist during initialization
            self.lux_slider.set_current_value(value)

    def create_manual_input_control(self) -> LuxAmbientSlider:
        if self.lux_slider is None:
            self.lux_slider = LuxAmbientSlider(self)
            self.lux_slider.new_lux_value_qtsignal.connect(self.update_manual_meter)

            def _toggle_lux_dialog():
                if LuxDialog.exists() and LuxDialog.get_instance().isVisible():
                    LuxDialog.get_instance().close()
                else:
                    LuxDialog.show_dialog(self.main_controller)

            self.lux_slider.title_button_pressed_qtsignal.connect(_toggle_lux_dialog)
            self.lux_slider.status_icon_pressed_qtsignal.connect(self.adjust_brightness_now)
        return self.lux_slider

    def get_lux_zone(self) -> LuxZone | None:
        if self.lux_slider and self.lux_slider.current_zone:
            return self.lux_slider.current_zone
        return None

    def stop_worker(self):
        if self.lux_auto_brightness_worker is not None:
            self.lux_auto_brightness_worker.stop()
            self.lux_auto_brightness_worker = None

    def start_worker(self, single_shot: bool):
        if self.lux_config.is_auto_enabled() or single_shot:
            if self.lux_meter is not None:
                if self.lux_auto_brightness_worker is not None:
                    self.stop_worker()
                self.lux_auto_brightness_worker = LuxAutoWorker(self, single_shot)
                self.lux_auto_brightness_worker.start()
                try:
                    self.lux_meter.new_lux_value_qtsignal.connect(self.update_manual_slider,
                                                                  type=Qt.ConnectionType.UniqueConnection)
                except TypeError:
                    pass

    def initialize_from_config(self) -> None:
        assert gui_misc.is_running_in_gui_thread()
        self.lux_config.load()
        try:
            if self.lux_meter is not None:
                self.lux_meter.stop_metering()
            device_name = self.lux_config.get_device_name().strip()
            if not device_name or device_name == LuxMeterSemiAutoDevice.obsolete_device_name:
                device_name = LuxMeterSemiAutoDevice.device_name
            LuxMeterSemiAutoDevice.set_location(self.main_controller.main_config.get_location())
            self.lux_meter = lux_create_device(device_name)
            if self.lux_config.is_auto_enabled():
                log.info("Lux auto-brightness settings refresh - restart monitoring.")
                self.start_worker(single_shot=False)
            else:
                log.info("Lux auto-brightness settings refresh - monitoring is off.")
                self.stop_worker()
            self.main_controller.update_window_status_indicators()  # Refresh indicators immediately
        except LuxDeviceException as lde:
            log.error(f"Error setting up lux meter {lde}", trace=True)
            MBox(MIcon.Critical, msg=tr("Error setting up lux meter: {}").format(self.lux_config.get_device_name()),
                 info=str(lde)).exec()
        if self.lux_slider is not None:
            self.lux_slider.set_current_value(round(self.lux_meter.get_value()))
        if self.lux_tool_button is not None:
            self.lux_tool_button.refresh_icon(self.current_auto_svg())  # Refresh indicators immediately
        if self.lux_lighting_check_button is not None:
            self.lux_lighting_check_button.refresh_icon(self.current_check_svg())

    def is_auto_enabled(self) -> bool:
        return self.lux_config is not None and self.lux_config.is_auto_enabled()

    def current_auto_svg(self) -> bytes:
        return AUTO_LUX_ON_SVG if self.is_auto_enabled() else AUTO_LUX_OFF_SVG

    def current_check_svg(self) -> bytes:
        return LIGHTING_CHECK_SVG if self.is_auto_enabled() else LIGHTING_CHECK_OFF_SVG

    def get_lux_config(self) -> LuxConfig:
        assert self.lux_config is not None
        return self.lux_config

    def toggle_auto(self) -> None:
        self.set_auto(not self.is_auto_enabled())

    def set_auto(self, enable: bool):
        assert self.lux_config is not None
        log.debug(f"LuxAutoController: set_auto {enable}")
        if enable:
            if self.lux_meter and self.lux_meter.has_semi_auto_capability and not self.main_controller.main_config.get_location():
                message = tr("Auto disabled, no location defined.")
                enable = False
            elif self.lux_config.is_auto_enabled():
                message = tr("Restarting automatic light metering.")
            else:
                message = tr("Switching to automatic light metering.")
            self.lux_config.set('lux-meter', 'automatic-brightness', 'yes' if enable else 'no')
        else:
            message = tr("Switching to manual input of ambient lux.")
            self.lux_config.set('lux-meter', 'automatic-brightness', 'no')
        self.lux_config.save(ConfIni.get_path('AutoLux'))
        self.main_controller.status_message(message, timeout=5000)
        LuxDialog.lux_dialog_message(message, timeout=5000)
        self.initialize_from_config()
        LuxDialog.reconfigure_instance()

    def adjust_brightness_now(self) -> None:
        if self.is_auto_enabled():
            if self.lux_auto_brightness_worker is not None:
                self.lux_auto_brightness_worker.adjust_now_requested = True
            else:
                log.error("adjust_brightness_now: No worker - unexpected - error?")
        else:
            self.start_worker(single_shot=True)

    def get_lux_profile(self, vdu_stable_id: VduStableId, brightness_range) -> List[LuxPoint]:
        if self.lux_config.has_option('lux-profile', vdu_stable_id):  # initialize removing duplicate points
            lux_points = list(set([LuxPoint(v[0], v[1]) for v in literal_eval(self.lux_config.get('lux-profile', vdu_stable_id))]))
        else:  # Create a default profile:
            min_v, max_v = (0, 100) if brightness_range is None else brightness_range
            defaults = [(0, 0.6), (100, 0.8), (1_000, 0.9), (10_000, 0.9), (100_000, 0.9)]
            lux_points = [LuxPoint(lux, min_v + round(r * (max_v - min_v))) for lux, r in defaults]
        if self.lux_config.has_option('lux-presets', 'lux-preset-points'):  # Merge in preset points
            merge_map = {point.lux: point for point in lux_points}
            for preset_point in self.lux_config.get_preset_points():
                # Look up the Preset's brightness for this VDU - get value from the actual Preset.
                if preset := self.main_controller.find_preset_by_name(preset_point.preset_name):  # Drop any that no longer exist
                    if point := merge_map.get(preset_point.lux):
                        point.preset_name = preset_point.preset_name  # Merge both points
                    else:
                        merge_map[preset_point.lux] = preset_point  # Add this point on its own
                        point = preset_point
                    # Point brightness for this VDU will be -1 if this VDU's brightness-control doesn't participate in the Preset.
                    point.brightness = preset.get_brightness(vdu_stable_id)
            lux_points = list(merge_map.values())
            lux_points.sort()
        log.debug(f"LuxAuto: get_lux_profile({vdu_stable_id=}) => {lux_points=}") if log.debug_enabled else None
        return lux_points


