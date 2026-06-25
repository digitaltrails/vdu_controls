# tests/test_work_scheduler.py
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure src is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

# Patch QThread and pyqtSignal before importing the module
with patch("vdu_controls.work_scheduler.QThread", MagicMock()), \
     patch("vdu_controls.work_scheduler.pyqtSignal", lambda *args, **kwargs: MagicMock()):
    from vdu_controls.work_scheduler import (
        WorkerThread,
        SchedulerJob,
        SchedulerJobType,
        ScheduleWorker,
        WorkException,
        thread_pid,
    )


# ----------------------------------------------------------------------
# Tests for WorkerThread
# ----------------------------------------------------------------------

def test_worker_thread_doze_no_stop():
    """doze sleeps for the requested time if stop_requested is False."""
    worker = WorkerThread(task_body=lambda w: None, loop=False)
    worker.stop_requested = False
    with patch("vdu_controls.work_scheduler.sys_time.sleep") as mock_sleep:
        worker.doze(2.0, sleep_unit=0.5)
        # Expected calls: 0.5, 0.5, 0.5, 0.5 (four times, then remaining 0)
        # Actually doze loops while seconds >= sleep_unit, subtracts, then sleeps remaining if >=0.1
        # For 2.0 with 0.5 unit: 4 loops (2.0,1.5,1.0,0.5) then seconds=0, no final sleep.
        mock_sleep.assert_has_calls([call(0.5), call(0.5), call(0.5), call(0.5)])
        assert mock_sleep.call_count == 4


def test_worker_thread_doze_with_stop():
    """doze exits early if stop_requested becomes True."""
    worker = WorkerThread(task_body=lambda w: None, loop=False)
    worker.stop_requested = False
    with patch("vdu_controls.work_scheduler.sys_time.sleep") as mock_sleep:
        # Simulate stop_requested becoming True after first sleep
        def side_effect(seconds):
            worker.stop_requested = True
        mock_sleep.side_effect = side_effect
        worker.doze(2.0, sleep_unit=0.5)
        # Only one sleep called
        mock_sleep.assert_called_once_with(0.5)


def test_worker_thread_run_calls_task_body():
    """run() calls task_body and then finishes (loop=False)."""
    task_body = MagicMock()
    worker = WorkerThread(task_body=task_body, loop=False)
    worker.run()
    task_body.assert_called_once_with(worker)


def test_worker_thread_run_loop():
    """run() loops while not stop_requested and loop=True."""
    task_body = MagicMock()
    worker = WorkerThread(task_body=task_body, loop=True)
    # Stop after two iterations
    def stop_after_two(*args):
        if task_body.call_count == 2:
            worker.stop_requested = True
    task_body.side_effect = stop_after_two
    worker.run()
    # Called twice: first iteration, second iteration sets stop_requested and then loop condition fails
    assert task_body.call_count == 2


def test_worker_thread_run_raises_work_exception():
    """run() catches WorkException and stores it."""
    def faulty_body(worker):
        raise WorkException("test error")
    worker = WorkerThread(task_body=faulty_body, loop=False)
    worker.run()
    assert isinstance(worker.work_exception, WorkException)
    assert str(worker.work_exception) == "test error"


def test_worker_thread_stop():
    """stop() sets stop_requested and waits for thread to finish (isRunning mocked)."""
    worker = WorkerThread(task_body=lambda w: None, loop=True)
    worker.isRunning = MagicMock(side_effect=[True, True, False])  # first two calls True, then False
    with patch("vdu_controls.work_scheduler.sys_time.sleep") as mock_sleep:
        worker.stop()
    assert worker.stop_requested is True
    mock_sleep.assert_called_with(0.1)  # called at least once


# ----------------------------------------------------------------------
# Tests for SchedulerJob
# ----------------------------------------------------------------------

