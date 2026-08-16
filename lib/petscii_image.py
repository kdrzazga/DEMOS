import pygame

from demos.petscii.files.globals import Constants


class PetsciiImage:
    """A 40x25 Commodore 64 text screen.

    chars holds one PETSCII code per cell (32 = space). reversed marks the cells
    drawn in reverse video -- the C64 charset has no separate reversed glyphs, so
    those cells are drawn by swapping foreground and background colours. colors
    holds the C64 colour index of each cell, and is only meaningful where chars
    is not a space.

    Render a cell with the C64_Pro_Mono-STYLE.ttf font as: chr(FONT_BASE + code)
    """

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
        self.background_color = Constants.BACKGROUND_COLOR
        self.font_base = Constants.FONT_BASE

    @classmethod
    def from_petscii_screen(cls, screen, char_size=16):
        image = cls(char_size)
        image.chars = tuple(tuple(cls._screen_to_petscii(code & 0x7F) for code in row)
                            for row in screen.characters)
        image.colors = screen.colors
        image.reversed = tuple(tuple(code >= 128 for code in row) for row in screen.characters)
        image.font_base = Constants.FONT_BASE + (0 if screen.uppercase else 0x100)
        image.background_color = screen.background_color
        return image

    @staticmethod
    def _screen_to_petscii(code):
        if code < 32:
            return code + 64
        if code < 64:
            return code
        if code < 96:
            return code + 32
        return code + 64

    def font(self, char_size=None):
        char_size = self.char_size if char_size is None else char_size
        if char_size not in self._fonts:
            self._fonts[char_size] = pygame.font.Font(Constants.FONT_PATH, char_size)
        return self._fonts[char_size]

    def size(self, char_size=None):
        """Pixel size of the whole screen at the given character size."""
        cell_width, cell_height = self.font(char_size).size("W")
        return Constants.COLUMNS * cell_width, Constants.ROWS * cell_height

    def render(self, surface, char_size=None, transparent_space=False, origin=(0, 0)):
        char_size = self.char_size if char_size is None else char_size
        cell_size = self.font(char_size).size("W")
        if not transparent_space:
            surface.fill(Constants.PALETTE[self.background_color])
        for row in range(Constants.ROWS):
            for column in range(Constants.COLUMNS):
                if transparent_space and self.is_blank(row, column):
                    continue
                self.draw_cell(surface, char_size, cell_size, row, column, origin)

    def render_from_corners(self, surface, char_size=None, transparent_space=False,
                            speed=Constants.REVEAL_SPEED, origin=(0, 0)):
        """Reveal the image from the four corners, adding speed characters per call."""
        self.render_progress += speed
        char_size = self.char_size if char_size is None else char_size
        cell_size = self.font(char_size).size("W")
        if not transparent_space:
            surface.fill(Constants.PALETTE[self.background_color])
        for corner in range(Constants.CORNERS):
            for row, column in self.cells_from_corner(corner):
                if transparent_space and self.is_blank(row, column):
                    continue
                self.draw_cell(surface, char_size, cell_size, row, column, origin)

    def cells_from_corner(self, corner):
        """The cells revealed so far at one corner: everything up to its newest character."""
        revealed = (self.render_progress - corner + Constants.CORNERS - 1) // Constants.CORNERS
        if revealed <= 0:
            return []
        order, character_cuts = self.corner_order(corner)
        return order[:character_cuts[min(revealed, len(character_cuts)) - 1]]

    def corner_order(self, corner):
        """Every cell in the order the corner fills them, and where each character sits."""
        if corner not in self._corner_orders:
            order = []
            for index in range(Constants.ROWS * Constants.COLUMNS):
                row, column = divmod(index, Constants.COLUMNS)
                if corner in (Constants.TOP_RIGHT, Constants.BOTTOM_RIGHT):
                    column = Constants.COLUMNS - 1 - column
                if corner in (Constants.BOTTOM_RIGHT, Constants.BOTTOM_LEFT):
                    row = Constants.ROWS - 1 - row
                order.append((row, column))
            character_cuts = [index + 1 for index, cell in enumerate(order)
                              if not self.is_blank(*cell)]
            self._corner_orders[corner] = order, character_cuts
        return self._corner_orders[corner]

    def draw_cell(self, surface, char_size, cell_size, row, column, origin=(0, 0)):
        background = Constants.PALETTE[self.background_color]
        foreground, cell_background = Constants.PALETTE[self.colors[row][column]], background
        if self.reversed[row][column]:
            foreground, cell_background = cell_background, foreground
        glyph = self.glyph(char_size, self.chars[row][column], foreground, cell_background)
        cell_width, cell_height = cell_size
        origin_x, origin_y = origin
        surface.blit(glyph, (origin_x + column * cell_width, origin_y + row * cell_height))

    def glyph(self, char_size, code, foreground, background):
        """A rendered character, built once and reused on later frames."""
        key = (char_size, code, foreground, background)
        if key not in self._glyphs:
            self._glyphs[key] = self.font(char_size).render(
                chr(self.font_base + code), False, foreground, background)
        return self._glyphs[key]

    def is_blank(self, row, column):
        return self.chars[row][column] == Constants.SPACE and not self.reversed[row][column]
