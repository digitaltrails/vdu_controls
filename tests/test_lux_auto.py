from __future__ import annotations
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import sys
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List, Optional

from vdu_controls.ddcutil_aggregator import VduStableId

# Ensure src is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

# The module under test – we need to import the classes after patching dependencies.
# We'll patch the heavy imports (Qt, vdu_controls.*) before importing the module.

# Patch all imports that rely on Qt or external hardware before importing the module.
@pytest.fixture(autouse=True)
def patch_external_dependencies():
    with patch.multiple(
        'vdu_controls.qt_imports',
        Qt=MagicMock(),
        pyqtSignal=MagicMock(),
    ), patch.multiple(
        'vdu_controls.gui_misc',
        is_running_in_gui_thread=MagicMock(return_value=True),
    ), patch.multiple(
        'vdu_controls.logging',
        info=MagicMock(),
        debug=MagicMock(),
        error=MagicMock(),
        warning=MagicMock(),
        debug_enabled=PropertyMock(return_value=True),
    ), patch.multiple(
        'vdu_controls.app_locale',
        tr=MagicMock(side_effect=lambda x: x),  # return the input as translation
    ), patch.multiple(
        'vdu_controls.ddcutil_abstract',
        DdcutilSetterRateExceeded=Exception,
    ), patch.multiple(
        'vdu_controls.vdu_exceptions',
        VduException=Exception,
    ), patch.multiple(
        'vdu_controls.lux_config',
        LuxConfig=MagicMock,
    ), patch.multiple(
        'vdu_controls.lux_meters',
        lux_create_device=MagicMock(return_value=MagicMock()),
        LuxMeterDevice=MagicMock,
        LuxMeterSemiAutoDevice=MagicMock,
        LuxDeviceException=Exception,
    ), patch.multiple(
        'vdu_controls.preset',
        PresetTransitionFlag=MagicMock(SCHEDULED=1),
    ), patch.multiple(
        'vdu_controls.vdu_bulk_change',
        BulkChangeWorker=MagicMock,
        BulkChangeItem=MagicMock,
    ), patch.multiple(
        'vdu_controls.widgets',
        MBox=MagicMock,
        MIcon=MagicMock,
        ToolButton=MagicMock,
    ), patch.multiple(
        'vdu_controls.work_scheduler',
        WorkerThread=MagicMock,
        thread_pid=MagicMock(return_value=12345),
    ), patch.multiple(
        'vdu_controls.lux_dialog',
        LuxDialog=MagicMock,
    ), patch.multiple(
        'vdu_controls.lux_ambient_slider',
        LuxAmbientSlider=MagicMock,
    ), patch.multiple(
        'vdu_controls.config_ini',
        ConfIni=MagicMock,
    ), patch.multiple(
        'vdu_controls.constants',
        MsgDestination=MagicMock(DEFAULT=0, COUNTDOWN=1),
    ), patch.multiple(
        'vdu_controls.svg',
        AUTO_LUX_ON_SVG=b'',
        LIGHTING_CHECK_SVG=b'',
        AUTO_LUX_OFF_SVG=b'',
        LIGHTING_CHECK_OFF_SVG=b'',
    ), patch.multiple(
        'vdu_controls.unicode',
        TIMER_RUNNING_SYMBOL='⏳',
        SUN_SYMBOL='☀️',
        PROCESSING_LUX_SYMBOL='⚙️',
        STEPPING_SYMBOL='🚶',
        ERROR_SYMBOL='❌',
        RAISED_HAND_SYMBOL='✋',
        ALMOST_EQUAL_SYMBOL='≈',
        SMOOTHING_SYMBOL='~',
    ):
        yield

# Now import the module after patching
from vdu_controls.lux_auto import (
    LuxSmooth,
    LuxAutoWorker,
    LuxAutoController,
    LuxToDo,
    LuxPoint,
)
from vdu_controls.vdu_exceptions import VduException


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def mock_main_controller():
    """Create a mock VduAppController with basic methods."""
    mc = MagicMock()
    mc.main_window = MagicMock()
    mc.main_config = MagicMock()
    mc.main_config.get_location = MagicMock(return_value="TestLocation")
    mc.get_vdu_stable_id_list = MagicMock(return_value=["sid1", "sid2"])
    mc.get_range = MagicMock(return_value=(0, 100))
    mc.get_value = MagicMock(return_value=50)
    mc.find_preset_by_name = MagicMock(return_value=None)
    mc.restore_preset = MagicMock()
    mc.update_window_status_indicators = MagicMock()
    mc.busy_doing = MagicMock(return_value=None)
    mc.show_vdu_exception = MagicMock()
    mc.status_message = MagicMock()
    return mc


