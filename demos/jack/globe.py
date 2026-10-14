import math

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from lib.historical_earth import HistoricalEarth
from demos.jack.camera import GlobeCamera
from demos.jack.framings import WORLD
from demos.jack.stage import MapEra


class Globe:
    def __init__(self, screen_width, screen_height, framing=WORLD, era=MapEra.PRE_WAR, radius=6.0,
                 field_of_view=45.0, era_fade_seconds=2.0, light_direction=(0.5, 0.6, 1.0, 0.0)):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = radius
        self.field_of_view = field_of_view
        self.era_fade_seconds = era_fade_seconds
        self.light_direction = light_direction
        self.earth = HistoricalEarth(0.0, 0.0, 0.0, year=era.value, radius=radius, tilt=0.0, spin_speed=0.0,
                                     moon_enabled=False, sign_scale=framing.sign_scale)
        self.era = era
        self.camera = GlobeCamera(framing)
        self.awaited_locations = None

    def show_era(self, era):
        if era != self.era:
            self.era = era
            self.earth.show_year(era.value, self.era_fade_seconds)

    def frame(self, framing, locations):
        if framing is self.camera.target and not self.camera.arrived:
            self.awaited_locations = tuple(locations)
            return self.camera.remaining_seconds()
        seconds = self.camera.glide_to(framing)
        if seconds > 0.0:
            self._take_down_signs(())
            self.awaited_locations = tuple(locations)
        else:
            self._put_up_signs(locations)
        return seconds

    def _take_down_signs(self, kept_labels):
        for label in tuple(self.earth.city_signs):
            if label not in kept_labels:
                self.earth.unmark_city(label)

    def _put_up_signs(self, locations):
        sign_size = self.radius * self.camera.target.sign_scale
        if sign_size != self.earth.sign_size:
            self._take_down_signs(())
            self.earth.sign_size = sign_size
        self._take_down_signs(tuple(location.label for location in locations))
        for location in locations:
            if location.label not in self.earth.city_signs:
                self.earth.mark_location(location.label, location.latitude, location.longitude)

    def update(self, dt):
        self.camera.update(dt)
        if self.awaited_locations is not None and self.camera.arrived:
            self._put_up_signs(self.awaited_locations)
            self.awaited_locations = None
        self.earth.spin = -self.camera.longitude
        self.earth.update(dt)

    def _look_target(self):
        latitude = math.radians(self.camera.latitude)
        reach = self.radius * self.camera.focus
        return 0.0, math.sin(latitude) * reach, math.cos(latitude) * reach

    def draw(self):
        glViewport(0, 0, self.screen_width, self.screen_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.screen_height, 0.1, 400.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
        elevation = math.radians(self.camera.elevation())
        distance = self.camera.distance
        gluLookAt(0.0, math.sin(elevation) * distance, math.cos(elevation) * distance,
                  *self._look_target(), 0.0, 1.0, 0.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        self.earth.draw()
