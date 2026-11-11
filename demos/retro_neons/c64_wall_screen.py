from OpenGL.GL import *

from lib.c64_screen import C64Screen


class C64WallScreen:

    def __init__(self, face, across, rise, width, ticker):
        self.face = face
        self.across = across
        self.rise = rise
        self.width = width
        self.height = 0.0
        self.ticker = ticker
        self.wall_offset = 0.45
        self.glow_spread = (1.06, 1.08)
        self.glow_strength = 0.35
        self.c64 = None
        self.corners = None
        self.showing = False

    def prepare(self):
        self.ticker.prepare()
        self.c64 = C64Screen()
        self.height = self.width / self.c64.aspect
        self.corners = (self.face.point(self.across, self.rise, self.wall_offset),
                        self.face.point(self.across + self.width, self.rise, self.wall_offset),
                        self.face.point(self.across + self.width, self.rise + self.height, self.wall_offset),
                        self.face.point(self.across, self.rise + self.height, self.wall_offset))

    @property
    def covered_rectangle(self):
        return self.across, self.rise, self.width, self.height

    def switch_on(self):
        self.showing = True
        self.c64.restart_typing()

    def update(self, seconds):
        if self.showing:
            self.c64.update(seconds)
            self.c64.refresh()
        else:
            self.ticker.update(seconds)

    def draw(self):
        if not self.showing:
            self.ticker.draw()
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.c64.texture_id)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        self._quad(self.corners)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glColor4f(*self.c64.border_color, self.glow_strength)
        self._quad(self._glow_corners())
        glPopAttrib()

    def _glow_corners(self):
        bottom_left, bottom_right, _, top_left = self.corners
        center = (self.corners[0] + self.corners[2]) * 0.5 + self.face.normal * 0.05
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
