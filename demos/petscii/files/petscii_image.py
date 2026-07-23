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

    SPACE = 32

    # corners the reveal grows from, filled in this order
    TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT = range(4)
    CORNERS = 4

    # characters added per call to render_from_corners
    REVEAL_SPEED = 6

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

    def __init__(self, char_size=16):
        pygame.font.init()
        self.char_size = char_size
        self._fonts = {}
        self._glyphs = {}
        self._corner_orders = {}
        self.render_progress = 0

    def font(self, char_size=None):
        char_size = self.char_size if char_size is None else char_size
        if char_size not in self._fonts:
            self._fonts[char_size] = pygame.font.Font(self.FONT_PATH, char_size)
        return self._fonts[char_size]

    def size(self, char_size=None):
        """Pixel size of the whole screen at the given character size."""
        cell_width, cell_height = self.font(char_size).size("W")
        return self.COLUMNS * cell_width, self.ROWS * cell_height

    def render(self, surface, char_size=None, transparent_space=False):
        char_size = self.char_size if char_size is None else char_size
        cell_size = self.font(char_size).size("W")
        if not transparent_space:
            surface.fill(self.PALETTE[self.BACKGROUND_COLOR])
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                if transparent_space and self.is_blank(row, column):
                    continue
                self.draw_cell(surface, char_size, cell_size, row, column)

    def render_from_corners(self, surface, char_size=None, transparent_space=False,
                            speed=REVEAL_SPEED):
        """Reveal the image from the four corners, adding speed characters per call."""
        self.render_progress += speed
        char_size = self.char_size if char_size is None else char_size
        cell_size = self.font(char_size).size("W")
        if not transparent_space:
            surface.fill(self.PALETTE[self.BACKGROUND_COLOR])
        for corner in range(self.CORNERS):
            for row, column in self.cells_from_corner(corner):
                if transparent_space and self.is_blank(row, column):
                    continue
                self.draw_cell(surface, char_size, cell_size, row, column)

    def cells_from_corner(self, corner):
        """The cells revealed so far at one corner: everything up to its newest character."""
        revealed = (self.render_progress - corner + self.CORNERS - 1) // self.CORNERS
        if revealed <= 0:
            return []
        order, character_cuts = self.corner_order(corner)
        return order[:character_cuts[min(revealed, len(character_cuts)) - 1]]

    def corner_order(self, corner):
        """Every cell in the order the corner fills them, and where each character sits."""
        if corner not in self._corner_orders:
            order = []
            for index in range(self.ROWS * self.COLUMNS):
                row, column = divmod(index, self.COLUMNS)
                if corner in (self.TOP_RIGHT, self.BOTTOM_RIGHT):
                    column = self.COLUMNS - 1 - column
                if corner in (self.BOTTOM_RIGHT, self.BOTTOM_LEFT):
                    row = self.ROWS - 1 - row
                order.append((row, column))
            character_cuts = [index + 1 for index, cell in enumerate(order)
                              if not self.is_blank(*cell)]
            self._corner_orders[corner] = order, character_cuts
        return self._corner_orders[corner]

    def draw_cell(self, surface, char_size, cell_size, row, column):
        background = self.PALETTE[self.BACKGROUND_COLOR]
        foreground, cell_background = self.PALETTE[self.colors[row][column]], background
        if self.reversed[row][column]:
            foreground, cell_background = cell_background, foreground
        glyph = self.glyph(char_size, self.chars[row][column], foreground, cell_background)
        cell_width, cell_height = cell_size
        surface.blit(glyph, (column * cell_width, row * cell_height))

    def glyph(self, char_size, code, foreground, background):
        """A rendered character, built once and reused on later frames."""
        key = (char_size, code, foreground, background)
        if key not in self._glyphs:
            self._glyphs[key] = self.font(char_size).render(
                chr(self.FONT_BASE + code), False, foreground, background)
        return self._glyphs[key]

    def is_blank(self, row, column):
        return self.chars[row][column] == self.SPACE and not self.reversed[row][column]
