# SPDX-FileCopyrightText: 2021-2026 Michael Hamilton
# SPDX-License-Identifier: GPL-3.0-or-later
from vdu_controls.constants import VDU_CONTROLS_VERSION
from vdu_controls.internationalization import tr
from vdu_controls.qt_imports import QT_TR_NOOP, Qt
from vdu_controls.widgets import MBox, MIcon, MBtn

RELEASE_WELCOME = QT_TR_NOOP("Welcome to vdu_controls {}").format(VDU_CONTROLS_VERSION)
RELEASE_NOTE = QT_TR_NOOP("Please read the online release notes:")
RELEASE_ANNOUNCEMENT = """<h3>{WELCOME}</h3>{NOTE}<br/>
<a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}">
https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}</a>
<br/>___________________________________________________________________________"""
RELEASE_INFO = QT_TR_NOOP('<b>Road Warrior: Support for Laptop-Panels</b><br/>'
                          '<br/>Laptop-panel support is optional - see Settings - '
                          ' and requires the brightnessctl command and python3-udev library.')

def release_notes(self):
    release_alert = MBox(
        MIcon.Information,
        msg=RELEASE_ANNOUNCEMENT.format(WELCOME=tr(RELEASE_WELCOME), NOTE=tr(RELEASE_NOTE), VERSION=VDU_CONTROLS_VERSION),
        info=RELEASE_INFO, buttons=MBtn.Close)
    release_alert.setTextFormat(Qt.TextFormat.RichText)
    release_alert.exec()