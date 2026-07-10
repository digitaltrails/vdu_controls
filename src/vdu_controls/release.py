# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from vdu_controls.constants import VDU_CONTROLS_VERSION
from vdu_controls.app_locale import tr
from vdu_controls.icon_utils import create_icon_from_svg_bytes
from vdu_controls.qt_imports import QT_TR_NOOP, Qt
from vdu_controls.scaling import dpx
from vdu_controls.svg import VDU_CONTROLS_ICON_SVG
from vdu_controls.widgets import MBox, MIcon, MBtn

class Release:
    RELEASE_WELCOME = QT_TR_NOOP("Welcome to vdu_controls {}")
    RELEASE_NOTE = QT_TR_NOOP("Please read the online release notes:")
    RELEASE_ANNOUNCEMENT = """<h3>{WELCOME}</h3>{NOTE}<br/>
    <a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}">
    https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}</a>
    <br/>_____________________________________________________________________________________________"""
    RELEASE_INFO = QT_TR_NOOP(
                              '<h3><span style="color: #ea4335;">\u26A0</span> Notable Changes - feedback requested</h3>'
                              'You may wish to comment on these changes:'
                              ' <ul><li>The <i>weather feature</i> is deprecated and may be removed from the next version.</b>'
                              ' If you rely on it, please comment on issue'
                              ' <a href="https://github.com/digitaltrails/vdu_controls/issues/133">#133</a>.'
                              ' <li>The <i>protect-nvram feature</i> has been made mandatory.</b>'
                              ' If you rely on disabling protect-nvram, please comment on issue'
                              ' <a href="https://github.com/digitaltrails/vdu_controls/issues/132">#132</a>.'
                              '</ul>'
                              "<h3><span style='color: #2196F3;'>\U0001F6C8</span> What's new:</h3> Usability improvements and code refactoring, "
                              'see the release notes for details (link above).'
                              '<br/><br/>'
                              )
    @staticmethod
    def release_notes():
        release_alert = MBox(
            MIcon.Information,
            msg=Release.RELEASE_ANNOUNCEMENT.format(WELCOME=tr(Release.RELEASE_WELCOME, Release.__name__).format(VDU_CONTROLS_VERSION),
                                                    NOTE=tr(Release.RELEASE_NOTE, Release.__name__),
                                                    VERSION=VDU_CONTROLS_VERSION),
            info=tr(Release.RELEASE_INFO, Release.__name__), buttons=MBtn.Close)
        release_alert.setTextFormat(Qt.TextFormat.RichText)
        icon = create_icon_from_svg_bytes(VDU_CONTROLS_ICON_SVG)
        release_alert.setIconPixmap(icon.pixmap(dpx(125), dpx(125)))
        release_alert.exec()