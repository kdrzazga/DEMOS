import numpy
import pygame

from lib.wall_screen import WallScreen
from lib.butterfly_credits import ButterflyCredits
from lib.particles import Texture2D


class ButterflyWallScreen(WallScreen):

    def __init__(self, face, across, rise, width, height):
        super().__init__(face, across, rise, width)
        self.place(height)
        self.glow_spread = (1.12, 1.25)
        self.glow_strength = 0.3
        self.glow_color = (1.0, 1.0, 1.0)
        self.backdrop_color = (0, 0, 0, 255)
        self.pixel_height = 360
        self.pixel_width = round(self.pixel_height * width / height)
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        self.credits = ButterflyCredits(0, 0, self.pixel_width, self.pixel_height)
        self.credits.butterflies.speed_factor = 2.0
        self.texture = None
        self.playing = False
        self.has_frame = False

    def prepare(self):
        self.texture = Texture2D(self._painted())

    def _painted(self):
        self.surface.fill(self.backdrop_color)
        self.credits.draw(self.surface)
        top_row_first = pygame.image.tobytes(self.surface, "RGBA", False)
        return numpy.frombuffer(top_row_first, dtype=numpy.uint8).reshape(self.pixel_height, self.pixel_width, 4)

    def update(self, seconds):
        if not self.playing:
            return
        self.credits.update(seconds)
        self.texture.update(self._painted())
        self.has_frame = True

    def draw(self):
        if self.has_frame:
            self.draw_picture(self.texture.id, self.glow_color)
