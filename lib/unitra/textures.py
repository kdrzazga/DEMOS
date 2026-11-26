import os
import random

import numpy
import pygame
from OpenGL.GL import *


class ResourceFolder:

    def __init__(self):
        self.path = os.path.dirname(os.path.abspath(__file__))

    def file(self, name):
        return os.path.join(self.path, name)


class FontLibrary:

    def __init__(self):
        self.folder = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        self.loaded = {}

    def font(self, file_name, pixel_size):
        key = (file_name, pixel_size)
        if key not in self.loaded:
            pygame.font.init()
            path = os.path.join(self.folder, file_name)
            self.loaded[key] = pygame.font.Font(path if os.path.exists(path) else None, pixel_size)
        return self.loaded[key]


class SurfaceTexture:

    def __init__(self, surface, repeat):
        self.width, self.height = surface.get_size()
        self.texture_id = glGenTextures(1)
        wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     pygame.image.tobytes(surface, "RGBA", True))

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def destroy(self):
        glDeleteTextures([self.texture_id])


class WoodTexture(SurfaceTexture):

    def __init__(self, surface, units_per_strip_height):
        super().__init__(surface, True)
        self.world_height = units_per_strip_height * 2.0
        self.world_width = self.world_height * self.width / self.height


class WoodGrain:

    def __init__(self):
        self.path = ResourceFolder().file("wood.png")
        self.dark_edge_columns = 10
        self.brightness_gain = 1.4
        self.brightness_variation = 0.05
        self.strip_count = 8
        self.units_per_strip_height = 1.0
        self.seed = 5005

    def mirrored_strip(self):
        strip = pygame.surfarray.array3d(pygame.image.load(self.path)).astype(numpy.float32)
        strip = strip[self.dark_edge_columns:]
        return numpy.concatenate((strip, strip[:, ::-1]), axis=1)

    def sheet(self):
        strip = self.mirrored_strip()
        generator = random.Random(self.seed)
        columns = []
        for index in range(self.strip_count):
            column = strip[::-1] if index % 2 else strip
            column = numpy.roll(column, generator.randrange(column.shape[1]), axis=1)
            gain = self.brightness_gain * (1.0 + generator.uniform(-self.brightness_variation, self.brightness_variation))
            columns.append(column * gain)
        pixels = numpy.clip(numpy.concatenate(columns, axis=0), 0, 255).astype(numpy.uint8)
        return pygame.surfarray.make_surface(pixels)

    def texture(self):
        return WoodTexture(self.sheet(), self.units_per_strip_height)


class LogoDecal:

    def __init__(self):
        self.path = ResourceFolder().file("logo.png")
        self.ink_color = (224, 221, 212)
        self.paper_luminance = 150.0
        self.ink_luminance = 30.0

    def surface(self):
        image = pygame.image.load(self.path)
        luminance = pygame.surfarray.array3d(image).astype(numpy.float32).mean(axis=2)
        coverage = (self.paper_luminance - luminance) / (self.paper_luminance - self.ink_luminance)
        decal = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        decal.fill(self.ink_color + (0,))
        alpha = pygame.surfarray.pixels_alpha(decal)
        alpha[:] = (numpy.clip(coverage, 0.0, 1.0) * 255).astype(numpy.uint8)
        del alpha
        return decal


class ScreenPicture:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

    def upload(self, rgb_rows_top_first):
        pixels = numpy.ascontiguousarray(rgb_rows_top_first, dtype=numpy.uint8)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE, pixels)

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def destroy(self):
        glDeleteTextures([self.texture_id])
