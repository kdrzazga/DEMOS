import random

import pygame

from demos.petscii.files.globals import Constants


class Noise:
    """A full-screen mesh of random PETSCII characters recreating the C64 noise effect."""

    CHAR_SIZE = 16
    FOREGROUND = (200, 200, 200)
    BACKGROUND = (0, 0, 0)
    REVERSE_RATIO = 0.6

    def __init__(self, width, height, char_size=CHAR_SIZE):
        pygame.font.init()
        self.font = pygame.font.Font(Constants.FONT_PATH, char_size)
        self.cell_width, self.cell_height = self.font.size("W")
        self.columns = width // self.cell_width + 1
        self.rows = height // self.cell_height + 1
        self.normal_glyphs, self.reverse_glyphs = self._build_glyphs()

    def render(self, surface):
        surface.fill(Noise.BACKGROUND)
        for row in range(self.rows):
            y = row * self.cell_height
            for column in range(self.columns):
                glyph = self._pick_glyph()
                surface.blit(glyph, (column * self.cell_width, y))

    def _pick_glyph(self):
        if random.random() < Noise.REVERSE_RATIO:
            return random.choice(self.reverse_glyphs)
        return random.choice(self.normal_glyphs)

    def _build_glyphs(self):
        normal, reverse = [], []
        for char in Noise._charset():
            normal.append(self.font.render(char, False, Noise.FOREGROUND, Noise.BACKGROUND))
            reverse.append(self.font.render(char, False, Noise.BACKGROUND, Noise.FOREGROUND))
        return normal, reverse

    @staticmethod
    def _charset():
        ascii_chars = [chr(code) for code in range(0x21, 0x7F)]
        petscii_graphics = [chr(code) for code in range(0xE000, 0xE200)]
        return ascii_chars + petscii_graphics
