# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import pathlib
import re
import select
import subprocess
import termios
import time
from decimal import Decimal
from importlib import import_module
from typing import Tuple

from vdu_controls.qt_imports import QObject, pyqtSignal

from vdu_controls.constants import CONFIG_DIR_PATH, getenv_logged

from vdu_controls.app_locale import tr
import vdu_controls.logging as log
from vdu_controls.misc import zoned_now, GeoLocation
from vdu_controls.solar_calc import calc_solar_lux
from vdu_controls.work_scheduler import WorkerThread

DAYLIGHT_FACTOR_MINIMUM = Decimal(0.00001)
DAYLIGHT_FACTOR_PLACES = abs(DAYLIGHT_FACTOR_MINIMUM.as_tuple().exponent)


class LuxMeterDevice(QObject):
    new_lux_value_qtsignal = pyqtSignal(int)

    def __init__(self, requires_worker: bool = True, manual: bool = False, semi_auto: bool = False) -> None:
        super().__init__()
        log.debug(f"LuxMeterDevice init {manual=} {semi_auto=}") if log.debug_enabled else None
        self.current_value: float | None = None
        self.requires_worker = requires_worker
        self.has_manual_capability = manual  # Can be both manual and semi-automatic
        self.has_semi_auto_capability = semi_auto
        self.has_auto_capability = not self.has_manual_capability or self.has_semi_auto_capability
        if self.requires_worker:  # use a thread to prevent any blocking due to slow updating
            log.info(f"LuxMeterDevice: starting worker for {self.__class__}")
            self.worker = WorkerThread(task_body=self.update_from_worker_thread, task_finished=self.cleanup, loop=True)

    def get_value(self) -> float | None:  # an un-smoothed raw value - TODO should smoothing be moved here?
        if self.current_value is None and self.requires_worker:
            self.worker.start() if not self.worker.isRunning() else None
            while self.current_value is None and not self.worker.stop_requested:  # have to block on the first time through.
                time.sleep(0.1)
        # careful - None has a meaning elsewhere, so don't change it to 0.0 without figuring out the consequences.
        return self.current_value

    def update_from_worker_thread(self, _: WorkerThread) -> None:  # Only for meters that have background workers.
        pass

    def set_current_value(self, new_value: float) -> None:
        self.current_value = max(new_value, 1.0)  # Never less than 1 - for safety - don't want to dim to zero.
        self.new_lux_value_qtsignal.emit(round(new_value))

    def cleanup(self, _: WorkerThread):
        pass

    def stop_metering(self) -> None:
        if self.requires_worker:
            self.worker.stop()

    def get_status(self) -> Tuple[bool, str]:  # True if OK, plus any message
        return True, ''


def lux_create_device(device_name: str) -> LuxMeterDevice:
    if device_name == LuxMeterSemiAutoDevice.device_name:
        return LuxMeterSemiAutoDevice()
    if not pathlib.Path(device_name).exists():
        raise LuxDeviceException(tr("Failed to set up {} - path does not exist.").format(device_name))
    if not os.access(device_name, os.R_OK):
        raise LuxDeviceException(tr("Failed to set up {} - no read access to device.").format(device_name))
    if pathlib.Path(device_name).is_char_device():
        return LuxMeterSerialDevice(device_name)
    elif pathlib.Path(device_name).is_fifo():
        return LuxMeterFifoDevice(device_name)
    elif pathlib.Path(device_name).exists() and os.access(device_name, os.X_OK):
        return LuxMeterExecutableDevice(device_name)
    raise LuxDeviceException(tr("Failed to set up {} - not a recognized kind of device or not executable.").format(device_name))


class LuxMeterFifoDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.device_name = device_name
        self.fifo: int | None = None
        self.buffer = b''

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        try:
            if self.fifo is None:
                log.info(f"Initialising fifo {self.device_name} - waiting on fifo data.")
                self.fifo = os.open(self.device_name, os.O_RDONLY | os.O_NONBLOCK)
            while not self.worker.stop_requested and len(select.select([self.fifo], [], [], 1.0)[0]) == 1:
                assert self.fifo is not None
                byte = os.read(self.fifo, 1)
                if byte is None:
                    self.cleanup()  # Fifo has closed, maybe meter is resetting
                elif byte == b'\n':
                    if len(self.buffer) > 0:
                        self.set_current_value(float(self.buffer.decode()))
                        self.buffer = b''
                else:
                    self.buffer += byte
        except (OSError, ValueError) as se:
            self.cleanup()
            self.buffer = b''
            log.warning(f"Reopen and retry {self.device_name=} {self.buffer=}", se, trace=True)

    def cleanup(self, worker: WorkerThread | None = None):
        if self.fifo is not None:
            log.info("closing fifo")
            os.close(self.fifo)
            self.fifo = None


class LuxMeterExecutableDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.runnable = device_name
        self.sleep_time = float(getenv_logged("LUX_METER_RUNNABLE_SLEEP", default='60.0'))

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        try:
            result = subprocess.run([self.runnable], stdout=subprocess.PIPE, check=True)
            self.set_current_value(float(result.stdout))
        except (OSError, ValueError, subprocess.CalledProcessError) as se:
            log.warning(f"Error running {self.runnable}, will retry in {self.sleep_time} seconds", se, trace=True)
        self.worker.doze(self.sleep_time)  # Don't re-run too fast


class LuxMeterSerialDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.device_name = device_name
        self.serial_device = None
        self.line_matcher = re.compile(r'\A([0-9]+[.][0-9]+)\r\n\Z', re.DOTALL)  # Be precise to try and catch errors
        self.backoff_secs = self.initial_backoff_secs = 10
        try:
            self.serial_module = import_module('serial')
        except ModuleNotFoundError as mnf:
            raise LuxDeviceException(tr("The required pyserial serial-port module is not installed on this system.")) from mnf

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        problem = None
        try:
            if self.serial_device is None:
                log.info(f"LuxMeterSerialDevice: Initializing character device {self.device_name}")
                self.serial_device = self.serial_module.Serial(self.device_name)
            if self.serial_device is not None:
                self.serial_device.reset_input_buffer()
                buffer = self.serial_device.read_until()
                decoded = buffer.decode('utf-8', errors='surrogateescape')
                if match := self.line_matcher.match(decoded):  # only accept correctly formatted output
                    self.set_current_value(float(match.group(1)))
                    self.backoff_secs = self.initial_backoff_secs
                else:
                    problem = f"value that failed to parse: {decoded.encode('unicode_escape')}"
            self.worker.doze(1.0)
        except (self.serial_module.SerialException, termios.error, FileNotFoundError, ValueError) as se:
            problem = se
        if problem:
            log.warning(f"Retry read of {self.device_name}, will reopen feed in {self.backoff_secs} seconds. Cause:", problem,
                        trace=True)
            self.cleanup()
            self.worker.doze(self.backoff_secs)
            self.backoff_secs = self.backoff_secs * 2 if self.backoff_secs < 300 else 300

    def cleanup(self, worker: WorkerThread | None = None):
        if self.serial_device is not None:
            log.debug("closing serial device") if log.debug_enabled else None
            self.serial_device.close()
            self.serial_device = None


