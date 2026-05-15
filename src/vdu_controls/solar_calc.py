# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
from collections import namedtuple
from datetime import datetime, timezone, timedelta
from typing import Tuple, Callable, Dict

from vdu_controls.misc import GeoLocation
from vdu_controls.constants import EASTERN_SKY, WESTERN_SKY
from vdu_controls.app_locale import tr
from vdu_controls.unicode import EAST_ELEVATION_SYMBOL, WEST_ELEVATION_SYMBOL, SUN_SYMBOL, DEGREE_SYMBOL

SolarElevationKey = namedtuple('SolarElevationKey', ['direction', 'elevation'])
SolarElevationData = namedtuple('SolarElevationData', ['azimuth', 'zenith', 'when'])


# FUNCTION TO COMPUTE SOLAR AZIMUTH AND ZENITH ANGLE
# Extracted from a larger gist by Antti Lipponen: https://gist.github.com/anttilipp/1c482c8cc529918b7b973339f8c28895
# which was translated to Python from http://www.psa.es/sdg/sunpos.htm
# Converted to only use the python math library (instead of numpy) by me for vdu_controls.
# Coding style also altered for use with vdu_controls.
def calc_solar_azimuth_zenith(localised_time: datetime, latitude: float, longitude: float) -> Tuple[float, float]:
    """
    Return azimuth degrees clockwise from true north and zenith in degrees from
    vertical direction.
    """
    assert localised_time.tzinfo is not None
    utc_datetime = localised_time.astimezone(timezone.utc)
    # UTC from now on...
    hours, minutes, seconds = utc_datetime.hour, utc_datetime.minute, utc_datetime.second
    year, month, day = utc_datetime.year, utc_datetime.month, utc_datetime.day

    earth_mean_radius = 6371.01
    astronomical_unit = 149597890

    # Calculate the difference in days between the current Julian Day and JD 2451545.0, which is noon 1 January 2000 Universal Time

    # Calculate the time of the day in UT decimal hours
    decimal_hours = hours + (minutes + seconds / 60.) / 60.
    # Calculate current Julian Day
    aux1 = int((month - 14.) / 12.)
    aux2 = int((1461. * (year + 4800. + aux1)) / 4.) + int((367. * (month - 2. - 12. * aux1)) / 12.) - int(
        (3. * int((year + 4900. + aux1) / 100.)) / 4.) + day - 32075.
    julian_date = aux2 - 0.5 + decimal_hours / 24.
    # Calculate the difference between current Julian Day and JD 2451545.0
    elapsed_julian_days = julian_date - 2451545.0

    # Calculate ecliptic coordinates (ecliptic longitude and obliquity of the ecliptic in radians but
    # without limiting the angle to be less than 2*Pi (i.e., the result may be greater than 2*Pi)
    omega = 2.1429 - 0.0010394594 * elapsed_julian_days
    mean_longitude = 4.8950630 + 0.017202791698 * elapsed_julian_days  # Radians
    mean_anomaly = 6.2400600 + 0.0172019699 * elapsed_julian_days
    ecliptic_longitude = mean_longitude + 0.03341607 * math.sin(mean_anomaly) + 0.00034894 * math.sin(
        2. * mean_anomaly) - 0.0001134 - 0.0000203 * math.sin(omega)
    ecliptic_obliquity = 0.4090928 - 6.2140e-9 * elapsed_julian_days + 0.0000396 * math.cos(omega)

    # Calculate celestial coordinates (right ascension and declination) in radians but without limiting
    # the angle to be less than 2*Pi (i.e., the result may be greater than 2*Pi)
    sin_ecliptic_longitude = math.sin(ecliptic_longitude)
    dy = math.cos(ecliptic_obliquity) * sin_ecliptic_longitude
    dx = math.cos(ecliptic_longitude)
    right_ascension = math.atan2(dy, dx)
    if right_ascension < 0.0:
        right_ascension = right_ascension + 2.0 * math.pi
    declination = math.asin(math.sin(ecliptic_obliquity) * sin_ecliptic_longitude)

    # Calculate local coordinates ( azimuth and zenith angle ) in degrees
    greenwich_mean_sidereal_time = 6.6974243242 + 0.0657098283 * elapsed_julian_days + decimal_hours
    local_mean_sidereal_time = (greenwich_mean_sidereal_time * 15. + longitude) * (math.pi / 180.)
    hour_angle = local_mean_sidereal_time - right_ascension
    latitude_in_radians = latitude * (math.pi / 180.)
    cos_latitude = math.cos(latitude_in_radians)
    sin_latitude = math.sin(latitude_in_radians)
    cos_hour_angle = math.cos(hour_angle)
    zenith_angle = math.acos(cos_latitude * cos_hour_angle * math.cos(declination) + math.sin(declination) * sin_latitude)
    dy = -math.sin(hour_angle)
    dx = math.tan(declination) * cos_latitude - sin_latitude * cos_hour_angle
    azimuth = math.atan2(dy, dx)
    if azimuth < 0.0:
        azimuth += 2 * math.pi
    azimuth = azimuth / (math.pi / 180.)
    # Parallax Correction
    parallax = (earth_mean_radius / astronomical_unit) * math.sin(zenith_angle)
    zenith_angle = (zenith_angle + parallax) / (math.pi / 180.)
    # Return azimuth as a clockwise angle from true north
    return azimuth, zenith_angle


