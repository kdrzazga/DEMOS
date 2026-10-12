import random

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *


class TextureFactory:
    def __init__(self, seed=3):
        self.generator = random.Random(seed)

    def upload(self, surface, repeat=True):
        width, height = surface.get_size()
        pixels = pygame.image.tobytes(surface, "RGBA", True)
        texture = glGenTextures(1)
        wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture

    def roof_tiles(self, size=64, rows=4, columns=4):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        tile_width = size // columns
        tile_height = size // rows
        for row in range(rows):
            top = row * tile_height
            shift = tile_width // 2 if row % 2 else 0
            for column in range(columns):
                shade = self.generator.randint(205, 245)
                for wrap in (0, -size):
                    left = column * tile_width + shift + wrap
                    for line in range(tile_height):
                        value = int(shade * (0.62 + 0.38 * line / tile_height))
                        pygame.draw.line(surface, (value, value, value, 255),
                                         (left, top + line), (left + tile_width - 1, top + line))
                    pygame.draw.line(surface, (110, 110, 110, 255), (left, top), (left, top + tile_height - 1))
            pygame.draw.line(surface, (80, 80, 80, 255), (0, top), (size - 1, top))
        return surface

    def paving(self, size=64, brick_width=16, brick_height=8):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        surface.fill((125, 125, 125, 255))
        for row in range(size // brick_height):
            top = row * brick_height
            shift = brick_width // 2 if row % 2 else 0
            for column in range(-1, size // brick_width + 1):
                value = self.generator.randint(175, 225)
                pygame.draw.rect(surface, (value, value, value, 255),
                                 (column * brick_width + shift + 1, top + 1, brick_width - 2, brick_height - 2))
        return surface

    def caption(self, text, ink, background, width=1024, height=112, spacing=18):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((*background, 255))
        font = pygame.font.SysFont("arial", int(height * 0.82), bold=True)
        glyphs = [font.render(letter, True, ink) for letter in text]
        total = sum(glyph.get_width() for glyph in glyphs) + spacing * (len(glyphs) - 1)
        scale = min(1.0, (width - 40) / total)
        left = (width - total * scale) / 2.0
        for glyph in glyphs:
            scaled = pygame.transform.smoothscale(
                glyph, (max(1, int(glyph.get_width() * scale)), max(1, int(glyph.get_height() * scale))))
            surface.blit(scaled, (int(left), (height - scaled.get_height()) // 2))
            left += (glyph.get_width() + spacing) * scale
        return surface
