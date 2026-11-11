import math

import numpy
from OpenGL.GL import *

from lib.c64_screen import C64Screen


class PlasmaPicture:

    def __init__(self, pixel_width, pixel_height):
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.speed = 0.8
        self.brightness = 0.9
        self.time = 0.0
        self.across, self.up = numpy.meshgrid(numpy.linspace(0.0, 1.0, pixel_width, dtype=numpy.float32),
                                              numpy.linspace(0.0, 1.0, pixel_height, dtype=numpy.float32))
        self.from_center = numpy.hypot(self.across - 0.5, self.up - 0.5)
        self.pixels = numpy.zeros((pixel_height, pixel_width, 3), dtype=numpy.uint8)
        self.texture_id = None

    def prepare(self):
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.pixel_width, self.pixel_height, 0, GL_RGB, GL_UNSIGNED_BYTE,
                     self._painted())

    def update(self, seconds):
        self.time += seconds
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.pixel_width, self.pixel_height, GL_RGB, GL_UNSIGNED_BYTE,
                        self._painted())

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


class C64WallScreen:

    def __init__(self, face, across, rise, width):
        self.face = face
        self.across = across
        self.rise = rise
        self.width = width
        self.height = 0.0
        self.wall_offset = 0.45
        self.glow_spread = (1.06, 1.08)
        self.glow_strength = 0.35
        self.plasma_glow_color = (0.6, 0.5, 0.9)
        self.plasma = PlasmaPicture(128, 88)
        self.c64 = None
        self.corners = None
        self.showing_c64 = False

    def prepare(self):
        self.c64 = C64Screen()
        self.height = self.width / self.c64.aspect
        self.corners = (self.face.point(self.across, self.rise, self.wall_offset),
                        self.face.point(self.across + self.width, self.rise, self.wall_offset),
                        self.face.point(self.across + self.width, self.rise + self.height, self.wall_offset),
                        self.face.point(self.across, self.rise + self.height, self.wall_offset))
        self.plasma.prepare()

    @property
    def covered_rectangle(self):
        return self.across, self.rise, self.width, self.height

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
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        if self.showing_c64:
            glBindTexture(GL_TEXTURE_2D, self.c64.texture_id)
            glow_color = self.c64.border_color
        else:
            glBindTexture(GL_TEXTURE_2D, self.plasma.texture_id)
            glow_color = self.plasma_glow_color
        glColor4f(1.0, 1.0, 1.0, 1.0)
        self._quad(self.corners)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glColor4f(*glow_color, self.glow_strength)
        self._quad(self._glow_corners())
        glPopAttrib()

    def _glow_corners(self):
        bottom_left, bottom_right, _, top_left = self.corners
        center = (self.corners[0] + self.corners[2]) * 0.5 + self.face.normal * 0.05
        half_across = (bottom_right - bottom_left) * (0.5 * self.glow_spread[0])
        half_up = (top_left - bottom_left) * (0.5 * self.glow_spread[1])
        return (center - half_across - half_up, center + half_across - half_up,
                center + half_across + half_up, center - half_across + half_up)

    @staticmethod
    def _quad(corners):
        glBegin(GL_QUADS)
        for corner, (u, v) in zip(corners, ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))):
            glTexCoord2f(u, v)
            glVertex3f(*corner)
        glEnd()
