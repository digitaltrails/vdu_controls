# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from vdu_controls import app_locale, icon_utils, scaling
from vdu_controls.qt_imports import Qt, QMessageBox, QLocale, QtCore, QGuiApplication

from vdu_controls.constants import VDU_CONTROLS_VERSION, IP_ADDRESS_INFO_URL, WEATHER_FORECAST_URL
from vdu_controls.ddcutil_aggregator import DdcutilAggregator
from vdu_controls.app_locale import tr
import vdu_controls.logging as log

from vdu_controls.widgets import DialogSingletonMixin

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
        if AboutDialog.exists():
            if (about_instance := AboutDialog.get_instance()).isVisible():
                about_instance.refresh_content()
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

        ddcutil_version_info_0 = "unknown"
        ddcutil_version_info_1 = "unknown"
        counts_str = "None"
        if self.main_controller and self.main_controller.ddcutil:
            counts_str = ','.join((str(v) for v in DdcutilAggregator.vcp_write_counters.values())) if len(DdcutilAggregator.vcp_write_counters) else counts_str
            ddcutil_version_info_0 = self.main_controller.ddcutil.ddcutil_version_info()[0]
            ddcutil_version_info_1 = self.main_controller.ddcutil.ddcutil_version_info()[1]
        log.info(f"Refreshing About Dialog {counts_str=}")
        # Has to be HTML, getting Qt Markdown to behave was too painful
        about_text = app_locale.load_resource_text("about.html")
        about_license = app_locale.load_resource_text("about_license.html")  # Always in English
        self.setInformativeText(about_text.format(
            about_license = about_license,
            vdu_controls_version = VDU_CONTROLS_VERSION,
            current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', default='unknown'),
            xdg_session_type = os.environ.get('XDG_SESSION_TYPE', default='unknown'),
            qapplication_platform = QGuiApplication.platformName(),
            qt_qversion = QtCore.QT_VERSION_STR,
            ddcutil_version_info_0 = ddcutil_version_info_0,
            ddcutil_version_info_1 = ddcutil_version_info_1,
            write_counts = counts_str,
            qlocale = QLocale.system().name(),
            ip_address_info_url = IP_ADDRESS_INFO_URL,
            weather_forecast_url = WEATHER_FORECAST_URL,
            translating=("translating" if True else "not translating")))

        self.setIconPixmap(icon_utils.get_splash_pixmap().scaledToHeight(scaling.npx(250)))
