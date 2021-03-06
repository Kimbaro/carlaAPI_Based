import glob
import os
import sys
import argparse
import logging
from environment_config_remote.WeatherManager import Weather_Manager
import random
import time
import json
import weakref
import numpy as np
import datetime
from environment_config_remote.blueprintAttribute import ActorData_Manager
from environment_config_remote.Data.weather_data import UI_DATA
import environment_config_remote.Data.ui_input_module as ui
from PyQt5.QtWidgets import *
from PyQt5 import uic

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('environment_config_remote/carla-0.9.9.4*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass

import carla
from carla import VehicleLightState as vls
from carla import ColorConverter as cc

# UI파일 연결
# 단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("environment_config_remote/Carla_UI.ui")[0]

# @todo 센서 및 설정정보 리스트, 가능하면 아래 배열 형식을 따를 수 있도록해야함.
# @todo 변수명 self.sensor_option
# @todo [sensor_bp_id, image_converting_type, description, save dir, {attr_name: attr_value, ....}]
# @todo LIDAR의 경우 : [sensor_bp_id, save dir, {attr_name: attr_value, ....}]


"""
    Sensor Class 
"""


class Sensor_Lidar(object):
    def __init__(self, world, target, config):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None  # <- 2020-08-07추가
        self.dim = (config.width, config.height)

        self.sensor_option = config.sensor_option
        self.sensor_position = config.sensor_position
        item = self.sensor_option

        bp_library = world.get_blueprint_library()
        bp = bp_library.find(item[0])
        for attr_name, attr_value in item[2].items():
            bp.set_attribute(attr_name, attr_value)
            if attr_name == str('range'):
                print("check=====")
                self.lidar_range = float(attr_value)

        sensor = self.world.spawn_actor(bp, self.sensor_position, attach_to=self.target)
        weak_self = weakref.ref(self)
        sensor.listen(lambda point_cloud: Sensor_Lidar._parse_image(weak_self, point_cloud, item[1]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    # PyGame 파트 ///////////////////////////////////
    # @staticmethod
    # def _parse_pygame(self, image):  # <- 2020-08-07추가
    #     # pygame set
    #     points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
    #     points = np.reshape(points, (int(points.shape[0] / 3), 3))
    #     lidar_data = np.array(points[:, :2])
    #     lidar_data *= min(self.dim) / (2.0 * self.lidar_range)
    #     lidar_data += (0.5 * self.dim[0], 0.5 * self.dim[1])
    #     lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
    #     lidar_data = lidar_data.astype(np.int32)
    #     lidar_data = np.reshape(lidar_data, (-1, 2))
    #     lidar_img_size = (self.dim[0], self.dim[1], 3)
    #     lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)
    #     lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
    #     self.surface = pygame.surfarray.make_surface(lidar_img)

    @staticmethod
    def _parse_image(weak_self, image, id):  # <- 2020-08-07추가
        self = weak_self()
        # Sensor_Lidar._parse_pygame(self, image)
        if self.recording:
            simulation_time = image.timestamp
            time = datetime.timedelta(seconds=int(simulation_time))
            time = str(time).replace(':', '-')
            image.save_to_disk('sensor/' + str(id) + '/%s' % time + '/%08d' % image.frame)

    def render(self, display):  # <- 2020-08-07추가
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


class Camera_Depth(object):
    def __init__(self, world, target, config):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None

        self.sensor_option = config.sensor_option
        self.sensor_position = config.sensor_position
        item = self.sensor_option

        bp_library = world.get_blueprint_library()
        bp = bp_library.find(item[0])
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, self.sensor_position, attach_to=self.target)
        weak_self = weakref.ref(self)
        sensor.listen(lambda image: Camera_Depth._parse_image(weak_self, image, item[1], item[3]))
        self.sensorActor = sensor  # 설정된 센서 저장.

    def set_recording(self, check=False):
        self.recording = check

    def destroy(self):  # target 센서 제거.
        self.sensorActor.destroy()

    # PyGame 파트 ///////////////////////////////////
    # @staticmethod
    # def _parse_pygame(self, image, cc):
    #     # pygame set
    #     array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    #     array = np.reshape(array, (image.height, image.width, 4))
    #     array = array[:, :, :3]
    #     array = array[:, :, ::-1]
    #     self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    @staticmethod
    def _parse_image(weak_self, image, cc, id):
        self = weak_self()

        image.convert(cc)
        # Camera_Rgb._parse_pygame(self, image, cc)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]

        # PyGame 파트 ///////////////////////////////////
        # self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        if self.recording:
            simulation_time = image.timestamp
            time = datetime.timedelta(seconds=int(simulation_time))
            time = str(time).replace(':', '-')
            image.save_to_disk('sensor/' + str(id) + '/%s' % time + '/%08d' % image.frame)

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))


