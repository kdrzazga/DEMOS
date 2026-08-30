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
from lib.multi_petscii_image import MultiPetsciiImage



class MultiPetsciiImageManager:

    SPEED = 0.0015

    def __init__(self, char_size=24, sweep=math.pi / 2, segments=80, window=0.4, radius=None):
        self.captions = MultiPetsciiImage(
            (Caption1(char_size), Caption2(char_size), Caption3(char_size), Caption4(char_size), Caption5(char_size)))
        self.tex_w, self.tex_h = self.captions.size()
        surface = pygame.Surface((self.tex_w, self.tex_h), pygame.SRCALPHA)
        self.captions.render(surface, transparent_space=True)
        self.texture = self._upload(surface)

        self.sweep = sweep
        self.segments = segments
        self.radius = window * self.tex_w / self.sweep if radius is None else radius
        self.window = self.radius * self.sweep / self.tex_w
        self.half_height = self.tex_h / 2.0
        self.camera_distance = (Constants.HEIGHT / 2.0) / math.tan(math.radians(Constants.FOV / 2))
        self.far_plane = 100000.0
        self.scroll = -self.window

    def update(self):
        if self.scroll < 1.0:
            self.scroll = min(1.0, self.scroll + MultiPetsciiImageManager.SPEED)

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
        glDisable(GL_DEPTH_TEST)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        center_y = Constants.HEIGHT / 2.0
        glBegin(GL_QUAD_STRIP)
        for i in range(self.segments + 1):
            s = i / self.segments
            theta = s * self.sweep
            x = Constants.WIDTH - self.radius * (1.0 - math.cos(theta))
            z = -self.radius * math.sin(theta)
            u = self.scroll + (1.0 - s) * self.window
            glTexCoord2f(u, 0.0); glVertex3f(x, center_y + self.half_height, z)
            glTexCoord2f(u, 1.0); glVertex3f(x, center_y - self.half_height, z)
        glEnd()
        glEnable(GL_DEPTH_TEST)
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
