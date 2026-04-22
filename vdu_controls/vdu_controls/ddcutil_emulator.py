# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import List

from vdu_controls.ddcutil_exe import DdcutilExeImpl


class DdcutilEmulatorImpl(DdcutilExeImpl):

    def __init__(self, ddcutil_exe: str, common_args: List[str] | None = None):
        super().__init__(common_args)
        self.ddcutil_exe = ddcutil_exe