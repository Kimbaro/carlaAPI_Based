import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla-0.9.9*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import carla
from carla import TrafficLightState as tls

import argparse
import logging
import datetime
import weakref
import math
import random
import hashlib
import builtins

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

# ==============================================================================
# -- 2D Rendering Color Palette ----------------------------------------------
# ==============================================================================

COLOR_BUTTER_0 = pygame.Color(252, 233, 79)
COLOR_BUTTER_1 = pygame.Color(237, 212, 0)
COLOR_BUTTER_2 = pygame.Color(196, 160, 0)

COLOR_ORANGE_0 = pygame.Color(252, 175, 62)
COLOR_ORANGE_1 = pygame.Color(245, 121, 0)
COLOR_ORANGE_2 = pygame.Color(209, 92, 0)

COLOR_CHOCOLATE_0 = pygame.Color(233, 185, 110)
COLOR_CHOCOLATE_1 = pygame.Color(193, 125, 17)
COLOR_CHOCOLATE_2 = pygame.Color(143, 89, 2)

COLOR_CHAMELEON_0 = pygame.Color(138, 226, 52)
COLOR_CHAMELEON_1 = pygame.Color(115, 210, 22)
COLOR_CHAMELEON_2 = pygame.Color(78, 154, 6)

COLOR_SKY_BLUE_0 = pygame.Color(114, 159, 207)
COLOR_SKY_BLUE_1 = pygame.Color(52, 101, 164)
COLOR_SKY_BLUE_2 = pygame.Color(32, 74, 135)

COLOR_PLUM_0 = pygame.Color(173, 127, 168)
COLOR_PLUM_1 = pygame.Color(117, 80, 123)
COLOR_PLUM_2 = pygame.Color(92, 53, 102)

COLOR_SCARLET_RED_0 = pygame.Color(239, 41, 41)
COLOR_SCARLET_RED_1 = pygame.Color(204, 0, 0)
COLOR_SCARLET_RED_2 = pygame.Color(164, 0, 0)

COLOR_ALUMINIUM_0 = pygame.Color(238, 238, 236)
COLOR_ALUMINIUM_1 = pygame.Color(211, 215, 207)
COLOR_ALUMINIUM_2 = pygame.Color(186, 189, 182)
COLOR_ALUMINIUM_3 = pygame.Color(136, 138, 133)
COLOR_ALUMINIUM_4 = pygame.Color(85, 87, 83)
COLOR_ALUMINIUM_4_5 = pygame.Color(66, 62, 64)
COLOR_ALUMINIUM_5 = pygame.Color(46, 52, 54)

COLOR_WHITE = pygame.Color(255, 255, 255)
COLOR_BLACK = pygame.Color(0, 0, 0)

# Module Defines
TITLE_WORLD = 'WORLD'
TITLE_HUD = 'HUD'
TITLE_INPUT = 'INPUT'

PIXELS_PER_METER = 12

MAP_DEFAULT_SCALE = 0.1
HERO_DEFAULT_SCALE = 1.0

PIXELS_AHEAD_VEHICLE = 150


# ==============================================================================
# -- Util -----------------------------------------------------------
# ==============================================================================


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


class Util(object):

    @staticmethod
    def blits(destination_surface, source_surfaces, rect=None, blend_mode=0):
        """Function that renders the all the source surfaces in a destination source"""
        for surface in source_surfaces:
            destination_surface.blit(surface[0], surface[1], rect, blend_mode)

    @staticmethod
    def length(v):
        """Returns the length of a vector"""
        return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

    @staticmethod
    def get_bounding_box(actor):
        """Gets the bounding box corners of an actor in world space"""
        bb = actor.trigger_volume.extent
        corners = [carla.Location(x=-bb.x, y=-bb.y),
                   carla.Location(x=bb.x, y=-bb.y),
                   carla.Location(x=bb.x, y=bb.y),
                   carla.Location(x=-bb.x, y=bb.y),
                   carla.Location(x=-bb.x, y=-bb.y)]
        corners = [x + actor.trigger_volume.location for x in corners]
        t = actor.get_transform()
        t.transform(corners)
        return corners


# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================


class FadingText(object):
    """Renders texts that fades out after some seconds that the user specifies"""

    def __init__(self, font, dim, pos):
        """Initializes variables such as text font, dimensions and position"""
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=COLOR_WHITE, seconds=2.0):
        """Sets the text, color and seconds until fade out"""
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill(COLOR_BLACK)
        self.surface.blit(text_texture, (10, 11))

    def tick(self, clock):
        """Each frame, it shows the displayed text for some specified seconds, if any"""
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        """ Renders the text in its surface and its position"""
        display.blit(self.surface, self.pos)


# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    def __init__(self, font, width, height):
        """Renders the help text that shows the controls for using no rendering mode"""
        lines = """Renders the help text that shows the controls for using no rendering mode""".__doc__.split("\n")

        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill(COLOR_BLACK)
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, COLOR_WHITE)
            self.surface.blit(text_texture, (22, n * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        """Toggles display of help text"""
        self._render = not self._render

    def render(self, display):
        """Renders the help text, if enabled"""
        if self._render:
            display.blit(self.surface, self.pos)

    @staticmethod
    def doc_data():
        """Renders the help text that shows the controls for using no rendering mode"""


# ==============================================================================
# -- HUD -----------------------------------------------------------------
# ==============================================================================


class HUD(object):
    """Class encharged of rendering the HUD that displays information about the world and the hero vehicle"""

    def __init__(self, name, width, height):
        """Initializes default HUD params and content data parameters that will be displayed"""
        self.name = name
        self.dim = (width, height)
        self._init_hud_params()
        self._init_data_params()

    def start(self):
        """Does nothing since it does not need to use other modules"""

    def _init_hud_params(self):
        """Initialized visual parameters such as font text and size"""
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 14)
        self._header_font = pygame.font.SysFont('Arial', 14, True)
        self.help = HelpText(pygame.font.Font(mono, 24), *self.dim)
        self._notifications = FadingText(
            pygame.font.Font(pygame.font.get_default_font(), 20),
            (self.dim[0], 40), (0, self.dim[1] - 40))

    def _init_data_params(self):
        """Initializes the content data structures"""
        self.show_info = True
        self.show_actor_ids = True
        self._info_text = {}

    def notification(self, text, seconds=2.0):
        """Shows fading texts for some specified seconds"""
        self._notifications.set_text(text, seconds=seconds)

    def tick(self, clock):
        """Updated the fading texts each frame"""
        self._notifications.tick(clock)

    def add_info(self, title, info):
        """Adds a block of information in the left HUD panel of the visualizer"""
        self._info_text[title] = info

    def render_vehicles_ids(self, vehicle_id_surface, list_actors, world_to_pixel, hero_actor, hero_transform):
        """When flag enabled, it shows the IDs of the vehicles that are spawned in the world. Depending on the vehicle type,
        it will render it in different colors"""

        vehicle_id_surface.fill(COLOR_BLACK)
        if self.show_actor_ids:
            vehicle_id_surface.set_alpha(150)
            for actor in list_actors:
                x, y = world_to_pixel(actor[1].location)

                angle = 0
                if hero_actor is not None:
                    angle = -hero_transform.rotation.yaw - 90

                color = COLOR_SKY_BLUE_0
                if int(actor[0].attributes['number_of_wheels']) == 2:
                    color = COLOR_CHOCOLATE_0
                if actor[0].attributes['role_name'] == 'hero':
                    color = COLOR_CHAMELEON_0

                font_surface = self._header_font.render(str(actor[0].id), True, color)
                rotated_font_surface = pygame.transform.rotate(font_surface, angle)
                rect = rotated_font_surface.get_rect(center=(x, y))
                vehicle_id_surface.blit(rotated_font_surface, rect)

        return vehicle_id_surface

    def render(self, display):
        """If flag enabled, it renders all the information regarding the left panel of the visualizer"""
        if self.show_info:
            info_surface = pygame.Surface((240, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            i = 0
            for title, info in self._info_text.items():
                if not info:
                    continue
                surface = self._header_font.render(title, True, COLOR_ALUMINIUM_0).convert_alpha()
                display.blit(surface, (8 + bar_width / 2, 18 * i + v_offset))
                v_offset += 12
                i += 1
                for item in info:
                    if v_offset + 18 > self.dim[1]:
                        break
                    if isinstance(item, list):
                        if len(item) > 1:
                            points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                            pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                        item = None
                    elif isinstance(item, tuple):
                        if isinstance(item[1], bool):
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect, 0 if item[1] else 1)
                        else:
                            rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect_border, 1)
                            f = (item[1] - item[2]) / (item[3] - item[2])
                            if item[2] < 0.0:
                                rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                            else:
                                rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect)
                        item = item[0]
                    if item:  # At this point has to be a str.
                        surface = self._font_mono.render(item, True, COLOR_ALUMINIUM_0).convert_alpha()
                        display.blit(surface, (8, 18 * i + v_offset))
                    v_offset += 18
                v_offset += 24
        self._notifications.render(display)
        self.help.render(display)


# ==============================================================================
# -- TrafficLightSurfaces ------------------------------------------------------
# ==============================================================================


class TrafficLightSurfaces(object):
    """Holds the surfaces (scaled and rotated) for painting traffic lights"""

    def __init__(self):
        def make_surface(tl):
            """Draws a traffic light, which is composed of a dark background surface with 3 circles that indicate its color depending on the state"""
            w = 40
            surface = pygame.Surface((w, 3 * w), pygame.SRCALPHA)
            surface.fill(COLOR_ALUMINIUM_5 if tl != 'h' else COLOR_ORANGE_2)
            if tl != 'h':
                hw = int(w / 2)
                off = COLOR_ALUMINIUM_4
                red = COLOR_SCARLET_RED_0
                yellow = COLOR_BUTTER_0
                green = COLOR_CHAMELEON_0

                # Draws the corresponding color if is on, otherwise it will be gray if its off
                pygame.draw.circle(surface, red if tl == tls.Red else off, (hw, hw), int(0.4 * w))
                pygame.draw.circle(surface, yellow if tl == tls.Yellow else off, (hw, w + hw), int(0.4 * w))
                pygame.draw.circle(surface, green if tl == tls.Green else off, (hw, 2 * w + hw), int(0.4 * w))

            return pygame.transform.smoothscale(surface, (15, 45) if tl != 'h' else (19, 49))

        self._original_surfaces = {
            'h': make_surface('h'),
            tls.Red: make_surface(tls.Red),
            tls.Yellow: make_surface(tls.Yellow),
            tls.Green: make_surface(tls.Green),
            tls.Off: make_surface(tls.Off),
            tls.Unknown: make_surface(tls.Unknown)
        }
        self.surfaces = dict(self._original_surfaces)

    def rotozoom(self, angle, scale):
        """Rotates and scales the traffic light surface"""
        for key, surface in self._original_surfaces.items():
            self.surfaces[key] = pygame.transform.rotozoom(surface, angle, scale)


# ==============================================================================
# -- Input -----------------------------------------------------------
# ==============================================================================

class InputControl(object):
    """Class that handles input received such as keyboard and mouse."""

    def __init__(self, name):
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

    def start(self, hud, world):
        """Assigns other initialized modules that input module needs."""
        self._hud = hud
        self._world = world

        self._hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def render(self, display):
        """Does nothing. Input module does not need render anything."""

    def tick(self, clock):
        """Executed each frame. Calls method for parsing input."""
        self.parse_input(clock)

    def _parse_events(self):
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
                elif event.key == K_TAB:
                    # Toggle between hero and map mode
                    if self._world.hero_actor is None:
                        self._world.select_hero_actor()
                        self.wheel_offset = HERO_DEFAULT_SCALE
                        self.control = carla.VehicleControl()
                        self._hud.notification('Hero Mode')
                    else:
                        self.wheel_offset = MAP_DEFAULT_SCALE
                        self.mouse_offset = [0, 0]
                        self.mouse_pos = [0, 0]
                        self._world.scale_offset = [0, 0]
                        self._world.hero_actor = None
                        self._hud.notification('Map Mode')
                elif event.key == K_F1:
                    self._hud.show_info = not self._hud.show_info
                elif event.key == K_i:
                    self._hud.show_actor_ids = not self._hud.show_actor_ids
                elif isinstance(self.control, carla.VehicleControl):
                    if event.key == K_q:
                        self.control.gear = 1 if self.control.reverse else -1
                    elif event.key == K_m:
                        self.control.manual_gear_shift = not self.control.manual_gear_shift
                        self.control.gear = self._world.hero_actor.get_control().gear
                        self._hud.notification('%s Transmission' % (
                            'Manual' if self.control.manual_gear_shift else 'Automatic'))
                    elif self.control.manual_gear_shift and event.key == K_COMMA:
                        self.control.gear = max(-1, self.control.gear - 1)
                    elif self.control.manual_gear_shift and event.key == K_PERIOD:
                        self.control.gear = self.control.gear + 1
                    elif event.key == K_p:
                        # Toggle autopilot
                        if self._world.hero_actor is not None:
                            self._autopilot_enabled = not self._autopilot_enabled
                            self._world.hero_actor.set_autopilot(self._autopilot_enabled)
                            self._hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
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

    def parse_input(self, clock):
        """Parses the input, which is classified in keyboard events and mouse"""
        self._parse_events()
        self._parse_mouse()
        if not self._autopilot_enabled:
            if isinstance(self.control, carla.VehicleControl):
                self._parse_keys(clock.get_time())
                self.control.reverse = self.control.gear < 0
            if (self._world.hero_actor is not None):
                self._world.hero_actor.apply_control(self.control)

    def exit_game(self):
        """Shuts down program and PyGame"""
        pygame.quit()
        sys.exit()

    @staticmethod
    def _is_quit_shortcut(key):
        """Returns True if one of the specified keys are pressed"""
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)


# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================

class MapImage(object):
    """Class encharged of rendering a 2D image from top view of a carla world. Please note that a cache system is used, so if the OpenDrive content
    of a Carla town has not changed, it will read and use the stored image if it was rendered in a previous execution"""

    def __init__(self, carla_world, carla_map, pixels_per_meter, show_triggers, show_connections, show_spawn_points):
        """ Renders the map image generated based on the world, its map and additional flags that provide extra information about the road network"""
        self._pixels_per_meter = pixels_per_meter
        self.scale = 1.0
        self.show_triggers = show_triggers
        self.show_connections = show_connections
        self.show_spawn_points = show_spawn_points

        waypoints = carla_map.generate_waypoints(2)
        margin = 50
        max_x = max(waypoints, key=lambda x: x.transform.location.x).transform.location.x + margin
        max_y = max(waypoints, key=lambda x: x.transform.location.y).transform.location.y + margin
        min_x = min(waypoints, key=lambda x: x.transform.location.x).transform.location.x - margin
        min_y = min(waypoints, key=lambda x: x.transform.location.y).transform.location.y - margin

        self.width = max(max_x - min_x, max_y - min_y)
        self._world_offset = (min_x, min_y)

        # Maximum size of a Pygame surface
        width_in_pixels = (1 << 14) - 1

        # Adapt Pixels per meter to make world fit in surface
        surface_pixel_per_meter = int(width_in_pixels / self.width)
        if surface_pixel_per_meter > PIXELS_PER_METER:
            surface_pixel_per_meter = PIXELS_PER_METER

        self._pixels_per_meter = surface_pixel_per_meter
        width_in_pixels = int(self._pixels_per_meter * self.width)

        self.big_map_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()

        # Load OpenDrive content
        opendrive_content = carla_map.to_opendrive()

        # Get hash based on content
        hash_func = hashlib.sha1()
        hash_func.update(opendrive_content.encode("UTF-8"))
        opendrive_hash = str(hash_func.hexdigest())

        # Build path for saving or loading the cached rendered map
        filename = carla_map.name + "_" + opendrive_hash + ".tga"
        dirname = os.path.join("cache", "no_rendering_mode")
        full_path = str(os.path.join(dirname, filename))

        if os.path.isfile(full_path):
            # Load Image
            self.big_map_surface = pygame.image.load(full_path)
        else:
            # Render map
            self.draw_road_map(
                self.big_map_surface,
                carla_world,
                carla_map,
                self.world_to_pixel,
                self.world_to_pixel_width)

            # If folders path does not exist, create it
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            # Remove files if selected town had a previous version saved
            list_filenames = glob.glob(os.path.join(dirname, carla_map.name) + "*")
            for town_filename in list_filenames:
                os.remove(town_filename)

            # Save rendered map for next executions of same map
            pygame.image.save(self.big_map_surface, full_path)

        self.surface = self.big_map_surface

    def draw_road_map(self, map_surface, carla_world, carla_map, world_to_pixel, world_to_pixel_width):
        """Draws all the roads, including lane markings, arrows and traffic signs"""
        map_surface.fill(COLOR_ALUMINIUM_4)
        precision = 0.05

        def lane_marking_color_to_tango(lane_marking_color):
            """Maps the lane marking color enum specified in PythonAPI to a Tango Color"""
            tango_color = COLOR_BLACK

            if lane_marking_color == carla.LaneMarkingColor.White:
                tango_color = COLOR_ALUMINIUM_2

            elif lane_marking_color == carla.LaneMarkingColor.Blue:
                tango_color = COLOR_SKY_BLUE_0

            elif lane_marking_color == carla.LaneMarkingColor.Green:
                tango_color = COLOR_CHAMELEON_0

            elif lane_marking_color == carla.LaneMarkingColor.Red:
                tango_color = COLOR_SCARLET_RED_0

            elif lane_marking_color == carla.LaneMarkingColor.Yellow:
                tango_color = COLOR_ORANGE_0

            return tango_color

        def draw_solid_line(surface, color, closed, points, width):
            """Draws solid lines in a surface given a set of points, width and color"""
            if len(points) >= 2:
                pygame.draw.lines(surface, color, closed, points, width)

        def draw_broken_line(surface, color, closed, points, width):
            """Draws broken lines in a surface given a set of points, width and color"""
            # Select which lines are going to be rendered from the set of lines
            broken_lines = [x for n, x in enumerate(zip(*(iter(points),) * 20)) if n % 3 == 0]

            # Draw selected lines
            for line in broken_lines:
                pygame.draw.lines(surface, color, closed, line, width)

        def get_lane_markings(lane_marking_type, lane_marking_color, waypoints, sign):
            """For multiple lane marking types (SolidSolid, BrokenSolid, SolidBroken and BrokenBroken), it converts them
             as a combination of Broken and Solid lines"""
            margin = 0.25
            marking_1 = [world_to_pixel(lateral_shift(w.transform, sign * w.lane_width * 0.5)) for w in waypoints]
            if lane_marking_type == carla.LaneMarkingType.Broken or (lane_marking_type == carla.LaneMarkingType.Solid):
                return [(lane_marking_type, lane_marking_color, marking_1)]
            else:
                marking_2 = [world_to_pixel(lateral_shift(w.transform,
                                                          sign * (w.lane_width * 0.5 + margin * 2))) for w in waypoints]
                if lane_marking_type == carla.LaneMarkingType.SolidBroken:
                    return [(carla.LaneMarkingType.Broken, lane_marking_color, marking_1),
                            (carla.LaneMarkingType.Solid, lane_marking_color, marking_2)]
                elif lane_marking_type == carla.LaneMarkingType.BrokenSolid:
                    return [(carla.LaneMarkingType.Solid, lane_marking_color, marking_1),
                            (carla.LaneMarkingType.Broken, lane_marking_color, marking_2)]
                elif lane_marking_type == carla.LaneMarkingType.BrokenBroken:
                    return [(carla.LaneMarkingType.Broken, lane_marking_color, marking_1),
                            (carla.LaneMarkingType.Broken, lane_marking_color, marking_2)]
                elif lane_marking_type == carla.LaneMarkingType.SolidSolid:
                    return [(carla.LaneMarkingType.Solid, lane_marking_color, marking_1),
                            (carla.LaneMarkingType.Solid, lane_marking_color, marking_2)]

            return [(carla.LaneMarkingType.NONE, carla.LaneMarkingColor.Other, [])]

        def draw_lane(surface, lane, color):
            """Renders a single lane in a surface and with a specified color"""
            for side in lane:
                lane_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in side]
                lane_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in side]

                polygon = lane_left_side + [x for x in reversed(lane_right_side)]
                polygon = [world_to_pixel(x) for x in polygon]

                if len(polygon) > 2:
                    pygame.draw.polygon(surface, color, polygon, 5)
                    pygame.draw.polygon(surface, color, polygon)

        def draw_lane_marking(surface, waypoints):
            """Draws the left and right side of lane markings"""
            # Left Side
            draw_lane_marking_single_side(surface, waypoints[0], -1)

            # Right Side
            draw_lane_marking_single_side(surface, waypoints[1], 1)

        def draw_lane_marking_single_side(surface, waypoints, sign):
            """Draws the lane marking given a set of waypoints and decides whether drawing the right or left side of
            the waypoint based on the sign parameter"""
            lane_marking = None

            marking_type = carla.LaneMarkingType.NONE
            previous_marking_type = carla.LaneMarkingType.NONE

            marking_color = carla.LaneMarkingColor.Other
            previous_marking_color = carla.LaneMarkingColor.Other

            markings_list = []
            temp_waypoints = []
            current_lane_marking = carla.LaneMarkingType.NONE
            for sample in waypoints:
                lane_marking = sample.left_lane_marking if sign < 0 else sample.right_lane_marking

                if lane_marking is None:
                    continue

                marking_type = lane_marking.type
                marking_color = lane_marking.color

                if current_lane_marking != marking_type:
                    # Get the list of lane markings to draw
                    markings = get_lane_markings(
                        previous_marking_type,
                        lane_marking_color_to_tango(previous_marking_color),
                        temp_waypoints,
                        sign)
                    current_lane_marking = marking_type

                    # Append each lane marking in the list
                    for marking in markings:
                        markings_list.append(marking)

                    temp_waypoints = temp_waypoints[-1:]

                else:
                    temp_waypoints.append((sample))
                    previous_marking_type = marking_type
                    previous_marking_color = marking_color

            # Add last marking
            last_markings = get_lane_markings(
                previous_marking_type,
                lane_marking_color_to_tango(previous_marking_color),
                temp_waypoints,
                sign)
            for marking in last_markings:
                markings_list.append(marking)

            # Once the lane markings have been simplified to Solid or Broken lines, we draw them
            for markings in markings_list:
                if markings[0] == carla.LaneMarkingType.Solid:
                    draw_solid_line(surface, markings[1], False, markings[2], 2)
                elif markings[0] == carla.LaneMarkingType.Broken:
                    draw_broken_line(surface, markings[1], False, markings[2], 2)

        def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
            """ Draws an arrow with a specified color given a transform"""
            transform.rotation.yaw += 180
            forward = transform.get_forward_vector()
            transform.rotation.yaw += 90
            right_dir = transform.get_forward_vector()
            end = transform.location
            start = end - 2.0 * forward
            right = start + 0.8 * forward + 0.4 * right_dir
            left = start + 0.8 * forward - 0.4 * right_dir

            # Draw lines
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [left, start, right]], 4)

        def draw_traffic_signs(surface, font_surface, actor, color=COLOR_ALUMINIUM_2, trigger_color=COLOR_PLUM_0):
            """Draw stop traffic signs and its bounding box if enabled"""
            transform = actor.get_transform()
            waypoint = carla_map.get_waypoint(transform.location)

            angle = -waypoint.transform.rotation.yaw - 90.0
            font_surface = pygame.transform.rotate(font_surface, angle)
            pixel_pos = world_to_pixel(waypoint.transform.location)
            offset = font_surface.get_rect(center=(pixel_pos[0], pixel_pos[1]))
            surface.blit(font_surface, offset)

            # Draw line in front of stop
            forward_vector = carla.Location(waypoint.transform.get_forward_vector())
            left_vector = carla.Location(-forward_vector.y, forward_vector.x,
                                         forward_vector.z) * waypoint.lane_width / 2 * 0.7

            line = [(waypoint.transform.location + (forward_vector * 1.5) + (left_vector)),
                    (waypoint.transform.location + (forward_vector * 1.5) - (left_vector))]

            line_pixel = [world_to_pixel(p) for p in line]
            pygame.draw.lines(surface, color, True, line_pixel, 2)

            # Draw bounding box of the stop trigger
            if self.show_triggers:
                corners = Util.get_bounding_box(actor)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, trigger_color, True, corners, 2)

        # def draw_crosswalk(surface, transform=None, color=COLOR_ALUMINIUM_2):
        #     """Given two points A and B, draw white parallel lines from A to B"""
        #     a = carla.Location(0.0, 0.0, 0.0)
        #     b = carla.Location(10.0, 10.0, 0.0)

        #     ab = b - a
        #     length_ab = math.sqrt(ab.x**2 + ab.y**2)
        #     unit_ab = ab / length_ab
        #     unit_perp_ab = carla.Location(-unit_ab.y, unit_ab.x, 0.0)

        #     # Crosswalk lines params
        #     space_between_lines = 0.5
        #     line_width = 0.7
        #     line_height = 2

        #     current_length = 0
        #     while current_length < length_ab:

        #         center = a + unit_ab * current_length

        #         width_offset = unit_ab * line_width
        #         height_offset = unit_perp_ab * line_height
        #         list_point = [center - width_offset - height_offset,
        #                       center + width_offset - height_offset,
        #                       center + width_offset + height_offset,
        #                       center - width_offset + height_offset]

        #         list_point = [world_to_pixel(p) for p in list_point]
        #         pygame.draw.polygon(surface, color, list_point)
        #         current_length += (line_width + space_between_lines) * 2

        def lateral_shift(transform, shift):
            """Makes a lateral shift of the forward vector of a transform"""
            transform.rotation.yaw += 90
            return transform.location + shift * transform.get_forward_vector()

        def draw_topology(carla_topology, index):
            """ Draws traffic signs and the roads network with sidewalks, parking and shoulders by generating waypoints"""
            topology = [x[index] for x in carla_topology]
            topology = sorted(topology, key=lambda w: w.transform.location.z)
            set_waypoints = []
            for waypoint in topology:
                waypoints = [waypoint]

                # Generate waypoints of a road id. Stop when road id differs
                nxt = waypoint.next(precision)
                if len(nxt) > 0:
                    nxt = nxt[0]
                    while nxt.road_id == waypoint.road_id:
                        waypoints.append(nxt)
                        nxt = nxt.next(precision)
                        if len(nxt) > 0:
                            nxt = nxt[0]
                        else:
                            break
                set_waypoints.append(waypoints)

                # Draw Shoulders, Parkings and Sidewalks
                PARKING_COLOR = COLOR_ALUMINIUM_4_5
                SHOULDER_COLOR = COLOR_ALUMINIUM_5
                SIDEWALK_COLOR = COLOR_ALUMINIUM_3

                shoulder = [[], []]
                parking = [[], []]
                sidewalk = [[], []]

                for w in waypoints:
                    # Classify lane types until there are no waypoints by going left
                    l = w.get_left_lane()
                    while l and l.lane_type != carla.LaneType.Driving:

                        if l.lane_type == carla.LaneType.Shoulder:
                            shoulder[0].append(l)

                        if l.lane_type == carla.LaneType.Parking:
                            parking[0].append(l)

                        if l.lane_type == carla.LaneType.Sidewalk:
                            sidewalk[0].append(l)

                        l = l.get_left_lane()

                    # Classify lane types until there are no waypoints by going right
                    r = w.get_right_lane()
                    while r and r.lane_type != carla.LaneType.Driving:

                        if r.lane_type == carla.LaneType.Shoulder:
                            shoulder[1].append(r)

                        if r.lane_type == carla.LaneType.Parking:
                            parking[1].append(r)

                        if r.lane_type == carla.LaneType.Sidewalk:
                            sidewalk[1].append(r)

                        r = r.get_right_lane()

                # Draw classified lane types
                draw_lane(map_surface, shoulder, SHOULDER_COLOR)
                draw_lane(map_surface, parking, PARKING_COLOR)
                draw_lane(map_surface, sidewalk, SIDEWALK_COLOR)

            # Draw Roads
            for waypoints in set_waypoints:
                waypoint = waypoints[0]
                road_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in waypoints]
                road_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in waypoints]

                polygon = road_left_side + [x for x in reversed(road_right_side)]
                polygon = [world_to_pixel(x) for x in polygon]

                if len(polygon) > 2:
                    pygame.draw.polygon(map_surface, COLOR_ALUMINIUM_5, polygon, 5)
                    pygame.draw.polygon(map_surface, COLOR_ALUMINIUM_5, polygon)

                # Draw Lane Markings and Arrows
                if not waypoint.is_junction:
                    draw_lane_marking(map_surface, [waypoints, waypoints])
                    for n, wp in enumerate(waypoints):
                        if ((n + 1) % 400) == 0:
                            draw_arrow(map_surface, wp.transform)

        topology = carla_map.get_topology()
        draw_topology(topology, 0)

        if self.show_spawn_points:
            for sp in carla_map.get_spawn_points():
                draw_arrow(map_surface, sp, color=COLOR_CHOCOLATE_0)

        if self.show_connections:
            dist = 1.5

            def to_pixel(wp):
                return world_to_pixel(wp.transform.location)

            for wp in carla_map.generate_waypoints(dist):
                col = (0, 255, 255) if wp.is_junction else (0, 255, 0)
                for nxt in wp.next(dist):
                    pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(nxt), 2)
                if wp.lane_change & carla.LaneChange.Right:
                    r = wp.get_right_lane()
                    if r and r.lane_type == carla.LaneType.Driving:
                        pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(r), 2)
                if wp.lane_change & carla.LaneChange.Left:
                    l = wp.get_left_lane()
                    if l and l.lane_type == carla.LaneType.Driving:
                        pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(l), 2)

        actors = carla_world.get_actors()

        # Find and Draw Traffic Signs: Stops and Yields
        font_size = world_to_pixel_width(1)
        font = pygame.font.SysFont('Arial', font_size, True)

        stops = [actor for actor in actors if 'stop' in actor.type_id]
        yields = [actor for actor in actors if 'yield' in actor.type_id]

        stop_font_surface = font.render("STOP", False, COLOR_ALUMINIUM_2)
        stop_font_surface = pygame.transform.scale(
            stop_font_surface, (stop_font_surface.get_width(), stop_font_surface.get_height() * 2))

        yield_font_surface = font.render("YIELD", False, COLOR_ALUMINIUM_2)
        yield_font_surface = pygame.transform.scale(
            yield_font_surface, (yield_font_surface.get_width(), yield_font_surface.get_height() * 2))

        for ts_stop in stops:
            draw_traffic_signs(map_surface, stop_font_surface, ts_stop, trigger_color=COLOR_SCARLET_RED_1)

        for ts_yield in yields:
            draw_traffic_signs(map_surface, yield_font_surface, ts_yield, trigger_color=COLOR_ORANGE_1)

    def world_to_pixel(self, location, offset=(0, 0)):
        """Converts the world coordinates to pixel coordinates"""
        x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
        y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
        return [int(x - offset[0]), int(y - offset[1])]

    def world_to_pixel_width(self, width):
        """Converts the world units to pixel units"""
        return int(self.scale * self._pixels_per_meter * width)

    def scale_map(self, scale):
        """Scales the map surface"""
        if scale != self.scale:
            self.scale = scale
            width = int(self.big_map_surface.get_width() * self.scale)
            self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))


