# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Any, List, Dict, TYPE_CHECKING

from vdu_controls.qt_imports import pyqtSignal

from vdu_controls.vdu_controls_config import ConfOpt
from vdu_controls.ddcutil_abstract import VcpOrigin

from vdu_controls.ddcutil_aggregator import VduStableId
import vdu_controls.logging as log
from vdu_controls.misc import zoned_now
from vdu_controls.work_scheduler import WorkerThread

if TYPE_CHECKING:
    from vdu_controls.vdu_controls_application import VduAppController

@dataclass
class BulkChangeItem:
    vdu_sid: VduStableId
    vcp_code: int
    final_value: int
    starting_value: int | None = None
    current_value: int | None = None
    transition: bool = False   # Whether stepping the value change is permitted.
    finished: bool = False   # If true, we will stop checking this value for changes (boilerplate).


class BulkChangeWorker(WorkerThread):
    progress_qtsignal = pyqtSignal(object)

    def __init__(self, name: str, main_controller: VduAppController,
                 progress_callable: Callable[[BulkChangeWorker], None],
                 finished_callable: Callable[[BulkChangeWorker], None],
                 step_interval: float = 0.0, ignore_others: bool = True, context: Any = None) -> None:
        super().__init__(task_body=self._perform_changes, task_finished=finished_callable)  # type: ignore
        log.debug(f"BulkChangeHandler: {name} init {ignore_others=}") if log.debug_enabled else None
        self.name = name
        self.ignore_others = ignore_others  # Ignore any other work going on - don't let other changes stop the work.
        self.context = context
        self.start_time: datetime | None = None
        self.main_controller = main_controller
        self.progress_callable = progress_callable
        self.progress_qtsignal.connect(self.progress_callable)
        self.to_do_list: List[BulkChangeItem] = []
        self.step_interval = step_interval
        # Turn off transitions if we are protecting NVRAM.
        # Also turn off if we're ignoring other work - we should do things as fast as possible.
        self.immediately = self.main_controller.main_config.is_protecting_nvram() or ignore_others
        self.change_count = 0
        self.total_elapsed_seconds = 0.0
        self.completed = False

    def add_item(self, item: BulkChangeItem):
        if self.immediately or self.step_interval < 0.1:
            item.transition = False
        self.to_do_list.append(item)

    def _perform_changes(self, _: BulkChangeWorker):
        self.start_time = zoned_now()
        try:
            if any([item.current_value is None for item in self.to_do_list]):  # Has the parent filled out expected values.
                self._refresh_current_values_from_vdu()
            if not self.immediately:
                self._do_stepped_changes()  # Transitions in a series of steps for items that allow transitions.
            if not self.stop_requested:  # if we did any stepping, we may have decided to stop.
                self._do_normal_changes()
                self.completed = len([item for item in self.to_do_list if item.current_value != item.final_value]) == 0
        finally:
            self.total_elapsed_seconds = (self.start_time - zoned_now()).total_seconds()
            if log.debug_enabled:
                log.debug(f"BulkChangeWorker: {self.name} {self.completed=} {self.change_count=} {self.total_elapsed_seconds=:.3f}")

    def _do_normal_changes(self):
        for item in [item for item in self.to_do_list if not item.transition and item.current_value != item.final_value]:
            if self.stop_requested:
                break
            if item.final_value != item.current_value:
                self.main_controller.set_value(item.vdu_sid, item.vcp_code, item.final_value)
                item.current_value = item.final_value
                item.finished = True
                self.change_count += 1

    def _do_stepped_changes(self):
        while step_changes := [item for item in self.to_do_list if item.transition
                                                                   and not item.finished
                                                                   and item.current_value != item.final_value]:
            assert not self.immediately
            log.debug(f"BulkChangeWorker stepping {len(step_changes)=}")
            if self.stop_requested:
                break
            for item in step_changes:
                if self.stop_requested:
                    break
                assert item.current_value is not None
                diff = item.final_value - item.current_value
                step_size = max(5, abs(diff) // 2)  # TODO find a good heuristic
                step = int(math.copysign(step_size, diff)) if abs(diff) > step_size else diff
                new_value = item.current_value + step
                item.finished = new_value == item.final_value   # Worried that the value might change again later
                origin = VcpOrigin.NORMAL if item.finished else VcpOrigin.TRANSIENT
                self.main_controller.set_value(item.vdu_sid, item.vcp_code, new_value, origin)
                item.current_value = new_value
                self.change_count += 1
                # self.doze(0.1)  # TODO do we need to pause to let things settle?
            self.progress_qtsignal.emit(self)
            self.doze(self.step_interval)
            self._refresh_current_values_from_vdu()
            if self.stop_requested:
                break

    def _refresh_current_values_from_vdu(self):
        log.debug(f"BulkChangeWorker {self.name} having to get current_values from VDU") if log.debug_enabled else None
        items_by_vdu: Dict[VduStableId, Dict[int, BulkChangeItem]] = {}
        for item in self.to_do_list:
            if item.vdu_sid not in items_by_vdu:
                items_by_vdu[item.vdu_sid] = {}
            items_by_vdu[item.vdu_sid][item.vcp_code] = item
        for vdu_sid, vdu_items_by_code in items_by_vdu.items():
            for vcp_code, vcp_value in self.main_controller.get_vdu_values(vdu_sid,
                                                                           [item.vcp_code for item in vdu_items_by_code.values()]):
                vdu_current_value = vcp_value.current
                item = vdu_items_by_code[vcp_code]
                # Testing ignore_others prevents initialization stopping due to any over
                # other changes that happen during startup.
                if item.current_value is not None and item.current_value != vdu_current_value and not self.ignore_others:
                    log.warning(f"BulkChangeWorker: Interrupted transitioning change {id=} "
                                f"something else changed the VDU: {vdu_current_value=} != {item.current_value=}")
                    self.stop_requested = True
                    break
                vdu_items_by_code[vcp_code].current_value = vdu_current_value

    def completed_items(self):
        return [item for item in self.to_do_list if item.current_value == item.final_value]
