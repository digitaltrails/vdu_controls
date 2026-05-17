# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import List, Tuple, Dict

from vdu_controls import logging as log
from vdu_controls.constants import CONFIG_DIR_PATH, VDU_CONTROLS_BASE_VERSION
from vdu_controls.misc import zoned_now


class ConfIni(configparser.ConfigParser):
    """
    ConfigParser is a little messy, and its class name is a bit misleading,
    wrap it and bend it to our needs.
    """

    METADATA_SECTION = "metadata"
    UNKNOWN_SECTION = "unknown"

    METADATA_VERSION_OPTION = 'version'
    METADATA_TIMESTAMP_OPTION = 'timestamp'
    UNKNOWN_OPTION = "UNKNOWN"

    def __init__(self) -> None:
        super().__init__(interpolation=None)
        if not self.has_section(ConfIni.METADATA_SECTION):
            self.add_section(ConfIni.METADATA_SECTION)

    def data_sections(self) -> List[str]:  # Section other than metadata and DEFAULT - real data.
        return [s for s in self.sections() if s != configparser.DEFAULTSECT and s != ConfIni.METADATA_SECTION]

    def get_version(self) -> Tuple[int, int, int]:
        if version := self.get(ConfIni.METADATA_SECTION, ConfIni.METADATA_VERSION_OPTION, fallback=None):
            try:
                parts = version.split('-')[0].split('.')
                assert len(parts) >= 3
                return int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                log.error(f"Illegal version number {version} should be i.j.k where i, j and k are integers.", trace=True)
        return 1, 6, 0

    def save(self, config_path) -> None:
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        with open(config_path, 'w', encoding="utf-8") as config_file:
            self[ConfIni.METADATA_SECTION][ConfIni.METADATA_VERSION_OPTION] = VDU_CONTROLS_BASE_VERSION
            self[ConfIni.METADATA_SECTION][ConfIni.METADATA_TIMESTAMP_OPTION] = str(zoned_now())
            self.write(config_file)
        log.info(f"Wrote config to {config_path.as_posix()}")

    def duplicate(self, new_ini=None) -> ConfIni:
        if new_ini is None:
            new_ini = ConfIni()
        for section in self.sections():
            if section != configparser.DEFAULTSECT and section != ConfIni.METADATA_SECTION:
                new_ini.add_section(section)
            for option in self[section]:
                new_ini[section][option] = self[section][option]
        return new_ini

    def diff(self, other: ConfIni, vdu_settings_only: bool = False) -> Dict[Tuple[str, str], str]:
        values = []
        for subject in (self, other):
            sections = set(subject.sections()) - {configparser.DEFAULTSECT, ConfIni.METADATA_SECTION}
            if vdu_settings_only:
                sections -= {'preset'}
            values.append([(section, option, value) for section in sections for option, value in subject[section].items()])
        differences = list(set(values[0]) ^ set(values[1]))
        return {(section, option): value for section, option, value in differences}

    @staticmethod
    def get_path(config_name: str) -> Path:
        return CONFIG_DIR_PATH.joinpath(config_name + '.conf')
