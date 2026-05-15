# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from vdu_controls.constants import TESTING_TIME_ZONE, TESTING_TIME_DELTA

# Conditional base StrEnum (works on 3.8+ and uses built-in when available) ---

if sys.version_info >= (3, 11):
    from enum import StrEnum as LocalStrEnum
else:
    # Custom fallback for Python 3.8 - 3.10
    class LocalStrEnum(str, Enum):
        
        def __str__(self) -> str:
            return self.value

        @classmethod
        def __contains__(cls, item):
            return item in cls._value2member_map_

        @classmethod
        def _missing_(cls, value):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}")


def intV(type_id: Enum | int) -> int:
    return type_id.value if isinstance(type_id, Enum) else type_id  # awfulness of enums in pyqt6


def zoned_now(rounded_to_minute: bool = False) -> datetime:
    now = datetime.now().astimezone()
    if TESTING_TIME_ZONE:  # This is a testing-only path that requires python > 3.8
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(TESTING_TIME_ZONE))  # for testing scheduling
    result = (now + timedelta(seconds=30)).replace(second=0, microsecond=0) if rounded_to_minute else now
    if TESTING_TIME_DELTA:
        result += TESTING_TIME_DELTA
    return result


def proper_name(*args) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', '_'.join([arg.strip() for arg in args]))


def clamp(v: int, min_v: int, max_v: int) -> int:
    return max(min(max_v, v), min_v)


@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    place_name: str | None

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if not isinstance(other, GeoLocation):
            return NotImplemented  # don't attempt to compare against unrelated types
        return self.latitude == other.latitude and self.longitude == other.longitude and \
            self.place_name == other.place_name
