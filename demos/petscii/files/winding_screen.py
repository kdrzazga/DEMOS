from OpenGL.GL import (
    GL_QUADS,
    GL_TEXTURE_2D,
    glBegin,
    glColor3f,
    glEnable,
    glEnd,
    glTexCoord2f,
    glVertex3f,
)

from demos.petscii.files.c64_base_screen import C64BaseScreen
from demos.petscii.files.globals import Constants
from demos.petscii.files.screen_winding_anim import ScreenWindingAnim


class WindingScreen(C64BaseScreen):

    def __init__(self):
        super().__init__()
        self.winding = ScreenWindingAnim(self.screen_surface,
                                         char_size=Constants.WIDTH // Constants.COLUMNS,
                                         border=0)

    def update(self, frame):
        super().update(frame)
        if self.arrived():
            self.winding.update(1.0 / Constants.FPS)

    def draw_header(self, frame):
        self.screen_surface.fill((0, 0, 0))
        self.winding.draw()
        self._upload(self.screen_surface)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.inset_w, self.inset_h, 0.0)
        glTexCoord2f(1, 0); glVertex3f(self.inset_w, self.inset_h, 0.0)
        glTexCoord2f(1, 1); glVertex3f(self.inset_w, -self.inset_h, 0.0)
        glTexCoord2f(0, 1); glVertex3f(-self.inset_w, -self.inset_h, 0.0)
        glEnd()
