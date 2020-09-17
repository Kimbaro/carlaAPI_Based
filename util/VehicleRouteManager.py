import carla
import math
import util.Drawing_Point as drawing_point
from util.Sort import Stack
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent  # pylint: disable=import-error

import random


class VehicleRouteManager:
    def __init__(self, world, map, target, speed=20.0, start_POI=None, end_POI=None):
        self.world = world
        self.map = map
        self.debug = world.debug
        self._start_POI = start_POI  # 시작지점
        self._end_POI = end_POI  # 끝지점
        # self.waypoints = map.generate_waypoints(5.0)
        self.spawn_points = self.map.get_spawn_points()
        self.speed = speed
        self.destination_loc = None  # 타겟의 현재 경유지점
        self.log_check = False  # 타겟차량의 속도와 이동경로 신호등
        self.move_key = None

        # self.agent = BasicAgent(target)  # 대상차량 , speed km/s
        """
        var name 'behavior'
        cautious : 약한주행운전
        normal : 기본
        aggressive : 강한주행운전
        
        var name 'ignore_traffic_light'
        True : 신호무시
        False : 
        """
        self.agent = BehaviorAgent(target, ignore_traffic_light=False, behavior='normal')  # 타겟차량, 신호따름, 보통주행
        self.control = None  # carla.VehicleControl, 차량의 세부 제어.
        self.routeDestinationList = Stack()  # 경유지 목록
        self.routePlannerList = []

        # 다음 경유지 탐색 시작은 루트플래너 큐리스트에 저장된 웨이포인트가 해당 값 미만 인 경우 시작함.
        self.num_min_waypoints = 5
        self.test_count = 0  # 테스트용. 이후 지울것.

        target_location = target.get_location()
        target_route_trace_wp = self.map.get_waypoint(target_location)
        start = target_route_trace_wp.next(20)
        end = target_route_trace_wp.next(90)
        self.agent.set_destination(start[0].transform.location, end[0].transform.location, clean=True)
        self.routePlannerList = self.agent._trace_route(start[0], end[0])  # 시작점과 끝나는 지점의 Waypoint list 를 반환.

    def add_route(self, waypoint):  # 경유할 목적지 등록.
        self.routeDestinationList.push(waypoint)

    def tick(self, target):
        self.agent.update_information()
        remaining_count = len(self.agent.get_local_planner().waypoints_queue)  # 타겟차량 루트플랜의 웨이포인트 큐 길이
        if remaining_count < self.num_min_waypoints:
            if remaining_count < 4:
                if self.routeDestinationList.is_empty():  # <- 스택이 비어있음.
                    self.test_count += 1
                    print("system : 목적지없음. 임의 목적지 루트플랜 작성. (", self.test_count)
                    route = self.agent.reroute()
                    self.routePlannerList = route  # 시작점과 끝나는 지점의 Waypoint list 를 반환
                    # print(route[0], route[1])
                else:  # 스택에 목적지가 존재함.
                    end = [self.routeDestinationList.pop(0)]
                    target_location = target.get_location()
                    target_route_trace_wp = self.map.get_waypoint(target_location)
                    start = target_route_trace_wp.next(20)
                    self.agent.set_destination(start[0].transform.location, end[0].transform.location)
                    self.routePlannerList = self.agent._trace_route(start[0], end[0])

        # self.routePlannerList = self.agent._trace_route(start, end)  # 시작점과 끝나는 지점의 Waypoint list 를 반환.
        self.agent.get_local_planner().set_speed(self.speed)  # 제어차량 평균 속도
        control = self.agent.run_step()  # 위 로직 설정 적용 및 동작시작.
        self.agent.vehicle.apply_control(control)  # return -> carla.VehicleControl

    def request_target_speed_log(self, check=False):
        self.agent.log_check = check

# ### 차량이 현재 이동하는 목적지를 시각적으로 표현 ----
# self.routePlannerList = self.agent._trace_route(
#     self.map.get_waypoint(target.get_location())
#     , self.map.get_waypoint(destination))  # 시작점과 끝나는 지점의 Waypoint list 를 반환.
# for routeData in self.routePlannerList:
#     debug_start = routeData[0]  # return -> carla.Waypoint
#     roadOption = routeData[1]  # return -> carla.RoadOption
#     # print(debug_start)
#     # print(roadOption, '\n')
#     drawing_point.draw_point(self.debug, debug_start.transform.location,
#                              color=carla.Color(255, 0, 0),
#                              lt=60.0)
