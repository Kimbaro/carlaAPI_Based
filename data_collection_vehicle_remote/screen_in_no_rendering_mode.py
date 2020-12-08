import glob
import os
import sys

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('data_collection_vehicle_remote/carla-0.9.9.4*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass

import carla

import data_collection_vehicle_remote.util.no_rendering_package.no_rendering_hud as hud_util
import data_collection_vehicle_remote.util.no_rendering_package.no_rendering_keyEvent as key_util
import data_collection_vehicle_remote.util.no_rendering_package.no_rendering_core as core_util
# from data_collection_vehicle_remote.util.blueprintAttribute import TargetActorAttr
from data_collection_vehicle_remote.util.VehicleRouteManager import VehicleRouteManager

import argparse
import random
import math
import time

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_i
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame import constants as k
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import data_collection_vehicle_remote.util.no_rendering_package.no_rendering_util as no_rendering_util


def main():
    """Parses the arguments received from commandline and runs the game loop"""
    # Define arguments that will be received and parsed
    argparser = argparse.ArgumentParser(
        description='CARLA No Rendering Mode Visualizer')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='localhost',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='920x600',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--map',
        metavar='TOWN',
        default=None,
        help='start a new episode at the given TOWN')
    argparser.add_argument(
        '--no-rendering',
        action='store_true',
        help='switch off server rendering')
    argparser.add_argument(
        '--show-triggers',
        action='store_true',
        help='show trigger boxes of traffic signs')
    argparser.add_argument(
        '--show-connections',
        action='store_true',
        help='show waypoint connections')
    argparser.add_argument(
        '--show-spawn-points',
        action='store_true',
        help='show recommended spawn points')

    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.res.split('x')]

    try:
        # Init Pygame
        pygame.init()

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        # Place a title to game window
        pygame.display.set_caption("pygame_set_caption")
        # Show loading screen
        font = pygame.font.SysFont('Arial', 20)
        # font = pygame.font.Font(pygame.font.get_default_font(), 20)
        text_surface = font.render('show_loading_text', True, no_rendering_util.COLOR_WHITE)
        display.blit(text_surface, text_surface.get_rect(center=(args.width / 2, args.height / 2)))

        pygame.display.flip()

        # Carla init
        client = carla.Client(args.host, 2000)
        client.set_timeout(10.0)
        world = client.get_world()
        map = world.get_map()

        # select spawn point
        spawnpoints = map.get_spawn_points()
        spawnpoint = random.choice(spawnpoints)
        blueprints = world.get_blueprint_library().filter('vehicle.*')

        # TARGET Vehicles Spawn
        # target_actor_attr = TargetActorAttr(world)
        blueprint = random.choice([x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4])
        # blueprint.set_attribute('role_name', target_actor_attr.remote_false)
        blueprint.set_attribute('role_name', "target")
        target = world.try_spawn_actor(blueprint, spawnpoint)
        # modules init
        input_control = key_util.InputControl("input control title", world, map)
        hud = hud_util.HUD_Main("hud title", args.width, args.height)
        rendering_world = core_util.World(client, target, "Simulator Info", args, timeout=2.0)

        ### 경로추적 생성.
        start_POI = map.get_waypoint(spawnpoint.location)
        routeManager = VehicleRouteManager(world, map, target, 20, start_POI)

        # modules start
        input_control.start(hud, rendering_world)
        print("system : check input_control")
        hud.start()
        print("system : check hud")
        rendering_world.start(hud, input_control)
        print("system : check rendering_world")

        # Game loop
        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(20)

            # Tick all modules
            routeManager.tick(target)
            rendering_world.tick(clock, routeManager)
            hud.tick(clock)
            input_control.tick(clock, routeManager)

            # Render all modules
            display.fill(no_rendering_util.COLOR_ALUMINIUM_4)
            rendering_world.render(display, routeManager)
            hud.render(display)
            input_control.render(display)
            pygame.display.flip()

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    finally:
        target.destroy()
        rendering_world.destroy()
        return


if __name__ == '__main__':
    main()
