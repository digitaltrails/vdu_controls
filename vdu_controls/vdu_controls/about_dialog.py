# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from vdu_controls.qt_imports import Qt, QtCore, QApplication, QMessageBox

from vdu_controls.constants import VDU_CONTROLS_VERSION, IP_ADDRESS_INFO_URL, WEATHER_FORECAST_URL, ABOUT_TEXT
from vdu_controls.ddcutil_aggregator import DdcutilAggregator
from vdu_controls.app_locale import tr, find_locale_specific_file
import vdu_controls.logging as log

from vdu_controls.widgets import DialogSingletonMixin, MIcon

if TYPE_CHECKING:
    from vdu_controls.vdu_controls_application import VduAppController

class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def invoke(main_controller: VduAppController) -> None:
        if AboutDialog.exists():
            AboutDialog.get_instance().refresh_content()
            AboutDialog.show_existing_dialog()
        else:
            AboutDialog(main_controller)

    @staticmethod
    def refresh():
        if AboutDialog.exists() and AboutDialog.get_instance().isVisible():
            AboutDialog.get_instance().refresh_content()
        else:
            log.debug("About dialog - no refresh - not visible") if log.debug_enabled else None

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.main_controller = main_controller
        self.refresh_content()
        self.setModal(False)
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh_content(self):
        self.setWindowTitle(tr('About'))
        self.setTextFormat(Qt.TextFormat.AutoText)
        self.setText(tr('About vdu_controls'))
        path = find_locale_specific_file("about_{}.txt")
        if path:
            with open(path, encoding='utf-8') as about_for_locale:
                about_text = about_for_locale.read().format(
                    VDU_CONTROLS_VERSION=VDU_CONTROLS_VERSION, IP_ADDRESS_INFO_URL=IP_ADDRESS_INFO_URL,
                    WEATHER_FORECAST_URL=WEATHER_FORECAST_URL)
        else:
            about_text = ABOUT_TEXT
        if self.main_controller and self.main_controller.ddcutil:
            counts_str = ','.join((str(v) for v in DdcutilAggregator.vcp_write_counters.values())) if len(DdcutilAggregator.vcp_write_counters) else '0'
            about_text += (f"<hr><p><small>desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')}; "
                           f"platform: {os.environ.get('XDG_SESSION_TYPE', default='unknown')} "
                           f"({QApplication.platformName()}, qt-{QtCore.qVersion()});<br/>"
                           f"ddcutil-interface: {self.main_controller.ddcutil.ddcutil_version_info()[0]}; "
                           f"ddcutil: {self.main_controller.ddcutil.ddcutil_version_info()[1]} (writes: {counts_str});</small>")
        self.setInformativeText(about_text)
        self.setIcon(MIcon.Information)
