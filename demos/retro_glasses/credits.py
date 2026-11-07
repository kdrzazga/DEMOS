import os

import pygame
from OpenGL.GL import *

from demos.retro_glasses.stage_view import ScreenTexture
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


class ThanksGraffitiPlaceholder:
    def __init__(self, area):
        self.area = area
        self.visible = True
        self.frame_color = (1.0, 1.0, 1.0, 0.35)
        self.dash_pattern = 0x00FF
        label_font = pygame.font.SysFont("arial", 28, bold=True)
        self.label = ScreenTexture(label_font.render("THANKS FOR WATCHING  (graffiti placeholder)", True,
                                                     (255, 255, 255)))

    def draw(self, overlay):
        if not self.visible:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_LINE_BIT | GL_CURRENT_BIT)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(2, self.dash_pattern)
        glLineWidth(2.0)
        glColor4f(*self.frame_color)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.area.left, self.area.top)
        glVertex2f(self.area.right, self.area.top)
        glVertex2f(self.area.right, self.area.bottom)
        glVertex2f(self.area.left, self.area.bottom)
        glEnd()
        glPopAttrib()
        center_x, center_y = self.area.center
        overlay.draw_at(self.label, self.frame_color[3], center_x - self.label.width / 2,
                        center_y - self.label.height / 2)


class Credits:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.caption_text = "Demo brought to you by"
        self.caption_height_share = 0.05
        self.caption_center_share = 0.58
        self.logo_center_share = 0.77
        self.logo_width_share = 0.42
        self.logo_plate_padding = 18
        self.logo_plate_color = (0.0, 0.0, 0.0, 1.0)
        self.thanks_area = ScreenArea(screen_width, screen_height, 0.1, 0.06, 0.9, 0.48)
        self.thanks_placeholder = ThanksGraffitiPlaceholder(self.thanks_area)
        self.caption = TypedLabel(self.caption_text, screen_height * self.caption_height_share, frames_per_letter=1)
        self.caption.build()
        self.logo = ScreenTexture(self._scaled_logo())
        self.visible = False
        self.logo_alpha = 0.0

    def _scaled_logo(self):
        logo = pygame.image.load(LOGO_PATH)
        logo_width = round(self.screen_width * self.logo_width_share)
        logo_height = round(logo.get_height() * logo_width / logo.get_width())
        return pygame.transform.smoothscale(logo, (logo_width, logo_height))

    def type_letters(self, letter_count):
        letter_count = min(max(letter_count, 0), len(self.caption_text))
        if letter_count > 0 and letter_count != self.caption.frame:
            self.caption.frame = letter_count - 1
            self.caption.update()

    def draw(self, overlay):
        if not self.visible:
            return
        self.thanks_placeholder.draw(overlay)
        self._draw_logo(overlay)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        self.caption.draw((self.screen_width / 2, self.screen_height * self.caption_center_share, 0.0),
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
