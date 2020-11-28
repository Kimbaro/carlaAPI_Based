#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
CARLA Dynamic Weather:

Connect to a CARLA Simulator instance and control the weather. Change Sun
position smoothly with time and generate storms occasionally.
"""

import glob
import os
import sys

try:
    sys.path.append(glob.glob('carla-0.9.9.4*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import argparse
import math


def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(value, maximum))


class Sun(object):
    def __init__(self, azimuth, altitude):
        self.azimuth = azimuth
        self.altitude = altitude
        self._t = 0.0

    def tick(self, delta_seconds):
        self._t += 0.008 * delta_seconds
        self._t %= 2.0 * math.pi
        self.azimuth += 0.25 * delta_seconds
        self.azimuth %= 360.0
        self.altitude = (70 * math.sin(self._t)) - 20

    def __str__(self):
        return 'Sun(alt: %.2f, azm: %.2f)' % (self.altitude, self.azimuth)


class UI_INPUT_CONTROL(object):
    def return_weather(self, clouds=0.0, rain=0.0, wetness=0.0, puddles=0.0, wind=0.0, fog=0.0, remote=False):
        clouds = clamp(clouds, 0.0, 100.0)
        rain = clamp(rain, 0.0, 100.0)
        wetness = clamp(wetness, 0.0, 100.0)
        puddles = clamp(puddles, 0.0, 100.0)
        wind = clamp(wind, 0.0, 100.0)
        fog = clamp(fog, 0.0, 100.0)
        remote = remote
        weather_set = [clouds, rain, wetness, puddles, wind, fog, remote]
        return weather_set


class Rain(object):
    def __init__(self, weather_set, precipitation):
        self._t = precipitation if precipitation > 0.0 else -50.0
        self._increasing = True
        self.clouds = weather_set[0]
        self.rain = weather_set[1]
        self.wetness = weather_set[2]
        self.puddles = weather_set[3]
        self.wind = weather_set[4]
        self.fog = weather_set[5]
        self.remote = weather_set[6]

    def tick(self, delta_seconds, weather_set):
        """
        :param delta_seconds: timestamp = world.wait_for_tick().timestamp
        :param weather_set: weather_set = [clouds, rain, wetness, puddles, wind, fog, remote]
        remote가  True인 경우 동적모드 활성화
        """

        if weather_set[6]:
            delta = (1.3 if self._increasing else -1.3) * delta_seconds
            self._t = clamp(delta + self._t, -250.0, 100.0)
            self.clouds = clamp(self._t + 40.0, 0.0, 90.0)
            self.rain = clamp(self._t, 0.0, 80.0)
            self.clouds = clamp(0, 0.0, 90.0)
            self.rain = clamp(5.0, 0.0, 100.0)
            self.puddles = clamp(100.0, 0.0, 85.0)
            self.wetness = clamp(50.0, 0.0, 100.0)

            delay = -10.0 if self._increasing else 90.0
            self.puddles = clamp(self._t + delay, 0.0, 85.0)
            self.wetness = clamp(self._t * 5, 0.0, 100.0)
            self.wind = 5.0 if self.clouds <= 20 else 90 if self.clouds >= 70 else 40
            self.fog = clamp(self._t - 10, 0.0, 30.0)
            self.fog = clamp(0, 0.0, 30.0)
            if self._t == -250.0:
                self._increasing = True
            if self._t == 100.0:
                self._increasing = False
        else:
            None


class Storm(object):
    """
    carla.WeatherParameters.precipitation() type float
    """

    def __init__(self, precipitation):
        self._t = precipitation if precipitation > 0.0 else -50.0
        self._increasing = True
        self.clouds = 0.0
        self.rain = 0.0
        self.wetness = 0.0
        self.puddles = 0.0
        self.wind = 0.0
        self.fog = 0.0

    def tick(self, delta_seconds):
        delta = (1.3 if self._increasing else -1.3) * delta_seconds
        self._t = clamp(delta + self._t, -250.0, 100.0)
        self.clouds = clamp(self._t + 40.0, 0.0, 90.0)
        self.rain = clamp(self._t, 0.0, 80.0)
        delay = -10.0 if self._increasing else 90.0
        self.puddles = clamp(self._t + delay, 0.0, 85.0)
        self.wetness = clamp(self._t * 5, 0.0, 100.0)
        self.wind = 5.0 if self.clouds <= 20 else 90 if self.clouds >= 70 else 40
        self.fog = clamp(self._t - 10, 0.0, 30.0)
        if self._t == -250.0:
            self._increasing = True
        if self._t == 100.0:
            self._increasing = False

    def __str__(self):
        return 'Storm(clouds=%d%%, rain=%d%%, wind=%d%%)' % (self.clouds, self.rain, self.wind)


class Weather(object):
    def __init__(self, weather):
        self.weather = weather
        self._sun = Sun(weather.sun_azimuth_angle, weather.sun_altitude_angle)
        self._storm = Storm(weather.precipitation)

    def tick(self, delta_seconds):
        self._sun.tick(delta_seconds)
        self._storm.tick(delta_seconds)
        self.weather.cloudiness = self._storm.clouds
        self.weather.precipitation = self._storm.rain
        self.weather.precipitation_deposits = self._storm.puddles
        self.weather.wind_intensity = self._storm.wind
        self.weather.fog_density = self._storm.fog
        self.weather.wetness = self._storm.wetness
        self.weather.sun_azimuth_angle = self._sun.azimuth
        self.weather.sun_altitude_angle = self._sun.altitude

    def __str__(self):
        return '%s %s' % (self._sun, self._storm)


def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='203.237.143.192',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-s', '--speed',
        metavar='FACTOR',
        default=10.0,
        type=float,
        help='rate at which the weather changes (default: 1.0)')
    args = argparser.parse_args()

    speed_factor = args.speed
    update_freq = 0.1 / speed_factor

    client = carla.Client(args.host, args.port)
    client.set_timeout(2.0)
    world = client.get_world()

    weather = Weather(world.get_weather())

    elapsed_time = 0.0

    while True:
        timestamp = world.wait_for_tick(seconds=30.0).timestamp
        elapsed_time += timestamp.delta_seconds
        # print(int(elapsed_time))
        if elapsed_time > update_freq:
            weather.tick(speed_factor * elapsed_time)
            world.set_weather(weather.weather)
            sys.stdout.write('\r' + str(weather) + 12 * ' ')
            sys.stdout.flush()
            elapsed_time = 0.0


if __name__ == '__main__':
    main()
