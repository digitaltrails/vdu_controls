# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import re
from datetime import datetime
from enum import Enum, IntFlag
from functools import partial
from pathlib import Path
from typing import Callable

from vdu_controls.qt_imports import QT_TR_NOOP
from vdu_controls.qt_imports import QIcon

from vdu_controls.weather_util import WeatherQuery
from vdu_controls.config_ini import ConfIni
from vdu_controls.ddcutil_aggregator import VduStableId
from vdu_controls.icon_utils import ThemeType, polychrome_light_or_dark, create_icon_from_path, create_icon_from_text
from vdu_controls.app_locale import tr
import vdu_controls.logging as log
from vdu_controls.misc import zoned_now, proper_name
from vdu_controls.solar_calc import SolarElevationKey, format_solar_elevation_abbreviation, format_solar_elevation_description, \
    parse_solar_elevation_ini_text
from vdu_controls.unicode import *
from vdu_controls.work_scheduler import SchedulerJob, ScheduleWorker, SchedulerJobType


class PresetTransitionFlag(IntFlag):
    _ignore_ = ['abbreviations', 'descriptions']  # Seems very hacky

    NONE = 0
    SCHEDULED = 1
    MENU = 2
    SIGNAL = 4
    ALWAYS = 7

    abbreviations = {NONE: '', SCHEDULED: TIME_CLOCK_SYMBOL, MENU: MENU_SYMBOL,  # type: ignore - not an enum value
                     SIGNAL: SIGNAL_SYMBOL, ALWAYS: TRANSITION_ALWAYS_SYMBOL}

    descriptions = {   # type: ignore  - not an enum value
        NONE: QT_TR_NOOP('Always immediately'), SCHEDULED: QT_TR_NOOP('Smoothly on solar/time'),
        MENU: QT_TR_NOOP('Smoothly on menu'),
        SIGNAL: QT_TR_NOOP('Smoothly on signal'), ALWAYS: QT_TR_NOOP('Always smoothly')}

    def abbreviation(self, abbreviations=abbreviations) -> str:  # Even more hacky
        if self.value in (PresetTransitionFlag.NONE, PresetTransitionFlag.ALWAYS):
            return abbreviations[self]
        return TRANSITION_SYMBOL + ''.join([abbreviations[component] for component in self.component_values()])

    def description(self, descriptions=descriptions) -> str:  # Yuck
        if self.value in (PresetTransitionFlag.NONE, PresetTransitionFlag.ALWAYS):
            return tr(descriptions[self])
        return ', '.join([tr(descriptions[component]) for component in self.component_values()])

    def component_values(self) -> list[PresetTransitionFlag]:
        # similar to Python 3.11 enum.show_flag_values(self) - list of power of two components for self
        return [option for option in PresetTransitionFlag if (option & (option - 1) == 0) and option != 0 and option in self]

    def __str__(self) -> str:
        assert self.name is not None  # TODO this failed once - get to repeat
        if self.value == PresetTransitionFlag.NONE:
            return self.name.lower()
        return ','.join([component.name.lower() for component in self.component_values()])  # type: ignore


def parse_transition_type(string_value: str) -> PresetTransitionFlag:
    transition_type = PresetTransitionFlag.NONE
    string_value = string_value.replace('schedule_or_signal', 'scheduled,signal')  # Backward compatible for unreleased 1.9.2
    for component_value in string_value.split(','):
        for option in PresetTransitionFlag:
            assert option.name is not None
            if component_value.lower() == option.name.lower():
                transition_type |= option
    return transition_type


