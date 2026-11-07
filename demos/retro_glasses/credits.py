import os

import pygame
from OpenGL.GL import *

from demos.retro_glasses.stage_view import ScreenTexture
from lib.typing_effect.typed_label import TypedLabel

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "lib", "resources", "K&Alogo.png")
THANKS_PICTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "exit.png")


class ScreenArea:
    def __init__(self, screen_width, screen_height, left_share, top_share, right_share, bottom_share):
        self.left = screen_width * left_share
        self.top = screen_height * top_share
        self.right = screen_width * right_share
        self.bottom = screen_height * bottom_share

    @property
    def center(self):
        return (self.left + self.right) / 2, (self.top + self.bottom) / 2


class ThanksPicture:
    def __init__(self, area):
        self.area = area
        self.alpha = 0.0
        self.texture = ScreenTexture(self._fitted_picture())

    def _fitted_picture(self):
        picture = pygame.image.load(THANKS_PICTURE_PATH)
        area_width = self.area.right - self.area.left
        area_height = self.area.bottom - self.area.top
        fit_scale = min(area_width / picture.get_width(), area_height / picture.get_height())
        fitted_size = (round(picture.get_width() * fit_scale), round(picture.get_height() * fit_scale))
        return pygame.transform.smoothscale(picture, fitted_size)

    def draw(self, overlay):
        if self.alpha <= 0.0:
            return
        center_x, center_y = self.area.center
        overlay.draw_at(self.texture, self.alpha, center_x - self.texture.width / 2,
                        center_y - self.texture.height / 2)


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
        self.thanks_picture = ThanksPicture(self.thanks_area)
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
        self.thanks_picture.draw(overlay)
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
