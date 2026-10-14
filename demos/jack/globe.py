import math

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from lib.historical_earth import HistoricalEarth
from demos.jack.stage import MapEra


class Globe:
    def __init__(self, screen_width, screen_height, era=MapEra.PRE_WAR, radius=6.0, field_of_view=45.0,
                 focused_distance=20.0, idle_distance=23.0, view_offset=25.0, idle_elevation=15.0,
                 idle_drift=3.0, turn_rate=1.1, era_fade_seconds=2.0, sign_scale=0.1,
                 light_direction=(0.5, 0.6, 1.0, 0.0)):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.field_of_view = field_of_view
        self.focused_distance = focused_distance
        self.idle_distance = idle_distance
        self.view_offset = view_offset
        self.idle_elevation = idle_elevation
        self.idle_drift = idle_drift
        self.turn_rate = turn_rate
        self.era_fade_seconds = era_fade_seconds
        self.light_direction = light_direction
        self.earth = HistoricalEarth(0.0, 0.0, 0.0, year=era.value, radius=radius, tilt=0.0, spin_speed=0.0,
                                     moon_enabled=False, sign_scale=sign_scale)
        self.era = era
        self.marked_labels = ()
        self.focused = False
        self.target_spin = 0.0
        self.elevation = idle_elevation
        self.target_elevation = idle_elevation
        self.distance = idle_distance
        self.target_distance = idle_distance

    def show_era(self, era):
        if era != self.era:
            self.era = era
            self.earth.show_year(era.value, self.era_fade_seconds)

    def show_locations(self, locations):
        wanted_labels = tuple(location.label for location in locations)
        for label in self.marked_labels:
            if label not in wanted_labels:
                self.earth.unmark_city(label)
        for location in locations:
            if location.label not in self.earth.city_signs:
                self.earth.mark_location(location.label, location.latitude, location.longitude)
        self.marked_labels = wanted_labels
        self.focused = bool(locations)
        if self.focused:
            self._look_at(locations[0])
        else:
            self.target_elevation = self.idle_elevation
            self.target_distance = self.idle_distance

    def _look_at(self, location):
        self.target_spin = -location.longitude
        self.target_elevation = location.latitude - self.view_offset
        self.target_distance = self.focused_distance

    def update(self, dt):
        if not self.focused:
            self.target_spin += self.idle_drift * dt
        ease = min(1.0, dt * self.turn_rate)
        turn = (self.target_spin - self.earth.spin + 180.0) % 360.0 - 180.0
        self.earth.spin += turn * ease
        self.elevation += (self.target_elevation - self.elevation) * ease
        self.distance += (self.target_distance - self.distance) * ease
        self.earth.update(dt)

    def draw(self):
        glViewport(0, 0, self.screen_width, self.screen_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.screen_height, 0.1, 400.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
        elevation = math.radians(self.elevation)
        gluLookAt(0.0, math.sin(elevation) * self.distance, math.cos(elevation) * self.distance,
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        self.earth.draw()
