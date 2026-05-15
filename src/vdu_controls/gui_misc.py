# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from vdu_controls.qt_imports import QThread

gui_thread: QThread | None = None

def set_gui_thread(thread: QThread):
    # print(">>>>>>>>>>>>>>>>>>>>>>>Setting GUI thread...")
    global gui_thread
    assert gui_thread is None
    gui_thread = thread

def is_running_in_gui_thread() -> bool:
    # print(f">>>>>>>>>>>>>>>>>>>>>Checking if GUI thread is running... {QThread.currentThread()} {gui_thread}")
    assert gui_thread is not None
    return QThread.currentThread() == gui_thread


