import math

import numpy
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CURRENT_BIT,
    GL_ENABLE_BIT,
    GL_FLOAT,
    GL_LIGHTING,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TRIANGLE_FAN,
    GL_VERTEX_ARRAY,
    glBlendFunc,
    glColor4f,
    glDisable,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glRotatef,
    glTranslatef,
    glVertexPointer,
)


class TravellingSurface:

    def __init__(self, content, content_center, content_half_size, camera_distance, field_of_view_degrees,
                 aspect_ratio):
        self.content = content
        self.content_center = tuple(float(value) for value in content_center)
        self.content_half_size = content_half_size
        self.screen_half_width = (camera_distance * math.tan(math.radians(field_of_view_degrees / 2.0))
                                  * aspect_ratio)
        self.travel_seconds = 14.0
        self.max_depth = 1.5 * camera_distance
        self.sway_period = 2.6
        self.sway_tilt_degrees = 12.0
        self.sway_roll_degrees = 4.0
        self.sway_bob_height = 0.04 * content_half_size
        self.drawing_starts_at_travel_share = 0.12
        self.drawing_ends_at_travel_share = 0.8
        self.surface_color = (0.0, 0.0, 0.0, 0.5)
        self.surface_margin = 0.07 * content_half_size
        self.surface_depth_offset = 0.002 * content_half_size
        self.time = 0.0

    def restart(self):
        self.set_time(0.0)
        self.content.restart()

    def update(self, delta_seconds):
        self.set_time(self.time + delta_seconds)

    def set_time(self, seconds):
        self.time = seconds
        self.content.time = self.drawing_progress() * self.content.total_seconds()

    def travel_progress(self):
        return max(0.0, min(1.0, self.time / self.travel_seconds))

    def drawing_progress(self):
        drawing_share = self.drawing_ends_at_travel_share - self.drawing_starts_at_travel_share
        return max(0.0, min(1.0, (self.travel_progress() - self.drawing_starts_at_travel_share) / drawing_share))

    def has_started(self):
        return self.time > 0.0

    def is_finished(self):
        return self.time >= self.travel_seconds

    def is_on_screen(self):
        return self.has_started() and not self.is_finished()

    def depth(self):
        return -self.max_depth * math.sin(math.pi * self.travel_progress())

    def draw(self):
        if not self.is_on_screen():
            return
        surface_half_size = self.content_half_size + self.surface_margin
        start_x = self.screen_half_width + surface_half_size
        sway_phase = 2.0 * math.pi * self.time / self.sway_period
        x = start_x - 2.0 * start_x * self.travel_progress()
        y = self.sway_bob_height * math.sin(sway_phase)
        content_x, content_y, content_z = self.content_center
        glPushMatrix()
        glTranslatef(x, y, self.depth())
        glRotatef(self.sway_tilt_degrees * math.sin(sway_phase), 0.0, 1.0, 0.0)
        glRotatef(self.sway_roll_degrees * math.sin(0.5 * sway_phase), 0.0, 0.0, 1.0)
        glTranslatef(-content_x, -content_y, -content_z)
        self._draw_surface(surface_half_size)
        self.content.draw()
        glPopMatrix()

    def _surface_corners(self, half_size):
        content_x, content_y, content_z = self.content_center
        surface_z = content_z - self.surface_depth_offset
        return numpy.array([(content_x - half_size, content_y - half_size, surface_z),
                            (content_x + half_size, content_y - half_size, surface_z),
                            (content_x + half_size, content_y + half_size, surface_z),
                            (content_x - half_size, content_y + half_size, surface_z)], dtype=numpy.float32)

    def _draw_surface(self, half_size):
        surface_corners = self._surface_corners(half_size)
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*self.surface_color)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, surface_corners)
        glDrawArrays(GL_TRIANGLE_FAN, 0, len(surface_corners))
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
