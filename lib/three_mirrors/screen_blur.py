import math

from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_CLIP_PLANE0,
    GL_DEPTH_TEST,
    GL_FALSE,
    GL_KEEP,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGB,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRUE,
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
    glIsEnabled,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glPopMatrix,
    glPushMatrix,
    glStencilOp,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2f,
)


class ScreenBlur:

    def __init__(self):
        self.texture = None
        self.texture_size = None
        self.rings = 2
        self.directions_per_ring = 8
        self.clip_plane_count = 6

    def apply(self, radius_pixels, stencil_level):
        left, bottom, width, height = (int(value) for value in glGetIntegerv(GL_VIEWPORT))
        self._prepare_texture(width, height)
        glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, left, bottom, width, height)
        stencil_level.restrict_to()
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        enabled_clip_planes = self._suspend_clip_planes()
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        self._enter_screen_space()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for sample_index, (offset_x, offset_y) in enumerate(self._sample_offsets(radius_pixels)):
            glColor4f(1.0, 1.0, 1.0, 1.0 / (sample_index + 1))
            self._draw_shifted_screen(offset_x / width, offset_y / height)
        glDisable(GL_BLEND)
        self._leave_screen_space()
        glDisable(GL_TEXTURE_2D)
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        self._resume_clip_planes(enabled_clip_planes)

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

    def _draw_shifted_screen(self, shift_u, shift_v):
        glBegin(GL_QUADS)
        for x, y in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
            glTexCoord2f(x + shift_u, y + shift_v)
            glVertex2f(x, y)
        glEnd()

    def _enter_screen_space(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def _leave_screen_space(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def _suspend_clip_planes(self):
        enabled = [GL_CLIP_PLANE0 + slot for slot in range(self.clip_plane_count)
                   if glIsEnabled(GL_CLIP_PLANE0 + slot)]
        for clip_plane in enabled:
            glDisable(clip_plane)
        return enabled

    def _resume_clip_planes(self, enabled_clip_planes):
        for clip_plane in enabled_clip_planes:
            glEnable(clip_plane)
