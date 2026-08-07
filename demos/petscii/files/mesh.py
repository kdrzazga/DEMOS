import pygame

from demos.petscii.files.font_to_mesh_converter import FontToMeshConverter
from demos.petscii.files.globals import Constants


class PetsciiMesh:

    def __init__(self, font_size, top_row=8, rows=11, top_char=239, fill_char=204,
                 bottom_char=247, border_char=32, color=(255, 255, 255), stretch=1.04):
        self.font_size = font_size
        self.top_row = top_row
        self.rows = rows
        self.top_char = top_char
        self.fill_char = fill_char
        self.bottom_char = bottom_char
        self.border_char = border_char
        self.color = color
        self.stretch = stretch
        self.font = pygame.font.Font(Constants.FONT_PATH, font_size)
        self.converter = FontToMeshConverter()
        self._highlight_glyphs = {}

    def draw(self, surface, highlights=None):
        highlights = highlights or {}
        columns = Constants.COLUMNS
        width = columns * self.font_size
        height = self.rows * self.font_size
        mesh = pygame.Surface((width, height))
        last_row = self.rows - 1
        last_column = columns - 1
        for row in range(self.rows):
            for column in range(columns):
                if (row, column) in highlights:
                    glyph = self.highlight_glyph(highlights[(row, column)])
                else:
                    code, reverse = self.cell(row, column, last_row, last_column)
                    glyph = self.glyph(code, reverse)
                mesh.blit(glyph, (column * self.font_size, row * self.font_size))

        stretched_width = int(width * self.stretch)
        mesh = pygame.transform.scale(mesh, (stretched_width, height))
        x = (Constants.WIDTH - stretched_width) // 2
        y = self.top_row * self.font_size
        surface.blit(mesh, (x, y))

    def draw_letter(self, surface, letter, x, color):
        self.draw(surface, self.highlights(self.converter.convert_letter(letter), x, color))

    def draw_text(self, surface, text, x=None, color=(255, 255, 255)):
        self.draw(surface, self.highlights(self.converter.convert_caption(text), x, color))

    def text_surface(self, text, color, x=None):
        highlights = self.highlights(self.converter.convert_caption(text), x, color)
        return self._compose({pos: self.highlight_glyph(c) for pos, c in highlights.items()})

    def lattice_surface(self):
        columns = Constants.COLUMNS
        last_row = self.rows - 1
        last_column = columns - 1
        cells = {(row, column): self.glyph(*self.cell(row, column, last_row, last_column))
                 for row in range(self.rows) for column in range(columns)}
        return self._compose(cells)

    def _compose(self, cell_glyphs):
        width = Constants.COLUMNS * self.font_size
        height = self.rows * self.font_size
        layer = pygame.Surface((width, height), pygame.SRCALPHA)
        for (row, column), glyph in cell_glyphs.items():
            layer.blit(glyph, (column * self.font_size, row * self.font_size))
        stretched = pygame.transform.scale(layer, (int(width * self.stretch), height))
        result = pygame.Surface((Constants.WIDTH, Constants.HEIGHT), pygame.SRCALPHA)
        result.blit(stretched, ((Constants.WIDTH - stretched.get_width()) // 2,
                                self.top_row * self.font_size))
        return result

    def highlights(self, pixels, x, color):
        interior_columns = Constants.COLUMNS - 2
        interior_rows = self.rows - 2
        text_height = max((row for row, _ in pixels), default=0) + 1
        row_offset = max(0, (interior_rows - text_height) // 2)
        if x is None:
            text_width = max((column for _, column in pixels), default=0) + 1
            x = (interior_columns - text_width) // 2
        highlights = {}
        for (row, column) in pixels:
            cell_row = 1 + row_offset + row
            cell_column = 1 + x + column
            if 1 <= cell_row <= self.rows - 2 and 1 <= cell_column <= interior_columns:
                highlights[(cell_row, cell_column)] = color
        return highlights

    def highlight_glyph(self, color):
        if color not in self._highlight_glyphs:
            self._highlight_glyphs[color] = self.font.render(
                chr(Constants.FONT_BASE + self.border_char), False, (0, 0, 0), color)
        return self._highlight_glyphs[color]

    def cell(self, row, column, last_row, last_column):
        if row == 0:
            return self.top_char, False
        if row == last_row:
            return self.bottom_char, False
        if column in (0, last_column):
            return self.border_char, True
        return self.fill_char, False

    def glyph(self, code, reverse):
        glyph = chr(Constants.FONT_BASE + code)
        if reverse:
            return self.font.render(glyph, False, (0, 0, 0), self.color)
        return self.font.render(glyph, False, self.color)
