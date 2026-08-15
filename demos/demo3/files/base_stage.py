from OpenGL.GL import *


class BaseStage:
    """Common scaffolding shared by every demo3 stage.

    A stage owns whatever GL resources it needs, advances itself and draws a
    single frame in :meth:`render`, tells the front-end when it is finished via
    the :attr:`done` property, and frees its GL objects in :meth:`destroy`. The
    window/context lifetime is owned by the front-end (see main.py), not here.
    """

    def __init__(self, win_w, win_h, res_path, fov):
        self.win_w = win_w
        self.win_h = win_h
        self.res_path = res_path
        self.fov = fov
        self.frame = 0

    def make_texture(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return tex

    def fill_screen(self, r, g, b, alpha):
        """Draw a screen-covering quad in clip space (identity matrices) with the
        given colour/alpha. Used for fade-to/from-black transitions. Assumes the
        caller has enabled blending when ``alpha < 1``."""
        if alpha <= 0.0:
            return
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor4f(r, g, b, alpha)
        glBegin(GL_QUADS)
        glVertex2f(-1.0, -1.0)
        glVertex2f(1.0, -1.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    @property
    def done(self):
        return False

    def destroy(self):
        pass
