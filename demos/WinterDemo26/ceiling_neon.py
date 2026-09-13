from OpenGL.GL import *


class CeilingNeon:
    def __init__(self, core_corners, glow_inner, glow_outer, glow_strength=0.55, core_whitening=0.45):
        self.core_corners = tuple(core_corners)
        self.glow_inner = tuple(glow_inner)
        self.glow_outer = tuple(glow_outer)
        self.glow_strength = glow_strength
        self.core_whitening = core_whitening

    def _draw_halo(self, color):
        glDepthMask(GL_FALSE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glBegin(GL_QUADS)
        for corner in range(4):
            following = (corner + 1) % 4
            for point, alpha in ((self.glow_inner[corner], self.glow_strength),
                                 (self.glow_inner[following], self.glow_strength),
                                 (self.glow_outer[following], 0.0),
                                 (self.glow_outer[corner], 0.0)):
                glColor4f(color[0], color[1], color[2], alpha)
                glVertex3f(*point)
        glEnd()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_TRUE)

    def _draw_core(self, color):
        glColor3f(*(channel + (1.0 - channel) * self.core_whitening for channel in color))
        glBegin(GL_QUADS)
        for point in self.core_corners:
            glVertex3f(*point)
        glEnd()

    def glow(self, color: tuple):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        self._draw_halo(color)
        self._draw_core(color)
        glPopAttrib()
