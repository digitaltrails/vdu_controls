# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import threading
import time
from datetime import timedelta
from enum import Enum
from typing import Callable, List, Dict

from vdu_controls.logging import *
from vdu_controls.misc import zoned_now

from vdu_controls.qt_imports import QThread, pyqtSignal

def thread_pid():
    return threading.get_native_id()  # More unique than get_ident (internal IDs get recycled immediately) - see with htop -H.


class WorkException(Exception):
    pass


class WorkerThread(QThread):
    finished_work_qtsignal = pyqtSignal(object)

    def __init__(self, task_body: Callable[[WorkerThread], None], task_finished: Callable[[WorkerThread], None] | None = None,
                 loop: bool = False) -> None:
        super().__init__()
        # init should always be initiated from the GUI thread to grant the worker's __init__ easy access to the GUI thread.
        log_debug(f"WorkerThread: init {self.__class__.__name__} from {thread_pid()=}") if log_debug_enabled else None
        self.stop_requested = False
        self.task_body = task_body
        self.task_finished = task_finished
        self.loop = loop
        if self.task_finished is not None:
            self.finished_work_qtsignal.connect(self.task_finished)
        self.work_exception: WorkException | None = None

    def run(self) -> None:  # called by QThread start(), or call it directly to run synchronously in an existing thread.
        # Long-running task, runs in a separate thread
        class_name = self.__class__.__name__
        try:
            log_debug(f"WorkerThread: {class_name=} running in {thread_pid()=} {self.task_body}") if log_debug_enabled else None
            while not self.stop_requested:
                self.task_body(self)  # Pass self so body can access context
                if not self.loop:
                    break
        except WorkException as e:
            self.work_exception = e
        log_debug(f"WorkerThread: {class_name=} finished {thread_pid()=}") if log_debug_enabled else None
        self.finished_work_qtsignal.emit(self)  # Pass self so body can access context

    def stop(self) -> None:
        log_debug(f"WorkerThread: stop requested {thread_pid()=} {self.task_body}") if log_debug_enabled else None
        self.stop_requested = True
        while self.isRunning():
            time.sleep(0.1)

    def doze(self, seconds: float, sleep_unit: float = 0.5):
        while seconds >= sleep_unit and not self.stop_requested:
            time.sleep(sleep_unit)
            seconds -= sleep_unit
        if not self.stop_requested:
            if seconds > 0.1:
                time.sleep(seconds)


class SchedulerJobType(Enum):
    RESTORE_PRESET = 1
    SCHEDULE_PRESETS = 2


# QTimer replacement - hibernation-tolerant scheduling at specific YYYYMMDD HHMM.
# After hibernation, overdue events will trigger immediately.
class SchedulerJob:  # designed to resemble a QTimer, which it was written to replace

    def __init__(self, when: datetime, job_type: SchedulerJobType, run_callable: Callable, skip_callabled: Callable | None = None):
        assert when.tzinfo is not None
        self.when = when.replace(second=0, microsecond=0)
        self.run_callable = run_callable
        self.skip_callable = skip_callabled
        self.job_type = job_type
        self.has_run = False
        self.attempts = 0
        ScheduleWorker.get_instance().add(self)

    def remaining_time(self):
        return (self.when - zoned_now()).seconds if ScheduleWorker.get_instance().is_supervising(self) else -1

    def run_job(self):
        try:
            self.attempts += 1
            self.run_callable()
        finally:
            self.has_run = True

    def dequeue(self):
        ScheduleWorker.get_instance().remove(self)

    def requeue(self):
        assert not ScheduleWorker.get_instance().is_supervising(self)
        self.has_run = False
        ScheduleWorker.get_instance().add(self)

    def __lt__(self, other: SchedulerJob):
        return self.when < other.when

    def __str__(self):
        return f"[{self.job_type=} {self.when=:%Y-%m-%d %H:%M:%S} {self.attempts=} {self.has_run=}]"


