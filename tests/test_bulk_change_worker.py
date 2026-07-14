# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any

# Import the module under test
from vdu_controls.vdu_bulk_change import BulkChangeItem, BulkChangeWorker
from vdu_controls.ddcutil_aggregator import VduStableId
from vdu_controls.vdu_controller import VcpSetterOrigin
from vdu_controls.vdu_controls_config import ConfOpt




# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def mock_main_controller():
    controller = Mock()
    controller.main_config.is_set.return_value = False
    controller.set_value = Mock()
    controller.get_vdu_values = Mock(return_value=[])
    return controller


@pytest.fixture
def mock_progress_callable():
    return Mock()


@pytest.fixture
def mock_finished_callable():
    return Mock()


@pytest.fixture
def worker(mock_main_controller, mock_progress_callable, mock_finished_callable):
    """Create a BulkChangeWorker instance without invoking __init__."""
    worker = BulkChangeWorker.__new__(BulkChangeWorker)

    worker.name = "test_worker"
    worker.ignore_others = True
    worker.context = None
    worker.start_time = None
    worker.main_controller = mock_main_controller
    worker.progress_callable = mock_progress_callable

    mock_signal = Mock()
    mock_signal.connect = Mock()
    worker.progress_qtsignal = mock_signal

    worker.to_do_list = []
    worker.step_interval = 0.2
    #worker.protect_nvram = False
    worker.change_count = 0
    worker.total_elapsed_seconds = 0.0
    worker.completed = False
    worker.stop_requested = False
    worker.doze = Mock()
    worker.immediately = False
    return worker


# ----------------------------------------------------------------------
# Tests for BulkChangeItem
# ----------------------------------------------------------------------

def test_bulk_change_item():
    item = BulkChangeItem(
        vdu_sid=VduStableId("test-serial"),
        vcp_code=0x10,
        final_value=75,
        starting_value=50,
        current_value=50,
        transition=True
    )
    assert item.vdu_sid == "test-serial"
    assert item.vcp_code == 0x10
    assert item.final_value == 75
    assert item.starting_value == 50
    assert item.current_value == 50
    assert item.transition is True


# ----------------------------------------------------------------------
# Tests for add_item
# ----------------------------------------------------------------------

def test_add_item_no_transition_when_immediately_true(worker):
    worker.immediately = True
    item = BulkChangeItem(VduStableId("test-serial"), 0x10, 75, transition=True)
    worker.add_item(item)
    assert item.transition is False


def test_add_item_no_transition_when_step_interval_too_small(worker):
    worker.step_interval = 0.05
    item = BulkChangeItem(VduStableId("test-serial"), 0x10, 75, transition=True)
    worker.add_item(item)
    assert item.transition is False


def test_add_item_keeps_transition_when_allowed(worker):
    worker.immediately = False
    worker.step_interval = 0.2
    item = BulkChangeItem(VduStableId("test-serial"), 0x10, 75, transition=True)
    worker.add_item(item)
    assert item.transition is True


# ----------------------------------------------------------------------
# Tests for _refresh_current_values_from_vdu
# ----------------------------------------------------------------------

def test_refresh_current_values_from_vdu_no_items(worker):
    worker.to_do_list = []
    worker._refresh_current_values_from_vdu()
    worker.main_controller.get_vdu_values.assert_not_called()


def test_refresh_current_values_from_vdu(worker):
    sid1 = VduStableId("monitor1")
    sid2 = VduStableId("monitor2")
    items = [
        BulkChangeItem(sid1, 0x10, 100, current_value=None),
        BulkChangeItem(sid1, 0x12, 50, current_value=None),
        BulkChangeItem(sid2, 0x10, 80, current_value=None),
    ]
    worker.to_do_list = items

    def get_values_side_effect(vdu_sid, vcp_codes):
        if vdu_sid == sid1:
            return [(0x10, Mock(current=95)), (0x12, Mock(current=45))]
        else:
            return [(0x10, Mock(current=75))]
    worker.main_controller.get_vdu_values.side_effect = get_values_side_effect

    worker._refresh_current_values_from_vdu()
    assert items[0].current_value == 95
    assert items[1].current_value == 45
    assert items[2].current_value == 75


def test_refresh_current_values_mismatch_and_ignore_others_false(worker):
    worker.ignore_others = False
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=50)
    worker.to_do_list = [item]
    worker.main_controller.get_vdu_values.return_value = [(0x10, Mock(current=60))]
    worker._refresh_current_values_from_vdu()
    assert worker.stop_requested is True
    assert item.current_value == 50


def test_refresh_current_values_mismatch_and_ignore_others_true(worker):
    worker.ignore_others = True
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=50)
    worker.to_do_list = [item]
    worker.main_controller.get_vdu_values.return_value = [(0x10, Mock(current=60))]
    worker._refresh_current_values_from_vdu()
    assert worker.stop_requested is False
    assert item.current_value == 60


# ----------------------------------------------------------------------
# Tests for _do_normal_changes
# ----------------------------------------------------------------------

def test_do_normal_changes(worker):
    sid = VduStableId("monitor")
    item1 = BulkChangeItem(sid, 0x10, 100, current_value=100, transition=False)
    item2 = BulkChangeItem(sid, 0x12, 50, current_value=40, transition=False)
    item3 = BulkChangeItem(sid, 0x14, 80, current_value=70, transition=True)
    worker.to_do_list = [item1, item2, item3]

    worker._do_normal_changes()
    # The actual call includes an origin (VcpSetterOrigin.NORMAL)
    worker.main_controller.set_value.assert_called_once_with(sid, 0x12, 50, VcpSetterOrigin.NORMAL_EVENT)
    assert item2.current_value == 50
    assert worker.change_count == 1
    assert item1.current_value == 100
    assert item3.current_value == 70


