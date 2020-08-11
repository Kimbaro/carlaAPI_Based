import glob
import os
import sys
from threading import Thread

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('carla-0.9.7*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass
import logging
import carla
import random
import argparse
from util.VehicleRouteManager import VehicleRouteManager

vehicles_list = []


def main():
    argparser = argparse.ArgumentParser(description="설정값")
    argparser.add_argument('--host', metavar='H', default='localhost', help='호스트 서버의 아이피 주소 입력.')
    argparser.add_argument('--port', metavar='P', default=2005, type=int, help='호스트 서버의 TCP포트 입력.')
    argparser.add_argument('--camera', metavar='WIDTHxHEIGHT', default='1280x720', help='카메라 센서 이미지')
    argparser.add_argument(
        '-n', '--number-of-vehicles',
        metavar='N',
        default=5,
        type=int,
        help='number of vehicles (default: 10)')

    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.camera.split('x')]

    # Carla init
    client = carla.Client(args.host, 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    map = world.get_map()

    # Route Set
    spawnpoints = map.get_spawn_points()
    blueprints = world.get_blueprint_library().filter('vehicle.audi.*')
    start_POI = map.get_waypoint(random.choice(spawnpoints).location)
    end_POI = map.get_waypoint(random.choice(spawnpoints).location)

    # TARGET Vehicles Spawn
    blueprint = random.choice([x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4])
    target = world.spawn_actor(blueprint, start_POI.transform)
    print("target id : ", target.id)
    vehicles_list.append(target)  # [0]에 차량.

    try:
        ### 경로추적 생성.
        routeManager = VehicleRouteManager(world, start_POI, end_POI, target)
        # 임의 경유지 등록
        for i in range(1):
            routeManager.add_route(random.choice(map.generate_waypoints(30)))

        while True:
            world.tick()
            routeManager.tick()
    finally:
        print('\ndestroying %d vehicles' % len(vehicles_list))
        for actor in vehicles_list:
            actor.destroy()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
