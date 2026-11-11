from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_LIGHTING,
    GL_ONE,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TRUE,
    glBindTexture,
    glBlendFunc,
    glColor4f,
    glDepthMask,
    glDisable,
    glEnable,
    glPopAttrib,
    glPushAttrib,
)

from demos.retro_neons.scene_mirror import SceneMirror
from lib.urban.neon.caption_screen import CaptionScreen
from lib.wall_screen import ScreenFront


class MatteCaptionScreen(CaptionScreen):

    def __init__(self, face, across, rise, width, height, text, tube_color):
        super().__init__(face, across, rise, width, height, text, tube_color)
        self.front = ScreenFront(self.corners, self.facing)

    def draw(self):
        if not self.front.faces_viewer():
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glColor4f(1.0, 1.0, 1.0, self.glow_strength)
        with SceneMirror().readable_texturing():
            self._quad(self._glow_corners())
            glDepthMask(GL_TRUE)
            glDisable(GL_BLEND)
            glColor4f(1.0, 1.0, 1.0, 1.0)
            self._quad(self.corners)
        glPopAttrib()
