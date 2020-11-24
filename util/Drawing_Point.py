import glob
import os
import sys

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass

import carla
import random

red = carla.Color(255, 0, 0)
green = carla.Color(0, 255, 0)
blue = carla.Color(47, 210, 231)
cyan = carla.Color(0, 255, 255)
yellow = carla.Color(255, 255, 0)
orange = carla.Color(255, 162, 0)
white = carla.Color(255, 255, 255)


def draw_point(debug, location, color=carla.Color(255, 0, 0), lt=-0.1):
    debug.draw_point(location + carla.Location(z=0.25), 0.1, color, lt)
    # debug.draw_point(location + carla.Location(z=0.25), 0.1, color, lt, False)


def draw_point_union(debug, location, color=carla.Color(255, 0, 0), lt=-0.1):
    debug.draw_line(
        location + carla.Location(z=0.4),
        location + carla.Location(z=0.4),
        thickness=0.5, color=color, life_time=lt, persistent_lines=False)


def draw_spawnpoint_info(debug, location, color=carla.Color(255, 0, 0), text="", lt=30):
    debug.draw_string(location + carla.Location(z=0.5), str(text), False, color, lt)
    # z 값 0.5 단위로 띄어서 할것
    # debug.draw_string(w_loc + carla.Location(z=-.5), str(w.lane_change), False, red, lt)


def draw_waypoint_info(debug, waypoint, num, lt=-0.1):
    w_loc = waypoint.transform.location
    debug.draw_string(w_loc + carla.Location(z=0.25), "No." + str(num), False, red, lt)
    debug.draw_point(w_loc + carla.Location(z=0.25), 0.1, red, lt)
    # debug.draw_string(w_loc + carla.Location(z=-.5), str(w.lane_change), False, red, lt)


def waypoints_viewer(world, map):
    debug = world.debug
    way_points = map.generate_waypoints(8.0)
    # waypoints_type_driving = [x for x in way_points if
    #                           x.lane_type == carla.LaneType.Driver]

    # way_points_junction = None
    # for waypoint in way_points:
    #     if waypoint.is_junction == True:
    #         # junction = waypoint.get_junction()    9.7에서 지원 안함
    #         for waypoint_j in junction.get_waypoints:
    #             print(waypoint_j)

    for n, waypoint in enumerate(way_points):
        # print(waypoint.lane_type)
        draw_point(debug, waypoint.transform.location, red)
        draw_waypoint_info(debug, waypoint, n)

    x = input('\n조회할 넘버 입력 : ')
    waypoint = way_points[int(x)]
    draw_point(debug, waypoint.transform.location, yellow)
    lt = waypoint.transform.location
    rt = waypoint.transform.rotation
    print("[ No." + str(x) + " ] Info =======")
    print("instance type : carla.Waypoint")
    print()
    print("waypoint_id : ", waypoint.id)
    print("road_id: ", waypoint.road_id)
    print("s_value: ", waypoint.s)
    print("section_id : ", waypoint.section_id)
    print("is_junction : ", waypoint.is_junction)
    print()
    print("lane_id: ", waypoint.lane_id)
    print("lane type: ", waypoint.lane_type)
    print("lane_width: ", waypoint.lane_width)
    print()
    print("right_lm_color : ", waypoint.right_lane_marking.color)
    print("right_lm_type : ", waypoint.right_lane_marking.type)
    print()
    print("left_lm_color : ", waypoint.left_lane_marking.color)
    print("left_lm_type : ", waypoint.left_lane_marking.type)
    print()
    print("rotation : " + str(rt.pitch) + " , " + str(rt.roll) + " , " + str(rt.yaw))
    print("location : " + str(lt.x) + " , " + str(lt.y) + " , " + str(lt.z))


def spawnPoints_viewer(world, map):
    debug = world.debug

    # spawn points
    for n, transform in enumerate(map.get_spawn_points()):
        lt = transform.location
        rt = transform.rotation
        # print(n)
        # print("spawn-list-rotation : " + str(rt.pitch) + " , " + str(rt.roll) + " , " + str(rt.yaw))
        # print("spawn-list-location : " + str(lt.x) + " , " + str(lt.y) + " , " + str(lt.z))
        draw_point(debug, transform.location, blue)
        draw_spawnpoint_info(debug, transform, n)

    x = input('\nLineNumber ?? : ')
    transform = map.get_spawn_points()[int(x)]
    draw_point(debug, transform.location, yellow)
    lt = transform.location
    rt = transform.rotation
    print("[ No." + str(x) + " ] Info =======")
    print("instance type : carla.Transform")
    print()
    print("rotation : " + str(rt.pitch) + " , " + str(rt.roll) + " , " + str(rt.yaw))
    print("location : " + str(lt.x) + " , " + str(lt.y) + " , " + str(lt.z))


# def main():
#     client = carla.Client('localhost', 2000)
#     client.set_timeout(10.0)
#     world = client.get_world()
#     map = world.get_map()
#
#     x = input('\ns=Spawnpoint , w=Waypoint : ')
#     if str(x) == 'w':
#         waypoints_viewer(world, map)
#     elif str(x) == 's':
#         spawnPoints_viewer(world, map)
#
#
# if __name__ == '__main__':
#     try:
#         main()
#     except KeyboardInterrupt:
#         print('\nCancelled by user. Bye!')
