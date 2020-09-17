import glob
import os
import sys
import weakref
import numpy as np
import math

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import carla
from carla import ColorConverter as cc
import random

# @todo 센서 및 설정정보 리스트, 가능하면 아래 배열 형식을 따를 수 있도록해야함.
sensor_camera_rgb = [['sensor.camera.rgb', cc.Raw, 'Camera RGB', 'a-0', {}],
                     ['sensor.camera.rgb', cc.Raw, 'Camera RGB Distorted', 'a-0',
                      {'lens_circle_multiplier': '3.0',
                       'lens_circle_falloff': '3.0',
                       'chromatic_aberration_intensity': '0.5',
                       'chromatic_aberration_offset': '0'}]
                     ]

sensor_camera_depth = [['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)', 'a-1', {}],
                       ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)', 'a-1', {}],
                       ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)', 'a-1', {}]
                       ]

sensor_camera_segmentation = [['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
                               'Camera Semantic Segmentation (CityScapes Palette)', 'a-2', {}],
                              ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)',
                               'a-2', {}]]

sensor_camera_dvs = [['sensor.camera.dvs', cc.Raw, 'Camera Dvs (Raw)', 'a-3', {}]
                     ]

sensor_lidar = [['sensor.lidar.ray_cast', 'b-0', {
    'channels': '65',
    'range': '50',
    'points_per_second': '700000',
    'rotation_frequency': '40.0',
    'upper_fov': '20.0',  # 상단
    'lower_fov': '-20.0',  # 하단
    'sensor_tick': '0.0'
}], ['sensor.lidar.ray_cast_semantic', 'b-0', {
    'channels': '60',
    'range': '50',
    'points_per_second': '100000',
    'rotation_frequency': '40.0',
    'upper_fov': '20.0',  # 상단
    'lower_fov': '-20.0',  # 하단
    'sensor_tick': '0.0'
}]]

sensor_radar = [
    ['sensor.other.radar', '', {
        'horizontal_fov': '45',
        'vertical_fov': '35',
        'range': '12'  # m/s
    }], ['sensor.other.radar', '', {
        'horizontal_fov': '35',
        'vertical_fov': '22',
        'range': '8.5'  # m/s
    }]
]

sensor_other = [['sensor.other.collision'],
                ['sensor.other.radar'],
                ['sensor.other.gnss'],
                ['sensor.other.imu'],
                ['sensor.other.lane_invasion'],
                ['sensor.other.obstacle']]

transforms = [
    carla.Transform(carla.Location(x=2.8, y=0.0, z=1.7)),
    carla.Transform(carla.Location(x=-5.5, z=2.5)),
    carla.Transform(carla.Location(0, 0, 2.3), carla.Rotation(0, 0, 0)),
    carla.Transform(carla.Location(x=2.8, z=1.7), carla.Rotation(pitch=5))
]

# self.sensor = self._parent.get_world().spawn_actor(
#     self.sensors[index][-1],
#     self._transforms[self.transform_index][0],
#     attach_to=self._parent,
#     attachment_type=self._transforms[self.transform_index][1])

"""
    Camera_Rgb
"""