class LuxMeterSemiAutoDevice(LuxMeterDevice):  # is both manual and automatic - semi-automatic
    obsolete_device_name = 'Slider-Control'
    device_name = 'solar-lux-calculator'
    location: GeoLocation | None = None
    daylight_factor: float | None = None
    status_message: str = ''

    def __init__(self) -> None:
        super().__init__(requires_worker=False, manual=True, semi_auto=True)
        self.current_value: float = LuxMeterSemiAutoDevice.get_stored_value()
        LuxMeterSemiAutoDevice.daylight_factor = None  # Force initialization from file
        _ = LuxMeterSemiAutoDevice.get_daylight_factor()

    def get_value(self) -> float | None:
        if location := LuxMeterSemiAutoDevice.get_location():
            if lux := calc_solar_lux(zoned_now(), location, LuxMeterSemiAutoDevice.get_daylight_factor()):
                self.set_current_value(lux)  # only set if in daylight
        return self.current_value

    def set_current_value(self, new_value: float) -> None:
        if (new_value := round(new_value)) != round(self.current_value):
            self.save_stored_value(new_value)
        super().set_current_value(new_value)

    def stop_metering(self) -> None:
        pass

    def get_status(self) -> Tuple[bool, str]:
        if self.location is None:
            return True, tr('No location defined.')
        if msg := LuxMeterSemiAutoDevice.status_message:
            LuxMeterSemiAutoDevice.status_message = ''
            return True, msg
        return super().get_status()

    @staticmethod
    def get_stored_value() -> float:
        persisted_path = CONFIG_DIR_PATH.joinpath("lux_manual_value.txt")
        if persisted_path.exists():
            try:
                return float(persisted_path.read_text())
            except ValueError:
                log.error(f"LuxSemiAuto: failed to parse stored lux value, removing {persisted_path.as_posix()}")
                persisted_path.unlink()
        return 1000.0

    @staticmethod
    def save_stored_value(new_value: float):
        if CONFIG_DIR_PATH.exists():
            CONFIG_DIR_PATH.joinpath("lux_manual_value.txt").write_text(str(round(new_value)))

    @staticmethod
    def get_daylight_factor() -> float:
        if LuxMeterSemiAutoDevice.daylight_factor is None:
            daylight_factor = 1.0
            persisted_path = CONFIG_DIR_PATH.joinpath("lux_daylight_factor.txt")
            if persisted_path.exists():
                try:
                    daylight_factor = float(persisted_path.read_text())
                except ValueError:
                    log.error(f"LuxSemiAuto: failed to parse daylight_factor, removing {persisted_path.as_posix()}")
                    persisted_path.unlink()
            else:
                log.error(f"LuxSemiAuto: {persisted_path.as_posix()} does not exist")
            log.debug(f'LuxSemiAuto: {daylight_factor=} ({persisted_path.as_posix()})') if log.debug_enabled else None
            LuxMeterSemiAutoDevice.daylight_factor = daylight_factor
        assert LuxMeterSemiAutoDevice.daylight_factor is not None
        return LuxMeterSemiAutoDevice.daylight_factor

    @staticmethod
    def update_df_from_lux_value(new_lux_value: float, semi_auto_source: bool):
        if location := LuxMeterSemiAutoDevice.location:
            solar_lux = calc_solar_lux(zoned_now(), location, 1.0)
            if solar_lux < 10:  # only for reasonable daylight lux levels.
                log.debug(f"LuxSemiAuto: update daylight-factor: ignored " 
                          f"{new_lux_value=}, associated {solar_lux=} too small.") if log.debug_enabled else None
                LuxMeterSemiAutoDevice.status_message = tr('Ignoring daylight-factor, Sun not bright enough.')
            else:
                daylight_factor = new_lux_value / solar_lux
                if 0.0 < daylight_factor <= 2.0 or semi_auto_source:
                    log.debug(f"LuxSemiAuto: update {daylight_factor=:0.6f} {semi_auto_source=}")
                    LuxMeterSemiAutoDevice.set_daylight_factor(daylight_factor, internal=True, persist=semi_auto_source)
                else:
                    log.debug(f"LuxSemiAuto: update daylight-factor: ignored "
                              f"{daylight_factor:0.6f}={new_lux_value}/{solar_lux}, DF out of workable range.") if log.debug_enabled else None
                    LuxMeterSemiAutoDevice.status_message = tr('Ignoring daylight-factor, out of viable range.')

    @staticmethod
    def set_daylight_factor(daylight_factor: float, internal: bool = False, persist: bool = False):
        daylight_factor = round(daylight_factor, DAYLIGHT_FACTOR_PLACES)
        daylight_factor = max(daylight_factor, DAYLIGHT_FACTOR_MINIMUM)
        if LuxMeterSemiAutoDevice.daylight_factor is None or abs(LuxMeterSemiAutoDevice.daylight_factor - daylight_factor) >= DAYLIGHT_FACTOR_MINIMUM:
            if persist:
                if CONFIG_DIR_PATH.exists():
                    persisted_path = CONFIG_DIR_PATH.joinpath("lux_daylight_factor.txt")
                    log.debug(f"LuxSemiAuto: save {daylight_factor=:0.6f} to {persisted_path.as_posix()}") if log.debug_enabled else None
                    persisted_path.write_text(f"{daylight_factor:.6f}")
            LuxMeterSemiAutoDevice.daylight_factor = daylight_factor

    @staticmethod
    def get_location() -> GeoLocation | None:
        return LuxMeterSemiAutoDevice.location

    @staticmethod
    def set_location(location: GeoLocation | None):
        LuxMeterSemiAutoDevice.location = location


class LuxDeviceException(Exception):
    pass
