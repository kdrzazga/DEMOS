import pygame
from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
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
    glOrtho,
    glPopMatrix,
    glPushMatrix,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex2f,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.globals import Constants


class TiltScreen:
    """Presents a pygame surface as an OpenGL quad, flat or with one edge tilted back.

    The surface is uploaded to a texture each frame. tilt() swings the moving edge back
    in z and shrink() slides it across towards the opposite side; both take a 0..1
    progress, so the caller only decides the pace. move_right_edge and move_left_edge
    then draw with that state, keeping the opposite edge pinned to z = 0.
    """

    TILT_DEPTH = -1.8

    def __init__(self, width, height, half_width=Constants.HALF_WIDTH,
                 camera_z=Constants.CAMERA_Z):
        self.width = width
        self.height = height
        self.half_width = half_width
        self.half_height = half_width * height / width
        self.camera_z = camera_z
        self.texture = glGenTextures(1)
        self.depth = 0.0
        self.slide = 0.0

    def reset(self):
        """Return the moving edge to the flat screen plane."""
        self.depth = 0.0
        self.slide = 0.0

    def tilt(self, progress):
        """Swing the moving edge back in z, progress 0 (flat) .. 1 (fully tilted)."""
        self.depth = TiltScreen.TILT_DEPTH * min(1.0, progress)

    def shrink(self, progress):
        """Slide the moving edge across to the far side, progress 0 .. 1 (collapsed)."""
        self.slide = min(1.0, progress)

    def presence(self):
        away = max(self.depth / TiltScreen.TILT_DEPTH, self.slide)
        return max(0.0, min(1.0, 1.0 - away))

    def draw_flat(self, surface):
        """Fill the window with the surface, untilted (the 2D presentation)."""
        self._upload(surface)
        self._begin_2d()
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(self.width, 0)
        glTexCoord2f(1, 1); glVertex2f(self.width, self.height)
        glTexCoord2f(0, 1); glVertex2f(0, self.height)
        glEnd()
        self._end_2d()

    def move_right_edge(self, surface):
        """Draw with the right edge tilted; the left edge stays at (-half_width, 0)."""
        hw, hh = self.half_width, self.half_height
        edge_x = hw - 2 * hw * self.slide
        self._draw_tilted(surface,
                          (-hw, hh, 0.0), (edge_x, hh, self.depth),
                          (edge_x, -hh, self.depth), (-hw, -hh, 0.0))

    def move_left_edge(self, surface):
        """Draw with the left edge tilted; the right edge stays at (half_width, 0)."""
        hw, hh = self.half_width, self.half_height
        edge_x = -hw + 2 * hw * self.slide
        self._draw_tilted(surface,
                          (edge_x, hh, self.depth), (hw, hh, 0.0),
                          (hw, -hh, 0.0), (edge_x, -hh, self.depth))

    def _draw_tilted(self, surface, top_left, top_right, bottom_right, bottom_left):
        self._upload(surface)
        self._begin_3d()
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(*top_left)
        glTexCoord2f(1, 0); glVertex3f(*top_right)
        glTexCoord2f(1, 1); glVertex3f(*bottom_right)
        glTexCoord2f(0, 1); glVertex3f(*bottom_left)
        glEnd()

    def _upload(self, surface):
        data = pygame.image.tobytes(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    def _begin_2d(self):
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def _end_2d(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, self.width / self.height, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.camera_z)
