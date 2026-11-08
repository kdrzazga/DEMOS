from OpenGL.GL import (
    GL_ALWAYS,
    GL_CLIP_PLANE0,
    GL_DECR,
    GL_EQUAL,
    GL_FALSE,
    GL_INCR,
    GL_KEEP,
    GL_LEQUAL,
    GL_STENCIL_TEST,
    GL_TEXTURE_2D,
    GL_TRUE,
    glClipPlane,
    glColorMask,
    glDepthFunc,
    glDepthMask,
    glDepthRange,
    glDisable,
    glEnable,
    glMultMatrixf,
    glPopMatrix,
    glPushMatrix,
    glStencilFunc,
    glStencilOp,
)

from lib.three_mirrors.mirror import Mirror
from lib.three_mirrors.screen_blur import ScreenBlur


class StencilLevel:

    def __init__(self, depth):
        self.depth = depth
        self.mask = 0xFF

    def deeper(self):
        return StencilLevel(self.depth + 1)

    def restrict_to(self):
        glStencilFunc(GL_EQUAL, self.depth, self.mask)

    def clip_plane_slot(self):
        return GL_CLIP_PLANE0 + self.depth


class MirrorCorner:

    def __init__(self, size):
        self.size = size
        self.mirrors = [
            Mirror.spanning((0.0, 0.0, 0.0), (0.0, size, 0.0), (0.0, 0.0, size)),
            Mirror.spanning((0.0, 0.0, 0.0), (0.0, 0.0, size), (size, 0.0, 0.0)),
            Mirror.spanning((0.0, 0.0, 0.0), (size, 0.0, 0.0), (0.0, size, 0.0)),
        ]
        self.max_reflections = 3
        self.reflection_limit = 5
        self.screen_blur = ScreenBlur()

    def change_reflections(self, step):
        self.max_reflections = min(max(self.max_reflections + step, 0), self.reflection_limit)

    def render(self, scene, eye):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_STENCIL_TEST)
        self._render_world(scene, eye, StencilLevel(0), None)
        glDisable(GL_STENCIL_TEST)

    def _render_world(self, scene, virtual_eye, level, mirror_behind):
        if level.depth < self.max_reflections:
            for mirror in self.mirrors:
                if mirror is not mirror_behind and mirror.faces(virtual_eye):
                    self._render_through(mirror, scene, virtual_eye, level)
        level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        scene.draw()
        for mirror in self.mirrors:
            mirror.draw_frame()

    def _render_through(self, mirror, scene, virtual_eye, level):
        inner_level = level.deeper()
        self._carve_window(mirror, level)
        self._push_depth_to_far(mirror, inner_level)
        glPushMatrix()
        glClipPlane(level.clip_plane_slot(), mirror.behind_clip_plane())
        glEnable(level.clip_plane_slot())
        glMultMatrixf(mirror.reflection_matrix())
        self._render_world(scene, mirror.reflect_point(virtual_eye), inner_level, mirror)
        glPopMatrix()
        glDisable(level.clip_plane_slot())
        if mirror.is_blurred():
            self.screen_blur.apply(mirror.blur_radius_pixels(), inner_level)
        self._glaze_window(mirror, inner_level)
        self._close_window(mirror, inner_level)

    def _carve_window(self, mirror, level):
        level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_INCR)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_FALSE)
        mirror.draw_shape()
        glDepthMask(GL_TRUE)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def _push_depth_to_far(self, mirror, inner_level):
        inner_level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthFunc(GL_ALWAYS)
        glDepthRange(1.0, 1.0)
        mirror.draw_shape()
        glDepthRange(0.0, 1.0)
        glDepthFunc(GL_LEQUAL)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def _glaze_window(self, mirror, inner_level):
        inner_level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glDepthFunc(GL_ALWAYS)
        mirror.draw_glass()
        glDepthFunc(GL_LEQUAL)

    def _close_window(self, mirror, inner_level):
        inner_level.restrict_to()
        glStencilOp(GL_KEEP, GL_DECR, GL_DECR)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthFunc(GL_ALWAYS)
        mirror.draw_shape()
        glDepthFunc(GL_LEQUAL)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
