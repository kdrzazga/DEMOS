import math

from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_CLIP_PLANE0,
    GL_COLOR_BUFFER_BIT,
    GL_CURRENT_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_FOG,
    GL_KEEP,
    GL_LIGHTING,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGB,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_BIT,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    GL_VIEWPORT,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor4f,
    glCopyTexSubImage2D,
    glDepthMask,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glGetIntegerv,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glStencilOp,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2f,
)


class ScreenRegion:

    def __init__(self, left, bottom, width, height):
        self.left = int(left)
        self.bottom = int(bottom)
        self.width = max(int(width), 0)
        self.height = max(int(height), 0)

    @staticmethod
    def of_viewport():
        return ScreenRegion(*glGetIntegerv(GL_VIEWPORT))

    @staticmethod
    def around(window_points):
        horizontal = [point[0] for point in window_points]
        vertical = [point[1] for point in window_points]
        left = math.floor(min(horizontal))
        bottom = math.floor(min(vertical))
        return ScreenRegion(left, bottom, math.ceil(max(horizontal)) - left, math.ceil(max(vertical)) - bottom)

    def is_empty(self):
        return self.width == 0 or self.height == 0

    def expanded(self, margin):
        reach = math.ceil(margin) + 1
        return ScreenRegion(self.left - reach, self.bottom - reach, self.width + 2 * reach, self.height + 2 * reach)

    def clamped_to(self, bounds):
        left = max(self.left, bounds.left)
        bottom = max(self.bottom, bounds.bottom)
        right = min(self.left + self.width, bounds.left + bounds.width)
        top = min(self.bottom + self.height, bounds.bottom + bounds.height)
        return ScreenRegion(left, bottom, right - left, top - bottom)


class ScreenBlur:

    def __init__(self):
        self.texture = None
        self.texture_size = None
        self.rings = 2
        self.directions_per_ring = 8
        self.clip_plane_count = 6
        self.saved_state = (GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT
                            | GL_CURRENT_BIT | GL_TEXTURE_BIT)

    def apply(self, radius_pixels, stencil_level, region):
        viewport = ScreenRegion.of_viewport()
        area = region.expanded(radius_pixels).clamped_to(viewport)
        if area.is_empty():
            return
        glPushAttrib(self.saved_state)
        self._prepare_texture(viewport.width, viewport.height)
        glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, area.left, area.bottom, area.width, area.height)
        stencil_level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        for slot in range(self.clip_plane_count):
            glDisable(GL_CLIP_PLANE0 + slot)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        self._enter_screen_space(viewport)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for sample_index, (offset_x, offset_y) in enumerate(self._sample_offsets(radius_pixels)):
            glColor4f(1.0, 1.0, 1.0, 1.0 / (sample_index + 1))
            self._draw_shifted_area(area, viewport, offset_x, offset_y)
        self._leave_screen_space()
        glPopAttrib()

    def _prepare_texture(self, width, height):
        if self.texture is None:
            self.texture = glGenTextures(1)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        if self.texture_size != (width, height):
            self.texture_size = (width, height)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

    def _sample_offsets(self, radius_pixels):
        offsets = [(0.0, 0.0)]
        for ring in range(1, self.rings + 1):
            ring_radius = radius_pixels * ring / self.rings
            twist = math.pi * ring / self.directions_per_ring
            for direction in range(self.directions_per_ring):
                angle = 2.0 * math.pi * direction / self.directions_per_ring + twist
                offsets.append((ring_radius * math.cos(angle), ring_radius * math.sin(angle)))
        return offsets

    def _draw_shifted_area(self, area, viewport, offset_x, offset_y):
        texture_right = area.width / viewport.width
        texture_top = area.height / viewport.height
        shift_u = offset_x / viewport.width
        shift_v = offset_y / viewport.height
        screen_left = area.left - viewport.left
        screen_bottom = area.bottom - viewport.bottom
        glBegin(GL_QUADS)
        for corner_u, corner_v in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
            glTexCoord2f(corner_u * texture_right + shift_u, corner_v * texture_top + shift_v)
            glVertex2f(screen_left + corner_u * area.width, screen_bottom + corner_v * area.height)
        glEnd()

    def _enter_screen_space(self, viewport):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, viewport.width, 0.0, viewport.height, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def _leave_screen_space(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
