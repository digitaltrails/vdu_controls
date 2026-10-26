#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import pytest

from vdu_controls.ddcutil_abstract import DdcutilServiceNotFound
from vdu_controls.ddcutil_qdbus import DdcutilDBusImpl
from vdu_controls.qt_imports import QApplication


@pytest.fixture(scope="session")
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_ddcutil_dbus_impl_not_found(app):
    with patch("vdu_controls.ddcutil_qdbus.is_dbus_service_registered", return_value=False):
        with pytest.raises(DdcutilServiceNotFound) as exc_info:
            DdcutilDBusImpl()
        assert "no registered service found" in str(exc_info.value)
