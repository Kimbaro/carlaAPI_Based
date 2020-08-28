import glob
import os
import sys

import datetime
import weakref
import math
import random
import hashlib
import carla
import util.Drawing_Point as drawing_point
import util.no_rendering_package.module_config as config

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


# ==============================================================================
# -- Input -----------------------------------------------------------
# ==============================================================================

class InputControl(object):
    """Class that handles input received such as keyboard and mouse."""

    def __init__(self, name, carla_world, carla_map):
        """Initializes input member variables when instance is created."""
        self.name = name
        self.mouse_pos = (0, 0)
        self.mouse_offset = [0.0, 0.0]
        self.wheel_offset = 0.1
        self.wheel_amount = 0.025
        self._steer_cache = 0.0
        self.control = None
        self._autopilot_enabled = False

        # Modules that input will depend on
        self._hud = None
        self._world = None

        # KeyboardControl var
        self.x = 0
        self.y = 0
        self.z = 0
        self.debug = carla_world.debug
        self.map = map
        self.log_check = False

        self.carla_world = carla_world
        self.carla_map = carla_map

    def start(self, hud, world):
        """Assigns other initialized modules that input module needs."""
        self._hud = hud
        self._world = world
        self._hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def render(self, display):
        """Does nothing. Input module does not need render anything."""

    def tick(self, clock, routeManager):
        """Executed each frame. Calls method for parsing input."""
        self.parse_input(clock, routeManager)

    def _parse_events(self, routeManager):
        """Parses input events. These events are executed only once when pressing a key."""
        self.mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                InputControl.exit_game()
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    InputControl.exit_game()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    self._hud.help.toggle()
                elif event.key == k.K_F1:
                    # Toggle between hero and map mode
                    self.wheel_offset = config.HERO_DEFAULT_SCALE
                    self._world.select_hero_actor()
                    self._hud.notification('타겟차량')
                elif event.key == k.K_F2:
                    self.wheel_offset = config.MAP_DEFAULT_SCALE
                    self.mouse_offset = [0, 0]
                    self.mouse_pos = [0, 0]
                    self._world.scale_offset = [0, 0]
                    self._world.select_hero_actor(map_mode_check=True)
                    self._hud.notification('전체지도')
                elif event.key == k.K_TAB:
                    self._hud.show_info = not self._hud.show_info
                if event.key == k.K_TAB:
                    print("Destination List Check")
                    print(routeManager.routeDestinationList)
                elif event.key == k.K_F12:
                    if self.log_check:
                        print("로그기록취소")
                        self.log_check = False
                    else:
                        print("로그기록작성")
                        self.log_check = True
                    routeManager.request_target_speed_log(self.log_check)

                if event.key == k.K_LEFT:
                    # print("K_LEFT")
                    self.x -= 10
                    w = self.carla_map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                                    lane_type=carla.LaneType.Driving)
                    routeManager.move_key = w
                    # drawing_point.draw_point(self.debug, w.transform.location,
                    #                          color=carla.Color(0, 255, 0),
                    #                          lt=1)
                elif event.key == k.K_RIGHT:
                    # print("K_RIGHT")
                    self.x += 10
                    w = self.carla_map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                                    lane_type=carla.LaneType.Driving)
                    routeManager.move_key = w
                    # drawing_point.draw_point(self.debug, w.transform.location,
                    #                          color=carla.Color(0, 255, 0),
                    #                          lt=1)
                elif event.key == k.K_UP:
                    # print("K_UP")
                    self.y -= 10
                    w = self.carla_map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                                    lane_type=carla.LaneType.Driving)
                    routeManager.move_key = w
                    # drawing_point.draw_point(self.debug, w.transform.location,
                    #                          color=carla.Color(0, 255, 0),
                    #                          lt=1)
                elif event.key == k.K_DOWN:
                    # print("K_DOWN")
                    self.y += 10
                    w = self.carla_map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                                    lane_type=carla.LaneType.Driving)
                    routeManager.move_key = w
                    # d = drawing_point.draw_point(self.debug, w.transform.location,
                    #                              color=carla.Color(0, 255, 0),
                    #                              lt=1)
                elif event.key == k.K_SPACE:
                    # print("K_KP_SPACE")
                    w = self.carla_map.get_waypoint(carla.Location(self.x, self.y, self.z), project_to_road=True,
                                                    lane_type=carla.LaneType.Driving)
                    routeManager.add_route(w)
                    # print(len(routeManager.routeDestinationList))
                    # drawing_point.draw_point(self.debug, w.transform.location,
                    #                          color=drawing_point.green,
                    #                          lt=120)


            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse wheel for zooming in and out
                if event.button == 4:
                    self.wheel_offset += self.wheel_amount
                    if self.wheel_offset >= 1.0:
                        self.wheel_offset = 1.0
                elif event.button == 5:
                    self.wheel_offset -= self.wheel_amount
                    if self.wheel_offset <= 0.1:
                        self.wheel_offset = 0.1

    def _parse_keys(self, milliseconds):
        """Parses keyboard input when keys are pressed"""
        keys = pygame.key.get_pressed()
        self.control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self.control.steer = round(self._steer_cache, 1)
        self.control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self.control.hand_brake = keys[K_SPACE]

    def _parse_mouse(self):
        """Parses mouse input"""
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            self.mouse_offset[0] += (1.0 / self.wheel_offset) * (x - self.mouse_pos[0])
            self.mouse_offset[1] += (1.0 / self.wheel_offset) * (y - self.mouse_pos[1])
            self.mouse_pos = (x, y)

    def parse_input(self, clock, routeManager):
        """Parses the input, which is classified in keyboard events and mouse"""
        self._parse_events(routeManager)
        self._parse_mouse()

    def exit_game(self):
        """Shuts down program and PyGame"""
        pygame.quit()
        sys.exit()

    @staticmethod
    def _is_quit_shortcut(key):
        """Returns True if one of the specified keys are pressed"""
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)