class World(object):
    """Class that contains all the information of a carla world that is running on the server side"""

    def __init__(self, world, name, args, timeout):
        self.client = None
        self.name = name
        self.args = args
        self.timeout = timeout
        self.server_fps = 0.0
        self.simulation_time = 0
        self.server_clock = pygame.time.Clock()

        # World data
        self.world = world  # carla.World
        self.town_map = world.get_map()
        self.actors_with_transforms = []

        self._hud = None
        self._input = None

        self.surface_size = [0, 0]
        self.prev_scaled_size = 0
        self.scaled_size = 0

        # Hero actor
        self.hero_actor = None
        self.spawned_hero = None
        self.hero_transform = None

        self.scale_offset = [0, 0]

        self.vehicle_id_surface = None
        self.result_surface = None

        self.traffic_light_surfaces = TrafficLightSurfaces()
        self.affected_traffic_light = None

        # Map info
        self.map_image = None
        self.border_round_surface = None
        self.original_surface_size = None
        self.hero_surface = None
        self.actors_surface = None

    # def _get_data_from_carla(self):
    #     """Retrieves the data from the server side"""
    #     try:
    #         self.client = carla.Client(self.args.host, self.args.port)
    #         self.client.set_timeout(self.timeout)
    #
    #         if self.args.map is None:
    #             world = self.client.get_world()
    #         else:
    #             world = self.client.load_world(self.args.map)
    #
    #         town_map = world.get_map()
    #         return (world, town_map)
    #
    #     except RuntimeError as ex:
    #         logging.error(ex)
    #         exit_game()

    def start(self, hud, input_control):
        """Build the map image, stores the needed modules and prepares rendering in Hero Mode"""
        # self.world, self.town_map = self._get_data_from_carla()

        # settings = self.world.get_settings()
        # settings.no_rendering_mode = self.args.no_rendering
        # self.world.apply_settings(settings)

        # Create Surfaces
        self.map_image = MapImage(
            carla_world=self.world,
            carla_map=self.town_map,
            pixels_per_meter=PIXELS_PER_METER,
            show_triggers=self.args.show_triggers,
            show_connections=self.args.show_connections,
            show_spawn_points=self.args.show_spawn_points)

        self._hud = hud
        self._input = input_control

        self.original_surface_size = min(self._hud.dim[0], self._hud.dim[1])
        self.surface_size = self.map_image.big_map_surface.get_width()

        self.scaled_size = int(self.surface_size)
        self.prev_scaled_size = int(self.surface_size)

        # Render Actors
        self.actors_surface = pygame.Surface((self.map_image.surface.get_width(), self.map_image.surface.get_height()))
        self.actors_surface.set_colorkey(COLOR_BLACK)

        self.vehicle_id_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
        self.vehicle_id_surface.set_colorkey(COLOR_BLACK)

        self.border_round_surface = pygame.Surface(self._hud.dim, pygame.SRCALPHA).convert()
        self.border_round_surface.set_colorkey(COLOR_WHITE)
        self.border_round_surface.fill(COLOR_BLACK)

        # Used for Hero Mode, draws the map contained in a circle with white border
        center_offset = (int(self._hud.dim[0] / 2), int(self._hud.dim[1] / 2))
        pygame.draw.circle(self.border_round_surface, COLOR_ALUMINIUM_1, center_offset, int(self._hud.dim[1] / 2))
        # pygame.draw.rect(self.border_round_surface, COLOR_ALUMINIUM_1, center_offset, int(self._hud.dim[1] / 2))
        pygame.draw.circle(self.border_round_surface, COLOR_WHITE, center_offset, int((self._hud.dim[1] - 8) / 2))
        # pygame.draw.rect(self.border_round_surface, COLOR_WHITE, center_offset, int((self._hud.dim[1] - 8) / 2))

        scaled_original_size = self.original_surface_size * (1.0 / 0.9)
        self.hero_surface = pygame.Surface((scaled_original_size, scaled_original_size)).convert()

        self.result_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
        self.result_surface.set_colorkey(COLOR_BLACK)

        # Start hero mode by default
        self.select_hero_actor()
        self.hero_actor.set_autopilot(False)
        self._input.wheel_offset = HERO_DEFAULT_SCALE
        self._input.control = carla.VehicleControl()

        # Register event for receiving server tick
        weak_self = weakref.ref(self)
        self.world.on_tick(lambda timestamp: World.on_world_tick(weak_self, timestamp))

    def select_hero_actor(self):
        """Selects only one hero actor if there are more than one. If there are not any, it will spawn one."""
        hero_vehicles = [actor for actor in self.world.get_actors()
                         if 'vehicle' in actor.type_id and actor.attributes['role_name'] == 'hero']
        if len(hero_vehicles) > 0:
            self.hero_actor = random.choice(hero_vehicles)
            self.hero_transform = self.hero_actor.get_transform()
        else:
            self._spawn_hero()

    def _spawn_hero(self):
        """Spawns the hero actor when the script runs"""
        # Get a random blueprint.
        blueprint = random.choice(self.world.get_blueprint_library().filter(self.args.filter))
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the player.
        while self.hero_actor is None:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.hero_actor = self.world.try_spawn_actor(blueprint, spawn_point)
        self.hero_transform = self.hero_actor.get_transform()

        # Save it in order to destroy it when closing program
        self.spawned_hero = self.hero_actor

    def tick(self, clock):
        """Retrieves the actors for Hero and Map modes and updates de HUD based on that"""
        actors = self.world.get_actors()

        # We store the transforms also so that we avoid having transforms of
        # previous tick and current tick when rendering them.
        self.actors_with_transforms = [(actor, actor.get_transform()) for actor in actors]
        if self.hero_actor is not None:
            self.hero_transform = self.hero_actor.get_transform()

        self.update_hud_info(clock)

    def update_hud_info(self, clock):
        """Updates the HUD info regarding simulation, hero mode and whether there is a traffic light affecting the hero actor"""

        hero_mode_text = []
        if self.hero_actor is not None:
            hero_speed = self.hero_actor.get_velocity()
            hero_speed_text = 3.6 * math.sqrt(hero_speed.x ** 2 + hero_speed.y ** 2 + hero_speed.z ** 2)

            affected_traffic_light_text = 'None'
            if self.affected_traffic_light is not None:
                state = self.affected_traffic_light.state
                if state == carla.TrafficLightState.Green:
                    affected_traffic_light_text = 'GREEN'
                elif state == carla.TrafficLightState.Yellow:
                    affected_traffic_light_text = 'YELLOW'
                else:
                    affected_traffic_light_text = 'RED'

            affected_speed_limit_text = self.hero_actor.get_speed_limit()
            if math.isnan(affected_speed_limit_text):
                affected_speed_limit_text = 0.0
            hero_mode_text = [
                'Hero Mode:                 ON',
                'Hero ID:              %7d' % self.hero_actor.id,
                'Hero Vehicle:  %14s' % get_actor_display_name(self.hero_actor, truncate=14),
                'Hero Speed:          %3d km/h' % hero_speed_text,
                'Hero Affected by:',
                '  Traffic Light: %12s' % affected_traffic_light_text,
                '  Speed Limit:       %3d km/h' % affected_speed_limit_text
            ]
        else:
            hero_mode_text = ['Hero Mode:                OFF']

        self.server_fps = self.server_clock.get_fps()
        self.server_fps = 'inf' if self.server_fps == float('inf') else round(self.server_fps)
        info_text = [
            'Server:  % 16s FPS' % self.server_fps,
            'Client:  % 16s FPS' % round(clock.get_fps()),
            'Simulation Time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            'Map Name:          %10s' % self.town_map.name,
        ]

        self._hud.add_info(self.name, info_text)
        self._hud.add_info('HERO', hero_mode_text)

    @staticmethod
    def on_world_tick(weak_self, timestamp):
        """Updates the server tick"""
        self = weak_self()
        if not self:
            return

        self.server_clock.tick()
        self.server_fps = self.server_clock.get_fps()
        self.simulation_time = timestamp.elapsed_seconds

    def _show_nearby_vehicles(self, vehicles):
        """Shows nearby vehicles of the hero actor"""
        info_text = []
        if self.hero_actor is not None and len(vehicles) > 1:
            location = self.hero_transform.location
            vehicle_list = [x[0] for x in vehicles if x[0].id != self.hero_actor.id]

            def distance(v):
                return location.distance(v.get_location())

            for n, vehicle in enumerate(sorted(vehicle_list, key=distance)):
                if n > 15:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                info_text.append('% 5d %s' % (vehicle.id, vehicle_type))
        self._hud.add_info('NEARBY VEHICLES', info_text)

    def _split_actors(self):
        """Splits the retrieved actors by type id"""
        vehicles = []
        traffic_lights = []
        speed_limits = []
        walkers = []

        for actor_with_transform in self.actors_with_transforms:
            actor = actor_with_transform[0]
            if 'vehicle' in actor.type_id:
                vehicles.append(actor_with_transform)
            elif 'traffic_light' in actor.type_id:
                traffic_lights.append(actor_with_transform)
            elif 'speed_limit' in actor.type_id:
                speed_limits.append(actor_with_transform)
            elif 'walker.pedestrian' in actor.type_id:
                walkers.append(actor_with_transform)

        return (vehicles, traffic_lights, speed_limits, walkers)

    def _render_traffic_lights(self, surface, list_tl, world_to_pixel):
        """Renders the traffic lights and shows its triggers and bounding boxes if flags are enabled"""
        self.affected_traffic_light = None

        for tl in list_tl:
            world_pos = tl.get_location()
            pos = world_to_pixel(world_pos)

            if self.args.show_triggers:
                corners = Util.get_bounding_box(tl)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, COLOR_BUTTER_1, True, corners, 2)

            if self.hero_actor is not None:
                corners = Util.get_bounding_box(tl)
                corners = [world_to_pixel(p) for p in corners]
                tl_t = tl.get_transform()

                transformed_tv = tl_t.transform(tl.trigger_volume.location)
                hero_location = self.hero_actor.get_location()
                d = hero_location.distance(transformed_tv)
                s = Util.length(tl.trigger_volume.extent) + Util.length(self.hero_actor.bounding_box.extent)
                if (d <= s):
                    # Highlight traffic light
                    self.affected_traffic_light = tl
                    srf = self.traffic_light_surfaces.surfaces['h']
                    surface.blit(srf, srf.get_rect(center=pos))

            srf = self.traffic_light_surfaces.surfaces[tl.state]
            surface.blit(srf, srf.get_rect(center=pos))

    def _render_speed_limits(self, surface, list_sl, world_to_pixel, world_to_pixel_width):
        """Renders the speed limits by drawing two concentric circles (outer is red and inner white) and a speed limit text"""

        font_size = world_to_pixel_width(2)
        radius = world_to_pixel_width(2)
        font = pygame.font.SysFont('Arial', font_size)

        for sl in list_sl:

            x, y = world_to_pixel(sl.get_location())

            # Render speed limit concentric circles
            white_circle_radius = int(radius * 0.75)

            pygame.draw.circle(surface, COLOR_SCARLET_RED_1, (x, y), radius)
            pygame.draw.circle(surface, COLOR_ALUMINIUM_0, (x, y), white_circle_radius)

            limit = sl.type_id.split('.')[2]
            font_surface = font.render(limit, True, COLOR_ALUMINIUM_5)

            if self.args.show_triggers:
                corners = Util.get_bounding_box(sl)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, COLOR_PLUM_2, True, corners, 2)

            # Blit
            if self.hero_actor is not None:
                # In hero mode, Rotate font surface with respect to hero vehicle front
                angle = -self.hero_transform.rotation.yaw - 90.0
                font_surface = pygame.transform.rotate(font_surface, angle)
                offset = font_surface.get_rect(center=(x, y))
                surface.blit(font_surface, offset)

            else:
                # In map mode, there is no need to rotate the text of the speed limit
                surface.blit(font_surface, (x - radius / 2, y - radius / 2))

    def _render_walkers(self, surface, list_w, world_to_pixel):
        """Renders the walkers' bounding boxes"""
        for w in list_w:
            color = COLOR_PLUM_0

            # Compute bounding box points
            bb = w[0].bounding_box.extent
            corners = [
                carla.Location(x=-bb.x, y=-bb.y),
                carla.Location(x=bb.x, y=-bb.y),
                carla.Location(x=bb.x, y=bb.y),
                carla.Location(x=-bb.x, y=bb.y)]

            w[1].transform(corners)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.polygon(surface, color, corners)

    def _render_vehicles(self, surface, list_v, world_to_pixel):
        """Renders the vehicles' bounding boxes"""
        for v in list_v:
            color = COLOR_SKY_BLUE_0
            if int(v[0].attributes['number_of_wheels']) == 2:
                color = COLOR_CHOCOLATE_1
            if v[0].attributes['role_name'] == 'hero':
                color = COLOR_CHAMELEON_0
            # Compute bounding box points
            bb = v[0].bounding_box.extent
            corners = [carla.Location(x=-bb.x, y=-bb.y),
                       carla.Location(x=bb.x - 0.8, y=-bb.y),
                       carla.Location(x=bb.x, y=0),
                       carla.Location(x=bb.x - 0.8, y=bb.y),
                       carla.Location(x=-bb.x, y=bb.y),
                       carla.Location(x=-bb.x, y=-bb.y)
                       ]
            v[1].transform(corners)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.lines(surface, color, False, corners, int(math.ceil(4.0 * self.map_image.scale)))

    def render_actors(self, surface, vehicles, traffic_lights, speed_limits, walkers):
        """Renders all the actors"""
        # Static actors
        self._render_traffic_lights(surface, [tl[0] for tl in traffic_lights], self.map_image.world_to_pixel)
        self._render_speed_limits(surface, [sl[0] for sl in speed_limits], self.map_image.world_to_pixel,
                                  self.map_image.world_to_pixel_width)

        # Dynamic actors
        self._render_vehicles(surface, vehicles, self.map_image.world_to_pixel)
        self._render_walkers(surface, walkers, self.map_image.world_to_pixel)

    def clip_surfaces(self, clipping_rect):
        """Used to improve perfomance. Clips the surfaces in order to render only the part of the surfaces that are going to be visible"""
        self.actors_surface.set_clip(clipping_rect)
        self.vehicle_id_surface.set_clip(clipping_rect)
        self.result_surface.set_clip(clipping_rect)

    def _compute_scale(self, scale_factor):
        """Based on the mouse wheel and mouse position, it will compute the scale and move the map so that it is zoomed in or out based on mouse position"""
        m = self._input.mouse_pos

        # Percentage of surface where mouse position is actually
        px = (m[0] - self.scale_offset[0]) / float(self.prev_scaled_size)
        py = (m[1] - self.scale_offset[1]) / float(self.prev_scaled_size)

        # Offset will be the previously accumulated offset added with the
        # difference of mouse positions in the old and new scales
        diff_between_scales = ((float(self.prev_scaled_size) * px) - (float(self.scaled_size) * px),
                               (float(self.prev_scaled_size) * py) - (float(self.scaled_size) * py))

        self.scale_offset = (self.scale_offset[0] + diff_between_scales[0],
                             self.scale_offset[1] + diff_between_scales[1])

        # Update previous scale
        self.prev_scaled_size = self.scaled_size

        # Scale performed
        self.map_image.scale_map(scale_factor)

    def render(self, display):
        """Renders the map and all the actors in hero and map mode"""
        if self.actors_with_transforms is None:
            return
        self.result_surface.fill(COLOR_BLACK)

        # Split the actors by vehicle type id
        vehicles, traffic_lights, speed_limits, walkers = self._split_actors()

        # Zoom in and out
        scale_factor = self._input.wheel_offset
        self.scaled_size = int(self.map_image.width * scale_factor)
        if self.scaled_size != self.prev_scaled_size:
            self._compute_scale(scale_factor)

        # Render Actors
        self.actors_surface.fill(COLOR_BLACK)
        self.render_actors(
            self.actors_surface,
            vehicles,
            traffic_lights,
            speed_limits,
            walkers)

        # Render Ids
        self._hud.render_vehicles_ids(self.vehicle_id_surface, vehicles,
                                      self.map_image.world_to_pixel, self.hero_actor, self.hero_transform)
        # Show nearby actors from hero mode
        self._show_nearby_vehicles(vehicles)

        # Blit surfaces
        surfaces = ((self.map_image.surface, (0, 0)),
                    (self.actors_surface, (0, 0)),
                    (self.vehicle_id_surface, (0, 0)),
                    )

        angle = 0.0 if self.hero_actor is None else self.hero_transform.rotation.yaw + 90.0
        self.traffic_light_surfaces.rotozoom(-angle, self.map_image.scale)

        center_offset = (0, 0)
        if self.hero_actor is not None:
            # Hero Mode
            hero_location_screen = self.map_image.world_to_pixel(self.hero_transform.location)
            hero_front = self.hero_transform.get_forward_vector()
            translation_offset = (
                hero_location_screen[0] - self.hero_surface.get_width() / 2 + hero_front.x * PIXELS_AHEAD_VEHICLE,
                (hero_location_screen[1] - self.hero_surface.get_height() / 2 + hero_front.y * PIXELS_AHEAD_VEHICLE))

            # Apply clipping rect
            clipping_rect = pygame.Rect(translation_offset[0],
                                        translation_offset[1],
                                        self.hero_surface.get_width(),
                                        self.hero_surface.get_height())
            self.clip_surfaces(clipping_rect)

            Util.blits(self.result_surface, surfaces)

            self.border_round_surface.set_clip(clipping_rect)

            self.hero_surface.fill(COLOR_ALUMINIUM_4)
            self.hero_surface.blit(self.result_surface, (-translation_offset[0],
                                                         -translation_offset[1]))

            rotated_result_surface = pygame.transform.rotozoom(self.hero_surface, angle, 0.9).convert()

            center = (display.get_width() / 2, display.get_height() / 2)
            rotation_pivot = rotated_result_surface.get_rect(center=center)
            display.blit(rotated_result_surface, rotation_pivot)

            display.blit(self.border_round_surface, (0, 0))
        else:
            # Map Mode
            # Translation offset
            translation_offset = (self._input.mouse_offset[0] * scale_factor + self.scale_offset[0],
                                  self._input.mouse_offset[1] * scale_factor + self.scale_offset[1])
            center_offset = (abs(display.get_width() - self.surface_size) / 2 * scale_factor, 0)

            # Apply clipping rect
            clipping_rect = pygame.Rect(-translation_offset[0] - center_offset[0], -translation_offset[1],
                                        self._hud.dim[0], self._hud.dim[1])
            self.clip_surfaces(clipping_rect)
            Util.blits(self.result_surface, surfaces)

            display.blit(self.result_surface, (translation_offset[0] + center_offset[0],
                                               translation_offset[1]))

    def destroy(self):
        """Destroy the hero actor when class instance is destroyed"""
        if self.spawned_hero is not None:
            self.spawned_hero.destroy()