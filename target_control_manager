import glob
import os
import sys
from threading import Thread

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('carla-0.9.9.4*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass
import logging
import carla
import random
import argparse
import weakref
import pygame
import numpy as np
from pygame import constants as k
from util.VehicleRouteManager import VehicleRouteManager
import util.Drawing_Point as drawing_point

vehicles_list = []


class Observer:
    def __init__(self, args, world, map):
        self.args = args
        self.world = world
        self.map = map
        self.start_POI = None
        self.observer = None
        self.clock = None
        self.display = None
        self.controller = None
        self.surface = None
        self.z = 100.0

    def observerInit(self):
        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        # sensor.camera.rgb 속성 설정
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        # camera_bp.set_attribute('sensor_tick', '1.0')

        self.start_POI = carla.Transform(carla.Location(x=0.0, y=0.0, z=30), carla.Rotation(pitch=-90.0))

        # 옵저버 객체 생성.
        self.observer = self.world.spawn_actor(camera_bp, self.start_POI)
        print("spawn observer")
        weak_self = weakref.ref(self)
        self.observer.listen(lambda image: Observer._parse_image(weak_self, image))

    def setLocation(self, x=0.0, y=0.0):
        self.observer.set_transform(carla.Transform(carla.Location(x, y, self.z), carla.Rotation(pitch=-90.0)))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    def destroy(self):
        self.observer.destroy()


class KeyboardControl(object):
    # def __init__(self, world):
    # world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)
    def __init__(self, world, map):
        self.index = -1
        self.isRecording = None
        self.check = False
        self.x = 0
        self.y = 0
        self.z = 0
        self.debug = world.debug
        self.map = map
        self.log_check = False

    def parse_events(self, routeManager):
        for event in pygame.event.get():
            # print("키 입력 이벤트 테스트 :: ", event.type)
            # 해당라인 부터 구현....
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                if event.key == k.K_TAB:
                    print("Destination List Check")
                    print(routeManager.routeDestinationList)
                elif event.key == k.K_F1:
                    if self.log_check:
                        print("로그기록취소")
                        self.log_check = False
                    else:
                        print("로그기록작성")
                        self.log_check = True
                    routeManager.request_target_speed_log(self.log_check)

                if event.key == k.K_LEFT:
                    print("K_LEFT")
                    self.y -= 10
                    w = self.map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                              lane_type=carla.LaneType.Driving)
                    drawing_point.draw_point(self.debug, w.transform.location,
                                             color=carla.Color(0, 255, 0),
                                             lt=1)
                elif event.key == k.K_RIGHT:
                    print("K_RIGHT")
                    self.y += 10
                    w = self.map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                              lane_type=carla.LaneType.Driving)
                    drawing_point.draw_point(self.debug, w.transform.location,
                                             color=carla.Color(0, 255, 0),
                                             lt=1)
                elif event.key == k.K_UP:
                    print("K_UP")
                    self.x += 10
                    w = self.map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                              lane_type=carla.LaneType.Driving)
                    drawing_point.draw_point(self.debug, w.transform.location,
                                             color=carla.Color(0, 255, 0),
                                             lt=1)
                elif event.key == k.K_DOWN:
                    print("K_DOWN")
                    self.x -= 10
                    w = self.map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                              lane_type=carla.LaneType.Driving)
                    d = drawing_point.draw_point(self.debug, w.transform.location,
                                                 color=carla.Color(0, 255, 0),
                                                 lt=1)
                elif event.key == k.K_SPACE:
                    print("K_KP_ENTER")
                    w = self.map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                              lane_type=carla.LaneType.Driving)
                    routeManager.add_route(w)
                    print(len(routeManager.routeDestinationList))
                    drawing_point.draw_point(self.debug, w.transform.location,
                                             color=drawing_point.green,
                                             lt=120)

    def tick(self, routeManager):
        self.parse_events(routeManager)

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == k.K_ESCAPE)


def main():
    argparser = argparse.ArgumentParser(description="설정값")
    argparser.add_argument('--host', metavar='H', default='203.237.143.101', help='호스트 서버의 아이피 주소 입력.')
    argparser.add_argument('--port', metavar='P', default=2000, type=int, help='호스트 서버의 TCP포트 입력.')
    argparser.add_argument('--camera', metavar='WIDTHxHEIGHT', default='800x480', help='카메라 센서 이미지')
    argparser.add_argument(
        '-n', '--number-of-vehicles',
        metavar='N',
        default=5,
        type=int,
        help='number of vehicles (default: 10)')

    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.camera.split('x')]

    pygame.init()
    display = pygame.display.set_mode(
        (args.width, args.height),
        pygame.HWSURFACE | pygame.DOUBLEBUF)

    # Carla init
    client = carla.Client(args.host, 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    map = world.get_map()

    # Route Set
    spawnpoints = map.get_spawn_points()
    spawnpoint = random.choice(spawnpoints)
    blueprints = world.get_blueprint_library().filter('vehicle.*')
    start_POI = map.get_waypoint(spawnpoint.location)
    end_POI = map.get_waypoint(random.choice(spawnpoints).location)

    # TARGET Vehicles Spawn
    blueprint = random.choice([x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4])
    target = world.try_spawn_actor(blueprint, spawnpoint)

    controller = KeyboardControl(world, map)

    # Observer
    observer = Observer(args, world, map)
    observer.observerInit()

    ### 경로추적 생성.
    routeManager = VehicleRouteManager(world, map, target, 20, start_POI)

    print("spawn target : ", target.id)
    vehicles_list.append(target)  # [0]에 차량.

    # sensorManager = SensorManager(world, observer.observer, args)
    observer.setLocation(target.get_location().x, target.get_location().y)

    try:
        # 임의 경유지 등록
        # for i in range(10):
        #     routeManager.add_route(random.choice(map.generate_waypoints(30)))
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            if controller.parse_events(routeManager):
                return
            world.tick()
            routeManager.tick(target)
            # sensorManager.select_sensor().render(display)
            observer.render(display)
            pygame.display.flip()
            observer.setLocation(target.get_location().x, target.get_location().y)
            # world.tick()
    finally:
        print('\ndestroying %d vehicles' % len(vehicles_list))
        # sensorManager.destroy()
        observer.destroy()
        for actor in vehicles_list:
            actor.destroy()
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
