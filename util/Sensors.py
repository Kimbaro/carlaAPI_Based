import glob
import os
import sys
import weakref
import numpy as np

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_g
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame.locals import K_MINUS
    from pygame.locals import K_EQUALS
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import carla
from carla import ColorConverter as cc
import random

# @todo 센서 및 설정정보 리스트, 가능하면 아래 배열 형식을 따를 수 있도록해야함.
sensor_camera_rgb = [['sensor.camera.rgb', cc.Raw, 'Camera RGB', 'a0', {}],
                     ['sensor.camera.rgb', cc.Raw, 'Camera RGB Distorted', 'a1',
                      {'lens_circle_multiplier': '3.0',
                       'lens_circle_falloff': '3.0',
                       'chromatic_aberration_intensity': '0.5',
                       'chromatic_aberration_offset': '0'}]
                     ]

sensor_camera_depth = [['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)', 'b0', {}],
                       ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)', 'b1', {}],
                       ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)', 'b2', {}]
                       ]

sensor_camera_segmentation = [['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
                               'Camera Semantic Segmentation (CityScapes Palette)', 'c0', {}],
                              ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)',
                               'c1', {}]]

sensor_lidar = [['sensor.lidar.ray_cast', 'd0', {
    'channels': '128',
    'range': '100',
    'points_per_second': '120000',
    'rotation_frequency': '20.0',
    'upper_fov': '15.0',  # 상단
    'lower_fov': '-20.0',  # 하단
    'sensor_tick': '0.0'
}], ['sensor.lidar.ray_cast', 'd1', {
    'channels': '128',
    'range': '50',
    'points_per_second': '120000',
    'rotation_frequency': '20.0',
    'upper_fov': '15.0',  # 상단
    'lower_fov': '-20.0',  # 하단
    'sensor_tick': '0.0'
}]]

sensor_other = [['sensor.other.collision'],
                ['sensor.other.radar'],
                ['sensor.other.gnss'],
                ['sensor.other.imu'],
                ['sensor.other.lane_invasion'],
                ['sensor.other.obstacle']]

transforms = [
    carla.Transform(carla.Location(x=0.8, z=1.7)),
    carla.Transform(carla.Location(x=-5.5, z=2.5)),
    carla.Transform(carla.Location(0, 0, 1.5), carla.Rotation(0, 0, 0))
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
        bp.set_attribute('fov', '110')
        bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[1], attach_to=self.target)
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
        Camera_Rgb._parse_pygame(self, image, cc)
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
        bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[1], attach_to=self.target)
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
    def __init__(self, world, target, config, select_sensor=0, tick=10):
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
        bp.set_attribute('sensor_tick', str(tick))
        # 감마 설정 시
        # if bp.has_attribute('gamma'):
        #     bp.set_attribute('gamma', str(gamma_correction))
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, transforms[1], attach_to=self.target)
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

        sensor = self.world.spawn_actor(bp, transforms[2], attach_to=self.target)
        print("생성 차량 id : ", sensor.id)
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
        lidar_data *= min(self.dim) / 100.0
        lidar_data += (0.5 * self.dim[0], 0.5 * self.dim[1])
        lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
        lidar_data = lidar_data.astype(np.int32)
        lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (self.dim[0], self.dim[1], 3)
        lidar_img = np.zeros((lidar_img_size), dtype=int)
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


class Sensor_Other:
    None


class SensorManager(object):
    def __init__(self, world, target, args):
        self.world = world
        self.target = target
        self.args = args
        self.sensor = None
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
                self.sensor = Camera_Rgb(self.world, self.target, self.args, select_sensor=0, tick=0.0)
            elif index == 0:
                print("sensor Camera_Rgb")
                self.sensor = Camera_Rgb(self.world, self.target, self.args, select_sensor=0, tick=0.0)
            elif index == 1:
                print("sensor Camera_Depth")
                self.sensor = Camera_Depth(self.world, self.target, self.args, select_sensor=0, tick=0.0)
            elif index == 2:
                print("sensor Camera_Lider")
                self.sensor = Sensor_Lider(self.world, self.target, self.args, select_sensor=1)
            return self.sensor
        else:
            print("sensor is alive")
            return self.sensor

    def recording(self, isRecording):
        self.sensor.set_recording(isRecording)

    def destroy(self):
        self.sensor.destroy()
        self.sensor = None
