import math

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from demos.retro_glasses.graffiti.thanks_for_watching_graffiti import ThanksForWatchingGraffiti
from lib.graffitti.swaying_surface import SwayingSurface


class ThanksGraffitiBanner:
    def __init__(self, area, screen_width, screen_height):
        self.area = area
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.alpha = 0.0
        self.seconds = 0.0
        self.field_of_view = 30.0
        self.camera_distance = 6.0
        self.area_fill_share = 0.9
        self.graffiti = ThanksForWatchingGraffiti()
        self.surface = SwayingSurface(*self._surface_size())
        self.surface.yaw_amplitude_degrees = 8.0
        self.surface.pitch_amplitude_degrees = 4.0

    @property
    def area_width(self):
        return self.area.right - self.area.left

    @property
    def area_height(self):
        return self.area.bottom - self.area.top

    @property
    def duration_seconds(self):
        return self.graffiti.duration_seconds

    def _surface_size(self):
        visible_height = 2.0 * self.camera_distance * math.tan(math.radians(self.field_of_view / 2.0))
        fitting_aspect_ratio = min(self.graffiti.aspect_ratio, self.area_width / self.area_height)
        surface_width = visible_height * self.area_fill_share * fitting_aspect_ratio
        return surface_width, surface_width / self.graffiti.aspect_ratio

    def update(self, seconds):
        self.seconds = seconds

    def _fade_surface(self):
        self.surface.colors[:, :3] *= self.alpha
        self.surface.colors[:, 3] = self.alpha

    def _begin_area_camera(self):
        glViewport(0, round(self.screen_height - self.area.bottom), self.screen_width, round(self.area_height))
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.area_height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

    @staticmethod
    def _end_area_camera():
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw(self):
        if self.alpha <= 0.0:
            return
        self.graffiti.render(self.seconds)
        self.surface.update(self.seconds)
        self._fade_surface()
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        self._begin_area_camera()
        self.surface.render(self.graffiti.texture)
        self._end_area_camera()
        glPopAttrib()