@pytest.fixture
def mock_lux_config():
    """Create a mock LuxConfig with default values."""
    lc = MagicMock()
    lc.get_interval_minutes = MagicMock(return_value=5)
    lc.getint = MagicMock(return_value=3)
    lc.getfloat = MagicMock(return_value=0.5)
    lc.getboolean = MagicMock(return_value=True)
    lc.is_auto_enabled = MagicMock(return_value=True)
    lc.get_device_name = MagicMock(return_value="test-device")
    lc.get = MagicMock(return_value="[]")  # for profile
    lc.has_option = MagicMock(return_value=False)
    lc.get_preset_points = MagicMock(return_value=[])
    return lc


@pytest.fixture
def mock_auto_controller(mock_main_controller, mock_lux_config):
    """Create a mock LuxAutoController."""
    ac = MagicMock(spec=LuxAutoController)
    ac.main_controller = mock_main_controller
    ac.lux_config = mock_lux_config
    ac.lux_meter = MagicMock()
    ac.lux_meter.has_manual_capability = False
    ac.lux_meter.get_status = MagicMock(return_value=(True, None))
    ac.lux_meter.get_value = MagicMock(return_value=500.0)
    ac.get_lux_config = MagicMock(return_value=mock_lux_config)
    ac.get_lux_profile = MagicMock(return_value=[
        LuxPoint(0, 0),
        LuxPoint(100, 50),
        LuxPoint(1000, 80),
        LuxPoint(10000, 90),
        LuxPoint(100000, 100),
    ])
    return ac


@pytest.fixture
def lux_worker(mock_auto_controller):
    """Create a LuxAutoWorker instance with mocked dependencies."""
    with patch('vdu_controls.lux_auto.LuxAutoWorker._lux_dialog_message_qtsignal', new_callable=MagicMock) as mock_signal:
        worker = LuxAutoWorker(mock_auto_controller, single_shot=False)
        # Mock signal emit to avoid GUI interaction
        worker.status_message = MagicMock()
        worker.doze = MagicMock()  # prevent sleeps
        worker._lux_dialog_message_qtsignal = MagicMock()
        return worker


# ----------------------------------------------------------------------
# Tests for LuxSmooth
# ----------------------------------------------------------------------

class TestLuxSmooth:
    def test_initialization(self):
        smoother = LuxSmooth(n=3, alpha=0.5)
        assert smoother.length == 3
        assert smoother.alpha == 0.5
        assert smoother.input == []
        assert smoother.output == []

    def test_smoothing_single_value(self):
        smoother = LuxSmooth(n=3, alpha=0.5)
        result = smoother.smooth(10.0)
        assert result == 10
        assert smoother.input == [10.0]
        assert smoother.output == [10.0]

    def test_smoothing_multiple_values(self):
        smoother = LuxSmooth(n=3, alpha=0.5)
        # sequence: 10, 20, 30
        # expected: y1=10, y2=10+0.5*(20-10)=15, y3=15+0.5*(30-15)=22.5 -> 22 (python rounds n.5 to n)
        assert smoother.smooth(10) == 10
        assert smoother.smooth(20) == 15
        assert smoother.smooth(30) == 22

    def test_smoothing_rolling_window(self):
        smoother = LuxSmooth(n=3, alpha=0.5)
        # input: 10, 20, 30, 40
        # after 30, window full. When 40 arrives, pop first and recompute.
        smoother.smooth(10)
        smoother.smooth(20)
        smoother.smooth(30)  # output: [10,15,23]
        assert smoother.output == [10,15,22.5]
        # Now push 40 -> input becomes [20,30,40], output becomes [15,23,?]
        # compute: y3 = 22.5 + 0.5*(40-22.5) = 31.25
        result = smoother.smooth(40)
        assert result == 31
        assert smoother.input == [20.0, 30.0, 40.0]
        assert smoother.output == [15.0, 22.5, 31.25]


# ----------------------------------------------------------------------
# Tests for LuxAutoWorker (core logic)
# ----------------------------------------------------------------------

