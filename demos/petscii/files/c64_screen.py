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
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.globals import Constants
from demos.petscii.files.mesh import PetsciiMesh
from demos.petscii.files.typer import Typer


class C64Screen:

    START_Z = -34 * 6
    TARGET_Z = -5
    ZOOM_SPEED = 1.6
    FAR_PLANE = 300.0

    HEADER2_OFFSET = 45
    HEADER3_OFFSET = 95

    def __init__(self):
        self.z = C64Screen.START_Z
        self.color = list(Constants.PALETTE[11])
        self.half_width = Constants.HALF_WIDTH
        self.half_height = Constants.HALF_WIDTH * Constants.HEIGHT / Constants.WIDTH
        self.inset_w = self.half_width * 0.8
        self.inset_h = self.half_height * 0.8

        font_size = self.font_size = Constants.WIDTH // Constants.COLUMNS
        start_x = (Constants.WIDTH - len(Constants.HEADER) * font_size) // 2
        start_x2 = (Constants.WIDTH - len(Constants.HEADER2) * font_size) // 2
        self.screen_surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.header_typer1 = Typer(0, Constants.HEADER,
                                   self.screen_surface, start_x, font_size, font_size)
        self.header_typer2 = Typer(C64Screen.HEADER2_OFFSET, Constants.HEADER2,
                                   self.screen_surface, start_x2, 3*font_size, font_size)
        self.header_typer3 = Typer(C64Screen.HEADER3_OFFSET, Constants.HEADER3,
                                   self.screen_surface, Constants.WIDTH*0.006, 5*font_size, font_size)
        self.texture = glGenTextures(1)

        self.mesh = PetsciiMesh(font_size)
        self.mesh_drawn = False
        self.header_start = None

        self.petscii_color = (255, 255, 255)
        self.petscii_texture = glGenTextures(1)
        self.mesh_texture = glGenTextures(1)
        self.petscii_ready = False
        self.petscii_start_frame = 0
        self.petscii_step = 12

        pygame.mixer.init()
        self.wolf = self.load_sound("wolf.mp3")
        self.wolf_background = self.load_sound("wolf-background1.mp3")
        self.music_started = False

        self.header_typers = (self.header_typer1, self.header_typer2, self.header_typer3)
        # the mesh appears once every header has finished typing
        self.mesh_start_frame = max(t.start_frame + len(t.text) * t.speed
                                    for t in self.header_typers)

    def update(self, frame):
        if self.z < C64Screen.TARGET_Z:
            self.z = min(C64Screen.TARGET_Z, self.z + C64Screen.ZOOM_SPEED)
        if frame > 20:
            self.change_color_rgb(frame, amplitude=127.5, offset=127.5)

    def render(self, frame):
        glDisable(GL_TEXTURE_2D)
        self._begin_3d()
        glColor3f(*self.gl_color())
        glBegin(GL_QUADS)
        glVertex3f(-self.half_width, self.half_height, self.z)
        glVertex3f(self.half_width, self.half_height, self.z)
        glVertex3f(self.half_width, -self.half_height, self.z)
        glVertex3f(-self.half_width, -self.half_height, self.z)
        glEnd()

        self.draw_background()
        if self.arrived():
            self.begin_headers(frame)
            self.start_music()
            self.draw_header(frame)
            self.draw_mesh(frame)

        glEnable(GL_TEXTURE_2D)

    def arrived(self):
        return self.z >= C64Screen.TARGET_Z

    def begin_headers(self, frame):
        if self.header_start is not None:
            return
        self.header_start = frame
        self.header_typer1.start_frame = frame
        self.header_typer2.start_frame = frame + C64Screen.HEADER2_OFFSET
        self.header_typer3.start_frame = frame + C64Screen.HEADER3_OFFSET
        self.mesh_start_frame = max(t.start_frame + len(t.text) * t.speed
                                    for t in self.header_typers)

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, Constants.WIDTH / Constants.HEIGHT, 0.1,
                       C64Screen.FAR_PLANE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, Constants.CAMERA_Z)

    def load_sound(self, filename):
        path = os.path.join(os.path.dirname(__file__), "resources", filename)
        return pygame.mixer.Sound(path)

    def start_music(self):
        if self.music_started:
            return
        self.wolf.play()
        self.wolf_background.play()
        self.music_started = True

    def gl_color(self):
        return tuple(channel / 255 for channel in self.color)

    def change_color_rgb(self, frame, amplitude, offset):
        t = (frame - 20) / 6
        r = int(amplitude * math.sin(t) + offset)
        g = int(amplitude * math.sin(t + 2 * math.pi / 3) + offset)
        b = int(amplitude * math.sin(t + 4 * math.pi / 3) + offset)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self.color = r, g, b

    def draw_background(self, color=(0, 0, 0)):
        glColor3f(*color)
        z = self.z + 0.01  # nudge towards the camera so it sits on top of the border
        glBegin(GL_QUADS)
        glVertex3f(-self.inset_w, self.inset_h, z)
        glVertex3f(self.inset_w, self.inset_h, z)
        glVertex3f(self.inset_w, -self.inset_h, z)
        glVertex3f(-self.inset_w, -self.inset_h, z)
        glEnd()

    def draw_header(self, frame):
        for typer in self.header_typers:
            typer.type(frame)

        self._upload(self.screen_surface)
        z = self.z + 0.02  # just in front of the black screen
        glEnable(GL_TEXTURE_2D)
        glColor3f(*self.gl_color())
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.inset_w, self.inset_h, z)
        glTexCoord2f(1, 0); glVertex3f(self.inset_w, self.inset_h, z)
        glTexCoord2f(1, 1); glVertex3f(self.inset_w, -self.inset_h, z)
        glTexCoord2f(0, 1); glVertex3f(-self.inset_w, -self.inset_h, z)
        glEnd()

    def draw_mesh(self, frame):
        if not self.mesh_drawn and frame > self.mesh_start_frame:
            self._upload(self.mesh.text_surface("PETSCII", self.petscii_color),
                         self.petscii_texture)
            self._upload(self.mesh.lattice_surface(), self.mesh_texture)
            self.mesh_drawn = True
            self.petscii_ready = True
            self.petscii_start_frame = frame

        if not self.petscii_ready:
            return

        z = self.z + 0.03
        cell = self.font_size * self.mesh.stretch / Constants.WIDTH * (2 * self.inset_w)
        x_offset = self.petscii_offset(frame - self.petscii_start_frame) * cell
        self.draw_layer(self.petscii_texture, self.inset_w, self.inset_h, z,
                        (1.0, 1.0, 1.0), x_offset)
        self.draw_layer(self.mesh_texture, self.inset_w, self.inset_h, z + 0.01,
                        self.gl_color())

    def draw_layer(self, texture, inset_w, inset_h, z, color, x_offset=0.0):
        glBindTexture(GL_TEXTURE_2D, texture)
        glColor3f(*color)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        left = -inset_w + x_offset
        right = inset_w + x_offset
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(left, inset_h, z)
        glTexCoord2f(1, 0); glVertex3f(right, inset_h, z)
        glTexCoord2f(1, 1); glVertex3f(right, -inset_h, z)
        glTexCoord2f(0, 1); glVertex3f(left, -inset_h, z)
        glEnd()
        glDisable(GL_BLEND)

    def petscii_offset(self, frames):
        steps = frames // self.petscii_step
        if steps < 2:
            return -steps
        steps -= 2
        phase = steps % 8
        if phase < 4:
            return -2 + phase
        return 2 - (phase - 4)

    def _upload(self, surface, texture=None):
        if texture is None:
            texture = self.texture
        data = pygame.image.tobytes(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