class Camera_Rgb(object):
    def __init__(self, world, target, config):
        self.world = world
        self.bp_library = world.get_blueprint_library()
        self.target = target
        self.sensorActor = None
        self.recording = False
        self.surface = None

        self.sensor_option = config.sensor_option
        self.sensor_position = config.sensor_position
        item = self.sensor_option

        bp_library = world.get_blueprint_library()
        bp = bp_library.find(item[0])
        for attr_name, attr_value in item[4].items():
            bp.set_attribute(attr_name, attr_value)

        sensor = self.world.spawn_actor(bp, self.sensor_position, attach_to=self.target)
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

        # PyGame 파트 ///////////////////////////////////
        # self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        if self.recording:
            simulation_time = image.timestamp
            time = datetime.timedelta(seconds=int(simulation_time))
            time = str(time).replace(':', '-')
            image.save_to_disk('sensor/' + str(id) + '/%s' % time + '/%08d' % image.frame)

    # PyGame 파트 ///////////////////////////////////
    # @staticmethod
    # def _parse_pygame(self, image, cc):
    #     # pygame set
    #     array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    #     array = np.reshape(array, (image.height, image.width, 4))
    #     array = array[:, :, :3]
    #     array = array[:, :, ::-1]
    #     self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
    #
    # def render(self, display):
    #     if self.surface is not None:
    #         display.blit(self.surface, (0, 0))


class Sensor_Manager(Camera_Rgb, Camera_Depth, Sensor_Lidar):
    def __init__(self, world, target, config):
        self.check = False
        self.index = -1
        self.world = world
        self.target = target
        self.args = config
        self.sensor = None
        self.recoding_check = False
        self.radar_sensor = None
        self.sensor_imu = None
        self.sensor_gnss = None

    def set_recording(self, check=False):
        self.sensor.set_recording(self.recoding_check)

    def recording(self):
        if self.recoding_check is False:
            self.recoding_check = True
            print("녹화시작")
        elif self.recoding_check is True:
            self.recoding_check = False
            print("녹화종료")
        self.sensor.set_recording(self.recoding_check)

    def select_sensor(self, index=-1, sensor_option=None, sensor_position=None):
        self.args.sensor_option = sensor_option
        self.args.sensor_position = sensor_position
        if self.sensor is None:
            if index == -1:
                print("sensor Camera_Rgb")
                self.sensor = Camera_Rgb(self.world, self.target, self.args)
            elif index == 0:
                print("sensor Camera_Rgb")
                self.sensor = Camera_Rgb(self.world, self.target, self.args)
            elif index == 1:
                print("sensor Camera_Depth")
                self.sensor = Camera_Depth(self.world, self.target, self.args)
            elif index == 2:
                print("sensor Lidar")
                self.sensor = Sensor_Lidar(self.world, self.target, self.args)

            return self.sensor
        else:
            return self.sensor

    def destroy(self):
        self.sensor.destroy()
        if self.radar_sensor is not None:
            self.radar_sensor.destroy()
        if self.sensor_imu is not None:
            self.sensor_imu.destroy()
        if self.sensor_gnss is not None:
            self.sensor_gnss.destroy()
        self.radar_sensor = None
        self.sensor = None