class TestLuxAutoWorker:
    def test_interpolate_brightness_linear(self, lux_worker):
        """Test interpolation between two points on logarithmic scale."""
        # Points: (0 lux, 0%), (100 lux, 50%) -> at 50 lux should be ~25%?
        # Actually interpolation is logarithmic in lux.
        point1 = LuxPoint(0, 0)
        point2 = LuxPoint(100, 50)
        # At 50 lux, log10(50)/log10(100000) = log10(50)/5. Usually small.
        # Let's compute expected using worker's formula.
        result = lux_worker.interpolate_brightness(50, point1, point2)
        # Manual calculation: x_smoothed = log10(50)/5 ≈ 0.3398, x1=0, x2=log10(100)/5=0.4
        # diff = (50-0)*(0.3398-0)/0.4 = 50*0.8495 = 42.48 => 42
        assert result == 42  # using rounding

    def test_interpolate_brightness_exact_match(self, lux_worker):
        point1 = LuxPoint(100, 20)
        point2 = LuxPoint(200, 80)
        result = lux_worker.interpolate_brightness(100, point1, point2)
        assert result == 20  # exactly at point1

    def test_interpolate_brightness_zero_lux(self, lux_worker):
        point1 = LuxPoint(0, 10)
        point2 = LuxPoint(100, 50)
        result = lux_worker.interpolate_brightness(0, point1, point2)
        assert result == 10

    def test_assess_preset_proximity_no_preset(self, lux_worker):
        """When no preset is close enough, return None."""
        # Create points with preset_name None
        p1 = LuxPoint(0, 0)
        p2 = LuxPoint(100, 50)
        p3 = LuxPoint(1000, 80)
        # proposed brightness = 55, sensitivity=10
        result = lux_worker.assess_preset_proximity(55, p1, p2, p3)
        assert result is None

    def test_assess_preset_proximity_with_preset(self, lux_worker):
        # Make matched_point have a preset_name
        p1 = LuxPoint(0, 0)
        p2 = LuxPoint(100, 50, preset_name="PresetA")
        p3 = LuxPoint(1000, 80)
        # proposed brightness = 52, diff to p2 is 2 < sensitivity (10) => returns "PresetA"
        result = lux_worker.assess_preset_proximity(52, p1, p2, p3)
        assert result == "PresetA"

    def test_assess_preset_proximity_closest(self, lux_worker):
        # Several presets, choose closest.
        p1 = LuxPoint(0, 0)
        p2 = LuxPoint(100, 50, preset_name="PresetA")
        p3 = LuxPoint(1000, 80, preset_name="PresetB")
        proposed = p3.brightness - lux_worker.sensitivity_percent + 1
        result = lux_worker.assess_preset_proximity(proposed, p1, p2, p3)
        assert result == "PresetB"

    def test_determine_changes_no_change_due_to_sensitivity(self, lux_worker, mock_main_controller):
        """If difference is less than sensitivity, return None."""
        lux_worker.interpolation_enabled = True
        lux_worker.sensitivity_percent = 10
        # Set current brightness to 48, proposed from profile at lux 500 -> should be ~50?
        # We'll mock the profile points and get_value.
        mock_main_controller.get_value.return_value = 48  # current
        # profile: (0,0), (100,50), (1000,80)...
        # For lux=500, interpolation between 100 and 1000: 50 + (80-50)*(log10(500)-log10(100))/(log10(1000)-log10(100))
        # log10(500)=2.699, log10(100)=2, log10(1000)=3 -> 50+30*(0.699/1)=50+20.97=70.97 -> 71
        # diff=71-48=23 > sensitivity(10) -> should return a LuxToDo.
        # But to test 'ignored too small', we need diff < sensitivity.
        # Let's set current brightness to 69, diff=71-69=2 < 10 => returns None.
        mock_main_controller.get_value.return_value = 69
        result = lux_worker.determine_changes("sid1", 500, [
            LuxPoint(0, 0),
            LuxPoint(100, 50),
            LuxPoint(1000, 80),
            LuxPoint(10000, 90),
            LuxPoint(100000, 100),
        ])
        assert result is None

    def test_determine_changes_with_preset(self, lux_worker, mock_main_controller):
        """Test that preset proximity returns a preset name."""
        lux_worker.sensitivity_percent = 10
        # Make a point with preset_name
        profile = [
            LuxPoint(0, 0),
            LuxPoint(100, 50, preset_name="PresetA"),
            LuxPoint(1000, 80),
            LuxPoint(10000, 90),
            LuxPoint(100000, 100),
        ]
        mock_main_controller.get_value.return_value = 45  # diff to 50 is 5 < 10
        result = lux_worker.determine_changes("sid1", 100, profile)  # lux exactly 100 -> brightness 50
        assert result is not None
        assert result.vdu_sid == "sid1"
        assert result.brightness == 50
        assert result.preset_name == "PresetA"
        assert result.current_brightness == 45

    def test_determine_changes_no_preset(self, lux_worker, mock_main_controller):
        """No preset, but brightness changes."""
        lux_worker.sensitivity_percent = 10
        profile = [
            LuxPoint(0, 0),
            LuxPoint(100, 50),
            LuxPoint(1000, 80),
        ]
        mock_main_controller.get_value.return_value = 20
        result = lux_worker.determine_changes("sid1", 150, profile)  # interpolate between 100 and 1000
        # Should return a todo without preset
        assert result is not None
        assert result.vdu_sid == "sid1"
        assert result.preset_name is None
        assert result.current_brightness == 20
        # brightness ~ 50 + (80-50)*(log10(150)-log10(100))/(log10(1000)-log10(100))
        # log10(150)=2.176, log10(100)=2, diff=0.176, /1 => 50+30*0.176=55.28->55
        assert result.brightness == 55

    def test_determine_changes_vdu_exception(self, lux_worker, mock_main_controller):
        """If get_value raises VduException, return None and increment error count."""
        mock_main_controller.get_value.side_effect = VduException("test error")
        profile = [LuxPoint(0,0), LuxPoint(100,50)]
        lux_worker.consecutive_error_count = 0
        result = lux_worker.determine_changes("sid1", 50, profile)
        assert result is None
        assert lux_worker.consecutive_error_count == 1

    def test_assemble_required_work(self, lux_worker, mock_auto_controller, mock_main_controller):
        """Test full assembly of work list."""
        # Mock get_vdu_stable_id_list to return two VDUs
        mock_main_controller.get_vdu_stable_id_list.return_value = ["sid1", "sid2"]
        # Mock get_range
        mock_main_controller.get_range.return_value = (0, 100)
        # Mock get_lux_profile to return a simple profile
        mock_auto_controller.get_lux_profile.return_value = [
            LuxPoint(0, 0),
            LuxPoint(100, 50),
        ]
        # Mock get_value to return current brightness
        mock_main_controller.get_value.side_effect = lambda sid, _: 20 if sid == "sid1" else 30
        # Mock smoother
        lux_worker.interpolation_enabled = True
        lux_worker.smoother.smooth = MagicMock(return_value=50)  # smoothed lux
        # Call assemble_required_work
        to_do_list = lux_worker.assemble_required_work(mock_auto_controller, metered_lux=50.0, requires_smoothing=True)
        # Should have 2 items
        assert len(to_do_list) == 2
        # Check first item
        assert to_do_list[0].vdu_sid == "sid1"
        assert to_do_list[0].brightness == 50
        assert to_do_list[0].preset_name is None
        assert to_do_list[0].current_brightness == 20
        # Second
        assert to_do_list[1].vdu_sid == "sid2"
        assert to_do_list[1].brightness == 50
        assert to_do_list[1].current_brightness == 30

    def test_assess_presets_collectively_all_match(self, lux_worker, mock_main_controller):
        """When all VDUs agree on the same preset, it should be applied."""
        # Create a mock preset
        mock_preset = MagicMock()
        mock_preset.get_vdu_sids.return_value = ["sid1", "sid2"]
        mock_preset.get_brightness.side_effect = lambda sid: 70 if sid == "sid1" else 80
        mock_main_controller.find_preset_by_name.return_value = mock_preset

        # Create to_do_list with two items, both with preset_name "PresetA"
        to_do_list = [
            LuxToDo(VduStableId("sid1"), 50, "PresetA", 40),
            LuxToDo(VduStableId("sid2"), 55, "PresetA", 45),
        ]
        # mock get_vdu_stable_id_list
        mock_main_controller.get_vdu_stable_id_list.return_value = ["sid1", "sid2"]

        lux_worker.assess_presets_collectively(to_do_list)
        # Brightness should be overwritten by preset's brightness
        assert to_do_list[0].brightness == 70
        assert to_do_list[1].brightness == 80

    def test_assess_presets_collectively_partial_match(self, lux_worker, mock_main_controller):
        """If preset does not cover all VDUs, ignore it."""
        mock_preset = MagicMock()
        mock_preset.get_vdu_sids.return_value = ["sid1"]  # only covers sid1
        mock_preset.get_brightness.return_value = 70
        mock_main_controller.find_preset_by_name.return_value = mock_preset
        mock_main_controller.get_vdu_stable_id_list.return_value = ["sid1", "sid2"]

        to_do_list = [
            LuxToDo(VduStableId("sid1"), 50, "PresetA", 40),
            LuxToDo(VduStableId("sid2"), 55, "PresetA", 45),
        ]
        lux_worker.assess_presets_collectively(to_do_list)
        # Brightness should NOT be changed because not all VDUs covered
        assert to_do_list[0].brightness == 50
        assert to_do_list[1].brightness == 55
        # preset_name should be cleared?
        assert to_do_list[0].preset_name is None
        assert to_do_list[1].preset_name is None

    def test_lux_summary_same(self, lux_worker):
        result = lux_worker.lux_summary(500, 500)  # Numbers the same
        assert result == "500 lux"

    def test_lux_summary_different(self, lux_worker):
        result = lux_worker.lux_summary(500, 480)  # Numbers differ
        assert result == "500 ↝ 480 lux (smoothed)"


