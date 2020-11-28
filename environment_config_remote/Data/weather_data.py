class UI_DATA(object):
    def __init__(self):
        self.A_people = 0
        self.A_vehicle = 0
        self.B_sun_type = "midday"
        self.B_remote = False
        self.C_fog = 0
        self.C_rain = 0
        self.C_wind = 0
        self.C_cloud = 0
        self.C_remote = False
        self.D_speed = 0
        self.D_remote = False

    def set_NPC_Spawn(self, p, v):
        self.A_people = p
        self.A_vehicle = v

    def set_groupbox_Time_Function(self, sun_type, remote):
        self.B_sun_type = sun_type
        self.B_remote = remote

    def set_show_Slider_weather(self, f, r, w, c):
        self.C_fog = f
        self.C_rain = r
        self.C_wind = w
        self.C_cloud = c

    def set_show_checkBox_weather(self, remote):
        self.C_remote = remote

    def set_speed_control(self, speed):
        self.D_speed = speed

    def set_auto_control(self, remote):
        self.D_remote = remote
