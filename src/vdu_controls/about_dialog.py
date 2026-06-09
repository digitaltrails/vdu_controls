# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import vdu_controls.logging as log
from vdu_controls import icon_utils, scaling, app_locale
from vdu_controls.app_locale import tr
from vdu_controls.constants import VDU_CONTROLS_VERSION, IP_ADDRESS_INFO_URL, WEATHER_FORECAST_URL, APPNAME, DDCUTIL_WEBSITE_URL, \
    DDCUTIL_SERVICE_WEBSITE_URL, BRIGHTNESSCTL_WEBSITE_URL, VDU_CONTROLS_WEBSITE_URL
from vdu_controls.ddcutil_aggregator import DdcutilAggregator
from vdu_controls.icon_utils import create_icon_from_svg_bytes
from vdu_controls.qt_imports import Qt, QMessageBox, QtCore, QGuiApplication
from vdu_controls.scaling import dpx
from vdu_controls.svg import VDU_CONTROLS_ICON_SVG
from vdu_controls.widgets import DialogSingletonMixin

if TYPE_CHECKING:
    from vdu_controls.vdu_controls_application import VduAppController

# Note: for legal reasons, the license should never be translated.
_ABOUT_TEMPLATE = '''
<b>{data.title}</b>
<p>
{data.intro}
<p>
{data.proj_home}
<p>
{data.release_notes}
<p>
<hr>
        <div dir="ltr">
        <small>
        <b>Copyright (C) 2021-2026 Contributors to vdu_controls</b>
        <br><br>
        This program is free software: you can redistribute it and/or modify it
        under the terms of the GNU General Public License as published by the
        Free Software Foundation, version 3.
        <br><br>
        
        <bold>
        This program is distributed in the hope that it will be useful, but
        WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
        or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
        more details.
        </bold>
        <br><br>
        You should have received a copy of the GNU General Public License along
        with this program. If not, see <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.
        </small>
        </div>
<hr>
<p><p>
<quote>
<small>
{data.dependencies}
<br><br>
{data.ip_address_lookup}
<br>
{data.weather_lookup}
</small>
</quote>
<hr>
<quote>
<small>
{data.tech_info}
</small>
</quote>
'''


class _AboutTemplateData:

    @staticmethod
    def _link(url_str: str, text: str = '') -> str:
        return f'<a href="{url_str}">{text if text else url_str}</a>'

    def __init__(self, counts_str, ddcutil_version_info_0, ddcutil_version_info_1) -> None:
        self.counts_str = counts_str
        self.ddcutil_version_info_0 = ddcutil_version_info_0
        self.ddcutil_version_info_1 = ddcutil_version_info_1

    @property
    def title(self) -> str:
        return tr('{0} version {1}').format(APPNAME, VDU_CONTROLS_VERSION)

    @property
    def intro(self):
        return tr('A virtual control panel for visual display units.')

    @property
    def proj_home(self) -> str:
        return tr('Visit {} for more details.').format(_AboutTemplateData._link(VDU_CONTROLS_WEBSITE_URL))

    @property
    def release_notes(self) -> str:
        return tr("Release notes: {}").format(
            _AboutTemplateData._link(VDU_CONTROLS_WEBSITE_URL + f'/releases/tag/v{VDU_CONTROLS_VERSION}', VDU_CONTROLS_VERSION))

    @property
    def dependencies(self):
        return tr('vdu_controls relies on {0}, a robust interface to ddc capable vdus; '
                  '{1}, a fast DBus-interface to libddcutil; '
                  'and {2}, a brightness control for laptop-panels.'
                  ).format(
            _AboutTemplateData._link(DDCUTIL_WEBSITE_URL, 'ddcutil'),
            _AboutTemplateData._link(DDCUTIL_SERVICE_WEBSITE_URL, 'ddcutil-service'),
            _AboutTemplateData._link(BRIGHTNESSCTL_WEBSITE_URL, 'brightnessctl'))

    @property
    def ip_address_lookup(self):
        return tr('At your request, your geographic location may be retrieved from {}').format(
            _AboutTemplateData._link(IP_ADDRESS_INFO_URL))

    @property
    def weather_lookup(self):
        return tr('At your request, weather for your location may be retrieved from {}.').format(
            _AboutTemplateData._link(WEATHER_FORECAST_URL))

    @property
    def tech_info(self):
        return f'''
            desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')};
            platform: qt-{QtCore.QT_VERSION_STR}/{QGuiApplication.platformName()};
            ddcutil-interface: {self.ddcutil_version_info_0}; 
            ddcutil: {self.ddcutil_version_info_1};
            locale: {app_locale.get_locale_name()} 
            ({"translating" if app_locale.get_translating_locale() == app_locale.get_locale_name() else "not translating"}); 
            installed translations: {', '.join(app_locale.available_translations())};
            NVRAM writes: {self.counts_str} 
            '''

class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def show_dialog(main_controller: VduAppController) -> None:
        if AboutDialog.exists():
            AboutDialog.get_instance().refresh_content()
            AboutDialog.show_existing_dialog()
        else:
            AboutDialog(main_controller)

    @staticmethod
    def refresh():
        if AboutDialog.exists():
            about_instance = AboutDialog.get_instance()
            if about_instance.isVisible():
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

        template_data = _AboutTemplateData(counts_str, ddcutil_version_info_0, ddcutil_version_info_1)
        about_html_text = _ABOUT_TEMPLATE.format(data=template_data)
        self.setInformativeText(about_html_text)
        icon = create_icon_from_svg_bytes(VDU_CONTROLS_ICON_SVG)
        self.setIconPixmap(icon.pixmap(dpx(125), dpx(125)))
