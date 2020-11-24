import glob
import os
import sys
from threading import Thread

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('carla-0.9.9*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass
import carla
import pygame
from pygame import constants as k
import argparse
from util.Sensors import SensorManager

vehicles_list = []


class KeyboardControl(object):
    # def __init__(self, world):
    # world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)
    def __init__(self):
        self.index = -1
        self.isRecording = None
        self.check = False

    def parse_events(self, sensorManager):
        if self.check:
            self.check = False

        for event in pygame.event.get():
            # print("키 입력 이벤트 테스트 :: ", event.type)
            # 해당라인 부터 구현....
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                if event.key == k.K_F12:
                    print("Recoding : 데이터 저장 ")
                    sensorManager.recording(True)
                if event.key == k.K_TAB:
                    print("생성된 차량 목록 : ", vehicles_list)
                if event.key == k.K_F1:
                    self.check = True
                    if self.check:
                        sensorManager.destroy()
                        print("F1 RGB")
                    self.index = 0
                elif event.key == k.K_F2:
                    self.check = True
                    if self.check:
                        sensorManager.destroy()
                        print("F2 DEPTH(Raw)")
                    self.index = 1
                elif event.key == k.K_F3:
                    self.check = True
                    if self.check:
                        sensorManager.destroy()
                    print("F3 Lidar")
                    self.index = 2
                elif event.key == k.K_F4:
                    self.check = True
                    if self.check:
                        sensorManager.destroy()
                    print("F4 Lidar(Semantic)")
                    self.index = 3

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == k.K_ESCAPE)

# 203.237.143.101
def main():
    argparser = argparse.ArgumentParser(description="설정값")
    argparser.add_argument('--host', metavar='H', default='203.237.143.101', help='호스트 서버의 아이피 주소 입력.')
    argparser.add_argument('--port', metavar='P', default=2000, type=int, help='호스트 서버의 TCP포트 입력.')
    argparser.add_argument('--camera', metavar='WIDTHxHEIGHT', default='1280x720', help='카메라 센서 이미지')
    argparser.add_argument(
        '-t', '--target_id',
        metavar='N',
        default=0,
        type=int,
        help='센서수집을 위한 대상 차량 actor_id')

    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.camera.split('x')]
    print(args.target_id)

    """
        Pygame Init
    """
    pygame.init()
    pygame.font.init()

    display = pygame.display.set_mode(
        (args.width, args.height),
        pygame.HWSURFACE | pygame.DOUBLEBUF)

    controller = KeyboardControl()
    """
        Pygame Init - END
    """
    # Carla init
    client = carla.Client(args.host, 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    target = world.get_actor(args.target_id)  # 타겟 차량 Actor_id
    print("select vehicle : ", target)
    # Sensors Spawn
    sensorManager = SensorManager(world, target, args)

    try:
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            if controller.parse_events(sensorManager):
                return
            world.tick()
            sensorManager.select_sensor(controller.index, controller.check).render(display)
            pygame.display.flip()
    finally:
        print('\ndestroying %d vehicles' % len(vehicles_list))
        sensorManager.destroy()
        # for actor in vehicles_list:
        #     actor.destroy()
        pygame.quit()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
