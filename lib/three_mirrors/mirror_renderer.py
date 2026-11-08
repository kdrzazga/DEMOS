from OpenGL.GL import (
    GL_ALWAYS,
    GL_CLIP_PLANE0,
    GL_DECR,
    GL_EQUAL,
    GL_FALSE,
    GL_INCR,
    GL_KEEP,
    GL_LEQUAL,
    GL_MODELVIEW_MATRIX,
    GL_PROJECTION_MATRIX,
    GL_STENCIL_TEST,
    GL_TEXTURE_2D,
    GL_TRUE,
    GL_VIEWPORT,
    glClipPlane,
    glColorMask,
    glDepthFunc,
    glDepthMask,
    glDepthRange,
    glDisable,
    glEnable,
    glGetDoublev,
    glGetIntegerv,
    glMultMatrixf,
    glPopMatrix,
    glPushMatrix,
    glStencilFunc,
    glStencilOp,
)
from OpenGL.GLU import gluProject

from lib.three_mirrors.screen_blur import ScreenBlur, ScreenRegion


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


class MirrorRenderer:

    def __init__(self, max_reflections, reflection_limit):
        self.max_reflections = max_reflections
        self.reflection_limit = reflection_limit
        self.screen_blur = ScreenBlur()

    def change_reflections(self, step):
        self.max_reflections = min(max(self.max_reflections + step, 0), self.reflection_limit)

    def render(self, reflectors, scene, eye):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_STENCIL_TEST)
        self._render_world(reflectors, scene, eye, StencilLevel(0), None)
        glDisable(GL_STENCIL_TEST)

    def _render_world(self, reflectors, scene, virtual_eye, level, reflector_behind):
        scene.illuminate()
        if level.depth < self.max_reflections:
            for reflector in reflectors:
                if reflector is not reflector_behind and reflector.faces(virtual_eye):
                    self._render_through(reflector, reflectors, scene, virtual_eye, level)
        level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        scene.draw()

    def _render_through(self, reflector, reflectors, scene, virtual_eye, level):
        inner_level = level.deeper()
        self._carve_window(reflector, level)
        self._push_depth_to_far(reflector, inner_level)
        glPushMatrix()
        glClipPlane(level.clip_plane_slot(), reflector.behind_clip_plane())
        glEnable(level.clip_plane_slot())
        glMultMatrixf(reflector.reflection_matrix())
        self._render_world(reflectors, scene, reflector.reflect_point(virtual_eye), inner_level, reflector)
        glPopMatrix()
        glDisable(level.clip_plane_slot())
        scene.illuminate()
        if reflector.is_blurred():
            self.screen_blur.apply(reflector.blur_radius_pixels(), inner_level, self._screen_region_of(reflector))
        self._glaze_window(reflector, inner_level)
        self._close_window(reflector, inner_level)

    def _screen_region_of(self, reflector):
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        window_points = [gluProject(*corner, modelview, projection, viewport) for corner in reflector.corners()]
        if all(0.0 <= point[2] <= 1.0 for point in window_points):
            return ScreenRegion.around(window_points)
        return ScreenRegion.of_viewport()

    def _carve_window(self, reflector, level):
        level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_INCR)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_FALSE)
        reflector.draw_shape()
        glDepthMask(GL_TRUE)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def _push_depth_to_far(self, reflector, inner_level):
        inner_level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthFunc(GL_ALWAYS)
        glDepthRange(1.0, 1.0)
        reflector.draw_shape()
        glDepthRange(0.0, 1.0)
        glDepthFunc(GL_LEQUAL)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def _glaze_window(self, reflector, inner_level):
        inner_level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glDepthFunc(GL_ALWAYS)
        reflector.draw_glass()
        glDepthFunc(GL_LEQUAL)

    def _close_window(self, reflector, inner_level):
        inner_level.restrict_to()
        glStencilOp(GL_KEEP, GL_DECR, GL_DECR)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthFunc(GL_ALWAYS)
        reflector.draw_shape()
        glDepthFunc(GL_LEQUAL)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
