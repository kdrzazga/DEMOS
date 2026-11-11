import random

import numpy
from OpenGL.GL import *

from demos.retro_neons.extended_neon_street import ExtendedNeonStreet
from demos.retro_neons.flight import CameraKey, FlightCamera, FlightPath
from lib.specialFX.rain import Rain
from lib.three_mirrors.mirror_renderer import ReflectorSet
from lib.urban.glass import GreenDistrict
from lib.urban.glass.night_scene import NightGround
from lib.vector3 import Vector3


def smoothstep(progress):
    progress = min(max(progress, 0.0), 1.0)
    return progress * progress * (3.0 - 2.0 * progress)


def blend(origin, target, amount):
    return tuple(start + (end - start) * amount for start, end in zip(origin, target))


class TravellingRain(Rain):

    def follow(self, displacement):
        self.drops -= numpy.array(tuple(displacement), dtype=numpy.float32)


class BareGround:

    def prepare(self):
        pass

    def draw(self):
        pass


class NightCity:

    def __init__(self):
        self.night = (0.008, 0.01, 0.02, 1.0)
        self.district_origin = Vector3(0.0, 0.0, -1123.0)
        self.district_facing = Vector3(0.0, 0.0, -1.0)
        self.district_ground_half_extent = 124.5
        self.approach_ground_half_extent = 175.5
        self.road_lamps_clearance = 20.0
        self.road_buildings_clearance = 30.0
        self.centre_line_clearance = 16.0
        self.road_entry_seconds = 13.5
        self.road_exit_seconds = 0.0
        self.road_end_z = -215.0
        self.road_key_count = 5
        self.cruise_speed = 90.0
        self.cruise_height = 12.0
        self.passage_after_tower = 2
        self.start_distance = 460.0
        self.start_yaw_degrees = 8.0
        self.distant_green_fog_density = 0.0015
        self.green_fog_density = 0.009
        self.distant_neon_fog_density = 0.0006
        self.neon_fog_density = 0.011
        self.hidden_neon_fog_density = 0.05
        self.reveal_seconds = 2.5
        self.reveal_window = None
        self.square_entry_z = -64.0
        self.square_screen_delay = 2.0
        self.square_screen_seconds = 0.0
        self.square_screen_on = False
        self.reveal = 0.0
        self.brightening_window = (0.0, 1.5)
        self.haze_window = (0.0, 1.0)
        self.brightness = 0.0
        self.light_slots = (GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3, GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7)
        self.rain_drops = 3500
        self.rain_low = Vector3(-40.0, -25.0, -40.0)
        self.rain_high = Vector3(40.0, 30.0, 40.0)
        self.haze = 0.0
        self.green = None
        self.approach_ground = None
        self.neon = None
        self.rain = None
        self.camera = None
        self.green_reflectors = None
        self.every_reflector = None
        self.rain_anchor = None

    def build(self):
        district = GreenDistrict()
        district.origin = self.district_origin
        district.facing = self.district_facing
        district.ground_half_extent = self.district_ground_half_extent
        self.green = district.build()
        self.green.ground = BareGround()
        self.green.prepare()
        self.approach_ground = NightGround(self.approach_ground_half_extent)
        self.approach_ground.center = Vector3(0.0, 0.0, self.district_origin.z - self.district_ground_half_extent
                                              - self.approach_ground_half_extent)
        self.approach_ground.prepare()
        self.neon = ExtendedNeonStreet(seed=7)
        self.neon.street_far = self.district_origin.z - self.district_ground_half_extent
        self.neon.road_lamps_far = self.district_origin.z + self.road_lamps_clearance
        self.neon.road_cars_far = self.district_origin.z + self.road_lamps_clearance
        self.neon.road_buildings_far = self.district_origin.z + self.road_buildings_clearance
        self.neon.centre_line_far = self.district_origin.z + self.centre_line_clearance
        self.neon.build()
        self.neon.rain.enabled = False
        self.rain = TravellingRain(self.rain_drops, self.rain_low, self.rain_high, random.Random(11))
        self.rain.enabled = False
        path = self._plan_flight()
        reveal_start = self._time_reaching(path, self.district_origin.z - self.start_distance / 2.0)
        self.reveal_window = (reveal_start, reveal_start + self.reveal_seconds)
        self.square_screen_seconds = self._time_reaching(path, self.square_entry_z) + self.square_screen_delay
        self.camera = FlightCamera(path, self.neon.camera)
        self.neon.camera = self.camera
        self.green_reflectors = self.green.reflector_set
        self.every_reflector = ReflectorSet(self.green.reflector_set.reflectors + self.neon.reflector_set.reflectors)
        self.rain_anchor = self.camera.eye()

    @staticmethod
    def _time_reaching(path, depth):
        step = 0.05
        seconds = 0.0
        while seconds < path.duration and path.sample(seconds)[2] < depth:
            seconds += step
        return seconds

    @property
    def reflector_set(self):
        return self.every_reflector if self.reveal > 0.0 else self.green_reflectors

    def _passage_x(self):
        street = self.green.streets[0]
        near, far = street.towers[self.passage_after_tower], street.towers[self.passage_after_tower + 1]
        near_width = street.plans[self.passage_after_tower].width
        far_width = street.plans[self.passage_after_tower + 1].width
        side = 1.0 if far.x > near.x else -1.0
        return ((near.x + side * near_width / 2.0) + (far.x - side * far_width / 2.0)) / 2.0

    def _plan_flight(self):
        passage_x = self._passage_x()
        front_z = self.district_origin.z
        avenue_x = sum(self.neon.avenue) / 2.0
        balcony = self.neon.camera
        landing_yaw, landing_pitch = FlightCamera.heading_of(balcony.base_target - balcony.base_eye)
        landing = balcony.base_eye
        return FlightPath([
            CameraKey(0.0, Vector3(passage_x, 7.0, front_z - self.start_distance), self.start_yaw_degrees, 3.0),
            CameraKey(6.0, Vector3(passage_x, 6.0, front_z - 168.0), 0.0, 0.0),
            CameraKey(9.0, Vector3(passage_x, 6.0, front_z - 40.0), 0.0, 0.0),
            CameraKey(12.0, Vector3(passage_x, 6.5, front_z + 20.0), 0.0, 0.0),
            CameraKey(self.road_entry_seconds, Vector3(passage_x, 7.0, front_z + 70.0), 0.0, 0.0),
            *self._road_keys(avenue_x, front_z + 70.0),
            *self._square_keys(avenue_x, landing, landing_yaw, landing_pitch),
        ])

    def _road_keys(self, avenue_x, road_start):
        road_length = self.road_end_z - road_start
        seconds = self.road_entry_seconds
        keys = []
        for index in range(1, self.road_key_count + 1):
            seconds += road_length / self.road_key_count / self.cruise_speed
            keys.append(CameraKey(seconds, Vector3(avenue_x, self.cruise_height, road_start
                                                   + road_length * index / self.road_key_count), 0.0, 0.0))
        self.road_exit_seconds = seconds
        return keys

    def _square_keys(self, avenue_x, landing, landing_yaw, landing_pitch):
        legs = ((1.6, Vector3(avenue_x, self.cruise_height, -140.0), 0.0, 0.0),
                (2.0, Vector3(avenue_x, 14.0, -62.0), 0.0, -3.0),
                (1.6, Vector3(avenue_x, 20.0, -30.0), 0.0, -8.0),
                (2.4, Vector3(avenue_x + 2.0, 19.5, -8.0), 40.0, -10.0),
                (2.0, Vector3(landing.x + 3.2, 18.5, landing.z - 1.5), 120.0, -12.0),
                (2.0, landing, landing_yaw, landing_pitch))
        seconds = self.road_exit_seconds
        keys = []
        for leg_seconds, eye, yaw_degrees, pitch_degrees in legs:
            seconds += leg_seconds
            keys.append(CameraKey(seconds, eye, yaw_degrees, pitch_degrees))
        arrival = self.road_exit_seconds + legs[0][0]
        self.haze_window = (arrival, arrival + legs[1][0] + legs[2][0] + 1.5)
        return keys

    @property
    def sky(self):
        return blend(self.night, self.neon.palette.fog, self.haze)

    def start_rain(self):
        self.rain.enabled = True
        self.neon.rain.enabled = True

    def update(self, seconds):
        self.green.update(seconds)
        self.neon.update(seconds)
        eye = self.camera.eye()
        self.rain.follow(eye - self.rain_anchor)
        self.rain_anchor = eye
        self.rain.update(seconds)
        self.brightness = self._progress_through(self.brightening_window)
        self.haze = self._progress_through(self.haze_window)
        self.reveal = self._progress_through(self.reveal_window)
        self.neon.play_butterfly_screen(self.reveal > 0.0)
        if not self.square_screen_on and self.camera.elapsed >= self.square_screen_seconds:
            self.square_screen_on = True
            self.neon.switch_square_screen()

    def _progress_through(self, window):
        start, end = window
        return smoothstep((self.camera.elapsed - start) / (end - start))

    def illuminate(self):
        pass

    @property
    def street_fog_density(self):
        return self.distant_neon_fog_density + (self.neon_fog_density - self.distant_neon_fog_density) * self.haze

    @property
    def neon_city_fog_density(self):
        return self.hidden_neon_fog_density + (self.street_fog_density - self.hidden_neon_fog_density) * self.reveal

    def draw_ground_mirror(self):
        glPushMatrix()
        glScalef(1.0, -self.neon.reflection_stretch, 1.0)
        self._light_green()
        self.green.draw()
        for facade in self.green_reflectors.reflectors:
            facade.draw_glass()
        self._fog_neon(self.neon_city_fog_density)
        self.neon.draw_street_reflections()
        glPopMatrix()

    def draw(self):
        self._light_green()
        self.green.draw()
        self.approach_ground.draw()
        self._light_neon()
        self._fog_neon(self.street_fog_density)
        self.neon.draw_street()
        self._fog_neon(self.neon_city_fog_density)
        self.neon.draw()
        glPushMatrix()
        glTranslatef(*self.rain_anchor)
        self.rain.draw()
        glPopMatrix()

    def _light_green(self):
        self.green.night = self.sky
        self.green.fog_density = (self.distant_green_fog_density * (1.0 - self.brightness)
                                  + self.green_fog_density * self.haze)
        self.green.configure()
        self.green.illuminate()

    def _light_neon(self):
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_FALSE)
        for slot in self.light_slots:
            glDisable(slot)
        self.neon.configure()
        self.neon.illuminate()

    def _fog_neon(self, density):
        glFogf(GL_FOG_DENSITY, density)
        glFogfv(GL_FOG_COLOR, self.sky)
