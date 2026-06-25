# tests/test_rate_limiter.py
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path

import pytest

# Ensure src is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from unittest.mock import patch

from vdu_controls.ddcutil_aggregator import DdcutilAggregator
from vdu_controls.ddcutil_abstract import DdcutilSetterRateExceeded


@pytest.fixture(autouse=True)
def reset_class_state():
    """
    Reset the class-level history before each test.
    This ensures tests are isolated.
    """
    DdcutilAggregator.clear_setter_cascade_blocking()
    yield


def test_rate_limiter_allows_first_rate_max_calls():
    """First max calls for a given (vdu, vcp) should succeed."""
    key = ("monitor1", 0x10)

    for i in range(DdcutilAggregator._RATE_MAX_CALLS):
        # No exception should be raised
        assert DdcutilAggregator._check_setter_rate_limit(key)

    # After max calls, history should have max timestamps
    assert len(DdcutilAggregator._setter_history[key]) == DdcutilAggregator._RATE_MAX_CALLS


def test_rate_limiter_blocks_max_plus_one_call():
    """The max+1 call within the window should raise RateLimitExceeded."""
    key = ("monitor1", 0x10)

    for _ in range(DdcutilAggregator._RATE_MAX_CALLS):
        assert DdcutilAggregator._check_setter_rate_limit(key)

    with pytest.raises(DdcutilSetterRateExceeded) as exc_info:
        assert not DdcutilAggregator._check_setter_rate_limit(key)

    assert "Cascade detected" in str(exc_info.value)
    assert f"{DdcutilAggregator._RATE_MAX_CALLS + 1} calls" in str(exc_info.value)


def test_rate_limiter_allows_after_window_expires():
    """
    After the time window passes, one more call should be allowed.
    We simulate time passing by patching time.monotonic.
    """
    key = ("monitor1", 0x10)

    # Freeze time at T=0.0
    with patch("time.monotonic", return_value=0.0):
        # Make max calls at T=0
        for _ in range(DdcutilAggregator._RATE_MAX_CALLS):
            assert DdcutilAggregator._check_setter_rate_limit(key)

    # Advance time to just past the window (2.0s + 0.001)
    with patch("time.monotonic", return_value=DdcutilAggregator._RATE_WINDOW_SECONDS + 0.001):
        # This call should succeed (old entries expire)
        assert DdcutilAggregator._check_setter_rate_limit(key)

    # After this, the deque should contain only the new timestamp(s)
    # The old max are pruned, plus the new one → length = 1
    assert len(DdcutilAggregator._setter_history[key]) == 1


def test_rate_limiter_with_combined_vdu_vcp_keys():
    """Different (vdu, vcp) keys have separate histories."""
    key1 = ("monitorA", 0x10)
    key2 = ("monitorB", 0x20)

    # Make max calls for key1 (fills its window)
    for _ in range(DdcutilAggregator._RATE_MAX_CALLS):
        assert DdcutilAggregator._check_setter_rate_limit(key1)

    # key2 should still be empty and allow calls
    assert DdcutilAggregator._check_setter_rate_limit(key2)  # No exception

    assert len(DdcutilAggregator._setter_history[key1]) == DdcutilAggregator._RATE_MAX_CALLS
    assert len(DdcutilAggregator._setter_history[key2]) == 1


def test_rate_limiter_handles_pruning_correctly():
    """
    Old entries are pruned before checking the count.
    """
    key = ("monitor1", 0x10)

    with patch("time.monotonic", return_value=0.0):
        for _ in range(DdcutilAggregator._RATE_MAX_CALLS - 1):
            assert DdcutilAggregator._check_setter_rate_limit(key)

    with patch("time.monotonic", return_value=DdcutilAggregator._RATE_WINDOW_SECONDS - 0.5):
        # Still within window, count < max, so allowed
        assert DdcutilAggregator._check_setter_rate_limit(key)

    with patch("time.monotonic", return_value=DdcutilAggregator._RATE_WINDOW_SECONDS + 0.1):
        assert DdcutilAggregator._check_setter_rate_limit(key)
        pass

def test_rate_limiter_vetos_after_cascade():
    """Different (vdu, vcp) keys have separate histories."""
    key1 = ("monitorA", 0x10)
    key2 = ("monitorB", 0x20)

    # Make max calls for key1 (fills its window)
    for _ in range(DdcutilAggregator._RATE_MAX_CALLS):
        assert DdcutilAggregator._check_setter_rate_limit(key1)

    assert DdcutilAggregator._check_setter_rate_limit(key2)

    with pytest.raises(DdcutilSetterRateExceeded) as exc_info:
        assert not DdcutilAggregator._check_setter_rate_limit(key1)

    assert "Cascade detected" in str(exc_info.value)
    assert len(DdcutilAggregator._setter_history[key1]) == DdcutilAggregator._RATE_MAX_CALLS + 1
    assert len(DdcutilAggregator._setter_history[key2]) == 1

    assert not DdcutilAggregator._check_setter_rate_limit(key1)
    assert not DdcutilAggregator._check_setter_rate_limit(key2)

def test_rate_limiter_clear_after_cascade():
    """Different (vdu, vcp) keys have separate histories."""
    key1 = ("monitorA", 0x10)
    key2 = ("monitorB", 0x20)

    # Make max calls for key1 (fills its window)
    for _ in range(DdcutilAggregator._RATE_MAX_CALLS):
        assert DdcutilAggregator._check_setter_rate_limit(key1)

    with pytest.raises(DdcutilSetterRateExceeded) as exc_info:
        assert not DdcutilAggregator._check_setter_rate_limit(key1)
    assert "Cascade detected" in str(exc_info.value)
    assert not DdcutilAggregator._check_setter_rate_limit(key1)
    assert not DdcutilAggregator._check_setter_rate_limit(key2)
    DdcutilAggregator.clear_setter_cascade_blocking()
    assert DdcutilAggregator._check_setter_rate_limit(key1)
    assert DdcutilAggregator._check_setter_rate_limit(key2)

