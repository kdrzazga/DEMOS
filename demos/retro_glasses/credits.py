import math
import os

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from demos.retro_glasses.stage_view import ScreenTexture
from demos.retro_glasses.thanks_graffiti import ThanksForWatchingGraffiti
from lib.graffitti.swaying_surface import SwayingSurface
from lib.typing_effect.typed_label import TypedLabel

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "lib", "resources", "K&Alogo.png")


class ScreenArea:
    def __init__(self, screen_width, screen_height, left_share, top_share, right_share, bottom_share):
        self.left = screen_width * left_share
        self.top = screen_height * top_share
        self.right = screen_width * right_share
        self.bottom = screen_height * bottom_share

    @property
    def center(self):
        return (self.left + self.right) / 2, (self.top + self.bottom) / 2


class ThanksGraffitiBanner:
    def __init__(self, area, screen_width, screen_height):
        self.area = area
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.alpha = 0.0
        self.seconds = 0.0
        self.field_of_view = 30.0
        self.camera_distance = 6.0
        self.area_fill_share = 0.9
        self.graffiti = ThanksForWatchingGraffiti()
        self.surface = SwayingSurface(*self._surface_size())
        self.surface.yaw_amplitude_degrees = 8.0
        self.surface.pitch_amplitude_degrees = 4.0

    @property
    def area_width(self):
        return self.area.right - self.area.left

    @property
    def area_height(self):
        return self.area.bottom - self.area.top

    @property
    def duration_seconds(self):
        return self.graffiti.duration_seconds

    def _surface_size(self):
        visible_height = 2.0 * self.camera_distance * math.tan(math.radians(self.field_of_view / 2.0))
        area_aspect_ratio = self.area_width / self.area_height
        surface_width = min(visible_height * self.area_fill_share * self.graffiti.aspect_ratio,
                            visible_height * self.area_fill_share * area_aspect_ratio)
        return surface_width, surface_width / self.graffiti.aspect_ratio

    def update(self, seconds):
        self.seconds = seconds

    def draw(self):
        if self.alpha <= 0.0:
            return
        self.graffiti.render(self.seconds)
        self.surface.update(self.seconds)
        self.surface.colors[:, :3] *= self.alpha
        self.surface.colors[:, 3] = self.alpha
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glViewport(0, round(self.screen_height - self.area.bottom), self.screen_width, round(self.area_height))
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.area_height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        self.surface.render(self.graffiti.texture)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()


class Credits:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.caption_lines = ["Demo RETRO GLASSES", "brought to you by"]
        self.caption_height_share = 0.05
        self.caption_center_shares = [0.54, 0.60]
        self.logo_center_share = 0.77
        self.logo_width_share = 0.42
        self.logo_plate_padding = 18
        self.logo_plate_color = (0.0, 0.0, 0.0, 1.0)
        self.thanks_area = ScreenArea(screen_width, screen_height, 0.1, 0.06, 0.9, 0.48)
        self.thanks_banner = ThanksGraffitiBanner(self.thanks_area, screen_width, screen_height)
        self.captions = [TypedLabel(line, screen_height * self.caption_height_share, frames_per_letter=1, font_px=36)
                         for line in self.caption_lines]
        for caption in self.captions:
            caption.build()
        self.logo = ScreenTexture(self._scaled_logo())
        self.visible = False
        self.logo_alpha = 0.0

    def _scaled_logo(self):
        logo = pygame.image.load(LOGO_PATH)
        logo_width = round(self.screen_width * self.logo_width_share)
        logo_height = round(logo.get_height() * logo_width / logo.get_width())
        return pygame.transform.smoothscale(logo, (logo_width, logo_height))

    @property
    def caption_letter_count(self):
        return sum(len(line) for line in self.caption_lines)

    def type_letters(self, letter_count):
        remaining_letters = max(letter_count, 0)
        for line, caption in zip(self.caption_lines, self.captions):
            line_letters = min(remaining_letters, len(line))
            remaining_letters -= line_letters
            if line_letters > 0 and line_letters != caption.frame:
                caption.frame = line_letters - 1
                caption.update()

    def draw(self, overlay):
        if not self.visible:
            return
        self.thanks_banner.draw()
        self._draw_logo(overlay)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        for caption, center_share in zip(self.captions, self.caption_center_shares):
            if caption.frame > 0:
                caption.draw((self.screen_width / 2, self.screen_height * center_share, 0.0),
                             (1.0, 0.0, 0.0), (0.0, -1.0, 0.0))
        glPopAttrib()

    def _draw_logo(self, overlay):
        if self.logo_alpha <= 0.0:
            return
        left = (self.screen_width - self.logo.width) / 2
        top = self.screen_height * self.logo_center_share - self.logo.height / 2
        padding = self.logo_plate_padding
        plate_color = self.logo_plate_color
        glColor4f(*plate_color[:3], plate_color[3] * self.logo_alpha)
        glBegin(GL_QUADS)
        glVertex2f(left - padding, top - padding)
        glVertex2f(left + self.logo.width + padding, top - padding)
        glVertex2f(left + self.logo.width + padding, top + self.logo.height + padding)
        glVertex2f(left - padding, top + self.logo.height + padding)
        glEnd()
        overlay.draw_at(self.logo, self.logo_alpha, left, top)
