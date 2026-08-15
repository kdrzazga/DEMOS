from collections import namedtuple

import pygame

from lib.textwall import TextWall
from demos.petscii.files.globals import Constants

Span = namedtuple("Span", ("start", "codes", "color", "inverted"))


class PetsciiTextWall(TextWall):

    def __init__(self, image, *, surface, x=0, y=0, initial_screen_y=0,
                 rows=Constants.ROWS, speed=20, loop=False, char_size=16):
        self.surface = surface
        self.image = image
        self.char_size = char_size
        self.cell_width, self.cell_height = image.font(char_size).size("W")
        super().__init__(self._build_row_strips(), speed=speed, x=x, y=y,
                         initial_screen_y=initial_screen_y, rows=rows,
                         line_step=self.cell_height, loop=loop)

    def draw_line(self, strip, x, y):
        self.surface.blit(strip, (int(x), int(y)))

    def _build_row_strips(self):
        return tuple(self._render_row(row) for row in range(Constants.ROWS))

    def _render_row(self, row):
        strip = pygame.Surface(
            (Constants.COLUMNS * self.cell_width, self.cell_height), pygame.SRCALPHA)
        for span in self._spans_in_row(row):
            strip.blit(self._render_span(span), (span.start * self.cell_width, 0))
        return strip

    def _spans_in_row(self, row):
        spans = []
        column = 0
        while column < Constants.COLUMNS:
            if self._is_blank(row, column):
                column += 1
                continue
            start = column
            color = self.image.colors[row][column]
            inverted = self.image.reversed[row][column]
            codes = []
            while column < Constants.COLUMNS and self._continues(row, column, color, inverted):
                codes.append(self.image.chars[row][column])
                column += 1
            spans.append(Span(start, tuple(codes), color, inverted))
        return spans

    def _continues(self, row, column, color, inverted):
        return (not self._is_blank(row, column)
                and self.image.colors[row][column] == color
                and self.image.reversed[row][column] == inverted)

    def _is_blank(self, row, column):
        return (self.image.chars[row][column] == Constants.SPACE
                and not self.image.reversed[row][column])

    def _render_span(self, span):
        glyphs = "".join(chr(self.image.font_base + code) for code in span.codes)
        foreground = Constants.PALETTE[span.color]
        font = self.image.font(self.char_size)
        if span.inverted:
            background = Constants.PALETTE[Constants.BACKGROUND_COLOR]
            return font.render(glyphs, False, background, foreground)
        return font.render(glyphs, False, foreground)
