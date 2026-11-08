import os

import pygame

from demos.retro_glasses.stage_view import ScreenTexture

NERD_ALERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "nerd-alert.png")


class NerdAlert:
    def __init__(self, screen_height):
        self.height_share = 0.3
        self.margin_share = 0.03
        self.blink_count = 3
        self.shown_seconds = 0.4
        self.hidden_seconds = 0.15
        self.margin = screen_height * self.margin_share
        self.texture = ScreenTexture(self._scaled_picture(screen_height))
        self.visible = False

    def _scaled_picture(self, screen_height):
        picture = pygame.image.load(NERD_ALERT_PATH)
        height = round(screen_height * self.height_share)
        width = round(picture.get_width() * height / picture.get_height())
        return pygame.transform.smoothscale(picture, (width, height))

    @property
    def blink_period(self):
        return self.shown_seconds + self.hidden_seconds

    def blink_at(self, seconds_since_start):
        blinking = 0.0 <= seconds_since_start < self.blink_count * self.blink_period
        self.visible = blinking and seconds_since_start % self.blink_period < self.shown_seconds

    def draw(self, overlay):
        if self.visible:
            overlay.draw_at(self.texture, 1.0, self.margin, self.margin)