def test_scheduler_job_creation():
    """SchedulerJob initializes correctly and adds itself to ScheduleWorker."""
    with patch("vdu_controls.work_scheduler.ScheduleWorker.get_instance") as mock_get:
        mock_worker = MagicMock()
        mock_get.return_value = mock_worker
        when = datetime(2025, 1, 1, 12, 0, tzinfo=datetime.now().astimezone().tzinfo)
        run_callable = MagicMock()
        job = SchedulerJob(when, SchedulerJobType.RESTORE_PRESET, run_callable)
        assert job.when == when.replace(second=0, microsecond=0)
        assert job.run_callable == run_callable
        assert job.job_type == SchedulerJobType.RESTORE_PRESET
        assert job.has_run is False
        assert job.attempts == 0
        mock_worker.add.assert_called_once_with(job)


def test_scheduler_job_remaining_time():
    """remaining_time() returns seconds until when (or -1 if not supervised)."""
    with patch("vdu_controls.work_scheduler.ScheduleWorker.get_instance") as mock_get:
        mock_worker = MagicMock()
        mock_worker.is_supervising.return_value = True
        mock_get.return_value = mock_worker
        # Mock zoned_now to return fixed time
        with patch("vdu_controls.work_scheduler.zoned_now") as mock_now:
            base = datetime(2025, 1, 1, 12, 0, tzinfo=datetime.now().astimezone().tzinfo)
            mock_now.return_value = base
            when = base + timedelta(seconds=120)
            job = SchedulerJob(when, SchedulerJobType.RESTORE_PRESET, MagicMock())
            assert job.remaining_time() == 120

            # When not supervising
            mock_worker.is_supervising.return_value = False
            assert job.remaining_time() == -1


def test_scheduler_job_run_job():
    """run_job() calls run_callable and increments attempts, sets has_run=True."""
    run_callable = MagicMock()
    job = SchedulerJob(datetime.now().astimezone(), SchedulerJobType.RESTORE_PRESET, run_callable)
    job.run_job()
    while not job.has_run:
        time.sleep(1)
    run_callable.assert_called_once()
    assert job.attempts == 1
    assert job.has_run is True


def test_scheduler_job_dequeue():
    """dequeue() removes job from ScheduleWorker."""
    with patch("vdu_controls.work_scheduler.ScheduleWorker.get_instance") as mock_get:
        mock_worker = MagicMock()
        mock_get.return_value = mock_worker
        job = SchedulerJob(datetime.now().astimezone(), SchedulerJobType.RESTORE_PRESET, MagicMock())
        job.dequeue()
        mock_worker.remove.assert_called_once_with(job)


def test_scheduler_job_requeue():
    """requeue() resets has_run and re-adds job to ScheduleWorker."""
    job = SchedulerJob(datetime.now().astimezone() + timedelta(days=1), SchedulerJobType.RESTORE_PRESET, MagicMock())
    assert ScheduleWorker.get_instance().is_supervising(job)
    assert job in ScheduleWorker.get_instance().pending_jobs_list
    job.dequeue()
    assert not ScheduleWorker.get_instance().is_supervising(job)
    job.has_run = True
    job.requeue()
    assert job.has_run is False
    assert job in ScheduleWorker.get_instance().pending_jobs_list


def test_scheduler_job_lt():
    """SchedulerJob comparison uses when attribute."""
    tz = datetime.now().astimezone().tzinfo
    earlier = SchedulerJob(datetime(2025, 1, 1, 12, 0, tzinfo=tz), SchedulerJobType.RESTORE_PRESET, MagicMock())
    later = SchedulerJob(datetime(2025, 1, 1, 13, 0, tzinfo=tz), SchedulerJobType.RESTORE_PRESET, MagicMock())
    assert earlier < later
    assert not (later < earlier)


# ----------------------------------------------------------------------
# Tests for ScheduleWorker
# ----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_schedule_worker_singleton():
    """Reset the ScheduleWorker singleton before each test."""
    with patch("vdu_controls.work_scheduler.ScheduleWorker._scheduler_lock", new=MagicMock()):
        ScheduleWorker._instance = None
        # Also need to patch QThread.start to avoid real thread creation
        with patch("vdu_controls.work_scheduler.QThread.start"):
            yield
        ScheduleWorker._instance = None


