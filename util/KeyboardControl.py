import carla
import util.Drawing_Point as drawing_point

import pygame
from pygame import constants as k


class KeyboardControl(object):
    # def __init__(self, world):
    # world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)
    def __init__(self, world, map, hud):
        self.index = -1
        self.isRecording = None
        self.check = False
        self.x = 0
        self.y = 0
        self.z = 0
        self.debug = world.debug
        self.map = map
        self.log_check = False
        self.hud = hud

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