class Camera_Rgb:
    def __init__(self, world, target, config, select_sensor=0, tick=0.0):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None
        bp_library = world.get_blueprint_library()
        # 센서 블루프린트 id를 불러옴.
        item = sensor_camera_rgb[select_sensor]
        ###센서 초기화.
        bp = bp_library.find(item[0])
        bp.set_attribute('image_size_x', str(config.width))
        bp.set_attribute('image_size_y', str(config.height))
        bp.set_attribute('shutter_speed', str(120.0))
        bp.set_attribute('fov', '110')
        # bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[0], attach_to=self.target)
        weak_self = weakref.ref(self)
        sensor.listen(lambda image: Camera_Rgb._parse_image(weak_self, image, item[1], item[3]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    @staticmethod
    def _parse_image(weak_self, image, cc, id):
        self = weak_self()

        image.convert(cc)
        # Camera_Rgb._parse_pygame(self, image, cc)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        if self.recording:
            image.save_to_disk('sensor/' + str(id) + '/%08d' % image.frame)

    @staticmethod
    def _parse_pygame(self, image, cc):
        # pygame set
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


"""
    Camera_Depth
"""


class Camera_Depth:
    def __init__(self, world, target, config, select_sensor=0, tick=0.0):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None  # <- 2020-08-07추가
        bp_library = world.get_blueprint_library()
        ###센서 초기화.
        item = sensor_camera_depth[select_sensor]

        bp = bp_library.find(item[0])
        bp.set_attribute('image_size_x', str(config.width))
        bp.set_attribute('image_size_y', str(config.height))
        bp.set_attribute('fov', '110')
        # bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[0], attach_to=self.target)
        weak_self = weakref.ref(self)
        sensor.listen(lambda image: Camera_Depth._parse_image(weak_self, image, item[1], item[3]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    @staticmethod
    def _parse_pygame(self, image, cc):
        # pygame set
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    @staticmethod
    def _parse_image(weak_self, image, cc, id):
        self = weak_self()
        image.convert(cc)
        Camera_Depth._parse_pygame(self, image, cc)
        if self.recording:
            image.save_to_disk('sensor/' + str(id) + '/%08d' % image.frame)

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


class Camera_Segmentation:
    def __init__(self, world, target, config, select_sensor=0, tick=0):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None  # <- 2020-08-07추가
        bp_library = world.get_blueprint_library()
        ###센서 초기화.
        item = sensor_camera_segmentation[select_sensor]

        bp = bp_library.find(item[0])
        bp.set_attribute('image_size_x', str(config.width))
        bp.set_attribute('image_size_y', str(config.height))
        bp.set_attribute('fov', '110')
        # bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[0], attach_to=self.target)
        weak_self = weakref.ref(self)
        sensor.listen(lambda image: Camera_Segmentation._parse_image(weak_self, image, item[1], item[3]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    @staticmethod
    def _parse_pygame(self, image, cc):  # <- 2020-08-07추가
        # pygame set
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))

        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    @staticmethod
    def _parse_image(weak_self, image, cc, id):  # <- 2020-08-07추가
        self = weak_self()
        image.convert(cc)
        Camera_Segmentation._parse_pygame(self, image, cc)
        if self.recording:
            image.save_to_disk('sensor/' + str(id) + '/%08d' % image.frame)

    def render(self, display):  # <- 2020-08-07추가
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


"""
    Camera_Dvs
"""


class Camera_Dvs:
    def __init__(self, world, target, config, select_sensor=0, tick=0.0):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None
        bp_library = world.get_blueprint_library()
        # 센서 블루프린트 id를 불러옴.
        item = sensor_camera_dvs[select_sensor]
        ###센서 초기화.
        bp = bp_library.find(item[0])
        bp.set_attribute('image_size_x', str(config.width))
        bp.set_attribute('image_size_y', str(config.height))
        bp.set_attribute('shutter_speed', str(120.0))
        bp.set_attribute('fov', '110')
        # bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[0], attach_to=self.target)
        weak_self = weakref.ref(self)
        sensor.listen(lambda image: Camera_Dvs._parse_image(weak_self, image, item[1], item[3]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    @staticmethod
    def _parse_image(weak_self, image, cc, id):
        self = weak_self()

        dvs_events = np.frombuffer(image.raw_data, dtype=np.dtype([
            ('x', np.uint16), ('y', np.uint16), ('t', np.int64), ('pol', np.bool)]))
        dvs_img = np.zeros((image.height, image.width, 3), dtype=np.uint8)
        # Blue is positive, red is negative
        dvs_img[dvs_events[:]['y'], dvs_events[:]['x'], dvs_events[:]['pol'] * 2] = 255
        self.surface = pygame.surfarray.make_surface(dvs_img.swapaxes(0, 1))

        if self.recording:
            image.save_to_disk('sensor/' + str(id) + '/%08d' % image.frame)

    @staticmethod
    def _parse_pygame(self, image, cc):
        # pygame set
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


class Sensor_Lider:
    def __init__(self, world, target, config, select_sensor=0):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None  # <- 2020-08-07추가
        self.dim = (config.width, config.height)
        bp_library = world.get_blueprint_library()
        ###센서 초기화.
        item = sensor_lidar[select_sensor]
        bp = bp_library.find(item[0])
        for attr_name, attr_value in item[2].items():
            bp.set_attribute(attr_name, attr_value)
            if attr_name == str('range'):
                print("check=====")
                self.lidar_range = float(attr_value)

        sensor = self.world.spawn_actor(bp, transforms[2], attach_to=self.target)
        print("센서 생성 id : ", sensor.id)
        weak_self = weakref.ref(self)
        sensor.listen(lambda point_cloud: Sensor_Lider._parse_image(weak_self, point_cloud, item[1]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    @staticmethod
    def _parse_pygame(self, image):  # <- 2020-08-07추가
        # pygame set
        points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0] / 3), 3))
        lidar_data = np.array(points[:, :2])
        lidar_data *= min(self.dim) / (2.0 * self.lidar_range)
        lidar_data += (0.5 * self.dim[0], 0.5 * self.dim[1])
        lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
        lidar_data = lidar_data.astype(np.int32)
        lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (self.dim[0], self.dim[1], 3)
        lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)
        lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
        self.surface = pygame.surfarray.make_surface(lidar_img)

    @staticmethod
    def _parse_image(weak_self, image, id):  # <- 2020-08-07추가
        self = weak_self()
        Sensor_Lider._parse_pygame(self, image)
        if self.recording:
            image.save_to_disk('sensor/' + str(id) + '/%08d' % image.frame)

    def render(self, display):  # <- 2020-08-07추가
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


class Sensor_Radar:
    def __init__(self, world, target, config, select_sensor=0):
        self.world = world
        self.debug = world.debug
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None  # <- 2020-08-07추가
        self.dim = (config.width, config.height)
        bp_library = world.get_blueprint_library()
        ###센서 초기화.
        item = sensor_radar[select_sensor]
        bp = bp_library.find(item[0])
        # print("test : ", bp)
        for attr_name, attr_value in item[2].items():
            bp.set_attribute(attr_name, attr_value)
            if attr_name == str('range'):
                print("check=====")
                self.velocity_range = float(attr_value)

        sensor = self.world.spawn_actor(bp, transforms[3], attach_to=self.target)
        print("센서 생성 id : ", sensor.id)
        weak_self = weakref.ref(self)

        # radar_data type -> carla.RadarDetection
        sensor.listen(lambda radar_data: Sensor_Radar._Radar_callback(weak_self, radar_data))

        self.sensorActor = sensor  # 설정된 센서 저장.

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    @staticmethod
    def _Radar_callback(weak_self, radar_data):
        # print("test : ", radar_data)
        self = weak_self()
        if not self:
            # print("radar is not self")
            return
        # To get a numpy [[vel, altitude, azimuth, depth],...[,,,]]:
        # points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
        # points = np.reshape(points, (len(radar_data), 4))

        current_rot = radar_data.transform.rotation
        for detect in radar_data:
            azi = math.degrees(detect.azimuth)
            alt = math.degrees(detect.altitude)
            # The 0.25 adjusts a bit the distance so the dots can
            # be properly seen
            fw_vec = carla.Vector3D(x=detect.depth - 0.25)
            carla.Transform(
                carla.Location(),
                carla.Rotation(
                    pitch=current_rot.pitch + alt,
                    yaw=current_rot.yaw + azi,
                    roll=current_rot.roll)).transform(fw_vec)

            def clamp(min_v, max_v, value):
                return max(min_v, min(value, max_v))

            norm_velocity = detect.velocity / self.velocity_range  # range [-1, 1]
            r = int(clamp(0.0, 1.0, 1.0 - norm_velocity) * 255.0)
            g = int(clamp(0.0, 1.0, 1.0 - abs(norm_velocity)) * 255.0)
            b = int(abs(clamp(- 1.0, 0.0, - 1.0 - norm_velocity)) * 255.0)
            self.debug.draw_point(
                radar_data.transform.location + fw_vec,
                size=0.075,
                life_time=0.06,
                persistent_lines=False,
                color=carla.Color(r, g, b))


# ==============================================================================
# -- GnssSensor ----------------------------------------------------------------
# ==============================================================================


class GnssSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    def destroy(self):  # target 센서 제거.
        self.sensor.destroy()

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude


# ==============================================================================
# -- IMUSensor -----------------------------------------------------------------
# ==============================================================================


class IMUSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.accelerometer = (0.0, 0.0, 0.0)
        self.gyroscope = (0.0, 0.0, 0.0)
        self.compass = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.imu')
        self.sensor = world.spawn_actor(
            bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(
            lambda sensor_data: IMUSensor._IMU_callback(weak_self, sensor_data))

    def destroy(self):  # target 센서 제거.
        self.sensor.destroy()

    @staticmethod
    def _IMU_callback(weak_self, sensor_data):
        self = weak_self()
        if not self:
            return
        limits = (-99.9, 99.9)
        self.accelerometer = (
            max(limits[0], min(limits[1], sensor_data.accelerometer.x)),
            max(limits[0], min(limits[1], sensor_data.accelerometer.y)),
            max(limits[0], min(limits[1], sensor_data.accelerometer.z)))
        self.gyroscope = (
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.x))),
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.y))),
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.z))))
        self.compass = math.degrees(sensor_data.compass)


