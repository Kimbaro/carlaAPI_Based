import carla
import math
import sys
import data_collection_vehicle_remote.util.Drawing_Point as drawing_point
from data_collection_vehicle_remote.util.Sort import Stack
from data_collection_vehicle_remote.agents.navigation.basic_agent import BasicAgent
from data_collection_vehicle_remote.agents.navigation.behavior_agent import \
    BehaviorAgent  # pylint: disable=import-error

import random

import sys


class VehicleRouteManager(BehaviorAgent):
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

        # self._weather = WeatherManager.Weather(world.get_weather())
        # self._weather_set = None
        # self._sun_set = None

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
        self.agent = BehaviorAgent(target, ignore_traffic_light=False, behavior='cautious')  # 타겟차량, 신호따름, 보통주행
        self.control = None  # carla.VehicleControl, 차량의 세부 제어.
        self.routeDestinationList = Stack()  # 경유지 목록
        self.routePlannerList = []

        # 다음 경유지 탐색 시작은 루트플래너 큐리스트에 저장된 웨이포인트가 해당 값 미만 인 경우 시작함.
        self.num_min_waypoints = 2
        self.test_count = 0  # 테스트용. 이후 지울것.

        # 날씨 정보 초기화
        # self.ui_world_weather(sun_type="sunset", fog_intensity=10.0, rain_intensity=10.0,
        #                       wind_intensity=10.0, cloudiness=10.0, remote_w=False, remote_s=False)

        # UI 서브스레드 실행
        # Process(target=ui_main).start()

    def add_route(self, waypoint):  # 경유할 목적지 등록.
        self.routeDestinationList.push(waypoint)

    def tick(self, target):
        # self.agent.update_information()
        remaining_count = len(self.agent.get_local_planner().waypoints_queue)  # 타겟차량 루트플랜의 웨이포인트 큐 길이
        if remaining_count > self.num_min_waypoints:
            self.agent.update_information()
        else:
            if remaining_count <= 1:  # 루트플랜의 경로 포인트가 1 이하 일때
                if self.routeDestinationList.is_empty():  # <- 사용자 목적지 선택 경로 스택이 비어있음.
                    self.test_count += 1
                    print("system : 목적지없음. 임의 목적지 루트플랜 작성. (", self.test_count)
                    route = self.agent.reroute_auto()
                    self.routePlannerList = route  # 시작점과 끝나는 지점의 Waypoint list 를 반환
                else:  # 사용자가 선택한 임의 목적지로 경로 할당
                    end = [self.routeDestinationList.pop(0)]
                    route = self.agent.reroute_self(end)
                    self.routePlannerList = route
                self.agent.update_information()
            else:
                self.agent.update_information()

        control = self.agent.run_step()  # 위 로직 설정 적용 및 동작시작.
        self.agent.vehicle.apply_control(control)  # return -> carla.VehicleControl

    def request_target_speed_log(self, check=False):
        self.agent.log_check = check

    #################################################
    # UI 이벤트 함수 구현부
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
    #
    # def ui_world_weather(self, sun_type="midday", fog_intensity=0.0, rain_intensity=0.0, wind_intensity=0.0,
    #                      cloudiness=0.0, remote_w=False, remote_s=False):
    #     """
    #     UI 날씨 제어
    #     :param sun_type: RADIO BUTTON => midday, sunset, midnight, dynamic (정오, 초저녁, 자정, 동적) default = clear
    #     :param fog_intensity: slideBar 0 ~ 100
    #     :param rain_intensity: slideBar 0 ~ 100
    #     :param wind_intensity: slideBar 0 ~ 100
    #     :param cloudiness: slideBar 0 ~ 100
    #     :param remote_w: 날씨제어, True 동적
    #     :param remote_s: 태양제어, True 동적
    #     """
    #
    #     print(UI_DATA.C_wind)
    #     ##
    #     rain = rain_intensity
    #     wetness = rain_intensity * 5
    #     puddles = rain_intensity
    #
    #     # UI 컴포넌트에 입력된 값을 저장한 객체생성
    #     self._weather_set = ui.UI_INPUT_CONTROL().return_weather(clouds=cloudiness, rain=rain, wetness=wetness,
    #                                                              puddles=puddles, wind=wind_intensity,
    #                                                              fog=fog_intensity, remote=remote_w)
    #     self._sun_set = ui.UI_INPUT_CONTROL().return_sun_type(sun_type=sun_type, remote=remote_s)
    #     ##
    #
    #     # print("초기값처리성공")
    #
    #     # # 날씨 반복구간
    #     # timestamp = self.world.wait_for_tick(seconds=30.0).timestamp
    #     # elapsed_time = timestamp.delta_seconds
    #     # print("틱수신성공")
    #     # self._weather.tick(elapsed_time, self._weather_set, self._sun_set)
    #     # sys.stdout.write('\r' + str(self._weather) + 12 * ' ')
    #     # sys.stdout.flush()
    #     # # 날씨 반복구간
    #
    # def ui_world_npc_walker(self):
    #     None
    #
    # def ui_world_npc_vehicle(self):
    #     None
