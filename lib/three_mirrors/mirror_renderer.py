import numpy
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
    glClipPlane,
    glColorMask,
    glDepthFunc,
    glDepthMask,
    glDepthRange,
    glDisable,
    glEnable,
    glGetDoublev,
    glMultMatrixf,
    glPopMatrix,
    glPushMatrix,
    glStencilFunc,
    glStencilOp,
)

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


class ReflectorSet:

    def __init__(self, reflectors):
        self.reflectors = list(reflectors)
        self.corner_block = numpy.array([[(*corner, 1.0) for corner in reflector.corners()]
                                         for reflector in self.reflectors], dtype=numpy.float64)
        planes = numpy.array([reflector.plane_equation() for reflector in self.reflectors], dtype=numpy.float64)
        self.normals = planes[:, :3]
        self.offsets = planes[:, 3]

    def __len__(self):
        return len(self.reflectors)

    def facing_indices(self, point):
        signed_distances = self.normals @ numpy.array(tuple(point)) - self.offsets
        return numpy.nonzero(signed_distances > 0.0)[0]


class ScreenProjector:

    def __init__(self):
        self.modelview = numpy.array(glGetDoublev(GL_MODELVIEW_MATRIX), dtype=numpy.float64).reshape(4, 4)
        self.projection = numpy.array(glGetDoublev(GL_PROJECTION_MATRIX), dtype=numpy.float64).reshape(4, 4)
        self.viewport = ScreenRegion.of_viewport()
        self.nearest_depth = 1e-4

    def regions_of(self, corner_block):
        if len(corner_block) == 0:
            return []
        clip = corner_block @ self.modelview @ self.projection
        depth = clip[..., 3]
        in_front = numpy.all(depth > self.nearest_depth, axis=1)
        safe_depth = numpy.where(depth > self.nearest_depth, depth, 1.0)
        window_x = self.viewport.left + (clip[..., 0] / safe_depth + 1.0) * 0.5 * self.viewport.width
        window_y = self.viewport.bottom + (clip[..., 1] / safe_depth + 1.0) * 0.5 * self.viewport.height
        lefts = numpy.floor(window_x.min(axis=1))
        rights = numpy.ceil(window_x.max(axis=1))
        bottoms = numpy.floor(window_y.min(axis=1))
        tops = numpy.ceil(window_y.max(axis=1))
        regions = []
        for index in range(len(corner_block)):
            if in_front[index]:
                region = ScreenRegion(lefts[index], bottoms[index],
                                      rights[index] - lefts[index], tops[index] - bottoms[index])
                regions.append(region.clamped_to(self.viewport))
            else:
                regions.append(self.viewport)
        return regions


class MirrorRenderer:

    def __init__(self, max_reflections, reflection_limit):
        self.max_reflections = max_reflections
        self.reflection_limit = reflection_limit
        self.reflection_budget = 64
        self.nested_reflection_budget = 2
        self.screen_blur = ScreenBlur()

    def change_reflections(self, step):
        self.max_reflections = min(max(self.max_reflections + step, 0), self.reflection_limit)

    def render(self, reflector_set, scene, eye):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_STENCIL_TEST)
        self._render_world(reflector_set, scene, eye, StencilLevel(0), None)
        glDisable(GL_STENCIL_TEST)

    def _budget_at(self, level):
        return self.reflection_budget if level.depth == 0 else self.nested_reflection_budget

    def _render_world(self, reflector_set, scene, virtual_eye, level, index_behind):
        scene.illuminate()
        facing = [index for index in reflector_set.facing_indices(virtual_eye) if index != index_behind]
        chosen = []
        if level.depth < self.max_reflections:
            chosen = self._choose_reflections(reflector_set, facing, level)
        for index, region in chosen:
            self._render_through(index, region, reflector_set, scene, virtual_eye, level)
        level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        scene.draw()
        reflected = {index for index, _ in chosen}
        for index in facing:
            if index not in reflected:
                reflector_set.reflectors[index].draw_glass()

    def _choose_reflections(self, reflector_set, facing, level):
        regions = ScreenProjector().regions_of(reflector_set.corner_block[facing])
        visible = [(index, region) for index, region in zip(facing, regions) if not region.is_empty()]
        visible.sort(key=lambda pair: pair[1].area(), reverse=True)
        return visible[:self._budget_at(level)]

    def _render_through(self, index, region, reflector_set, scene, virtual_eye, level):
        reflector = reflector_set.reflectors[index]
        inner_level = level.deeper()
        self._carve_window(reflector, level)
        self._push_depth_to_far(reflector, inner_level)
        glPushMatrix()
        glClipPlane(level.clip_plane_slot(), reflector.behind_clip_plane())
        glEnable(level.clip_plane_slot())
        glMultMatrixf(reflector.reflection_matrix())
        self._render_world(reflector_set, scene, reflector.reflect_point(virtual_eye), inner_level, index)
        glPopMatrix()
        glDisable(level.clip_plane_slot())
        scene.illuminate()
        if reflector.is_blurred():
            self.screen_blur.apply(reflector.blur_radius_pixels(), inner_level, region)
        self._glaze_window(reflector, inner_level)
        self._close_window(reflector, inner_level)

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