# ==============================================================================
# -- All Sensor Start ---------------------------------------------------------
# ==============================================================================

class SensorManager(object):
    def __init__(self, world, target, args):
        self.world = world
        self.target = target
        self.args = args
        self.sensor = None
        self.recoding_check = False
        self.radar_sensor = None
        # self.sensor_a0 = Camera_Rgb(world, target, args, select_sensor=0, tick=0.0)
        # self.sensor_b0 = Camera_Depth(world, target, args, select_sensor=0, tick=0.0)
        # self.sensor_b1 = Camera_Depth(world, target, args, select_sensor=1, tick=0.0)
        # self.sensor_b2 = Camera_Depth(world, target, args, select_sensor=2, tick=0.0)
        # self.sensor_c0 = Camera_Segmentation(world, target, args, select_sensor=0, tick=0.0)
        # self.sensor_d0 = Sensor_Lider(world, target, args, select_sensor=1)
        # self.sensor_list = [self.sensor_a0, self.sensor_b0, self.sensor_b1, self.sensor_b2, self.sensor_c0,
        #                     self.sensor_d0]

    def select_sensor(self, index=-1, check=False):
        if self.sensor is None:
            if index == -1:
                print("sensor Camera_Rgb")
                self.sensor = Camera_Rgb(self.world, self.target, self.args, select_sensor=0)
            elif index == 0:
                print("sensor Camera_Rgb")
                self.sensor = Camera_Rgb(self.world, self.target, self.args, select_sensor=0)
            elif index == 1:
                print("sensor Camera_Depth")
                self.sensor = Camera_Depth(self.world, self.target, self.args, select_sensor=0)
            elif index == 2:
                print("sensor Lider_Raycast")
                self.sensor = Sensor_Lider(self.world, self.target, self.args, select_sensor=0)
            elif index == 3:
                print("sensor Camera_segmentation")
                self.sensor = Camera_Segmentation(self.world, self.target, self.args, select_sensor=0)
            elif index == 4:
                print("sensor Camera_dvs")
                self.sensor = Camera_Dvs(self.world, self.target, self.args, select_sensor=0)

            return self.sensor
        else:
            # print("sensor is alive")
            return self.sensor

    def set_radar(self):
        if self.radar_sensor is None:
            self.radar_sensor = Sensor_Radar(self.world, self.target, self.args, select_sensor=0)
            print("레이다 시작")
        elif self.radar_sensor is not None:
            self.radar_sensor.destroy()
            self.radar_sensor = None
            print("레이다 종료")

    def recording(self):
        if self.recoding_check is False:
            self.recoding_check = True
            print("녹화시작")
        elif self.recoding_check is True:
            self.recoding_check = False
            print("녹화종료")

        self.sensor.set_recording(self.recoding_check)

    def destroy(self):
        self.sensor.destroy()
        self.sensor = None
