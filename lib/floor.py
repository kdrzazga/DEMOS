import math
import random

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.globals import Constants


class JumpingLetter:

    def __init__(self, x, floor_level, z, texture, target_x=None, target_y=None,
                 target_z=None, height=0.84, speed=0.03,
                 sway_amplitude=0.5, sway_speed=0.1):
        self.base_x = x
        self.x = x
        self.z = z
        self.texture = texture
        self.target_x = target_x
        self.target_y = target_y
        self.target_z = target_z
        self.min_y = floor_level
        self.max_y = floor_level + height + random.randint(1,9)/100
        self.y = floor_level
        self.direction = 1
        self.speed = speed + random.randint(0,3)/100
        self.sway_amplitude = sway_amplitude
        self.sway_speed = sway_speed
        self.phase = random.uniform(0, 2 * math.pi)

    def update(self):
        self.y += self.direction * self.speed
        if self.y >= self.max_y:
            self.y, self.direction = self.max_y, -1
        elif self.y <= self.min_y:
            self.y, self.direction = self.min_y, 1
        self.phase += self.sway_speed
        self.x = self.base_x + self.sway_amplitude * math.sin(self.phase)

    def settle(self):
        self.x += (self.target_x - self.x) * 0.15
        self.y += (self.target_y - self.y) * 0.15
        self.z += (self.target_z - self.z) * 0.15


class JumpingLettersToCaption:

    CURRENT_ROW = 0

    def __init__(self, caption, initial_frame, duration, target_x, target_y, target_z,
                 floor_level=-1.5, half_width=Constants.HALF_WIDTH, depth=2.0,
                 char_size=12, letter_size=0.25, color=Constants.PALETTE[1]):
        self.caption = caption
        self.letters = list(caption)
        self.initial_frame = initial_frame
        self.duration = duration
        self.letter_size = letter_size
        self.target_y = target_y  # settled world-y, used to hide it as a stage rises past
        self.started = False
        self.letter_objects = []
        self.visible=True

        for row, line in enumerate(caption.split("\n")):
            for column, char in enumerate(line):
                if char == " ":
                    continue
                texture = self._build_letter_texture(char, char_size, color)
                letter_target_x = target_x + column * letter_size
                letter_target_y = target_y - row * letter_size
                start_x = random.uniform(1 - half_width, half_width - 1)
                start_z = random.uniform(0.5 - depth, 0.2)
                self.letter_objects.append(
                    JumpingLetter(start_x, floor_level, start_z, texture,
                                  letter_target_x, letter_target_y, target_z))

    def update(self, frame):
        relative = frame - self.initial_frame
        if relative < 0:
            return
        self.started = True
        if relative < self.duration:
            for letter in self.letter_objects:
                letter.update()
        else:
            for letter in self.letter_objects:
                letter.settle()

    def draw(self):
        if not self.started or not self.visible:
            return
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor3f(1.0, 1.0, 1.0)
        half = self.letter_size / 2
        for letter in self.letter_objects:
            glBindTexture(GL_TEXTURE_2D, letter.texture)
            left, right = letter.x - half, letter.x + half
            top, bottom = letter.y + half, letter.y - half
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex3f(left, top, letter.z)
            glTexCoord2f(1.0, 0.0); glVertex3f(right, top, letter.z)
            glTexCoord2f(1.0, 1.0); glVertex3f(right, bottom, letter.z)
            glTexCoord2f(0.0, 1.0); glVertex3f(left, bottom, letter.z)
            glEnd()
        glDisable(GL_BLEND)

    def _build_letter_texture(self, char, char_size, color):
        pygame.font.init()
        font = pygame.font.Font(Constants.FONT_PATH, char_size)
        glyph = chr(Constants.FONT_BASE + ord(char))
        surface = font.render(glyph, True, color)
        data = pygame.image.tobytes(surface, "RGBA")
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return texture


