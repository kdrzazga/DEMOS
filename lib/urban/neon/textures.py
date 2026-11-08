import math

import pygame
from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_REPEAT,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glBindTexture,
    glGenTextures,
    glTexParameteri,
)
from OpenGL.GLU import gluBuild2DMipmaps


class GlTexture:

    def __init__(self, surface, repeating):
        width, height = surface.get_size()
        pixels = pygame.image.tobytes(surface, "RGBA", True)
        wrap = GL_REPEAT if repeating else GL_CLAMP_TO_EDGE
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels)

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.texture_id)


class AtlasRegion:

    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

    def corners(self):
        return ((self.left, self.bottom), (self.right, self.bottom), (self.right, self.top), (self.left, self.top))


class TextureAtlas:

    def __init__(self, size):
        self.size = size
        self.surface = pygame.Surface((size, size), pygame.SRCALPHA)
        self.padding = 3
        self.cursor_x = 0
        self.cursor_y = 0
        self.shelf_height = 0
        self.texture = None

    def add(self, image):
        width, height = image.get_size()
        if self.cursor_x + width + self.padding > self.size:
            self.cursor_x = 0
            self.cursor_y += self.shelf_height + self.padding
            self.shelf_height = 0
        if self.cursor_y + height > self.size:
            raise ValueError("texture atlas is full")
        self.surface.blit(image, (self.cursor_x, self.cursor_y))
        inset = 0.5
        region = AtlasRegion((self.cursor_x + inset) / self.size,
                             1.0 - (self.cursor_y + height - inset) / self.size,
                             (self.cursor_x + width - inset) / self.size,
                             1.0 - (self.cursor_y + inset) / self.size)
        self.cursor_x += width + self.padding
        self.shelf_height = max(self.shelf_height, height)
        return region

    def upload(self):
        self.texture = GlTexture(self.surface, repeating=False)
        return self.texture


class SignArt:

    def __init__(self, region, glow_color, aspect):
        self.region = region
        self.glow_color = glow_color
        self.aspect = aspect