def calc_solar_lux(localised_time: datetime, location: GeoLocation, daylight_factor: float) -> int:
    """
    E. Elvegård and G. Sjöstedt, "The Calculation of Illumination from Sun and Sky," _Illuminating Engineering_, Apr. 1940.
    [Illuminating Engineering Society, 100 Significant Papers](https://www.ies.org/research/publications/100-significant-papers/)
    """
    latitude, longitude = location.latitude, location.longitude
    _, zenith = calc_solar_azimuth_zenith(localised_time, latitude, longitude)
    solar_altitude = 90 - zenith  # After sunset use
    if solar_altitude < 3:  # 3 degrees is a minimum, the functional limit for the algorithm
        return 0
    al_e8_illumination_unit = 77000  # E8 in Lux
    air_mass = 1.0 / math.cos(math.radians(zenith))  # approximation:  https://en.wikipedia.org/wiki/Air_mass_(solar_energy)
    solar_lux = 1.6 * al_e8_illumination_unit * math.sin(math.radians(solar_altitude)) * 10 ** (-0.1 * air_mass)
    illumination = int(daylight_factor * solar_lux)
    return illumination


def spherical_kilometers(lat1, lon1, lat2, lon2) -> float:
    """
    Spherical distance from https://stackoverflow.com/a/21623206/609575 (great circle distance km)
    """
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    a = min(1.0, max(0.0, a))  # Guard against floating‑point errors
    return 12742 * math.asin(math.sqrt(a))


def create_elevation_map(local_now: datetime, latitude: float, longitude: float,
                         callback: Callable[[float, float, datetime], None]
                                   | None = None) -> Dict[SolarElevationKey, SolarElevationData]:
    """
    Create a minute-by-minute map of today's SolarElevations.
    For a given dict[SolarElevation], record the first minute it occurs.
    Calls the callback for every 1 minute point, not just each integer elevation.
    """
    elevation_time_map = {}
    local_when = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    while local_when.day == local_now.day:
        a, z = calc_solar_azimuth_zenith(local_when, latitude, longitude)
        e = round(90.0 - z)
        key = SolarElevationKey(elevation=round(e), direction=(EASTERN_SKY if a < 180 else WESTERN_SKY))
        if key not in elevation_time_map:
            elevation_time_map[key] = SolarElevationData(azimuth=a, zenith=z, when=local_when)
        if callback:
            callback(a, z, local_when)
        local_when += timedelta(minutes=1)
    return elevation_time_map


def format_solar_elevation_abbreviation(elevation: SolarElevationKey) -> str:
    direction_char = EAST_ELEVATION_SYMBOL if elevation.direction == EASTERN_SKY else WEST_ELEVATION_SYMBOL
    return f"{SUN_SYMBOL} {direction_char} {elevation.elevation}{DEGREE_SYMBOL}"


def format_solar_elevation_description(elevation: SolarElevationKey) -> str:
    # Note - repeating the constants here to force them to be included by pylupdate5 internationalization
    direction_text = tr('eastern-sky') if elevation.direction == EASTERN_SKY else tr('western-sky')
    return f"{direction_text} {elevation.elevation}{DEGREE_SYMBOL}"


def format_solar_elevation_ini_text(elevation: SolarElevationKey | None) -> str:
    return f"{elevation.direction} {elevation.elevation}" if elevation is not None else ''


def parse_solar_elevation_ini_text(ini_text: str) -> SolarElevationKey:
    parts = ini_text.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Invalid SolarElevation: '{ini_text}'")
    if parts[0] not in [EASTERN_SKY, WESTERN_SKY]:
        raise ValueError(f"Invalid value for  SolarElevation direction: '{parts[0]}'")
    solar_elevation = SolarElevationKey(parts[0], int(parts[1]))
    return solar_elevation
