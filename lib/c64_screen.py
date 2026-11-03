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

    def scrolled_rows(self):
        if not self.typers:
            return 0
        bottom_row = max((typer.row for typer in self.typers
                          if typer.has_started(self.time)), default=0)
        cursor = self.cursor_typer()
        if cursor.shows_cursor and cursor.is_finished(self.time):
            bottom_row = max(bottom_row, cursor.row + 1)
        return max(bottom_row - (self.frame.rows - 1), 0)

    def draw(self):
        scrolled_rows = self.scrolled_rows()
        for row, column, image in self.rendered_lines:
            self.surface.blit(image, self.cell_position(row - scrolled_rows, column))
        if not self.typers:
            return
        for typer in self.typers:
            typer.scroll_up(scrolled_rows)
            typer.type_at(self.time)
        typer = self.cursor_typer()
        if typer.shows_cursor and (typer.is_typing(self.time) or self.cursor_visible()):
            typer.draw_cursor(self.time)


class DimmedPicture:
    def __init__(self, surface, sprite, start_time):
        self.surface = surface
        self.sprite = sprite
        self.start_time = start_time
        self.darkness = 0.6
        self.fade_duration = 0.5
        self.shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    def is_shown(self, time):
        return time >= self.start_time

    def restart(self):
        self.sprite.restart()

    def update(self, time, seconds):
        if self.is_shown(time):
            self.sprite.update(seconds)

    def draw(self, time):
        if not self.is_shown(time):
            return
        fade = min((time - self.start_time) / self.fade_duration, 1.0)
        self.shade.fill((0, 0, 0, round(255 * self.darkness * fade)))
        self.surface.blit(self.shade, (0, 0))
        self.sprite.draw(self.surface)


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
        self.picture = None
        self.normal_border_index = self.frame.border_color
        self.picture_border_index = 0
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

    def normalized_color(self, index):
        red, green, blue = Constants.PALETTE[index]
        return (red / 255.0, green / 255.0, blue / 255.0)

    @property
    def border_color(self):
        return self.normalized_color(self.frame.border_color)

    @property
    def normal_border_color(self):
        return self.normalized_color(self.normal_border_index)

    @property
    def is_showing_picture(self):
        return (self.picture is not None
                and self.picture.is_shown(self.startup_text.time))

    def update_border(self):
        if self.is_showing_picture:
            self.frame.set_border_color(self.picture_border_index)
        else:
            self.frame.set_border_color(self.normal_border_index)

    def set_content(self, content):
        self.frame.set_content(content)

    def set_typers(self, typers):
        self.typers = typers
        self.startup_text.typers = typers

    @property
    def center(self):
        return self.width / 2.0, self.height / 2.0

    def show_picture(self, sprite, start_time):
        self.picture = DimmedPicture(self.surface, sprite, start_time)

    @property
    def is_off(self):
        return self.blank_seconds_left > 0.0

    def off(self, duration_sec: float):
        self.blank_seconds_left = max(duration_sec, 0.0)

    def update(self, seconds):
        self.frame.update(seconds)
        self.blank_seconds_left = max(self.blank_seconds_left - seconds, 0.0)
        if self.picture is not None and self.startup_text.typing:
            self.picture.update(self.startup_text.time, seconds)
        self.update_border()

    def restart_typing(self):
        self.startup_text.restart()
        if self.picture is not None:
            self.picture.restart()

    def hold_typing(self):
        self.startup_text.hold()
        if self.picture is not None:
            self.picture.restart()

    def draw_blank(self):
        self.surface.fill(Constants.PALETTE[self.frame.border_color])

    def refresh(self):
        if self.is_off:
            self.draw_blank()
        else:
            self.frame.draw()
            if self.picture is not None:
                self.picture.draw(self.startup_text.time)
        pixels = pygame.image.tobytes(self.surface, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
                        GL_RGBA, GL_UNSIGNED_BYTE, pixels)
