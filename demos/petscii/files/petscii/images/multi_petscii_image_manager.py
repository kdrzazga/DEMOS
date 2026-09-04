import math

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_BORDER,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUAD_STRIP,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_BORDER_COLOR,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor3f,
    glDepthRange,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glTexCoord2f,
    glTexImage2D,
    glTexParameterfv,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.images.caption1 import Caption1
from demos.petscii.files.petscii.images.caption2 import Caption2
from demos.petscii.files.petscii.images.caption3 import Caption3
from demos.petscii.files.petscii.images.caption4 import Caption4
from demos.petscii.files.petscii.images.caption5 import Caption5
from demos.petscii.files.petscii.images.caption6 import Caption6
from demos.petscii.files.petscii.images.caption7 import Caption7
from demos.petscii.files.petscii.images.caption8 import Caption8
from demos.petscii.files.petscii.images.caption9 import Caption9
from demos.petscii.files.petscii.images.caption10 import Caption10
from demos.petscii.files.petscii.images.caption11 import Caption11
from demos.petscii.files.petscii.images.caption_empty import CaptionEmpty
from lib.multi_petscii_image import MultiPetsciiImage


class MultiPetsciiImageManager:

    SPEED = 0.0015 * 1.65

    def __init__(self, char_size=24, sweep=math.pi / 2, segments=80, radius=None):
        self.captions = MultiPetsciiImage(
            (Caption1(char_size), Caption2(char_size), Caption3(char_size), Caption4(char_size)
             , Caption5(char_size), Caption6(char_size), Caption7(char_size), Caption8(char_size), CaptionEmpty(char_size)
             , Caption9(char_size), Caption10(char_size), Caption11(char_size)
             ))
        self.tex_w, self.tex_h = self.captions.size()
        surface = pygame.Surface((self.tex_w, self.tex_h), pygame.SRCALPHA)
        self.captions.render(surface, transparent_space=True)
        self.texture = self._upload(surface)

        self.sweep = sweep
        self.segments = segments
        self.radius = Constants.WIDTH if radius is None else radius
        self.half_height = self.tex_h / 2.0
        self.camera_distance = (Constants.HEIGHT / 2.0) / math.tan(math.radians(Constants.FOV / 2))
        self.far_plane = 100000.0

        self.bend_end_x = Constants.WIDTH - self.radius * (1.0 - math.cos(sweep))
        self.bend_end_z = -self.radius * math.sin(sweep)
        tan_h = math.tan(math.radians(Constants.FOV / 2)) * (Constants.WIDTH / Constants.HEIGHT)
        self.left_x = Constants.WIDTH / 2.0 - (self.camera_distance - self.bend_end_z) * tan_h
        bend_len = self.radius * sweep
        flat_len = max(0.0, self.bend_end_x - self.left_x)
        track_len = bend_len + flat_len
        self.bend_fraction = bend_len / track_len
        self.window = track_len / self.tex_w
        self.scroll = -self.window

    def update(self):
        if self.scroll < 1.0:
            self.scroll = min(1.0, self.scroll + MultiPetsciiImageManager.SPEED)

    def _curve_point(self, s):
        if s <= self.bend_fraction:
            theta = (s / self.bend_fraction) * self.sweep
            return (Constants.WIDTH - self.radius * (1.0 - math.cos(theta)),
                    -self.radius * math.sin(theta))
        p = (s - self.bend_fraction) / (1.0 - self.bend_fraction)
        return (self.bend_end_x + p * (self.left_x - self.bend_end_x), self.bend_end_z)

    def draw(self):
        window_width, window_height = pygame.display.get_surface().get_size()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, window_width / window_height, 1.0, self.far_plane)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(-Constants.WIDTH / 2.0, -Constants.HEIGHT / 2.0, -self.camera_distance)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glDepthRange(0.999, 1.0)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        center_y = Constants.HEIGHT / 2.0
        yy = center_y - 6*24
        glBegin(GL_QUAD_STRIP)
        for i in range(self.segments + 1):
            s = i / self.segments
            x, z = self._curve_point(s)
            u = self.scroll + (1.0 - s) * self.window
            glTexCoord2f(u, 0.0); glVertex3f(x, yy + self.half_height, z)
            glTexCoord2f(u, 1.0); glVertex3f(x, yy - self.half_height, z)
        glEnd()
        glDepthRange(0.0, 1.0)
        glDisable(GL_BLEND)

    def _upload(self, surface):
        data = pygame.image.tobytes(surface, "RGBA")
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, [0.0, 0.0, 0.0, 0.0])
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(),
                     surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return texture
