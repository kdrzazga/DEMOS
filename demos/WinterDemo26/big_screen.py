import colorsys
import math
import random
import pygame
from OpenGL.GL import *


class BigScreen:
    """Party projection screen on two stands: a dark frame around an unlit, animated plasma picture.

    Local frame: centred on x, standing on y=0, the picture faces +z.
    display_text() puts the lines of a UTF-8 text file on top of the picture.
    """

    def __init__(self, x, y, z, width=12.0, height=6.75, lift=1.6, columns=32, rows=18):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.lift = lift
        self.columns = columns
        self.rows = rows
        self.frame_border = 0.25
        self.frame_depth = 0.2
        self.stand_width = 0.18
        self.stand_inset = 0.18
        self.frame_color = (0.06, 0.06, 0.07)
        self.plasma_speed = 0.8
        self.time = 0.0
        self.text_resolution = (1024, 576)
        self.text_margin = 40
        self.text_line_gap = 0.5
        self.text_color = (255, 255, 255)
        self.text_shadow_color = (0, 0, 0)
        self.text_shadow_offset = 3
        self.text_texture = None
        self.text_line_areas = ()
        self.shown_file = None
        self.language_files = None
        self.language_font = None
        self.language_size = 48
        self.languages_started = 0.0
        self.text_interfered = False
        self.first_language_duration = 3.0
        self.second_language_duration = 2.0
        self.interference_duration = 1.0
        self.language_cycle = 10.0
        self.shake_pixels = 3
        self.interference_streak_count = 80
        self.interference_streak_thickness = (3, 10)
        self.interference_random = random.Random(3)
        self.display_list = self._compile()

    def _box(self, min_corner, max_corner):
        x0, y0, z0 = min_corner
        x1, y1, z1 = max_corner
        faces = (
            ((0.0, 1.0, 0.0), ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))),
            ((0.0, -1.0, 0.0), ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))),
            ((0.0, 0.0, 1.0), ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))),
            ((0.0, 0.0, -1.0), ((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0))),
            ((1.0, 0.0, 0.0), ((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1))),
            ((-1.0, 0.0, 0.0), ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))),
        )
        glBegin(GL_QUADS)
        for normal, corners in faces:
            glNormal3f(*normal)
            for corner in corners:
                glVertex3f(*corner)
        glEnd()

    def _compile(self):
        half_width = self.width / 2.0 + self.frame_border
        bottom = self.lift - self.frame_border
        top = self.lift + self.height + self.frame_border
        half_depth = self.frame_depth / 2.0
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glColor3f(*self.frame_color)
        self._box((-half_width, bottom, -half_depth), (half_width, top, half_depth))
        for side in (-1.0, 1.0):
            stand_x = side * (half_width - self.stand_inset)
            self._box((stand_x - self.stand_width / 2.0, 0.0, -half_depth * 1.5),
                      (stand_x + self.stand_width / 2.0, bottom, half_depth * 1.5))
        glEndList()
        return display_list

    def update(self, delta_seconds):
        self.time += delta_seconds
        if self.language_files is not None:
            language_file, self.text_interfered = self._language_phase()
            if language_file != self.shown_file:
                self.display_text(language_file, self.language_font, self.language_size)

    def _plasma_color(self, u, v, brightness):
        moment = self.time * self.plasma_speed
        wave = (math.sin(u * 7.0 + moment)
                + math.sin(v * 5.0 - moment * 1.3)
                + math.sin((u + v) * 6.0 + moment * 0.7)
                + math.sin(math.hypot(u - 0.5, v - 0.5) * 12.0 - moment * 1.7)) / 4.0
        red = 0.5 + 0.5 * math.sin(math.pi * wave)
        green = 0.5 + 0.5 * math.sin(math.pi * wave + 2.1)
        blue = 0.5 + 0.5 * math.sin(math.pi * wave + 4.2)
        return red * brightness, green * brightness, blue * brightness

    def _draw_picture(self, brightness):
        left = -self.width / 2.0
        front = self.frame_depth / 2.0 + 0.005
        glDisable(GL_LIGHTING)
        for row in range(self.rows):
            v_low = row / self.rows
            v_high = (row + 1) / self.rows
            glBegin(GL_QUAD_STRIP)
            for column in range(self.columns + 1):
                u = column / self.columns
                picture_x = left + u * self.width
                glColor3f(*self._plasma_color(u, v_low, brightness))
                glVertex3f(picture_x, self.lift + v_low * self.height, front)
                glColor3f(*self._plasma_color(u, v_high, brightness))
                glVertex3f(picture_x, self.lift + v_high * self.height, front)
            glEnd()
        glEnable(GL_LIGHTING)

    def display_text(self, file, font=None, size=48):
        paragraphs = self._read_paragraphs(file)
        text_font = self._load_font(font, size)
        self._delete_text_texture()
        self.text_texture, self.text_line_areas = self._text_to_texture(self._wrap_lines(paragraphs, text_font),
                                                                        text_font)
        self.shown_file = file

    def display_2_languages_text(self, file1, file2, font=None, size=48):
        """Alternates two texts in a 10 s cycle: file1 3 s, interference 1 s, file2 2 s, interference 1 s,
        file1 until the cycle repeats. During interference the text shakes and streaks cover it.
        Both texts use the same font size: the largest up to size at which no line of either file has to wrap.
        """
        self.language_files = (file1, file2)
        self.language_font = font
        self.language_size = self._size_fitting_without_wrap(self.language_files, font, size)
        self.languages_started = self.time
        self.text_interfered = False
        self.display_text(file1, font, self.language_size)

    def _read_paragraphs(self, file):
        with open(file, encoding="utf-8") as text_file:
            return text_file.read().splitlines()

    def _load_font(self, font, size):
        if not pygame.font.get_init():
            pygame.font.init()
        return pygame.font.Font(font, size)

    def _size_fitting_without_wrap(self, files, font, size):
        usable_width = self.text_resolution[0] - 2 * self.text_margin
        lines = [line for file in files for line in self._read_paragraphs(file)]
        while size > 1:
            text_font = self._load_font(font, size)
            if all(text_font.size(line)[0] <= usable_width for line in lines):
                break
            size -= 1
        return size

    def clear_text(self):
        self.language_files = None
        self.text_interfered = False
        self._delete_text_texture()

    def _delete_text_texture(self):
        if self.text_texture is not None:
            glDeleteTextures([self.text_texture])
            self.text_texture = None
            self.text_line_areas = ()
            self.shown_file = None

    def _language_phase(self):
        """Returns the file to show now and whether the interference is running."""
        first_file, second_file = self.language_files
        moment = (self.time - self.languages_started) % self.language_cycle
        first_interference_end = self.first_language_duration + self.interference_duration
        second_language_end = first_interference_end + self.second_language_duration
        if moment < self.first_language_duration:
            return first_file, False
        if moment < first_interference_end:
            return first_file, True
        if moment < second_language_end:
            return second_file, False
        if moment < second_language_end + self.interference_duration:
            return second_file, True
        return first_file, False

    def _wrap_lines(self, paragraphs, text_font):
        usable_width = self.text_resolution[0] - 2 * self.text_margin
        lines = []
        for paragraph in paragraphs:
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}" if line else word
                if line and text_font.size(candidate)[0] > usable_width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        return lines

    def _text_to_texture(self, lines, text_font):
        """Returns the texture and the areas (left, top, width, height) of its lines, in texture pixels from the top."""
        texture_width, texture_height = self.text_resolution
        surface = pygame.Surface(self.text_resolution, pygame.SRCALPHA)
        font_height = text_font.get_height()
        line_step = round(font_height * (1.0 + self.text_line_gap))
        block_height = len(lines) * line_step - (line_step - font_height)
        top = max(self.text_margin, (texture_height - block_height) // 2)
        line_areas = []
        for index, line in enumerate(lines):
            if not line:
                continue
            line_top = top + index * line_step
            shadow = text_font.render(line, True, self.text_shadow_color)
            text = text_font.render(line, True, self.text_color)
            line_left = (texture_width - text.get_width()) // 2
            surface.blit(shadow, (line_left + self.text_shadow_offset, line_top + self.text_shadow_offset))
            surface.blit(text, (line_left, line_top))
            line_areas.append((line_left, line_top, text.get_width(), font_height))
        pixels = pygame.image.tobytes(surface, "RGBA", True)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texture_width, texture_height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, pixels)
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture, tuple(line_areas)

    def _texture_pixel_size(self):
        return self.width / self.text_resolution[0]

    def _shake_offset(self):
        shake = self.interference_random.randint(-self.shake_pixels, self.shake_pixels)
        lift = self.interference_random.randint(-self.shake_pixels, self.shake_pixels)
        return shake * self._texture_pixel_size(), lift * self._texture_pixel_size()

    def _draw_text(self, brightness):
        offset = self._shake_offset() if self.text_interfered else (0.0, 0.0)
        left = -self.width / 2.0 + offset[0]
        right = self.width / 2.0 + offset[0]
        bottom = self.lift + offset[1]
        top = self.lift + self.height + offset[1]
        front = self.frame_depth / 2.0 + 0.01
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, self.text_texture)
        glColor4f(brightness, brightness, brightness, 1.0)
        glNormal3f(0.0, 0.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(left, bottom, front)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(right, bottom, front)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(right, top, front)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(left, top, front)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        if self.text_interfered:
            self._draw_interference(brightness)

    def draw(self, brightness=1.0):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glCallList(self.display_list)
        self._draw_picture(brightness)
        if self.text_texture is not None:
            self._draw_text(brightness)
        glPopMatrix()

    def _random_streak(self):
        """A streak (left, top, right, bottom) in texture pixels across the whole screen, within a random text line."""
        _, line_top, _, line_height = self.interference_random.choice(self.text_line_areas)
        thickness = min(self.interference_random.randint(*self.interference_streak_thickness), line_height)
        streak_top = line_top + self.interference_random.randint(0, line_height - thickness)
        return 0, streak_top, self.text_resolution[0], streak_top + thickness

    def _draw_interference(self, brightness):
        if not self.text_line_areas:
            return
        pixel_size = self._texture_pixel_size()
        left = -self.width / 2.0
        top = self.lift + self.height
        front = self.frame_depth / 2.0 + 0.015
        glDisable(GL_LIGHTING)
        glBegin(GL_QUADS)
        for _ in range(self.interference_streak_count):
            streak_left, streak_top, streak_right, streak_bottom = self._random_streak()
            hue = self.interference_random.random()
            glColor3f(*colorsys.hsv_to_rgb(hue, 1.0, brightness))
            glVertex3f(left + streak_left * pixel_size, top - streak_bottom * pixel_size, front)
            glVertex3f(left + streak_right * pixel_size, top - streak_bottom * pixel_size, front)
            glVertex3f(left + streak_right * pixel_size, top - streak_top * pixel_size, front)
            glVertex3f(left + streak_left * pixel_size, top - streak_top * pixel_size, front)
        glEnd()
        glEnable(GL_LIGHTING)
