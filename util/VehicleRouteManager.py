import carla
import util.Drawing_Point as drawing_point
from util.Sort import Stack
from agents.navigation.basic_agent import BasicAgent


class VehicleRouteManager:
    def __init__(self, world, map, target, speed=20.0, start_POI=None, end_POI=None):
        self.map = map
        self.debug = world.debug
        self._start_POI = start_POI  # 시작지점
        self._end_POI = end_POI  # 끝지점
        self._vehicle = target  # 대상 차량
        self.agent = BasicAgent(target)  # 대상차량 , speed km/s
        self.routePlannerList = None  # 시작지점에서 끝점 까지의 경로
        self.control = None  # carla.VehicleControl, 차량의 세부 제어.
        self.routeDestinationList = Stack()  # 경유지 목록
        # self.routeDestinationList.push(end_POI)  # 스택방식의 정렬이므로 종점을 우선 푸쉬

        # if start_POI is not None:
        #     drawing_point.draw_spawnpoint_info(self.debug, start_POI.transform.location, color=carla.Color(0, 255, 0),
        #                                        text='START_POI',
        #                                        lt=180)
        # if end_POI is not None:
        #     drawing_point.draw_spawnpoint_info(self.debug, end_POI.transform.location, color=carla.Color(0, 255, 0),
        #                                        text='END_POI',
        #                                        lt=180)

        # self.agent.done() 내부의  localplanner는 최초 주행경로가 대입되어야 이후 주행 중이지 않을때 true를 반환함.
        # 초기에 set_destination을 대입하지 않았을 경우 최초 주행경로가 없기 때문에 false를 반환함.
        destination1 = target.get_location()
        self.agent.set_destination((destination1.x, destination1.y, destination1.z))

    def add_route(self, waypoint):  # 경유할 목적지 등록.
        self.routeDestinationList.push(waypoint)

    def tick(self):
        control = self.agent.run_step()
        if (self.agent.done()) == True:  ### 타겟차량이 더이상 루트플랜이 없는 경우.
            if self.routeDestinationList.is_empty():  # <- Stack
                None
                # 경유지 자동할당.
                # waypoint = random.choice(self.map.generate_waypoints(20.0))
                # self.routeDestinationList.push(waypoint)  # add route
                # print("route destination is empty")
            else:
                ### routeDestinationList 스택에 저장된 경로가 존재하는 경우
                # waypoint = self.routeDestinationList.pop()
                waypoint = self.routeDestinationList.pop(0)

                ### 차량이 현재 이동하는 목적지를 시각적으로 표현 ----
                self.routePlannerList = self.agent._trace_route(self.map.get_waypoint(self._vehicle.get_location()),
                                                                waypoint)  # 시작점과 끝나는 지점의 경로를 반환.
                for routeData in self.routePlannerList:
                    debug_start = routeData[0]  # return -> carla.Waypoint
                    roadOption = routeData[1]  # return -> carla.RoadOption
                    # print(debug_start)
                    # print(roadOption, '\n')
                    drawing_point.draw_point(self.debug, debug_start.transform.location, color=carla.Color(255, 0, 0),
                                             lt=60.0)

                # drawing_point.draw_point(self.debug, waypoint.transform.location, lt=60.0)  # 목적지 위치를 시각적으로 표현
                ###---- END
                self.agent.set_destination((waypoint.transform.location.x,
                                            waypoint.transform.location.y,
                                            waypoint.transform.location.z))

        # carla.VehicleControl
        self.agent._vehicle.apply_control(control)  # return -> carla.VehicleControl