# ----------------------------------------------------------------------
# Tests for LuxAutoController (basic)
# ----------------------------------------------------------------------

class TestLuxAutoController:
    def test_initialization(self, mock_main_controller):
        with patch('vdu_controls.lux_auto.LuxConfig') as MockLuxConfig:
            mock_lux_config = MagicMock()
            MockLuxConfig.return_value = mock_lux_config
            controller = LuxAutoController(mock_main_controller)
            assert controller.main_controller == mock_main_controller
            assert controller.lux_config == mock_lux_config
            assert controller.lux_meter is None
            assert controller.lux_auto_brightness_worker is None

    def test_set_auto_enable_no_location_semi_auto(self, mock_main_controller):
        """If semi-auto and no location, auto should be disabled."""
        with (patch('vdu_controls.lux_auto.LuxConfig') as MockLuxConfig,
              patch('vdu_controls.lux_auto.LuxDialog') as MockLuxDialog,
              patch('vdu_controls.lux_auto.lux_create_device') as mock_lux_create):
            mock_lux_config = MagicMock()
            mock_lux_config.is_auto_enabled = MagicMock(return_value=False)
            MockLuxConfig.return_value = mock_lux_config
            MockLuxDialog.exists = MagicMock(return_value=True)
            controller = LuxAutoController(mock_main_controller)
            # Create a semi-auto meter
            controller.lux_meter = MagicMock()
            controller.lux_meter.has_semi_auto_capability = True
            mock_main_controller.main_config.get_location.return_value = ""  # no location
            controller.set_auto(enable=True)
            # Should not enable
            mock_lux_config.set.assert_called_with('lux-meter', 'automatic-brightness', 'no')
            mock_lux_config.save.assert_called()

    def test_set_auto_enable_with_location(self, mock_main_controller):
        with (patch('vdu_controls.lux_auto.LuxConfig') as MockLuxConfig,
              patch('vdu_controls.lux_auto.LuxDialog') as MockLuxDialog,
              patch('vdu_controls.lux_auto.lux_create_device') as mock_lux_create):
            mock_lux_config = MagicMock()
            mock_lux_config.is_auto_enabled = MagicMock(return_value=False)
            MockLuxConfig.return_value = mock_lux_config
            controller = LuxAutoController(mock_main_controller)
            controller.lux_meter = MagicMock()
            controller.lux_meter.has_semi_auto_capability = True
            mock_main_controller.main_config.get_location.return_value = "Somewhere"
            controller.set_auto(enable=True)
            mock_lux_config.set.assert_called_with('lux-meter', 'automatic-brightness', 'yes')
            mock_lux_config.save.assert_called()

    def test_toggle_auto(self, mock_main_controller):
        with (patch('vdu_controls.lux_auto.LuxConfig') as MockLuxConfig,
              patch('vdu_controls.lux_auto.LuxDialog') as MockLuxDialog):
            mock_lux_config = MagicMock()
            mock_lux_config.is_auto_enabled = MagicMock(return_value=False)
            MockLuxConfig.return_value = mock_lux_config
            controller = LuxAutoController(mock_main_controller)
            controller.lux_meter = MagicMock()
            controller.lux_meter.has_semi_auto_capability = False
            controller.initialize_from_config = MagicMock()
            controller.toggle_auto()
            mock_lux_config.set.assert_called_with('lux-meter', 'automatic-brightness', 'yes')
            controller.initialize_from_config.assert_called()