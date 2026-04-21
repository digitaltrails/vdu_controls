# SPDX-FileCopyrightText: 2021-2026 Michael Hamilton
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import locale
import os
import unicodedata
import urllib
from datetime import datetime

from vdu_controls.config_ini import GeoLocation
from vdu_controls.constants import WEATHER_FORECAST_URL
from vdu_controls.internationalization import tr
from vdu_controls.logging import log_info
from vdu_controls.misc import zoned_now
from vdu_controls.solar_calc import spherical_kilometers


class WeatherQuery:

    def __init__(self, location: GeoLocation) -> None:
        self.location = location
        self.maximum_distance_km = int(os.getenv("VDU_CONTROLS_WEATHER_KM", default='200'))
        local_local = locale.getlocale()
        lang = local_local[0][:2] if local_local is not None and local_local[0] is not None else 'C'
        ascii_location = unicodedata.normalize('NFD', location.place_name).encode('ascii', 'ignore').decode("ascii")
        self.url = f"{WEATHER_FORECAST_URL}/{ascii_location}?" + urllib.parse.urlencode({'lang': lang, 'format': 'j1'})
        self.weather_data = None
        self.proximity_km = 0
        self.proximity_ok = True
        self.longitude = self.latitude = self.country_name = self.area_name = None
        self.cloud_cover = self.visibility = self.weather_desc = self.weather_code = None
        self.when: datetime | None = None

    def run_query(self) -> None:
        location_name = self.location.place_name
        local_local = locale.getlocale()
        lang = local_local[0][:2] if local_local is not None and local_local[0] is not None else 'C'
        if location_name is None or location_name.strip() == '':
            location_name = ''
        self.when = zoned_now()
        try:
            log_info(f"QueryWeather: {self.url}")
            with urllib.request.urlopen(self.url, timeout=15) as request:
                json_content = request.read()
                self.weather_data = json.loads(json_content)
                if self.weather_data is not None:
                    current_conditions = self.weather_data['current_condition'][0]
                    self.weather_code = current_conditions['weatherCode']
                    lang_key = f"lang_{lang}"
                    if lang_key in current_conditions:
                        self.weather_desc = current_conditions[lang_key][0]['value']
                    else:
                        self.weather_desc = current_conditions['weatherDesc'][0]['value']
                    self.visibility = current_conditions['visibility']
                    self.cloud_cover = current_conditions['cloudcover']
                    nearest_area = self.weather_data['nearest_area'][0]
                    self.area_name = nearest_area['areaName'][0]['value']
                    self.country_name = nearest_area['country'][0]['value']
                    self.latitude = nearest_area['latitude']
                    self.longitude = nearest_area['longitude']
                    self.proximity_km = round(spherical_kilometers(float(self.latitude), float(self.longitude),
                                                                   self.location.latitude, self.location.longitude))
                    self.proximity_ok = self.proximity_km <= self.maximum_distance_km
                    log_info(f"QueryWeather result: {self}")
                    return
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(tr("Unknown location {}").format(location_name), tr("Please check Location in Settings")) from e
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(e)) from e
        except Exception as ue:
            # Can't afford to fall over because of a problem with a remote site
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(ue)) from ue
        raise ValueError(tr("Failed to get weather from {}").format(self.url))

    def __str__(self) -> str:
        if self.weather_data is None:
            return ""
        return f"{self.area_name}, {self.country_name}, {self.weather_desc} ({self.weather_code})," \
               f"cloud_cover {self.cloud_cover}, visibility {self.visibility}, location={self.latitude},{self.longitude}"