def test_schedule_worker_singleton():
    """get_instance creates one instance and reuses it."""
    worker1 = ScheduleWorker.get_instance()
    worker2 = ScheduleWorker.get_instance()
    assert worker1 is worker2
    # Calling get_instance after stop should create new instance
    ScheduleWorker.shutdown()
    # Whether it actually ran or not, isRunning should be false.
    assert not ScheduleWorker._instance.isRunning()
    worker3 = ScheduleWorker.get_instance()
    assert not worker3.isFinished()


def test_schedule_worker_add_remove():
    """add() and remove() work correctly."""
    worker = ScheduleWorker.get_instance()
    job = MagicMock(spec=SchedulerJob)
    worker.add(job)
    assert job in worker.pending_jobs_list
    worker.remove(job)
    assert job not in worker.pending_jobs_list


def test_schedule_worker_cycle_runs_due_jobs():
    """_cycle() runs jobs whose when <= now, and removes them."""
    worker = ScheduleWorker.get_instance()
    tz = datetime.now().astimezone().tzinfo
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz)
    past_job = MagicMock(spec=SchedulerJob)
    past_job.when = now - timedelta(minutes=1)
    past_job.has_run = False
    past_job.job_type = SchedulerJobType.RESTORE_PRESET
    past_job.run_job = MagicMock()
    past_job.skip_callable = None
    future_job = MagicMock(spec=SchedulerJob)
    future_job.when = now + timedelta(minutes=1)
    future_job.has_run = False
    future_job.run_job = MagicMock()
    worker.pending_jobs_list = [past_job, future_job]

    with patch("vdu_controls.work_scheduler.zoned_now", return_value=now):
        worker._cycle()

    # Past job should be removed and run
    assert past_job not in worker.pending_jobs_list
    past_job.run_job.assert_called_once()
    # Future job remains
    assert future_job in worker.pending_jobs_list
    future_job.run_job.assert_not_called()


def test_schedule_worker_cycle_multiple_same_type_keeps_latest():
    """When multiple jobs of same type are due, only the latest (largest when) runs,
       and older ones have skip_callable called if provided."""
    worker = ScheduleWorker.get_instance()
    tz = datetime.now().astimezone().tzinfo
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz)
    earlier = MagicMock(spec=SchedulerJob)
    earlier.when = now - timedelta(minutes=10)
    earlier.has_run = False
    earlier.job_type = SchedulerJobType.RESTORE_PRESET
    earlier.run_job = MagicMock()
    earlier.skip_callable = MagicMock()
    later = MagicMock(spec=SchedulerJob)
    later.when = now - timedelta(minutes=5)
    later.has_run = False
    later.job_type = SchedulerJobType.RESTORE_PRESET
    later.run_job = MagicMock()
    later.skip_callable = MagicMock()
    worker.pending_jobs_list = [earlier, later]

    with patch("vdu_controls.work_scheduler.zoned_now", return_value=now):
        worker._cycle()

    # Only later runs, earlier is skipped
    later.run_job.assert_called_once()
    earlier.run_job.assert_not_called()
    earlier.skip_callable.assert_called_once()
    later.skip_callable.assert_not_called()
    # Both removed from pending
    assert earlier not in worker.pending_jobs_list
    assert later not in worker.pending_jobs_list


def test_schedule_worker_cycle_skip_callable_not_called_if_no_skip():
    """If a skipped job has no skip_callable, nothing bad happens."""
    worker = ScheduleWorker.get_instance()
    tz = datetime.now().astimezone().tzinfo
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz)
    earlier = MagicMock(spec=SchedulerJob)
    earlier.when = now - timedelta(minutes=10)
    earlier.has_run = False
    earlier.job_type = SchedulerJobType.RESTORE_PRESET
    earlier.run_job = MagicMock()
    earlier.skip_callable = None  # No skip callable
    later = MagicMock(spec=SchedulerJob)
    later.when = now - timedelta(minutes=5)
    later.has_run = False
    later.job_type = SchedulerJobType.RESTORE_PRESET
    later.run_job = MagicMock()
    later.skip_callable = None
    worker.pending_jobs_list = [earlier, later]

    with patch("vdu_controls.work_scheduler.zoned_now", return_value=now):
        worker._cycle()

    later.run_job.assert_called_once()
    earlier.run_job.assert_not_called()
    # No exception


