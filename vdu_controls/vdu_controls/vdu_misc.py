# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtCore import QThread, QLocale

from vdu_controls.constants import WEATHER_FORECAST_URL
from vdu_controls.internationalization import tr
from vdu_controls.widgets import MBox, MIcon

gui_thread: QThread | None = None

def set_gui_thread(thread: QThread):
    global gui_thread
    gui_thread = thread

def is_running_in_gui_thread() -> bool:
    return QThread.currentThread() == gui_thread


def weather_bad_location_dialog(weather) -> None:
    kilometres = weather.proximity_km
    use_km = QLocale.system().measurementSystem() == QLocale.MeasurementSystem.MetricSystem
    MBox(MIcon.Warning, msg=tr("The site {} reports your location as {}, {}, {},{} "
                               "which is about {} {} from the latitude and longitude specified in Settings."
                               ).format(WEATHER_FORECAST_URL, weather.area_name, weather.country_name, weather.latitude,
                                        weather.longitude,
                                        round(kilometres if use_km else kilometres * 0.621371), 'km' if use_km else 'miles'),
         info=tr("Please check the location specified in Settings."), details=f"{weather}").exec()
