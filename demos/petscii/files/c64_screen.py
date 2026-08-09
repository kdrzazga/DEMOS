import math
import os

import pygame
from OpenGL.GL import (
    GL_MODELVIEW,
    GL_NEAREST,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_BLEND,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
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
    glMultMatrixf,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.c64_base_screen import C64BaseScreen
from demos.petscii.files.globals import Constants
from demos.petscii.files.mesh import PetsciiMesh
from demos.petscii.files.typer import Typer


class C64Screen(C64BaseScreen):

    START_Z = -34 * 6
    TARGET_Z = -5
    ZOOM_SPEED = 1.6
    FINALE_ZOOM_SPEED = 0.04
    FAR_PLANE = 300.0
    TILT_DEPTH = -5.0

    HEADER2_OFFSET = 45
    HEADER3_OFFSET = 95

    def __init__(self):
        super().__init__()

    def draw_mesh(self, frame):
        if not self.mesh_drawn and frame > self.mesh_start_frame:
            self._upload(self.mesh.lattice_surface(), self.mesh_texture)
            self.mesh_drawn = True
            self.caption_ready = True

        if not self.caption_ready:
            return

        if self.mesh_caption != self.drawn_caption:
            self.build_caption(frame)

        z = 0.0
        cell = self.font_size * self.mesh.stretch / Constants.WIDTH * (2 * self.inset_w)
        x_offset = self.caption_offset(frame - self.caption_start_frame,
                                       self.caption_amplitude) * cell
        self.draw_layer(self.caption_texture, self.inset_w, self.inset_h, z,
                        (1.0, 1.0, 1.0), x_offset)
        self.draw_layer(self.mesh_texture, self.inset_w, self.inset_h, z + 0.01,
                        self.gl_color())

    def build_caption(self, frame):
        self._upload(self.mesh.text_surface(self.mesh_caption, self.caption_color),
                     self.caption_texture)
        self.drawn_caption = self.mesh_caption
        self.caption_start_frame = frame
        width = self.mesh.caption_width(self.mesh_caption)
        self.caption_amplitude = max(1, (Constants.COLUMNS - 2 - width) // 2 - 1)