class Preset:
    """A config/ini file of user-created settings presets - such as Sunny, Cloudy, Night, etc."""

    def __init__(self, name) -> None:
        self.name = name
        self.path = ConfIni.get_path(proper_name('Preset', name))
        self.preset_ini = ConfIni()
        self.scheduler_job: SchedulerJob | None = None
        self.schedule_status = PresetScheduleStatus.UNSCHEDULED
        self.elevation_time_today: datetime | None = None
        self.in_transition_step = 0

    def get_title_name(self) -> str:
        return self.name

    def get_icon_path(self) -> Path | None:
        if self.preset_ini.has_section("preset"):
            path_text = self.preset_ini.get("preset", "icon", fallback=None)
            return Path(path_text) if path_text else None
        return None

    def create_icon(self, theme_type: ThemeType = ThemeType.UNDECIDED) -> QIcon:
        icon_path = self.get_icon_path()
        if theme_type == ThemeType.UNDECIDED:
            theme_type = polychrome_light_or_dark()
        if icon_path and icon_path.exists():
            return create_icon_from_path(icon_path, theme_type)
        else:
            # Only room for two letters at most - use first and last if more than one word.
            full_acronym = [word[0] for word in re.split(r"[ _-]", self.name) if word != '']
            abbreviation = full_acronym[0] if len(full_acronym) == 1 else full_acronym[0] + full_acronym[-1]
            return create_icon_from_text(abbreviation, theme_type)

    def load(self) -> ConfIni:
        if self.path.exists():
            log.debug(f"Reading preset file '{self.path.as_posix()}'") if log.debug_enabled else None
            preset_text = Path(self.path).read_text()
            preset_ini = ConfIni()
            preset_ini.read_string(preset_text)
        else:
            preset_ini = ConfIni()
        self.preset_ini = preset_ini
        return self.preset_ini

    def save(self) -> None:
        self.preset_ini.save(self.path)

    def delete(self) -> None:
        log.info(f"Deleting preset file '{self.path.as_posix()}'")
        self.remove_elevation_trigger()
        if self.path.exists():
            os.remove(self.path.as_posix())

    def get_brightness(self, vdu_stable_id: VduStableId) -> int:
        if vdu_stable_id in self.preset_ini:
            return self.preset_ini.getint(vdu_stable_id, 'brightness', fallback=-1)
        return -1

    def get_vdu_sids(self):
        return [section_name for section_name in self.preset_ini.data_sections() if section_name != 'preset']

    def get_solar_elevation(self) -> SolarElevationKey | None:
        if elevation_spec := self.preset_ini.get('preset', 'solar-elevation', fallback=None):
            solar_elevation = parse_solar_elevation_ini_text(elevation_spec)
            return solar_elevation
        return None

    def get_at_time(self) -> datetime | None:
        if at_time_spec := self.preset_ini.get('preset', 'at-time', fallback=None):
            return datetime.combine(datetime.today(), datetime.strptime(at_time_spec, "%H:%M").time()).astimezone()
        return None

    def get_solar_elevation_abbreviation(self) -> str:
        if elevation := self.get_solar_elevation():
            result = format_solar_elevation_abbreviation(elevation)
            if self.elevation_time_today:
                result += f" {TIME_CLOCK_SYMBOL}{self.elevation_time_today.strftime('%H:%M')}"
            else:
                # Not possible today - sun doesn't get that high
                result += ' ' + TOO_HIGH_SYMBOL
            if self.get_weather_restriction_filename() is not None:
                result += ' ' + WEATHER_RESTRICTION_SYMBOL
            result += ' ' + self.schedule_status.symbol()
            return result
        if at_time := self.get_at_time():
            return f" {TIME_CLOCK_SYMBOL}{at_time.strftime('%H:%M')} " + self.schedule_status.symbol()
        return ''

    def get_schedule_description(self) -> str:
        if not ScheduleWorker.is_running():
            return tr("(Schedule is disabled in Settings)")
        result = suffix = basic_desc = weather_suffix = ''
        if elevation := self.get_solar_elevation():
            basic_desc = SUN_SYMBOL + " " + format_solar_elevation_description(elevation)
            weather_fn = self.get_weather_restriction_filename()
            weather_suffix = tr(" (subject to {} weather)").format(
                Path(weather_fn).stem.replace('_', ' ')) if weather_fn is not None else ''
            if at_time := self.elevation_time_today:
                suffix = ''
            elif ScheduleWorker.is_running():
                suffix = tr("the sun does not rise this high today")
        elif at_time := self.get_at_time():
            basic_desc = TIME_CLOCK_SYMBOL
        # This might not work too well in translation - rethink?
        if at_time:
            if self.scheduler_job and self.scheduler_job.remaining_time() > 0:
                template = tr("{0} later today at {1}") + weather_suffix
            elif at_time < zoned_now():
                template = (tr("{0} earlier today at {1}")
                            + weather_suffix
                            + f" ({tr(self.schedule_status.description(), context=PresetScheduleStatus.__name__)})")
            else:
                template = tr("{0} suspended for {1}")
            result = template.format(basic_desc, f"{at_time.replace(second=0, microsecond=0):%H:%M}")
        result = result + ' ' + suffix
        return result

    def get_daylight_factor(self) -> float | None:
        if self.preset_ini.get('preset', 'daylight-factor', fallback=None):
            return self.preset_ini.getfloat('preset', 'daylight-factor', fallback=None)
        return None

    def get_transition_type(self) -> PresetTransitionFlag:
        return parse_transition_type(self.preset_ini.get('preset', 'transition-type', fallback="NONE"))

    def get_step_interval_seconds(self) -> int:
        return self.preset_ini.getint('preset', 'transition-step-interval-seconds', fallback=0)

    def schedule(self, when_today: datetime, run_action: Callable, skip_action: Callable | None = None, overdue: bool = False):
        self.scheduler_job = SchedulerJob(when_today, SchedulerJobType.RESTORE_PRESET, partial(run_action, self),
                                          partial(skip_action, self) if skip_action else None)
        if not overdue:
            self.elevation_time_today = when_today
            self.schedule_status = PresetScheduleStatus.SCHEDULED
        log.info(f"Scheduled preset '{self.name}' for {when_today} in "
                 f"{round(self.scheduler_job.remaining_time() / 60)} minutes {self.get_solar_elevation()} {overdue=}")

    def remove_elevation_trigger(self, quietly: bool = False) -> None:
        if self.scheduler_job:
            log.info(f"Preset timer and schedule status cleared for '{self.name}'") if not quietly else None
            self.scheduler_job.dequeue()
            self.scheduler_job = None
        if self.elevation_time_today is not None:
            self.elevation_time_today = None
        self.schedule_status = PresetScheduleStatus.UNSCHEDULED

    def toggle_timer(self) -> None:
        if self.elevation_time_today and self.elevation_time_today > zoned_now():
            if self.scheduler_job is not None:
                if self.scheduler_job.remaining_time() > 0:
                    log.info(f"Preset scheduled timer cleared for '{self.name}'")
                    self.scheduler_job.dequeue()
                    self.schedule_status = PresetScheduleStatus.SUSPENDED
                else:
                    log.info(f"Preset scheduled timer restored for '{self.name}'")
                    self.scheduler_job.requeue()
                    self.schedule_status = PresetScheduleStatus.SCHEDULED

    def is_weather_dependent(self) -> bool:
        return self.get_weather_restriction_filename() is not None

    def check_weather(self, weather: WeatherQuery) -> bool:
        weather_restriction_filename = self.get_weather_restriction_filename()
        if weather.weather_code is None or weather_restriction_filename is None:
            return True
        path = Path(weather_restriction_filename)
        if not path.exists():
            log.error(f"Preset '{self.name}' missing weather requirements file: {weather_restriction_filename}")
            return True
        with open(path, encoding="utf-8") as weather_file:
            code_list = weather_file.readlines()
            for code_line in code_list:
                parts = code_line.split()
                if parts and weather.weather_code.strip() == parts[0]:
                    log.info(f"Preset '{self.name}' met {path.name} requirements. Current weather is: "
                             f"{weather.area_name} {weather.weather_code} {weather.weather_desc}")
                    return True
        log.info(f"Preset '{self.name}' failed {path.name} requirements. Current weather is: "
                 f"{weather.area_name} {weather.weather_code} {weather.weather_desc}")
        return False

    def get_weather_restriction_filename(self) -> str | None:
        weather_restriction_filename = \
            self.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None)
        return weather_restriction_filename


class PresetScheduleStatus(Enum):
    UNSCHEDULED = 0, ' ', QT_TR_NOOP('unscheduled')
    # This hourglass character is too tall - it causes a jump when rendered - but nothing else is quite as appropriate.
    SCHEDULED = 1, TIMER_RUNNING_SYMBOL, QT_TR_NOOP('scheduled')
    SUSPENDED = 2, ' ', QT_TR_NOOP('suspended')
    SUCCEEDED = 3, SUCCESS_SYMBOL, QT_TR_NOOP('succeeded')
    SKIPPED_SUPERSEDED = 4, SKIPPED_SYMBOL, QT_TR_NOOP('skipped, superseded')
    WEATHER_CANCELLATION = 5, WEATHER_CANCELLATION_SYMBOL, QT_TR_NOOP('weather cancellation')

    def symbol(self) -> str:
        return self.value[1]

    def description(self) -> str:
        return self.value[2]

    def __str__(self) -> str:
        return str(self.value[0])