def test_schedule_worker_cycle_does_not_run_already_run_jobs():
    """Jobs that already have has_run=True are not executed again."""
    worker = ScheduleWorker.get_instance()
    tz = datetime.now().astimezone().tzinfo
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz)
    job = MagicMock(spec=SchedulerJob)
    job.when = now - timedelta(minutes=1)
    job.has_run = True   # Already ran
    job.job_type = SchedulerJobType.RESTORE_PRESET
    job.run_job = MagicMock()
    worker.pending_jobs_list = [job]

    with patch("vdu_controls.work_scheduler.zoned_now", return_value=now):
        worker._cycle()

    # Should be removed but not run
    assert job not in worker.pending_jobs_list
    job.run_job.assert_not_called()


def test_schedule_worker_dequeue_all():
    """dequeue_all removes all jobs, optionally filtered by type."""
    worker = ScheduleWorker.get_instance()
    job1 = MagicMock(spec=SchedulerJob)
    job1.job_type = SchedulerJobType.RESTORE_PRESET
    job2 = MagicMock(spec=SchedulerJob)
    job2.job_type = SchedulerJobType.SCHEDULE_PRESETS
    worker.pending_jobs_list = [job1, job2]

    ScheduleWorker.dequeue_all(job_type=SchedulerJobType.RESTORE_PRESET)
    assert job1 not in worker.pending_jobs_list
    assert job2 in worker.pending_jobs_list

    ScheduleWorker.dequeue_all()  # remove all
    assert job2 not in worker.pending_jobs_list


def test_schedule_worker_shutdown():
    """shutdown stops the worker and removes all jobs."""
    worker = ScheduleWorker.get_instance()
    worker.isRunning = MagicMock(return_value=True)
    worker.stop = MagicMock()
    worker._remove_all = MagicMock()
    ScheduleWorker.shutdown()
    worker._remove_all.assert_called_once()
    worker.stop.assert_called_once()
    # Instance should be set to None after shutdown? Actually shutdown does not set _instance to None,
    # but get_instance will create a new one if isFinished() returns True.
    # We'll just check that stop and remove_all are called.


def test_schedule_worker_check():
    """check() calls _cycle if instance is running."""
    worker = ScheduleWorker.get_instance()
    worker._cycle = MagicMock()
    worker.isRunning = MagicMock(return_value=True)
    ScheduleWorker.check()
    worker._cycle.assert_called_once()
    # If not running, no cycle
    worker.isRunning.return_value = False
    worker._cycle.reset_mock()
    ScheduleWorker.check()
    worker._cycle.assert_not_called()


def test_schedule_worker_is_running():
    """is_running returns correct status."""
    worker = ScheduleWorker.get_instance()
    worker.isRunning = MagicMock(return_value=True)
    assert ScheduleWorker.is_running() is True
    worker.isRunning.return_value = False
    assert ScheduleWorker.is_running() is False
    # Also when instance is None
    ScheduleWorker._instance = None
    assert ScheduleWorker.is_running() is False


def test_schedule_worker_task_body_calls_cycle_and_doze():
    """task_body runs _cycle then sleeps until near next minute."""
    worker = ScheduleWorker.get_instance()
    worker._cycle = MagicMock()
    worker.doze = MagicMock()
    # Mock zoned_now to return fixed time and then a later time for sleep calculation
    base = datetime(2025, 1, 1, 12, 34, 5, tzinfo=datetime.now().astimezone().tzinfo)
    with patch("vdu_controls.work_scheduler.zoned_now", return_value=base):
        worker.task_body(worker)
    worker._cycle.assert_called_once()
    # Sleep should be to next minute's 5 seconds: (12:35:05 - 12:34:05) = 60 seconds
    worker.doze.assert_called_once_with(60)


# ----------------------------------------------------------------------
# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__])
