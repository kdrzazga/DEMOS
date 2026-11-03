import pygame
from OpenGL.GL import *

from lib.c64_frame import C64Frame
from lib.globals import Constants
from lib.typing_effect.c64_typer import C64Typer


class C64StartupText:
    def __init__(self, surface, frame, font, typers):
        self.surface = surface
        self.frame = frame
        self.font = font
        self.typers = typers
        self.text_color = Constants.PALETTE[14]
        self.lines = [(1, 4, Constants.HEADER),
                      (3, 0, Constants.HEADER2),
                      (5, 0, Constants.HEADER3)]
        self.blink_period = 0.66
        self.time = 0.0
        self.blink_time = 0.0
        self.typing = True
        self.rendered_lines = [(row, column, self.render(text))
                               for row, column, text in self.lines]

    def render(self, text):
        glyphs = "".join(chr(Constants.FONT_BASE + ord(character))
                         for character in text.upper())
        return self.font.render(glyphs, False, self.text_color)

    def cell_position(self, row, column):
        return (self.frame.char_x + column * self.frame.cell_width,
                self.frame.char_y + row * self.frame.cell_height)

    def update(self, seconds):
        self.blink_time += seconds
        if self.typing:
            self.time += seconds

    def restart(self):
        self.time = 0.0
        self.typing = True

    def hold(self):
        self.time = 0.0
        self.typing = False

    def cursor_visible(self):
        return self.blink_time % self.blink_period < self.blink_period / 2.0

    def cursor_typer(self):
        started = [typer for typer in self.typers if typer.has_started(self.time)]
        return started[-1] if started else self.typers[0]

    def draw(self):
        for row, column, image in self.rendered_lines:
            self.surface.blit(image, self.cell_position(row, column))
        if not self.typers:
            return
        for typer in self.typers:
            typer.type_at(self.time)
        typer = self.cursor_typer()
        if typer.shows_cursor and (typer.is_typing(self.time) or self.cursor_visible()):
            typer.draw_cursor(self.time)


class C64Screen:
    def __init__(self):
        self.cell_size = 8
        self.border = 32
        self.width = Constants.COLUMNS * self.cell_size + 2 * self.border
        self.height = Constants.ROWS * self.cell_size + 2 * self.border
        self.surface = pygame.Surface((self.width, self.height))
        self.frame = C64Frame(self.surface, cell_width=self.cell_size,
                              cell_height=self.cell_size, border=self.border)
        self.font = pygame.font.Font(Constants.FONT_PATH, self.cell_size)
        self.typers = [C64Typer(self.frame, 6, 0, 'LOAD"*",8,1', 1.5)]
        self.startup_text = C64StartupText(self.surface, self.frame,
                                           self.font, self.typers)
        self.frame.set_content(self.startup_text)
        self.blank_seconds_left = 0.0
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, None)
        self.refresh()

    @property
    def aspect(self):
        return self.width / self.height

    @property
    def border_color(self):
        red, green, blue = Constants.PALETTE[self.frame.border_color]
        return (red / 255.0, green / 255.0, blue / 255.0)

    def set_content(self, content):
        self.frame.set_content(content)

    def set_typers(self, typers):
        self.typers = typers
        self.startup_text.typers = typers

    @property
    def is_off(self):
        return self.blank_seconds_left > 0.0

    def off(self, duration_sec: float):
        self.blank_seconds_left = max(duration_sec, 0.0)

    def update(self, seconds):
        self.frame.update(seconds)
        self.blank_seconds_left = max(self.blank_seconds_left - seconds, 0.0)

    def restart_typing(self):
        self.startup_text.restart()

    def hold_typing(self):
        self.startup_text.hold()

    def draw_blank(self):
        self.surface.fill(Constants.PALETTE[self.frame.border_color])

    def refresh(self):
        if self.is_off:
            self.draw_blank()
        else:
            self.frame.draw()
        pixels = pygame.image.tobytes(self.surface, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
                        GL_RGBA, GL_UNSIGNED_BYTE, pixels)
