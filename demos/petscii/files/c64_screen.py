import math

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
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
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
from demos.petscii.files.typer import Typer


class C64Screen:
    """A coloured rectangle zooming in from the distance between the two noise screens.

    It is as wide as the noise screens, so once it reaches the screen plane its left
    and right edges sit exactly on their outer edges.
    """

    START_Z = -34 * 6
    TARGET_Z = -5
    ZOOM_SPEED = 1
    FAR_PLANE = 300.0

    HEADER_START_FRAME = 850
    HEADER2_START_FRAME = HEADER_START_FRAME + 45

    def __init__(self):
        self.z = C64Screen.START_Z
        self.color = list(Constants.PALETTE[11])
        self.half_width = Constants.HALF_WIDTH
        self.half_height = Constants.HALF_WIDTH * Constants.HEIGHT / Constants.WIDTH

        font_size = Constants.WIDTH // Constants.COLUMNS
        start_x = (Constants.WIDTH - len(Constants.HEADER) * font_size) // 2
        start_x2 = (Constants.WIDTH - len(Constants.HEADER2) * font_size) // 2
        self.screen_surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.header_typer1 = Typer(C64Screen.HEADER_START_FRAME, Constants.HEADER,
                                   self.screen_surface, start_x, font_size, font_size)
        self.header_typer2 = Typer(C64Screen.HEADER2_START_FRAME, Constants.HEADER2,
                                   self.screen_surface, start_x2, 3*font_size, font_size)
        self.header_typer3 = Typer(C64Screen.HEADER2_START_FRAME + 50, Constants.HEADER3,
                                   self.screen_surface, Constants.WIDTH*0.006, 5*font_size, font_size)
        self.texture = glGenTextures(1)

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

        if frame > C64Screen.HEADER_START_FRAME - 50:
            self.draw_background()
            if frame > C64Screen.HEADER_START_FRAME:
                self.draw_header(frame)

        glEnable(GL_TEXTURE_2D)

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, Constants.WIDTH / Constants.HEIGHT, 0.1,
                       C64Screen.FAR_PLANE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, Constants.CAMERA_Z)

    def gl_color(self):
        """self.color (0..255 per channel) as OpenGL floats (0..1)."""
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
        inset_w = self.half_width * 0.8
        inset_h = self.half_height * 0.8
        z = self.z + 0.01  # nudge towards the camera so it sits on top of the border
        glBegin(GL_QUADS)
        glVertex3f(-inset_w, inset_h, z)
        glVertex3f(inset_w, inset_h, z)
        glVertex3f(inset_w, -inset_h, z)
        glVertex3f(-inset_w, -inset_h, z)
        glEnd()

    def draw_header(self, frame):
        """Type the BASIC header onto the black screen and draw it as a textured quad."""
        #self.screen_surface.fill((0, 0, 0))

        for typer in (self.header_typer1, self.header_typer2, self.header_typer3):
            typer.type(frame)

        self._upload(self.screen_surface)
        inset_w = self.half_width * 0.8
        inset_h = self.half_height * 0.8
        z = self.z + 0.02  # just in front of the black screen
        glEnable(GL_TEXTURE_2D)
        glColor3f(*self.gl_color())
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-inset_w, inset_h, z)
        glTexCoord2f(1, 0); glVertex3f(inset_w, inset_h, z)
        glTexCoord2f(1, 1); glVertex3f(inset_w, -inset_h, z)
        glTexCoord2f(0, 1); glVertex3f(-inset_w, -inset_h, z)
        glEnd()

    def _upload(self, surface):
        data = pygame.image.tobytes(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
