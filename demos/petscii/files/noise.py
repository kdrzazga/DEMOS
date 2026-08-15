import random
from array import array

import pygame

from demos.petscii.files.globals import Constants


class Noise:
    """A full-screen mesh of random PETSCII characters recreating the C64 noise effect."""

    CHAR_SIZE = 16
    FOREGROUND = (200, 200, 200)
    BACKGROUND = (0, 0, 0)
    REVERSE_RATIO = 0.6
    MIN_VOLUME = 0.05
    STATIC_SECONDS = 0.75
    STATIC_AMPLITUDE = 0.35

    def __init__(self, width, height, char_size=CHAR_SIZE):
        pygame.font.init()
        self.font = pygame.font.Font(Constants.FONT_PATH, char_size)
        self.cell_width, self.cell_height = self.font.size("W")
        self.columns = width // self.cell_width + 1
        self.rows = height // self.cell_height + 1
        self.normal_glyphs, self.reverse_glyphs = self._build_glyphs()
        self.static = self._build_static()
        self.channel = None

    def render(self, surface):
        surface.fill(Noise.BACKGROUND)
        for row in range(self.rows):
            y = row * self.cell_height
            for column in range(self.columns):
                glyph = self._pick_glyph()
                surface.blit(glyph, (column * self.cell_width, y))

    def start(self):
        if self.channel is None:
            self.channel = self.static.play(loops=-1)

    def set_intensity(self, amount):
        if self.channel is None:
            return
        amount = max(0.0, min(1.0, amount))
        self.channel.set_volume(Noise.MIN_VOLUME + (1.0 - Noise.MIN_VOLUME) * amount)

    def stop(self):
        if self.channel is not None:
            self.channel.stop()
            self.channel = None

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

    def _build_static(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        sample_rate, _, channels = pygame.mixer.get_init()
        sample_count = int(sample_rate * Noise.STATIC_SECONDS)
        amplitude = int(32767 * Noise.STATIC_AMPLITUDE)
        samples = array("h")
        for _ in range(sample_count):
            value = random.randint(-amplitude, amplitude)
            for _ in range(channels):
                samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    @staticmethod
    def _charset():
        ascii_chars = [chr(code) for code in range(0x21, 0x7F)]
        petscii_graphics = [chr(code) for code in range(0xE000, 0xE200)]
        return ascii_chars + petscii_graphics