class NPC_Manager(object):

    def __init__(self, world, client, args, target, carla_package):
        """
        :param world:
        :param client:
        :param args:
        :param target:
        :param carla_package: [SpawnActor, SetAutopilot, SetVehicleLightState, FutureActor, DestroyActor]
        """
        self.world = world
        self.client = client
        self.args = args
        self.target = target
        self.vehicles_list = []
        self.walkers_list = []
        self.all_id = []
        self.carla_package = carla_package
        self.synchronous_master = False

        # Traffic Manager Init
        self.traffic_manager = client.get_trafficmanager(self.args.tm_port)
        self.traffic_manager.set_global_distance_to_leading_vehicle(3.0)
        if self.args.hybrid:
            self.traffic_manager.set_hybrid_physics_mode(True)

        if self.args.sync:
            settings = self.world.get_settings()
            self.traffic_manager.set_synchronous_mode(True)
            if not settings.synchronous_mode:
                self.synchronous_master = True
                settings.synchronous_mode = True
                settings.fixed_delta_seconds = 0.05
                self.world.apply_settings(settings)
            else:
                self.synchronous_master = False

        # Blueprint Setting
        _blueprints = self.world.get_blueprint_library().filter("vehicle.*")
        self.blueprintsWalkers = self.world.get_blueprint_library().filter("walker.pedestrian.*")

        self.blueprints = [x for x in _blueprints if int(x.get_attribute('number_of_wheels')) == 4 if
                           not x.id.endswith('cybertruck') if not x.id.endswith('carlacola')]
        self.spawn_points = self.world.get_map().get_spawn_points()
        self.number_of_spawn_points = len(self.spawn_points)

    def destroy_npc(self):
        DestroyActor = self.carla_package[4]
        self.client.apply_batch([DestroyActor(x) for x in self.all_id])
        self.all_id = []
        self.walkers_list = []
        self.client.apply_batch([DestroyActor(x) for x in self.vehicles_list])
        self.vehicles_list = []

    #################################################
    # UI 차량관련 이벤트 함수 구현부
    #################################################
    def ui_dcv_remote_speed(self, mode=False, speed=0):
        """
        UI 데이터수집차량 속도 제어기

        사용예시) no_rendering_keyEvent.py 에서
        routeManager.ui_dcv_remote_speed(mode=True, speed=0) 인 경우 속도 0으로 강제로 제어함.
        routeManager.ui_dcv_remote_speed(mode=False) 인 경우 Auto모드 활성화

        :param mode: False인 경우 Auto모드
        :param speed: Auto모드가 아닐때 입력 속도를 반영함.
        """
        if mode is True:
            self.agent.emergency_speed_control(remote=True, speed=speed)
        elif mode is False:
            self.agent.emergency_speed_control(remote=False)

    def ui_world_npc_walker(self, input_number):
        SpawnActor = self.carla_package[0]
        DestroyActor = self.carla_package[4]

        if len(self.walkers_list) >= 1:  # 생성된 워커 제거
            self.client.apply_batch([DestroyActor(x) for x in self.all_id])
            self.all_id = []
            self.walkers_list = []
            time.sleep(0.5)

        if input_number > 0:
            percentagePedestriansRunning = 0.0  # how many pedestrians will run
            percentagePedestriansCrossing = 0.0  # how many pedestrians will walk through the road

            # 1. take all the random locations to spawn
            spawn_points = []
            for i in range(input_number):
                spawn_point = carla.Transform()
                loc = self.world.get_random_location_from_navigation()
                if (loc != None):
                    spawn_point.location = loc
                    spawn_points.append(spawn_point)

            # 2. we spawn the walker object
            batch = []
            walker_speed = []
            for spawn_point in spawn_points:
                walker_bp = random.choice(self.blueprintsWalkers)
                # set as not invincible
                if walker_bp.has_attribute('is_invincible'):
                    walker_bp.set_attribute('is_invincible', 'false')
                # set the max speed
                if walker_bp.has_attribute('speed'):
                    if (random.random() > percentagePedestriansRunning):
                        # walking
                        walker_speed.append(walker_bp.get_attribute('speed').recommended_values[1])
                    else:
                        # running
                        walker_speed.append(walker_bp.get_attribute('speed').recommended_values[2])
                else:
                    logging.warning("Walker has no speed")
                    walker_speed.append(0.0)
                batch.append(SpawnActor(walker_bp, spawn_point))

            results = self.client.apply_batch_sync(batch, True)
            walker_speed2 = []
            for i in range(len(results)):
                if results[i].error:
                    # log.error(results[i].error)
                    pass
                else:
                    self.walkers_list.append({"id": results[i].actor_id})
                    walker_speed2.append(walker_speed[i])
            walker_speed = walker_speed2
            # 3. we spawn the walker controller
            batch = []
            walker_controller_bp = self.world.get_blueprint_library().find('controller.ai.walker')
            for i in range(len(self.walkers_list)):
                batch.append(SpawnActor(walker_controller_bp, carla.Transform(), self.walkers_list[i]["id"]))
            results = self.client.apply_batch_sync(batch, True)
            for i in range(len(results)):
                if results[i].error:
                    # logging.error(results[i].error)
                    pass
                else:
                    self.walkers_list[i]["con"] = results[i].actor_id
            # 4. we put altogether the walkers and controllers id to get the objects from their id
            for i in range(len(self.walkers_list)):
                self.all_id.append(self.walkers_list[i]["con"])
                self.all_id.append(self.walkers_list[i]["id"])
            all_actors = self.world.get_actors(self.all_id)

            # 5. initialize each controller and set target to walk to (list is [controler, actor, controller, actor ...])
            # set how many pedestrians can cross the road
            self.world.set_pedestrians_cross_factor(percentagePedestriansCrossing)
            for i in range(0, len(self.all_id), 2):
                # start walker
                all_actors[i].start()
                # set walk to random point
                all_actors[i].go_to_location(self.world.get_random_location_from_navigation())
                # max speed
                all_actors[i].set_max_speed(float(walker_speed[int(i / 2)]))

            # wait for a tick to ensure client receives the last transform of the walkers we have just created
            if not self.args.sync or not synchronous_master:
                self.world.wait_for_tick()
            else:
                self.world.tick()

            count = len(self.walkers_list)
            count_fail = input_number - count
            print('보행자 %d 오브젝트 충돌, 보행자 %d 스폰' % (count_fail, count))

    def ui_world_npc_vehicle(self, input_number):
        SpawnActor = self.carla_package[0]
        SetAutopilot = self.carla_package[1]
        SetVehicleLightState = self.carla_package[2]
        FutureActor = self.carla_package[3]
        DestroyActor = self.carla_package[4]

        if len(self.vehicles_list) >= 1:  # 생성된 차량 제거
            self.client.apply_batch([DestroyActor(x) for x in self.vehicles_list])
            self.vehicles_list = []
            time.sleep(0.5)

        if input_number > 0:
            # --------------
            # Spawn vehicles
            # --------------
            batch = []
            for n, transform in enumerate(self.spawn_points):
                if n >= input_number:
                    break
                blueprint = random.choice(self.blueprints)
                if blueprint.has_attribute('color'):
                    color = random.choice(blueprint.get_attribute('color').recommended_values)
                    blueprint.set_attribute('color', color)
                if blueprint.has_attribute('driver_id'):
                    driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
                    blueprint.set_attribute('driver_id', driver_id)

                # prepare the light state of the cars to spawn
                light_state = vls.NONE
                # autopilot vehicle right on
                light_state = vls.Position | vls.LowBeam | vls.LowBeam

                # spawn the cars and set their autopilot and light state all together
                batch.append(SpawnActor(blueprint, transform)
                             .then(SetAutopilot(FutureActor, True, self.traffic_manager.get_port()))
                             .then(SetVehicleLightState(FutureActor, light_state)))

                for response in self.client.apply_batch_sync(batch, self.synchronous_master):
                    if response.error:
                        # logging.error(response.error)
                        pass
                    else:
                        self.traffic_manager.global_percentage_speed_difference(10.0)  # 제한 속도의 10% 속도로 주행
                        self.vehicles_list.append(response.actor_id)
            time.sleep(0.5)

            # 교통규칙 위배 옵션 설정 ==
            # danger_car_id = random.choice(self.vehicles_list)
            # danger_car = self.world.get_actor(danger_car_id)
            # data = danger_car.attributes
            # print("danger car info : ", str(data['role_name']))
            # self.traffic_manager.ignore_lights_percentage(danger_car, 100)  # 신호 위반 확률
            # self.traffic_manager.distance_to_leading_vehicle(danger_car, 0)  # 앞차와의 간격 ?
            # self.traffic_manager.vehicle_percentage_speed_difference(danger_car, -200)  # 제한 속도의 200% 속도로 주행
            # 교통규칙 위배 옵션 설정 == END

            count = len(self.vehicles_list)
            count_fail = input_number - count
            print('차량 %d 오브젝트 충돌, 차량 %d 스폰' % (count_fail, count))


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class, NPC_Manager, Sensor_Manager, Weather_Manager):
    def __init__(self, ui_data):
        super().__init__()
        self.ui_data = ui_data
        self.setupUi(self)

        # NPC 설정
        self.pushButton_NPC_Spawn.clicked.connect(self.NPC_Spawn)

        # 시간 변경 radio 버튼
        self.radioButton_1.clicked.connect(self.groupbox_Time_Function)
        self.radioButton_2.clicked.connect(self.groupbox_Time_Function)
        self.radioButton_3.clicked.connect(self.groupbox_Time_Function)
        self.radioButton_auto.clicked.connect(self.groupbox_Time_Function)

        # 날씨 번경 Slider and checkbox
        self.horizontalSlider_fog.sliderReleased.connect(self.show_Slider_weather)
        self.horizontalSlider_rain.sliderReleased.connect(self.show_Slider_weather)
        self.horizontalSlider_wind.sliderReleased.connect(self.show_Slider_weather)
        self.horizontalSlider_clouds.sliderReleased.connect(self.show_Slider_weather)
        self.checkBox_weather_auto.stateChanged.connect(self.show_checkBox_weather)

        # 속도 설정
        self.pushButton_Speed.clicked.connect(self.speed_control)
        self.lineEdit_speed.returnPressed.connect(self.speed_control)

        # Auto
        self.checkBox_etc_auto.clicked.connect(self.auto_control)

        # Sensor button (센서 설정, 데이터 수집 시작, 수집 멈춤)
        self.pushButton_Setting.clicked.connect(self.Sensor_Setting)
        self.pushButton_Play.clicked.connect(self.Sensor_Play)
        self.pushButton_Stop.clicked.connect(self.Sensor_Stop)

        # Carla Init
        argparser = argparse.ArgumentParser(description="설정값")
        argparser.add_argument(
            '--hybrid',
            action='store_true',
            help='Enanble')
        argparser.add_argument(
            '--sync',
            action='store_true',
            help='Synchronous mode execution')
        argparser.add_argument('--host', metavar='H', default='127.0.0.1', help='호스트 서버의 아이피 주소 입력.')
        argparser.add_argument('--port', metavar='P', default=2000, type=int, help='호스트 서버의 TCP포트 입력.')
        argparser.add_argument(
            '--tm-port',
            metavar='P',
            default=8000,
            type=int,
            help='트래픽매니저 전용 rpc 포트 (default: 8000)')
        argparser.add_argument(
            '-t', '--target_id',
            metavar='N',
            default='target',
            type=str,
            help='센서수집을 위한 대상 차량 actor_id')
        argparser.add_argument('--camera', metavar='WIDTHxHEIGHT', default='1280x720', help='카메라 센서 이미지')

        self.args = argparser.parse_args()
        self.args.width, self.args.height = [int(x) for x in self.args.camera.split('x')]
        print(self.args.target_id)

        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        SetVehicleLightState = carla.command.SetVehicleLightState
        FutureActor = carla.command.FutureActor
        DestroyActor = carla.command.DestroyActor

        self.carla_package = [SpawnActor, SetAutopilot, SetVehicleLightState, FutureActor, DestroyActor]

        self.client = carla.Client(self.args.host, 2000)
        self.client.set_timeout(10.0)
        print("carla connect")
        self.world = self.client.get_world()
        print("search target")

        # search DCV
        target_actor_attr = ActorData_Manager(self.world)
        self.target = target_actor_attr.split()
        # self.target = self.world.get_actor(self.args.target_id)  # 타겟 차량 Actor_id
        # print("select vehicle : ", self.target)
        self._weather = Weather_Manager(self.world.get_weather(), self.world)
        self._npc = NPC_Manager(self.world, self.client, self.args, self.target, self.carla_package)
        self._sun_set = None
        self._weather_set = None
        self._sensor = None
        self._sensor_list = []
        self.sensor_option = None
        self.sensor_position = None
        self.sensor_count = 0

    # NPC 버튼 클릭 후 값 가져오기
    def NPC_Spawn(self):
        people = int(self.Edit_People.text())
        vehicle = int(self.Edit_Vehicle.text())
        self.ui_data.set_NPC_Spawn(people, vehicle)
        self._npc.ui_world_npc_vehicle(self.ui_data.A_vehicle)
        self._npc.ui_world_npc_walker(self.ui_data.A_people)
        print("Spawn Complete")

    # 시간 변경 radio 버튼 함수
    def groupbox_Time_Function(self):
        elapsed_time = 0
        if self.radioButton_1.isChecked():
            self.ui_data.B_sun_type = "midday"
        elif self.radioButton_2.isChecked():
            self.ui_data.B_sun_type = "sunset"
        elif self.radioButton_3.isChecked():
            self.ui_data.B_sun_type = "midnight"
        elif self.radioButton_auto.isChecked():
            if self.ui_data.B_remote is True:
                self.ui_data.B_remote = False
            else:
                self.ui_data.B_remote = True
        self._weather_set = ui.UI_INPUT_CONTROL().return_weather(clouds=self.ui_data.C_cloud, rain=self.ui_data.C_rain,
                                                                 wetness=self.ui_data.C_rain * 5,
                                                                 puddles=self.ui_data.C_rain, wind=self.ui_data.C_wind,
                                                                 fog=self.ui_data.C_fog, remote=self.ui_data.C_remote)
        self._sun_set = ui.UI_INPUT_CONTROL().return_sun_type(sun_type=self.ui_data.B_sun_type,
                                                              remote=self.ui_data.B_remote)
        timestamp = self.world.wait_for_tick().timestamp
        elapsed_time += timestamp.delta_seconds
        self._weather.tick(elapsed_time, self._weather_set, self._sun_set)

    # 날씨 번경 Slider
    def show_Slider_weather(self):
        elapsed_time = 0
        self.ui_data.C_fog = self.horizontalSlider_fog.value()
        self.ui_data.C_rain = self.horizontalSlider_rain.value()
        self.ui_data.C_wind = self.horizontalSlider_wind.value()
        self.ui_data.C_cloud = self.horizontalSlider_clouds.value()
        self._weather_set = ui.UI_INPUT_CONTROL().return_weather(clouds=self.ui_data.C_cloud, rain=self.ui_data.C_rain,
                                                                 wetness=self.ui_data.C_rain * 5,
                                                                 puddles=self.ui_data.C_rain, wind=self.ui_data.C_wind,
                                                                 fog=self.ui_data.C_fog, remote=self.ui_data.C_remote)
        self._sun_set = ui.UI_INPUT_CONTROL().return_sun_type(sun_type=self.ui_data.B_sun_type,
                                                              remote=self.ui_data.B_remote)
        timestamp = self.world.wait_for_tick().timestamp
        elapsed_time += timestamp.delta_seconds
        self._weather.tick(elapsed_time, self._weather_set, self._sun_set)

    # 날씨 번경 checkBox
    def show_checkBox_weather(self):
        if self.checkBox_weather_auto.isChecked():
            if self.ui_data.C_remote is True:
                self.ui_data.C_remote = False
            else:
                self.ui_data.C_remote = True

    # 속도 제어
    def speed_control(self):
        speed = int(self.lineEdit_speed.text())
        self.ui_data.D_speed = speed

    # Auto
    def auto_control(self):
        if self.checkBox_etc_auto.isChecked():
            if self.ui_data.D_remote is True:
                self.ui_data.D_remote = False
            else:
                self.ui_data.D_remote = True

    # 센서 설치 (데이터 수집은 별도)
    # x, y 값 없을시 에러 -> 없을시 화면 크기 반환
    def Sensor_Setting(self):
        if self.tabWidget_Sensor_control.currentIndex() == 1:
            print("Depth")
            X = int(self.lineEdit_Depth_X.text())
            Y = int(self.lineEdit_Depth_Y.text())
            Fov = float(self.lineEdit_Depth_Fov.text())
            sensor_tick = float(self.lineEdit_Depth_Time.text())
            sensor_x = float(self.lineEdit_Location_X.text())
            sensor_y = float(self.lineEdit_Location_Y.text())
            sensor_z = float(self.lineEdit_Location_Z.text())
            sensor_roll = float(self.lineEdit_Rotation_Roll.text())
            sensor_pitch = float(self.lineEdit_Rotation_Pitch.text())
            sensor_yaw = float(self.lineEdit_Rotation_Yaw.text())
            print(X, Y, Fov, sensor_x, sensor_y, sensor_z, sensor_roll, sensor_pitch, sensor_yaw)

            self._sensor = Sensor_Manager(self.world, self.target, self.args)
            self.sensor_option = ['sensor.camera.depth', cc.Raw, 'Camera Depth', 'depth' + str(self.sensor_count), {
                'image_size_x': str(X),
                'image_size_y': str(Y),
                'fov': str(Fov)
            }]
            self.sensor_position = carla.Transform(carla.Location(x=sensor_x, y=sensor_y, z=sensor_z),
                                                   carla.Rotation(roll=sensor_roll, pitch=sensor_pitch, yaw=sensor_yaw))

            self._sensor.select_sensor(1, self.sensor_option, self.sensor_position)
            self._sensor_list.append(self._sensor)
            self.sensor_count = self.sensor_count + 1


        elif self.tabWidget_Sensor_control.currentIndex() == 2:
            print("Lider")
            channels = int(self.lineEdit_Lider_Number.text())
            range = int(self.lineEdit_Lider_Max.text())
            points_per_second = int(self.lineEdit_Lider_Points_Second.text())
            rotation_frequency = int(self.lineEdit_Lider_rotation.text())
            upper_fov = int(self.lineEdit_Lider_Highest.text())
            lower_fov = int(self.lineEdit_Lider_Lowest.text())
            sensor_tick = int(self.lineEdit_Lider_Time.text())
            # ==
            sensor_x = float(self.lineEdit_Location_X.text())
            sensor_y = float(self.lineEdit_Location_Y.text())
            sensor_z = float(self.lineEdit_Location_Z.text())
            sensor_roll = float(self.lineEdit_Rotation_Roll.text())
            sensor_pitch = float(self.lineEdit_Rotation_Pitch.text())
            sensor_yaw = float(self.lineEdit_Rotation_Yaw.text())
            print(channels, range, points_per_second, rotation_frequency, upper_fov, lower_fov, sensor_tick)

            self._sensor = Sensor_Manager(self.world, self.target, self.args)
            self.sensor_option = ['sensor.lidar.ray_cast', 'lidar' + str(self.sensor_count), {
                'channels': str(channels),
                'range': str(range),
                'points_per_second': str(points_per_second),
                'rotation_frequency': str(rotation_frequency),
                'upper_fov': str(upper_fov),  # 상단
                'lower_fov': str(lower_fov),  # 하단
                'sensor_tick': str(sensor_tick)
            }]
            self.sensor_position = carla.Transform(carla.Location(x=sensor_x, y=sensor_y, z=sensor_z),
                                                   carla.Rotation(roll=sensor_roll, pitch=sensor_pitch, yaw=sensor_yaw))

            self._sensor.select_sensor(2, self.sensor_option, self.sensor_position)
            self._sensor_list.append(self._sensor)
            self.sensor_count = self.sensor_count + 1

        else:
            print("RGB")
            X = int(self.lineEdit_RGB_X.text())
            Y = int(self.lineEdit_RGB_Y.text())
            Fov = float(self.lineEdit_RGB_Fov.text())
            sensor_tick = float(self.lineEdit_RGB_Time.text())
            sensor_x = float(self.lineEdit_Location_X.text())
            sensor_y = float(self.lineEdit_Location_Y.text())
            sensor_z = float(self.lineEdit_Location_Z.text())
            sensor_roll = float(self.lineEdit_Rotation_Roll.text())
            sensor_pitch = float(self.lineEdit_Rotation_Pitch.text())
            sensor_yaw = float(self.lineEdit_Rotation_Yaw.text())
            print(X, Y, Fov, sensor_x, sensor_y, sensor_z, sensor_roll, sensor_pitch, sensor_yaw)

            self._sensor = Sensor_Manager(self.world, self.target, self.args)
            self.sensor_option = ['sensor.camera.rgb', cc.Raw, 'Camera RGB', 'rgb' + str(self.sensor_count), {
                'image_size_x': str(X),
                'image_size_y': str(Y),
                'fov': str(Fov)
            }]
            self.sensor_position = carla.Transform(carla.Location(x=sensor_x, y=sensor_y, z=sensor_z),
                                                   carla.Rotation(roll=sensor_roll, pitch=sensor_pitch, yaw=sensor_yaw))

            self._sensor.select_sensor(0, self.sensor_option, self.sensor_position)
            self._sensor_list.append(self._sensor)
            self.sensor_count = self.sensor_count + 1

    def Sensor_Play(self):
        print("센서 데이터 수집", self.target)
        for n, _sensor in enumerate(self._sensor_list):
            _sensor.recording()

        # self._sensor.recording()

    def Sensor_Stop(self):
        print("센서 종료")
        for n, _sensor in enumerate(self._sensor_list):
            _sensor.recording()

        # self._sensor.recording()

    # 창 종료시 이벤트 발생
    def closeEvent(self, event):
        for n, _sensor in enumerate(self._sensor_list):
            _sensor.destroy()

        self._npc.destroy_npc()
        self.target.destroy()

        # self._sensor.destroy()


def main():
    ui_data = UI_DATA()
    app = QApplication(sys.argv)
    myWindow = WindowClass(ui_data)
    myWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
