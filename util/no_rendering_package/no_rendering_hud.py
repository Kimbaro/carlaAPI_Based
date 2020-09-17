import glob
import os
import sys

import datetime
import weakref
import math
import random
import hashlib
import util.no_rendering_package.color_palette as c

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')


# ==============================================================================
# -- Alert ----------------------------------------------------------------
# ==============================================================================


class ALERT_Text(object):
    """Renders texts that fades out after some seconds that the user specifies"""

    def __init__(self, font, dim, pos):
        """Initializes variables such as text font, dimensions and position"""
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=c.COLOR_WHITE, seconds=2.0):
        """Sets the text, color and seconds until fade out"""
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill(c.COLOR_ORANGE_0)
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
# -- Text ------------------------------------------------------------------
# ==============================================================================


class HUD_Text(object):
    def __init__(self, font, width, height):
        """Renders the help text that shows the controls for using no rendering mode"""
        lines = """Renders the help text that shows the controls for using no rendering mode""".__doc__.split("\n")

        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill(c.COLOR_BLACK)
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, c.COLOR_WHITE)
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


class HUD_Main(object):
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
        self._font_mono = pygame.font.Font(mono, 12)
        self._header_font = pygame.font.SysFont('Arial', 14, True)
        self.help = HUD_Text(pygame.font.Font(mono, 24), *self.dim)
        self._notifications = ALERT_Text(
            pygame.font.Font(pygame.font.get_default_font(), 20),
            (self.dim[0], 40), (0, self.dim[1] - 40))

    def _init_data_params(self):
        """Initializes the content data structures"""
        self.show_info = True
        self.show_actor_ids = False
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

        vehicle_id_surface.fill(c.COLOR_BLACK)
        if self.show_actor_ids:
            vehicle_id_surface.set_alpha(150)
            for actor in list_actors:
                x, y = world_to_pixel(actor[1].location)

                angle = 0
                if hero_actor is not None:
                    angle = -hero_transform.rotation.yaw - 90

                color = c.COLOR_SKY_BLUE_0
                if int(actor[0].attributes['number_of_wheels']) == 2:
                    color = c.COLOR_CHOCOLATE_0
                if actor[0].attributes['role_name'] == 'hero':
                    color = c.COLOR_CHAMELEON_0

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
                surface = self._header_font.render(title, True, c.COLOR_ALUMINIUM_0).convert_alpha()
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
                            pygame.draw.rect(display, c.COLOR_ALUMINIUM_0, rect, 0 if item[1] else 1)
                        else:
                            rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                            pygame.draw.rect(display, c.COLOR_ALUMINIUM_0, rect_border, 1)
                            f = (item[1] - item[2]) / (item[3] - item[2])
                            if item[2] < 0.0:
                                rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                            else:
                                rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                            pygame.draw.rect(display, c.COLOR_ALUMINIUM_0, rect)
                        item = item[0]
                    if item:  # At this point has to be a str.
                        surface = self._font_mono.render(item, True, c.COLOR_ALUMINIUM_0).convert_alpha()
                        display.blit(surface, (8, 18 * i + v_offset))
                    v_offset += 18
                v_offset += 24
        self._notifications.render(display)
        self.help.render(display)