def test_do_normal_changes_stop_requested(worker):
    sid = VduStableId("monitor")
    item1 = BulkChangeItem(sid, 0x10, 100, current_value=90, transition=False)
    item2 = BulkChangeItem(sid, 0x12, 50, current_value=40, transition=False)
    worker.to_do_list = [item1, item2]
    worker.stop_requested = True
    worker._do_normal_changes()
    worker.main_controller.set_value.assert_not_called()
    assert worker.change_count == 0


# ----------------------------------------------------------------------
# Tests for _do_stepped_changes
# ----------------------------------------------------------------------

def test_do_stepped_changes_no_transition_items(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=100, transition=True)
    worker.to_do_list = [item]
    worker._do_stepped_changes()
    worker.main_controller.set_value.assert_not_called()
    worker.progress_qtsignal.emit.assert_not_called()


def test_do_stepped_changes_single_step(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=95, transition=True)
    worker.to_do_list = [item]
    worker.step_interval = 0.1

    worker._do_stepped_changes()
    worker.main_controller.set_value.assert_called_once_with(
        sid, 0x10, 100, VcpSetterOrigin.NORMAL_EVENT
    )
    assert item.current_value == 100
    assert worker.change_count == 1
    worker.doze.assert_called_once_with(0.1)
    worker.progress_qtsignal.emit.assert_called_once_with(worker)


def test_do_stepped_changes_multiple_steps(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=50, transition=True)
    worker.to_do_list = [item]
    worker.step_interval = 0.2

    def get_values_side_effect(vdu_sid, vcp_codes):
        return [(0x10, Mock(current=item.current_value))]
    worker.main_controller.get_vdu_values.side_effect = get_values_side_effect

    worker._do_stepped_changes()
    assert worker.main_controller.set_value.call_count >= 2
    last_call = worker.main_controller.set_value.call_args_list[-1]
    assert last_call == call(sid, 0x10, 100, VcpSetterOrigin.NORMAL_EVENT)
    assert item.current_value == 100
    assert worker.change_count > 1


def test_do_stepped_changes_stop_requested_during_loop(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=50, transition=True)
    worker.to_do_list = [item]
    worker.step_interval = 0.2

    def get_values_side_effect(vdu_sid, vcp_codes):
        worker.stop_requested = True
        return [(0x10, Mock(current=item.current_value))]
    worker.main_controller.get_vdu_values.side_effect = get_values_side_effect

    worker._do_stepped_changes()
    assert worker.main_controller.set_value.call_count == 1
    assert item.current_value != 100


# ----------------------------------------------------------------------
# Tests for _perform_changes
# ----------------------------------------------------------------------

def test_perform_changes_calls_refresh_if_needed(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=None)
    worker.to_do_list = [item]
    worker._refresh_current_values_from_vdu = Mock()
    worker._do_stepped_changes = Mock()
    worker._do_normal_changes = Mock()
    with patch.object(worker, "start_time", None):
        worker._perform_changes(worker)
    worker._refresh_current_values_from_vdu.assert_called_once()
    worker._do_stepped_changes.assert_called_once()
    worker._do_normal_changes.assert_called_once()


def test_perform_changes_skips_refresh_if_all_current_values_present(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=90)
    worker.to_do_list = [item]
    worker._refresh_current_values_from_vdu = Mock()
    worker._do_stepped_changes = Mock()
    worker._do_normal_changes = Mock()
    with patch.object(worker, "start_time", None):
        worker._perform_changes(worker)
    worker._refresh_current_values_from_vdu.assert_not_called()


def test_perform_changes_sets_completed_flag(worker):
    sid = VduStableId("monitor")
    item1 = BulkChangeItem(sid, 0x10, 100, current_value=100)
    item2 = BulkChangeItem(sid, 0x12, 50, current_value=50)
    worker.to_do_list = [item1, item2]
    worker._do_stepped_changes = Mock()
    worker._do_normal_changes = Mock()
    worker._refresh_current_values_from_vdu = Mock()
    with patch.object(worker, "start_time", None):
        worker._perform_changes(worker)
    assert worker.completed is True


def test_perform_changes_completed_false_if_not_all_done(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=90)
    worker.to_do_list = [item]
    worker._do_stepped_changes = Mock()
    worker._do_normal_changes = Mock()
    worker._refresh_current_values_from_vdu = Mock()
    with patch.object(worker, "start_time", None):
        worker._perform_changes(worker)
    assert worker.completed is False


def test_perform_changes_elapsed_time(worker):
    sid = VduStableId("monitor")
    item = BulkChangeItem(sid, 0x10, 100, current_value=100)
    worker.to_do_list = [item]
    worker._do_stepped_changes = Mock()
    worker._do_normal_changes = Mock()
    worker._refresh_current_values_from_vdu = Mock()
    with patch("vdu_controls.vdu_bulk_change.zoned_now") as mock_now:
        start = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 0, 5)
        mock_now.side_effect = [start, end]
        worker._perform_changes(worker)
    assert worker.total_elapsed_seconds < 0


# ----------------------------------------------------------------------
# Test for completed_items()
# ----------------------------------------------------------------------

def test_completed_items(worker):
    sid = VduStableId("monitor")
    item1 = BulkChangeItem(sid, 0x10, 100, current_value=100)
    item2 = BulkChangeItem(sid, 0x12, 50, current_value=40)
    worker.to_do_list = [item1, item2]
    completed = worker.completed_items()
    assert completed == [item1]