class SignPainter:

    def __init__(self, palette, randomness):
        self.palette = palette
        self.randomness = randomness

    def vertical_glyphs(self):
        return self._glyph_panel(64, 256, columns=1, rows=4)

    def horizontal_glyphs(self):
        return self._glyph_panel(256, 64, columns=5, rows=1)

    def tall_banner(self):
        return self._glyph_panel(128, 256, columns=2, rows=3)

    def _glyph_panel(self, width, height, columns, rows):
        background = self.palette.background(self.randomness)
        ink = self.palette.contrasting_tube(self.randomness, background)
        frame = self.palette.tube(self.randomness)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((*background, 255))
        pygame.draw.rect(surface, frame, surface.get_rect(), max(2, width // 40))
        margin = width // 10
        cell_width = (width - 2 * margin) / columns
        cell_height = (height - 2 * margin) / rows
        for column in range(columns):
            for row in range(rows):
                cell = pygame.Rect(margin + column * cell_width + cell_width * 0.12,
                                   margin + row * cell_height + cell_height * 0.12,
                                   cell_width * 0.76, cell_height * 0.76)
                self._glyph(surface, cell, ink)
        glow = ink if sum(background) / 3.0 > 150 else frame
        return surface, glow

    def _glyph(self, surface, cell, ink):
        thickness = max(2, int(min(cell.width, cell.height) / 8))
        strokes = self.randomness.randint(3, 6)
        for _ in range(strokes):
            kind = self.randomness.random()
            if kind < 0.35:
                y = self.randomness.uniform(cell.top, cell.bottom)
                left = self.randomness.uniform(cell.left, cell.centerx)
                right = self.randomness.uniform(cell.centerx, cell.right)
                pygame.draw.line(surface, ink, (left, y), (right, y), thickness)
            elif kind < 0.7:
                x = self.randomness.uniform(cell.left, cell.right)
                top = self.randomness.uniform(cell.top, cell.centery)
                bottom = self.randomness.uniform(cell.centery, cell.bottom)
                pygame.draw.line(surface, ink, (x, top), (x, bottom), thickness)
            elif kind < 0.88:
                start = (self.randomness.uniform(cell.left, cell.right), self.randomness.uniform(cell.top, cell.centery))
                end = (self.randomness.uniform(cell.left, cell.right), self.randomness.uniform(cell.centery, cell.bottom))
                pygame.draw.line(surface, ink, start, end, thickness)
            else:
                box = pygame.Rect(0, 0, cell.width * 0.4, cell.height * 0.3)
                box.center = (self.randomness.uniform(cell.left + box.width / 2, cell.right - box.width / 2),
                              self.randomness.uniform(cell.top + box.height / 2, cell.bottom - box.height / 2))
                pygame.draw.rect(surface, ink, box, thickness)

    def billboard(self):
        width, height = 256, 160
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        top_color = self.palette.tube(self.randomness)
        bottom_color = self.palette.background(self.randomness)
        for y in range(height):
            mix = y / (height - 1)
            color = tuple(int(top * (1.0 - mix) + bottom * mix) for top, bottom in zip(top_color, bottom_color))
            pygame.draw.line(surface, (*color, 255), (0, y), (width, y))
        for _ in range(self.randomness.randint(3, 7)):
            color = self.palette.tube(self.randomness)
            center = (self.randomness.randint(0, width), self.randomness.randint(0, height))
            radius = self.randomness.randint(12, 60)
            pygame.draw.circle(surface, color, center, radius, self.randomness.choice((0, 0, 6)))
        figure = pygame.Rect(0, 0, width // 5, height // 2)
        figure.center = (self.randomness.randint(width // 4, 3 * width // 4), height // 2)
        pygame.draw.ellipse(surface, self.palette.background(self.randomness), figure)
        strip = pygame.Rect(8, height - 34, width - 16, 26)
        pygame.draw.rect(surface, (15, 15, 15), strip)
        ink = self.palette.tube(self.randomness)
        for index in range(6):
            cell = pygame.Rect(strip.left + 6 + index * (strip.width - 12) / 6, strip.top + 3,
                               (strip.width - 12) / 6 - 6, strip.height - 6)
            self._glyph(surface, cell, ink)
        pygame.draw.rect(surface, (240, 240, 230), surface.get_rect(), 4)
        return surface, top_color

    def screen(self):
        width, height = 192, 128
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        base = self.palette.tube(self.randomness)
        surface.fill((*base, 255))
        block = 8
        for x in range(0, width, block):
            for y in range(0, height, block):
                shade = self.randomness.uniform(0.45, 1.15)
                color = tuple(min(255, int(channel * shade)) for channel in base)
                pygame.draw.rect(surface, color, (x, y, block, block))
        for _ in range(4):
            accent = self.palette.tube(self.randomness)
            pygame.draw.ellipse(surface, accent, (self.randomness.randint(0, width - 60),
                                                  self.randomness.randint(0, height - 50), 60, 50))
        return surface, base

    def storefront(self):
        width, height = 256, 48
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        glow = self.randomness.choice(self.palette.window_lights)
        surface.fill((*glow, 255))
        bay = width // self.randomness.randint(3, 6)
        for x in range(0, width, bay):
            pygame.draw.line(surface, (30, 25, 20), (x, 0), (x, height), 3)
        awning = self.palette.tube(self.randomness)
        pygame.draw.rect(surface, awning, (0, 0, width, 10))
        return surface, glow


class SpritePainter:

    def glow(self, size):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size / 2.0
        for y in range(size):
            for x in range(size):
                distance = math.hypot(x + 0.5 - center, y + 0.5 - center) / center
                strength = max(0.0, 1.0 - distance) ** 2
                surface.set_at((x, y), (255, 255, 255, int(255 * strength)))
        return surface

    def walker(self, variant):
        width, height = 64, 128
        sharp = pygame.Surface((width, height), pygame.SRCALPHA)
        white = (255, 255, 255, 255)
        shoulder_width = (30, 36, 26, 34)[variant % 4]
        pygame.draw.circle(sharp, white, (width // 2, 18), 11)
        pygame.draw.ellipse(sharp, white, (width // 2 - shoulder_width // 2, 28, shoulder_width, 54))
        pygame.draw.rect(sharp, white, (width // 2 - 11, 70, 9, 52))
        pygame.draw.rect(sharp, white, (width // 2 + 2, 70, 9, 52))
        if variant % 4 == 3:
            pygame.draw.ellipse(sharp, white, (width // 2 - 28, 0, 56, 26))
        return self._soften(sharp)

    def _soften(self, surface):
        width, height = surface.get_size()
        small = pygame.transform.smoothscale(surface, (width // 4, height // 4))
        return pygame.transform.smoothscale(small, (width, height))


class ClothPainter:

    def __init__(self, palette, randomness):
        self.palette = palette
        self.randomness = randomness

    def graffiti_shirt(self):
        size = 256
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        surface.fill((236, 234, 226, 255))
        ink = (20, 20, 22)
        for _ in range(26):
            points = [(self.randomness.randint(0, size), self.randomness.randint(0, size))]
            for _ in range(self.randomness.randint(3, 7)):
                last_x, last_y = points[-1]
                points.append((last_x + self.randomness.randint(-40, 40), last_y + self.randomness.randint(-30, 30)))
            pygame.draw.lines(surface, ink, False, points, self.randomness.choice((2, 3, 5)))
        for _ in range(4):
            stripe_y = self.randomness.randint(0, size)
            pygame.draw.line(surface, (180, 30, 40), (0, stripe_y), (size, stripe_y + 10), 3)
        return surface
