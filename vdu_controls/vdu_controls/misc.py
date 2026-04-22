# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
import re
from datetime import datetime, timedelta
from enum import Enum

from vdu_controls.constants import TESTING_TIME_ZONE, TESTING_TIME_DELTA


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