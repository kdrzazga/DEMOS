import pygame

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
        self.border_char = border_char  # drawn in reverse video (inverted space)
        self.color = color              # white on the surface, tinted by the blink
        self.stretch = stretch          # widen so the edges reach the C64 border
        self.font = pygame.font.Font(Constants.FONT_PATH, font_size)

    def draw(self, surface):
        columns = Constants.COLUMNS
        width = columns * self.font_size
        height = self.rows * self.font_size
        mesh = pygame.Surface((width, height))
        last_row = self.rows - 1
        last_column = columns - 1
        for row in range(self.rows):
            for column in range(columns):
                code, reverse = self.cell(row, column, last_row, last_column)
                mesh.blit(self.glyph(code, reverse),
                          (column * self.font_size, row * self.font_size))

        stretched_width = int(width * self.stretch)
        mesh = pygame.transform.scale(mesh, (stretched_width, height))
        x = (Constants.WIDTH - stretched_width) // 2
        y = self.top_row * self.font_size
        surface.blit(mesh, (x, y))

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