# Worker that runs SchedulerJobs - hibernation-tolerant scheduling at specific YYYYMMDD HHMM.
# (An implementation based on sched.scheduler might also work - but the following is definitely going to work cross platform)
class ScheduleWorker(WorkerThread):
    _instance: 'ScheduleWorker | None' = None
    _scheduler_lock = threading.RLock()

    @staticmethod
    def get_instance():
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance is None or ScheduleWorker._instance.isFinished():
                ScheduleWorker._instance = ScheduleWorker()
                ScheduleWorker._instance.start()
            return ScheduleWorker._instance

    @staticmethod
    def shutdown():
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance is not None and ScheduleWorker._instance.isRunning():
                ScheduleWorker._instance._remove_all()
                ScheduleWorker._instance.stop()

    @staticmethod
    def check():
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance and ScheduleWorker._instance.isRunning():
                log_info(f"Scheduler: off-schedule check requested (queue len={len(ScheduleWorker._instance.pending_jobs_list)})")
                ScheduleWorker._instance._cycle()

    @staticmethod
    def dequeue_all(job_type: SchedulerJobType | None = None):
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance:
                ScheduleWorker._instance._remove_all(job_type)

    @staticmethod
    def is_running() -> bool:
        with ScheduleWorker._scheduler_lock:
            return ScheduleWorker._instance and ScheduleWorker._instance.isRunning()

    def __init__(self) -> None:
        super().__init__(self.task_body, None, True)
        self.pending_jobs_list: List[SchedulerJob] = []

    def task_body(self, _: WorkerThread):
        self._cycle()
        now = datetime.now()  # want just over the next minute boundary e.g. 13:45:05
        sleep_seconds = ((now + timedelta(seconds=60 + 30)).replace(second=5, microsecond=0) - now).seconds
        self.doze(sleep_seconds)  # Have to wake every minute in case PC-sleep or hibernate has occurred.

    def _cycle(self):
        with ScheduleWorker._scheduler_lock:
            local_now = zoned_now()
            run_now: Dict[SchedulerJobType, SchedulerJob] = {}
            for job in self.pending_jobs_list:
                if job.when <= local_now:  # Eligible to run now
                    self.pending_jobs_list.remove(job)
                    if not job.has_run:  # Only the most recent of each type should run
                        if existing_job := run_now.get(job.job_type, None):
                            if job.when > existing_job.when:
                                existing_job.skip_callable()
                                run_now[job.job_type] = job
                            else:
                                job.skip_callable()
                        else:
                            run_now[job.job_type] = job
            for job in run_now.values():
                log_debug(f"Scheduler: Starting {job=!s} queued={len(self.pending_jobs_list)}") if log_debug_enabled else None
                job.run_job()

    def add(self, job: SchedulerJob) -> SchedulerJob:
        with ScheduleWorker._scheduler_lock:
            assert job not in self.pending_jobs_list
            self.pending_jobs_list.append(job)
            log_debug(f"Scheduler: added {job=!s} queued={len(self.pending_jobs_list)}") if log_debug_enabled else None
            return job

    def remove(self, job: SchedulerJob):
        with ScheduleWorker._scheduler_lock:
            if job in self.pending_jobs_list:
                self.pending_jobs_list.remove(job)
                log_debug(f"Scheduler: removed {job=!s} queued={len(self.pending_jobs_list)}") if log_debug_enabled else None

    def _remove_all(self, job_type: SchedulerJobType | None = None):
        with ScheduleWorker._scheduler_lock:
            for job in [j for j in self.pending_jobs_list if job_type is None or j.job_type == job_type]:
                self.remove(job)
            log_debug(f"Scheduler: remove type {job_type!s} ({len(self.pending_jobs_list)} remain)") if log_debug_enabled else None

    def is_supervising(self, job: SchedulerJob):
        return job in self.pending_jobs_list


