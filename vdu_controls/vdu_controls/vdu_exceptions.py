# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from vdu_controls.ddcutil_abstract import DdcutilDisplayNotFound
from vdu_controls.work_scheduler import WorkException


class VduException(WorkException):

    def __init__(self, vdu_description=None, vcp_code=None, exception=None, operation=None) -> None:
        super().__init__()
        self.vdu_description = vdu_description
        self.attr_id = vcp_code
        self.cause = exception
        self.operation = operation

    def is_display_not_found_error(self) -> bool:
        return self.cause is not None and isinstance(self.cause, DdcutilDisplayNotFound)

    def __str__(self) -> str:
        return f"VduException: {self.vdu_description} op={self.operation} attr={self.attr_id} {self.cause}"
