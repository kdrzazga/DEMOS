import pygame

from demos.petscii.files.globals import Constants


class FontToMeshConverter:

    def __init__(self, pixel_size=8):
        pygame.font.init()
        self.pixel_size = pixel_size
        self._fonts = {}
        self._cache = {}

    def font(self, pixel_size):
        if pixel_size not in self._fonts:
            self._fonts[pixel_size] = pygame.font.Font(Constants.FONT_PATH, pixel_size)
        return self._fonts[pixel_size]

    def convert_letter(self, letter, pixel_size=None):
        pixel_size = pixel_size or self.pixel_size
        key = (letter, pixel_size)
        if key not in self._cache:
            glyph = self.font(pixel_size).render(letter, False, (255, 255, 255))
            width, height = glyph.get_size()
            self._cache[key] = tuple(
                (row, column)
                for row in range(height)
                for column in range(width)
                if glyph.get_at((column, row))[:3] != (0, 0, 0))
        return self._cache[key]

    def convert_caption(self, caption, pixel_size=None):
        pixel_size = pixel_size or self.pixel_size
        char_width = self.font(pixel_size).size("W")[0]
        pixels = []
        for index, letter in enumerate(caption):
            base = index * char_width
            for (row, column) in self.convert_letter(letter, pixel_size):
                pixels.append((row, base + column))
        return tuple(pixels)

    def fit_caption(self, caption, max_columns, rows):
        glyph = self.font(self.pixel_size).render(caption, False, (255, 255, 255), (0, 0, 0))
        native_width, native_height = glyph.get_size()
        columns = min(max_columns, max(1, round(native_width * rows / native_height)))
        scaled = pygame.transform.scale(glyph, (columns, rows))
        return tuple(
            (row, column)
            for row in range(rows)
            for column in range(columns)
            if scaled.get_at((column, row))[:3] != (0, 0, 0))
