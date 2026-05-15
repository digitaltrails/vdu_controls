# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from ast import literal_eval
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from vdu_controls.config_ini import ConfIni
import vdu_controls.logging as log

@dataclass
class LuxPoint:
    lux: int
    brightness: int
    preset_name: str | None = None

    def __lt__(self, other) -> bool:  # Brightness doesn't matter for comparison purposes.
        return self.lux < other.lux

    def __eq__(self, other) -> bool:  # Brightness doesn't matter for comparison purposes.
        return self.lux == other.lux and self.preset_name == other.preset_name

    def __hash__(self):  # Brightness doesn't matter for comparison purposes.
        return hash((self.lux, self.preset_name))

    def __str__(self):
        return f"({self.lux} lux, {self.brightness}%, preset={self.preset_name})"


class LuxConfig(ConfIni):

    def __init__(self) -> None:
        super().__init__()
        self.path = ConfIni.get_path('AutoLux')
        self.last_modified_time = 0.0
        self.cached_profiles_map: Dict[str, List[LuxPoint]] = {}

    def get_device_name(self) -> str:
        return self.get("lux-meter", "lux-device", fallback='')

    def get_preset_points(self) -> List[LuxPoint]:
        if self.has_option('lux-presets', 'lux-preset-points'):
            return [LuxPoint(lux, -1, name) for lux, name in literal_eval(self.get('lux-presets', 'lux-preset-points'))]
        return []

    def get_interval_minutes(self) -> int:
        return self.getint('lux-meter', 'interval-minutes', fallback=10)

    def is_auto_enabled(self) -> bool:
        return self.getboolean("lux-meter", "automatic-brightness", fallback=False)

    def load(self, force: bool = False) -> LuxConfig:
        self.cached_profiles_map.clear()
        if self.path.exists():
            if Path.stat(self.path).st_mtime > self.last_modified_time or force:
                log.info(f"Reading autolux file '{self.path.as_posix()}'")
                text = Path(self.path).read_text()
                self.read_string(text)
                self.last_modified_time = Path.stat(self.path).st_mtime
        for section_name in ['lux-meter', 'lux-profile', 'lux-ui', 'lux-presets']:
            if not self.has_section(section_name):
                self.add_section(section_name)
        return self
