import glob
import os
import sys

try:
    # 파이썬에서 참조할 모듈의 경로 및 설정
    sys.path.append(glob.glob('carla-0.9.9*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

except IndexError:
    pass

import carla

import argparse
import random

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
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import util.no_rendering_package.no_rendering_util as no_rendering_util


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
        default='127.0.0.1',
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
        default='1280x720',
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

    # Init Pygame
    pygame.init()
    display = pygame.display.set_mode(
        (args.width, args.height),
        pygame.HWSURFACE | pygame.DOUBLEBUF)

    # Place a title to game window
    pygame.display.set_caption("pygame_set_caption")

    # Show loading screen
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    text_surface = font.render('show_loading_text', True, no_rendering_util.COLOR_WHITE)
    display.blit(text_surface, text_surface.get_rect(center=(args.width / 2, args.height / 2)))
    pygame.display.flip()

    # Carla init
    client = carla.Client(args.host, 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    settings = world.get_settings()
    settings.no_rendering_mode = True
    world.apply_settings(settings)
    map = world.get_map()

    # modules set
    input_control = no_rendering_util.InputControl("input control title")
    print("test :: ", input_control.__doc__.split("\n"))
    hud = no_rendering_util.HUD("hud title", args.width, args.height)
    rendering_world = no_rendering_util.World(world, "rendering core module title", args, timeout=2.0)

    # modules start
    input_control.start(hud, rendering_world)
    hud.start()
    rendering_world.start(hud, input_control)

    # select spawn point
    spawnpoints = map.get_spawn_points()
    spawnpoint = random.choice(spawnpoints)
    blueprints = world.get_blueprint_library().filter('vehicle.*')

    # TARGET Vehicles Spawn
    blueprint = random.choice([x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4])
    target = world.try_spawn_actor(blueprint, spawnpoint)

    # Game loop
    clock = pygame.time.Clock()
    while True:
        clock.tick_busy_loop(60)

        # Tick all modules
        rendering_world.tick(clock)
        hud.tick(clock)
        input_control.tick(clock)

        # Render all modules
        display.fill(no_rendering_util.COLOR_ALUMINIUM_4)
        rendering_world.render(display)
        hud.render(display)
        input_control.render(display)
        pygame.display.flip()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
