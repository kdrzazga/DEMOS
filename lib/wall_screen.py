import numpy
from OpenGL.GL import *


class ScreenFront:

    def __init__(self, corners, normal):
        center = (corners[0] + corners[2]) * 0.5
        self.center = numpy.array((*center, 1.0))
        self.normal = numpy.array((*normal, 0.0))

    def faces_viewer(self):
        modelview = numpy.array(glGetDoublev(GL_MODELVIEW_MATRIX), dtype=numpy.float64).reshape(4, 4)
        center_from_viewer = (self.center @ modelview)[:3]
        normal_from_viewer = (self.normal @ modelview)[:3]
        return float(center_from_viewer @ normal_from_viewer) < 0.0


class WallScreen:

    def __init__(self, face, across, rise, width):
        self.face = face
        self.across = across
        self.rise = rise
        self.width = width
        self.height = 0.0
        self.wall_offset = 0.45
        self.glow_lift = 0.05
        self.glow_spread = (1.06, 1.08)
        self.glow_strength = 0.35
        self.corners = None
        self.front = None

    def place(self, height):
        self.height = height
        self.corners = (self.face.point(self.across, self.rise, self.wall_offset),
                        self.face.point(self.across + self.width, self.rise, self.wall_offset),
                        self.face.point(self.across + self.width, self.rise + height, self.wall_offset),
                        self.face.point(self.across, self.rise + height, self.wall_offset))
        self.front = ScreenFront(self.corners, self.face.normal)

    @property
    def covered_rectangle(self):
        return self.across, self.rise, self.width, self.height

    def draw_picture(self, texture_id, glow_color):
        if not self.front.faces_viewer():
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glColor4f(*glow_color, self.glow_strength)
        self._quad(self._glow_corners())
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        self._quad(self.corners)
        glPopAttrib()

    def _glow_corners(self):
        bottom_left, bottom_right, _, top_left = self.corners
        center = (self.corners[0] + self.corners[2]) * 0.5 + self.face.normal * self.glow_lift
        half_across = (bottom_right - bottom_left) * (0.5 * self.glow_spread[0])
        half_up = (top_left - bottom_left) * (0.5 * self.glow_spread[1])
        return (center - half_across - half_up, center + half_across - half_up,
                center + half_across + half_up, center - half_across + half_up)

    @staticmethod
    def _quad(corners):
        glBegin(GL_QUADS)
        for corner, (u, v) in zip(corners, ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))):
            glTexCoord2f(u, v)
            glVertex3f(*corner)
        glEnd()
