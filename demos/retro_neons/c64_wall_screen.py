import math

import numpy

from lib.wall_screen import WallScreen
from lib.c64_screen import C64Screen
from lib.particles import Texture2D


class PlasmaPicture:

    def __init__(self, pixel_width, pixel_height):
        self.speed = 0.8
        self.brightness = 0.9
        self.time = 0.0
        self.across, self.up = numpy.meshgrid(numpy.linspace(0.0, 1.0, pixel_width, dtype=numpy.float32),
                                              numpy.linspace(0.0, 1.0, pixel_height, dtype=numpy.float32))
        self.from_center = numpy.hypot(self.across - 0.5, self.up - 0.5)
        self.pixels = numpy.full((pixel_height, pixel_width, 4), 255, dtype=numpy.uint8)
        self.texture = None

    def prepare(self):
        self.texture = Texture2D(self._painted())

    def update(self, seconds):
        self.time += seconds
        self.texture.update(self._painted())

    def _painted(self):
        moment = self.time * self.speed
        wave = (numpy.sin(self.across * 7.0 + moment)
                + numpy.sin(self.up * 5.0 - moment * 1.3)
                + numpy.sin((self.across + self.up) * 6.0 + moment * 0.7)
                + numpy.sin(self.from_center * 12.0 - moment * 1.7)) / 4.0
        for channel, shift in enumerate((0.0, 2.1, 4.2)):
            self.pixels[:, :, channel] = (255.0 * self.brightness
                                          * (0.5 + 0.5 * numpy.sin(math.pi * wave + shift))).astype(numpy.uint8)
        return self.pixels


class C64WallScreen(WallScreen):

    def __init__(self, face, across, rise, width):
        super().__init__(face, across, rise, width)
        self.plasma_glow_color = (0.6, 0.5, 0.9)
        self.plasma = PlasmaPicture(128, 88)
        self.c64 = None
        self.showing_c64 = False

    def prepare(self):
        self.c64 = C64Screen()
        self.place(self.width / self.c64.aspect)
        self.plasma.prepare()

    def switch_on(self):
        self.showing_c64 = True
        self.c64.restart_typing()

    def update(self, seconds):
        if self.showing_c64:
            self.c64.update(seconds)
            self.c64.refresh()
        else:
            self.plasma.update(seconds)

    def draw(self):
        if self.showing_c64:
            self.draw_picture(self.c64.texture_id, self.c64.border_color)
        else:
            self.draw_picture(self.plasma.texture.id, self.plasma_glow_color)
