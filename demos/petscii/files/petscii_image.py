import os

import pygame

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class PetsciiImage:
    """A 40x25 Commodore 64 text screen.

    chars holds one PETSCII code per cell (32 = space). reversed marks the cells
    drawn in reverse video -- the C64 charset has no separate reversed glyphs, so
    those cells are drawn by swapping foreground and background colours. colors
    holds the C64 colour index of each cell, and is only meaningful where chars
    is not a space.

    Render a cell with the C64_Pro_Mono-STYLE.ttf font as: chr(FONT_BASE + code)
    """

    COLUMNS = 40
    ROWS = 25
    FONT_BASE = 0xE000

    FONT_PATH = os.path.join(_ROOT, "lib", "resources", "C64_Pro_Mono-STYLE.ttf")
    CHAR_SIZE = 16

    SPACE = 32

    # $D020 and $D021 as set by the program
    BORDER_COLOR = 0
    BACKGROUND_COLOR = 0

    # standard C64 palette, indexed by colour code
    PALETTE = (
        (0, 0, 0),        # 0  black
        (255, 255, 255),  # 1  white
        (104, 55, 43),    # 2  red
        (112, 164, 178),  # 3  cyan
        (111, 61, 134),   # 4  purple
        (88, 141, 67),    # 5  green
        (53, 40, 121),    # 6  blue
        (184, 199, 111),  # 7  yellow
        (111, 79, 37),    # 8  orange
        (67, 57, 0),      # 9  brown
        (154, 103, 89),   # 10 light red
        (68, 68, 68),     # 11 dark grey
        (108, 108, 108),  # 12 grey
        (154, 210, 132),  # 13 light green
        (108, 94, 181),   # 14 light blue
        (149, 149, 149),  # 15 light grey
    )

    chars = ()
    reversed = ()
    colors = ()

    def __init__(self):
        pygame.font.init()
        self._fonts = {}

    def font(self, char_size=CHAR_SIZE):
        if char_size not in self._fonts:
            self._fonts[char_size] = pygame.font.Font(self.FONT_PATH, char_size)
        return self._fonts[char_size]

    def size(self, char_size=CHAR_SIZE):
        """Pixel size of the whole screen at the given character size."""
        cell_width, cell_height = self.font(char_size).size("W")
        return self.COLUMNS * cell_width, self.ROWS * cell_height

    def render(self, surface, char_size=CHAR_SIZE, transparent_space=False):
        font = self.font(char_size)
        cell_width, cell_height = font.size("W")
        background = self.PALETTE[self.BACKGROUND_COLOR]
        if not transparent_space:
            surface.fill(background)
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                if transparent_space and self.is_blank(row, column):
                    continue
                foreground, cell_background = self.PALETTE[self.colors[row][column]], background
                if self.reversed[row][column]:
                    foreground, cell_background = cell_background, foreground
                glyph = font.render(chr(self.FONT_BASE + self.chars[row][column]), False,
                                    foreground, cell_background)
                surface.blit(glyph, (column * cell_width, row * cell_height))

    def is_blank(self, row, column):
        return self.chars[row][column] == self.SPACE and not self.reversed[row][column]
