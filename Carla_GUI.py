import glob
import os
import sys
import argparse
from Data.weather_data import UI_DATA
import Data.ui_input_module as ui
from PyQt5.QtWidgets import *
from PyQt5 import uic
import WeatherManager

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('carla-0.9.9.4*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass

import carla

# UI파일 연결
# 단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("Carla_UI.ui")[0]


class UI_Manager(object):
    def __init__(self, world, weather, vehicle):
        self.world = world
        self.weather = weather
        self.vehicle = vehicle
        self._weather_set = None
        self._sun_set = None
        # 날씨 정보 초기화
        self.ui_world_weather(sun_type="midnight", fog_intensity=10.0, rain_intensity=10.0,
                              wind_intensity=10.0, cloudiness=10.0, remote_w=False, remote_s=False)

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

    def ui_world_weather(self, sun_type="midnight", fog_intensity=0.0, rain_intensity=0.0, wind_intensity=0.0,
                         cloudiness=0.0, remote_w=False, remote_s=False):
        """
        UI 날씨 제어
        :param sun_type: RADIO BUTTON => midday, sunset, midnight, dynamic (정오, 초저녁, 자정, 동적) default = clear
        :param fog_intensity: slideBar 0 ~ 100
        :param rain_intensity: slideBar 0 ~ 100
        :param wind_intensity: slideBar 0 ~ 100
        :param cloudiness: slideBar 0 ~ 100
        :param remote_w: 날씨제어, True 동적
        :param remote_s: 태양제어, True 동적
        """

        timestamp = self.world.wait_for_tick(seconds=30.0).timestamp
        elapsed_time = timestamp.delta_seconds

        ##
        rain = rain_intensity
        wetness = rain_intensity * 5
        puddles = rain_intensity

        # UI 컴포넌트에 입력된 값을 저장한 객체생성
        self._weather_set = ui.UI_INPUT_CONTROL().return_weather(clouds=cloudiness, rain=rain, wetness=wetness,
                                                                 puddles=puddles, wind=wind_intensity,
                                                                 fog=fog_intensity, remote=remote_w)
        self._sun_set = ui.UI_INPUT_CONTROL().return_sun_type(sun_type=sun_type, remote=remote_s)
        self.weather.tick(elapsed_time, self._weather_set, self._sun_set)
        ##

        # print("초기값처리성공")

        # # 날씨 반복구간
        # timestamp = self.world.wait_for_tick(seconds=30.0).timestamp
        # elapsed_time = timestamp.delta_seconds
        # print("틱수신성공")
        # self._weather.tick(elapsed_time, self._weather_set, self._sun_set)
        # sys.stdout.write('\r' + str(self._weather) + 12 * ' ')
        # sys.stdout.flush()
        # # 날씨 반복구간

    def ui_world_npc_walker(self):
        None

    def ui_world_npc_vehicle(self):
        None


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class):
    def __init__(self, ui_data):
        super().__init__()
        self.ui_data = ui_data
        self.setupUi(self)
        # NPC 설정
        self.pushButton_NPC_Spawn.clicked.connect(self.NPC_Spawn)
        self.Edit_People.returnPressed.connect(self.NPC_Spawn)
        self.Edit_Vehicle.returnPressed.connect(self.NPC_Spawn)

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
        self.lineEdit.returnPressed.connect(self.speed_control)

        # Auto
        self.checkBox.clicked.connect(self.auto_control)

        # Carla Init
        argparser = argparse.ArgumentParser(description="설정값")
        argparser.add_argument('--host', metavar='H', default='localhost', help='호스트 서버의 아이피 주소 입력.')
        argparser.add_argument('--port', metavar='P', default=2000, type=int, help='호스트 서버의 TCP포트 입력.')
        argparser.add_argument(
            '-t', '--target_id',
            metavar='N',
            default=0,
            type=int,
            help='센서수집을 위한 대상 차량 actor_id')

        args = argparser.parse_args()
        print(args.target_id)

        client = carla.Client(args.host, 2000)
        client.set_timeout(10.0)
        self.world = client.get_world()
        self.target = self.world.get_actor(args.target_id)  # 타겟 차량 Actor_id
        print("select vehicle : ", self.target)
        self._weather = WeatherManager.Weather(self.world.get_weather(), self.world)
        self._sun_set = None
        self._weather_set = None

    # NPC 버튼 클릭 후 값 가져오기
    def NPC_Spawn(self):
        people = int(self.Edit_People.text())
        vehicle = int(self.Edit_Vehicle.text())
        self.ui_data.set_NPC_Spawn(people, vehicle)

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
        speed = int(self.lineEdit.text())
        self.ui_data.D_speed = speed

    # Auto
    def auto_control(self):
        if self.checkBox.isChecked():
            if self.ui_data.D_remote is True:
                self.ui_data.D_remote = False
            else:
                self.ui_data.D_remote = True


if __name__ == "__main__":
    ui_data = UI_DATA()
    app = QApplication(sys.argv)
    myWindow = WindowClass(ui_data)
    myWindow.show()
    app.exec_()