class Floor:
    """Parallel horizontal lines forming a floor, drawn from the PETSCII
    horizontal-line glyph (code 196) rather than graphics primitives. The lines
    lie on the plane y = level_y and recede in depth, so perspective spaces them
    like a floor. density is the gap in world units between neighbouring lines.
    Jumping balls (the BALL glyph) bounce off the floor plane on top."""

    HORIZONTAL_LINE = 196
    BALL_CHARS = (113, 48, 79, 143) # PETSCII codes for:ball, empty ball, O,o

    def __init__(self, width, height, initial_frame=0, half_width=Constants.HALF_WIDTH,
                 camera_z=Constants.CAMERA_Z, far_plane=50.0, depth=2.0,
                 density=0.25, reveal_frames=25, level_y=None, char_size=16,
                 color=Constants.PALETTE[12], ball_size=0.12,
                 ball_color=Constants.PALETTE[1]):
        self.width = width
        self.height = height
        self.initial_frame = initial_frame
        self.half_width = half_width
        self.half_height = half_width * height / width
        self.camera_z = camera_z
        self.far_plane = far_plane
        self.depth = depth
        self.density = density
        self.reveal_frames = reveal_frames
        self.level_y = -self.half_height if level_y is None else level_y
        self.ball_size = ball_size
        self.texture = glGenTextures(1)
        self.line_thickness = self._build_texture(char_size, color)
        self.balls = []

    def update(self):
        for ball in self.balls:
            ball.update()

    def _build_texture(self, char_size, color):
        pygame.font.init()
        font = pygame.font.Font(Constants.FONT_PATH, char_size)
        glyph = chr(Constants.FONT_BASE + Floor.HORIZONTAL_LINE)
        surface = font.render(glyph * Constants.COLUMNS, False, color, (0, 0, 0))
        data = pygame.image.tobytes(surface, "RGBA", True)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return 2 * self.half_width * surface.get_height() / surface.get_width()

    def draw(self, frame):
        relative_frame = frame - self.initial_frame
        reveal = max(0.0, min(1.0, relative_frame / self.reveal_frames))
        self._begin_3d()
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glColor3f(1.0, 1.0, 1.0)
        index = 0
        z = 0.0
        while z > -self.depth:
            self._draw_line(z, index, reveal)
            z -= self.density
            index += 1
        self._draw_balls()

    def _draw_balls(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor3f(1.0, 1.0, 1.0)
        half = self.ball_size / 2
        for ball in self.balls:
            glBindTexture(GL_TEXTURE_2D, ball.texture)
            left, right = ball.x - half, ball.x + half
            top, bottom = ball.y + half, ball.y - half
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex3f(left, top, ball.z)
            glTexCoord2f(1.0, 0.0); glVertex3f(right, top, ball.z)
            glTexCoord2f(1.0, 1.0); glVertex3f(right, bottom, ball.z)
            glTexCoord2f(0.0, 1.0); glVertex3f(left, bottom, ball.z)
            glEnd()
        glDisable(GL_BLEND)

    def _draw_line(self, near_z, index, reveal):
        if reveal <= 0.0:
            return
        span = 2 * self.half_width
        if index % 2 == 0:
            left_x = -self.half_width
            right_x = left_x + reveal * span
            u_left, u_right = 0.0, reveal
        else:
            right_x = self.half_width
            left_x = right_x - reveal * span
            u_left, u_right = 1.0 - reveal, 1.0
        far_z = near_z - self.line_thickness
        glBegin(GL_QUADS)
        glTexCoord2f(u_left, 0.0); glVertex3f(left_x, self.level_y, near_z)
        glTexCoord2f(u_right, 0.0); glVertex3f(right_x, self.level_y, near_z)
        glTexCoord2f(u_right, 1.0); glVertex3f(right_x, self.level_y, far_z)
        glTexCoord2f(u_left, 1.0); glVertex3f(left_x, self.level_y, far_z)
        glEnd()

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, self.width / self.height, 0.1, self.far_plane)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.camera_z)
