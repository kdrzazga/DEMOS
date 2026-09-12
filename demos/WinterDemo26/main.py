import math
import os
import random
import sys
import threading
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from lib import Globals

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.WinterDemo26.land import Land, FlattyLand
from demos.WinterDemo26.tree import Tree
from demos.WinterDemo26.snowman import Snowman
from demos.WinterDemo26.snow import Snow
from demos.WinterDemo26.igloo import Igloo
from demos.WinterDemo26.patch import GroundPatch
from demos.WinterDemo26.bonfire import Bonfire
from demos.WinterDemo26.christmas_robin import ChristmasRobin
from demos.WinterDemo26.cloud import Cloud
from demos.WinterDemo26.stars import Stars
from lib.backdrop import SpaceBackdrop
from lib.pygame_demo import PygameDemo
from lib.saturn import Saturn
from lib.mars import Mars
from lib.earth import Earth
from demos.WinterDemo26.santa_ride import SantaRide
from demos.WinterDemo26.santa_claus import SantaClaus
from lib.urban.city_factory import CityFactory
from lib.urban.house import House


class WinterDemo(PygameDemo):
    def __init__(self, windowed=False, triggered=False):
        super().__init__(1100, 700, "3D Winter", fps=60, opengl=True,
                         windowed=windowed, triggered=triggered)

    def setup(self):
        self.sky_color = (0.66, 0.76, 0.86)
        self.tree_positions = ((-8.0, -4.0), (-5.5, 3.0), (6.5, -6.0), (9.0, 2.5),
                               (-10.0, -9.0), (3.0, 8.0), (-2.0, -11.0), (11.0, -1.0),
                               (-12.0, -14.0), (1.0, 13.0), (-4.0, -14.0), (12.0, -12.0))
        self.elapsed = 0.0
        self.sway_duration = 5.0
        self.travel_duration = 2.5
        self.settle_duration = 4.0
        self.enter_duration = 3.0
        self.igloo_show_duration = 6.0
        self.ascend_duration = 4.6
        self.hole_tilt_duration = 0.4
        self.hole_hold_duration = 0.5
        self.space_duration = 10.0
        self.ascend_top = 40.0
        self.space_color = (0.01, 0.01, 0.04)
        self.nebula_delay = 2.0
        self.nebula_fade = 2.5
        self.nebula_travel_speed = 90.0
        self.nebula_travel_cap = 700.0
        self.santa_delay = 2.0
        self.santa_approach = 6.0
        self.santa_size = 2.0
        self.santa_start_offset = (110.0, 100.0, 30.0)
        self.santa_end_offset = (18.0, 22.0, 6.0)
        self.ride_duration = 5.0
        self.planets_duration = 17.0
        self.turn_left = 35.0
        self.turn_duration = 1.4
        self.flight_pitch = 0.0
        self.flight_speed = 90.0
        self.shoulder_offset = (20.0, 5.0, 10.0)
        self.shoulder_lead = 12.0
        self.camera_blend = 2.2
        self.flight_fog_end = 600.0
        self.flight_far = 2000.0
        self.planet_plan = ((850.0, 150.0, 45.0), (1150.0, -60.0, -25.0))
        self.field_of_view = 55.0
        self.earth_radius = 60.0
        self.earth_tilt = 23.4
        self.earth_longitude = 10.0
        self.earth_latitude = 50.0
        self.earth_spin_speed = 1.5
        self.approach_duration = 8.0
        self.dive_blend = 2.0
        self.sky_cloud_count = 130
        self.sky_cloud_shell = (61.0, 78.0)
        self.dive_end_radius = 62.0
        self.sky_cloud_core = 8.0
        self.sky_cloud_spread = 24.0
        self.sky_cloud_crowding = 1.6
        self.sky_cloud_size = (5.0, 9.0)
        self.sky_cloud_puffs = 9
        self.sky_cloud_seed = 7
        self.sky_cloud_haze_share = 0.5
        self.sky_cloud_opacity = (0.25, 0.70)
        self.slalom_amplitude = 3.5
        self.slalom_period = 3.4
        self.cloud_start_fill = 0.90
        self.cloud_reveal_schedule = ((150.0, 5), (100.0, 13), (80.0, 52),
                                      (78.0, 99), (75.0, 124), (63.0, 130))
        self.glide_duration = 15.0
        self.glide_speed = 40.0
        self.glide_level = 2.5
        self.glide_drop = 60.0
        self.glide_altitude = 30.0
        self.glide_site_ahead = 200.0
        self.glide_site_aside = -8.0
        self.glide_look_down = 5.0
        self.glide_sky_fade = 3.0
        self.glide_fog_end = 1600.0
        self.city_ahead = 580.0
        self.city_aside = 25.0
        self.city_matrix = 7
        self.city_sink = 0.0
        self.city_seed = 5
        self.landing_duration = 5.0
        self.rooftop_duration = 4.2
        self.jump_duration = 1.6
        self.roof_camera_offset = (11.0, 5.5, 8.0)
        self.landing_turn = 180.0
        self.rooftop_santa_size = 1.6
        self.jump_arc = 2.4
        self.roof_stand_offset = 1.4
        self.landing_floors = 5
        self.landing_bays = 12
        self.sleigh_offset_ratio = 0.30
        self.landing_margin = 0.4
        self.landing_chimney_scale = 3.4
        self.landing_chimney_width_scale = 1.21
        self.landing_snow = 0.0
        self.landing_color = (0.44, 0.34, 0.36)
        self.city_flat_size = (176.0, 112.0)
        self.city_flat_falloff = 100.0
        self.igloo_flat_falloff = 60.0
        self.land_extent = 560.0
        self.land_resolution = 280
        self.snowman_end = self.sway_duration
        self.transition_end = self.snowman_end + self.travel_duration
        self.outside_end = self.transition_end + self.settle_duration
        self.enter_end = self.outside_end + self.enter_duration
        self.show_end = self.enter_end + self.igloo_show_duration
        self.hole_gaze_duration = self.hole_tilt_duration + self.hole_hold_duration
        self.ascend_end = self.show_end + self.hole_gaze_duration + self.ascend_duration
        self.space_end = self.ascend_end + self.space_duration
        self.nebula_start = self.ascend_end + self.nebula_delay
        self.santa_start = self.nebula_start + self.santa_delay
        self.ride_start = self.santa_start + self.santa_approach
        self.ride_end = self.ride_start + self.ride_duration
        self.planets_end = self.ride_end + self.planets_duration
        self.glide_end = self.planets_end + self.glide_duration
        self.landing_end = self.glide_end + self.landing_duration
        self.rooftop_end = self.landing_end + self.rooftop_duration
        self.roof_house = None
        self.eye = (0.0, 10.0, 26.0)
        self.target = (0.0, 3.0, 0.0)
        self.thanks_printed = False
        self._start_music()
        self._init_gl()
        self._set_approach_angles()
        self.flatty_offset = (160.0, 0.0, 0.0)
        self.flatty_land = FlattyLand(extent=80.0, resolution=144, seed=11)
        city_x, city_z = self._city_ground_spot()
        self.land = Land(extent=self.land_extent, resolution=self.land_resolution, seed=7, stretch=7.0,
                         clearings=((self.flatty_offset[0], self.flatty_offset[2],
                                     self.flatty_land.extent, self.flatty_land.depth_extent),),
                         flattenings=((self.flatty_offset[0], self.flatty_offset[2],
                                       self.flatty_land.extent, self.flatty_land.depth_extent,
                                       self.igloo_flat_falloff, 0.0),
                                      (city_x, city_z, self.city_flat_size[0],
                                       self.city_flat_size[1], self.city_flat_falloff, None)))
        self.city_offset = (city_x, 0.0, city_z)
        self.trees = self._create_trees()
        self.snowman = Snowman(1.7, 0.0, self.land.surface_height(1.7, 0.0) - 0.6)
        self.igloo = Igloo(self.flatty_offset[0], self.flatty_offset[2],
                           self.flatty_land.surface_height(0.0, 0.0),
                           base_radius=3.5, layers_count=6)
        self.igloo_patch = GroundPatch(0.0, 0.0, self.igloo.base_radius * 4.0, self.flatty_land)
        self.bonfire = Bonfire(self.igloo.x, self.igloo.ground_height, self.igloo.z, scale=0.9,
                               smoke_fade_height=3.0 * self.igloo.base_radius)
        self.robins = self._create_robins()
        self.clouds = self._create_clouds()
        self.stars = Stars(seed=5)
        self.space_backdrop = SpaceBackdrop(self.width / self.height, fov=65.0)
        self.santa_ride = self._create_santa_ride()
        self.planets = self._create_planets()
        self.sky_clouds = self._create_sky_clouds()
        self.city = CityFactory(seed=self.city_seed).create_big_city(matrix_size=self.city_matrix)
        self.rooftop_santa = SantaClaus(0.0, 0.0, 0.0, size=self.rooftop_santa_size, wave=True, seed=9)
        self.baked_surfaces = {}
        threading.Thread(target=self._bake_surfaces, daemon=True).start()
        self.snow = Snow(220, (-22.0, 22.0, -20.0, 20.0, -1.5, 18.0))
        self.igloo_snow = Snow(200, (self.flatty_offset[0] - 22.0, self.flatty_offset[0] + 22.0,
                                     self.flatty_offset[2] - 20.0, self.flatty_offset[2] + 20.0,
                                     -1.5, 18.0), seed=123,
                               dome=(self.igloo.x, self.igloo.z, self.igloo.base_radius, self.igloo.ground_height))

    def _play_scene(self):
        time = self.elapsed
        if time <= self.snowman_end:
            self._snowman_scene()
        elif time <= self.transition_end:
            self._igloo_transition()
        elif time <= self.outside_end:
            self._igloo_approach()
        elif time <= self.enter_end:
            self._enter_igloo()
        elif time <= self.show_end:
            self._igloo_scene()
        elif time <= self.ascend_end:
            self._ascend_scene()
        elif time <= self.space_end:
            self._space_scene()
        elif time <= self.ride_end:
            self._santa_ride_scene()
        elif time <= self.planets_end:
            self._planets_scene()
        elif time <= self.glide_end:
            self._sky_glide_scene()
        elif time <= self.landing_end:
            self._landing_scene()
        elif time <= self.rooftop_end:
            self._rooftop_scene()
        else:
            self._finish()

    def _start_music(self):
        music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dzisiaj.mp3")
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
        except pygame.error:
            pass

    def _init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.98, 0.92, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_AMBIENT, (0.14, 0.07, 0.02, 1.0))
        glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.09)
        glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.032)
        glClearColor(self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0)
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, (self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0))
        glFogf(GL_FOG_START, 30.0)
        glFogf(GL_FOG_END, 80.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.1, 220.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _create_trees(self):
        trees = []
        for index, (x, z) in enumerate(self.tree_positions):
            ground = self.land.surface_height(x, z)
            trees.append(Tree(x, z, ground, snow_top=index % 3 != 0, seed=index + 1))
        return trees

    def _create_robins(self):
        placements = ((-1.45, 0.55, 1.0, 0.15, 1), (1.30, -0.35, 0.8, 0.85, 2))
        robins = []
        for offset_x, offset_z, size, hue, seed in placements:
            ground = self.flatty_land.surface_height(offset_x, offset_z) + self.igloo_patch.height_offset
            facing = math.degrees(math.atan2(-offset_x, -offset_z))
            robins.append(ChristmasRobin(self.bonfire.x + offset_x, self.bonfire.z + offset_z, ground,
                                         size=size, hue=hue, facing=facing, head_bob=True, seed=seed))
        return robins

    def _create_clouds(self):
        placements = ((-14.0, 24.0, -9.0, 5.0, 1), (12.0, 27.5, 8.0, 6.2, 2),
                      (-8.0, 31.0, 13.0, 4.4, 3), (16.0, 34.0, -12.0, 7.0, 4),
                      (-18.0, 37.0, 4.0, 5.6, 5), (6.0, 39.5, -16.0, 4.8, 6))
        clouds = []
        for offset_x, height, offset_z, size, seed in placements:
            clouds.append(Cloud(self.igloo.x + offset_x, height, self.igloo.z + offset_z, size=size, seed=seed))
        return clouds

    def _santa_anchor(self):
        return (self.igloo.x, self.ascend_top + 8.0, self.igloo.z)

    def _santa_waypoint(self, offset):
        anchor = self._santa_anchor()
        return (anchor[0] + offset[0], anchor[1] + offset[1], anchor[2] + offset[2])

    def _set_approach_angles(self):
        course = tuple(self.santa_end_offset[axis] - self.santa_start_offset[axis] for axis in range(3))
        self.approach_facing = math.degrees(math.atan2(course[0], course[2]))
        self.approach_pitch = math.degrees(math.atan2(-course[1], math.hypot(course[0], course[2])))

    def _city_ground_spot(self):
        course = self._glide_direction()
        right = self._unit(self._cross(course, (0.0, 1.0, 0.0)))
        along = self.city_ahead - self.glide_site_ahead
        aside = self.city_aside - self.glide_site_aside
        cell = 2.0 * self.land_extent / self.land_resolution
        local_x = course[0] * along + right[0] * aside + self.flatty_offset[0] / 2.0
        local_z = course[2] * along + right[2] * aside
        return (round(local_x / cell) * cell, round(local_z / cell) * cell)

    def _create_santa_ride(self):
        start = self._santa_waypoint(self.santa_start_offset)
        return SantaRide(start[0], start[1], start[2], size=self.santa_size,
                         facing=self.approach_facing, pitch=self.approach_pitch, bob=True, seed=4)

    def _santa_progress(self):
        return (self.elapsed - self.santa_start) / self.santa_approach

    def _place_santa(self, progress):
        start = self._santa_waypoint(self.santa_start_offset)
        end = self._santa_waypoint(self.santa_end_offset)
        self.santa_ride.x, self.santa_ride.y, self.santa_ride.z = self._lerp(start, end, self._clamp01(progress))

    def _cross(self, first, second):
        return (first[1] * second[2] - first[2] * second[1],
                first[2] * second[0] - first[0] * second[2],
                first[0] * second[1] - first[1] * second[0])

    def _unit(self, vector):
        length = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
        return (vector[0] / length, vector[1] / length, vector[2] / length)

    def _flight_direction(self):
        facing = math.radians(self.approach_facing + self.turn_left)
        pitch = math.radians(self.flight_pitch)
        return (math.sin(facing) * math.cos(pitch), -math.sin(pitch), math.cos(facing) * math.cos(pitch))

    def _flight_point(self, along, side, rise):
        base = self._santa_waypoint(self.santa_end_offset)
        forward = self._flight_direction()
        right = self._unit(self._cross(forward, (0.0, 1.0, 0.0)))
        return tuple(base[axis] + forward[axis] * along + right[axis] * side
                     + (0.0, 1.0, 0.0)[axis] * rise for axis in range(3))

    def _half_width(self):
        half_height = math.radians(self.field_of_view / 2.0)
        return math.atan(math.tan(half_height) * self.width / self.height)

    def _dive_angle(self):
        heading = math.radians(self.approach_facing + self.turn_left)
        tilt = math.radians(self.earth_tilt)
        across = math.sin(heading) * math.sin(tilt)
        along = math.cos(tilt)
        return math.asin(math.sin(math.radians(self.earth_latitude)) / math.hypot(across, along))             - math.atan2(across, along)

    def _approach_direction(self):
        heading = math.radians(self.approach_facing + self.turn_left)
        dive = self._dive_angle()
        return (math.sin(heading) * math.cos(dive), -math.sin(dive), math.cos(heading) * math.cos(dive))

    def _europe_spin(self):
        tilt = math.radians(self.earth_tilt)
        toward = tuple(-axis for axis in self._approach_direction())
        return math.degrees(math.atan2(toward[0] * math.cos(tilt) + toward[1] * math.sin(tilt),
                                       toward[2])) - self.earth_longitude

    def _cruise_end(self):
        return self.planets_end - self.approach_duration

    def _cruise_point(self):
        return self._flight_point((self._cruise_end() - self.ride_start) * self.flight_speed, 0.0, 0.0)

    def _approach_length(self):
        return self.flight_speed * self.approach_duration / 2.0

    def _earth_center(self):
        direction = self._approach_direction()
        base = self._cruise_point()
        span = self._approach_length() + self.dive_end_radius
        return tuple(base[axis] + direction[axis] * span for axis in range(3))

    def _create_planets(self):
        self.earth = Earth(0.0, 0.0, 0.0, radius=self.earth_radius, tilt=self.earth_tilt,
                           spin_speed=self.earth_spin_speed, moon_orbit_scale=0.04)
        self.earth.x, self.earth.y, self.earth.z = self._earth_center()
        self.earth.spin = self._europe_spin() - self.earth_spin_speed * self.planets_end
        self.saturn = Saturn(0.0, 0.0, 0.0, radius=26.0, seed=11, defer_texture=True)
        self.mars = Mars(0.0, 0.0, 0.0, radius=12.0, seed=17, defer_texture=True)
        bodies = [self.saturn, self.mars]
        for body, (along, side, rise) in zip(bodies, self.planet_plan):
            body.x, body.y, body.z = self._flight_point(along, side, rise)
        bodies.append(self.earth)
        return bodies

    def _flight_heading(self):
        moment = min(self.elapsed, self.planets_end)
        if moment <= self._cruise_end():
            return self._flight_direction()
        blend = self._ease(self._clamp01((moment - self._cruise_end()) / self.dive_blend))
        return self._unit(self._lerp(self._flight_direction(), self._approach_direction(), blend))

    def _flight_path_point(self, aside=0.0):
        moment = min(self.elapsed, self.planets_end)
        cruise_end = self._cruise_end()
        along = max(0.0, min(moment, cruise_end) - self.ride_start) * self.flight_speed
        point = self._flight_point(along, aside, 0.0)
        if moment <= cruise_end:
            return point
        eased = 1.0 - (1.0 - (moment - cruise_end) / self.approach_duration) ** 2
        direction = self._approach_direction()
        return tuple(point[axis] + direction[axis] * self._approach_length() * eased for axis in range(3))

    def _slalom_reach(self):
        moment = min(self.elapsed, self.planets_end)
        rise = self._ease(self._clamp01((moment - self.ride_start) / self.turn_duration))
        settle = self._ease(self._clamp01((moment - self._cruise_end()) / self.dive_blend))
        return self.slalom_amplitude * rise * (1.0 - settle)

    def _slalom_phase(self):
        travelled = max(0.0, min(self.elapsed, self.planets_end) - self.ride_start)
        return math.tau * travelled / self.slalom_period

    def _slalom_offset(self):
        return math.sin(self._slalom_phase()) * self._slalom_reach()

    def _slalom_drift(self):
        return math.cos(self._slalom_phase()) * self._slalom_reach() * math.tau / self.slalom_period

    def _flight_position(self):
        return self._flight_path_point(self._slalom_offset())

    def _santa_heading(self):
        forward = self._flight_heading()
        right = self._unit(self._cross(self._flight_direction(), (0.0, 1.0, 0.0)))
        drift = self._slalom_drift()
        return self._unit(tuple(forward[axis] * self.flight_speed + right[axis] * drift
                                for axis in range(3)))

    def _earth_gap(self):
        centre = (self.earth.x, self.earth.y, self.earth.z)
        return math.sqrt(sum((self.eye[axis] - centre[axis]) ** 2 for axis in range(3)))

    def _santa_earth_gap(self):
        centre = (self.earth.x, self.earth.y, self.earth.z)
        rider = (self.santa_ride.x, self.santa_ride.y, self.santa_ride.z)
        return math.sqrt(sum((rider[axis] - centre[axis]) ** 2 for axis in range(3)))

    def _visible_cloud_count(self):
        if not self._in_flight():
            return 0
        gap = self._santa_earth_gap()
        schedule = self.cloud_reveal_schedule
        shown = schedule[-1][1]
        if gap >= schedule[0][0]:
            shown = schedule[0][1]
        else:
            for far, near in zip(schedule, schedule[1:]):
                if gap >= near[0]:
                    reached = (far[0] - gap) / (far[0] - near[0])
                    shown = far[1] + (near[1] - far[1]) * reached
                    break
        return min(len(self.sky_clouds), int(round(shown)))

    def _cloud_approach(self):
        if not self._in_flight():
            return 0.0
        gap = self._earth_gap()
        near = self.earth_radius / math.sin(self.cloud_start_fill * math.radians(self.field_of_view / 2.0))
        full = self.earth_radius / math.sin(self._half_width())
        return self._ease(self._clamp01((near - gap) / (near - full)))

    def _create_sky_clouds(self):
        axis = tuple(-value for value in self._approach_direction())
        right = self._unit(self._cross(axis, (0.0, 1.0, 0.0)))
        lift = self._cross(right, axis)
        centre = self._earth_center()
        generator = random.Random(self.sky_cloud_seed)
        clouds = []
        for index in range(self.sky_cloud_count):
            aside = self.sky_cloud_spread * generator.random() ** self.sky_cloud_crowding
            swing = generator.uniform(0.0, math.tau)
            reach = generator.uniform(*self.sky_cloud_shell)
            spot = tuple(centre[axis_index] + axis[axis_index] * reach
                         + (math.cos(swing) * right[axis_index]
                            + math.sin(swing) * lift[axis_index]) * aside
                         for axis_index in range(3))
            hazy = (aside > self.sky_cloud_core
                    and generator.random() < self.sky_cloud_haze_share)
            opacity = generator.uniform(*self.sky_cloud_opacity) if hazy else 1.0
            clouds.append((reach, Cloud(spot[0], spot[1], spot[2],
                                        size=generator.uniform(*self.sky_cloud_size),
                                        puff_count=self.sky_cloud_puffs, seed=index + 11,
                                        opacity=opacity)))
        clouds.sort(key=lambda entry: entry[0])
        layered = [(rank, entry[1]) for rank, entry in enumerate(clouds)]
        layered.sort(key=lambda entry: -entry[1].opacity)
        return tuple(layered)

    def _place_santa_flight(self):
        self.santa_ride.x, self.santa_ride.y, self.santa_ride.z = self._flight_position()
        heading = self._santa_heading()
        moment = min(self.elapsed, self.planets_end)
        turn = self._ease(self._clamp01((moment - self.ride_start) / self.turn_duration))
        facing = math.degrees(math.atan2(heading[0], heading[2]))
        pitch = math.degrees(math.atan2(-heading[1], math.hypot(heading[0], heading[2])))
        self.santa_ride.facing = self.approach_facing + (facing - self.approach_facing) * turn
        self.santa_ride.pitch = self.approach_pitch + (pitch - self.approach_pitch) * turn

    def _shoulder_view(self):
        course = self._flight_path_point()
        forward = self._flight_heading()
        right = self._unit(self._cross(forward, (0.0, 1.0, 0.0)))
        back, lift, side = self.shoulder_offset
        eye = tuple(course[axis] - forward[axis] * back + (0.0, 1.0, 0.0)[axis] * lift
                    + right[axis] * side for axis in range(3))
        return eye, tuple(course[axis] + forward[axis] * self.shoulder_lead for axis in range(3))

    def _santa_ride_scene(self):
        self._place_santa_flight()
        eye, target = self._shoulder_view()
        blend = self._ease(self._clamp01((self.elapsed - self.ride_start) / self.camera_blend))
        if blend < 1.0:
            parked_eye, parked_target = self._space_view(1.0)
            eye = self._lerp(parked_eye, eye, blend)
            target = self._lerp(parked_target, target, blend)
        self.eye, self.target = eye, target

    def _planets_scene(self):
        self._santa_ride_scene()

    def _gliding(self):
        return self.elapsed > self.planets_end

    def _glide_span(self):
        return min(self.elapsed, self.glide_end) - self.planets_end

    def _glide_origin(self):
        return self._flight_path_point()

    def _glide_direction(self):
        approach = self._approach_direction()
        flat = math.hypot(approach[0], approach[2])
        return (approach[0] / flat, 0.0, approach[2] / flat)

    def _dive_pitch(self):
        direction = self._approach_direction()
        return math.degrees(math.atan2(-direction[1], math.hypot(direction[0], direction[2])))

    def _glide_position(self):
        span = self._glide_span()
        origin = self._glide_origin()
        course = self._glide_direction()
        drop = self.glide_drop * self._ease(self._clamp01(span / self.glide_level))
        return (origin[0] + course[0] * span * self.glide_speed,
                origin[1] - drop,
                origin[2] + course[2] * span * self.glide_speed)

    def _glide_view(self):
        rider = self._glide_position()
        course = self._glide_direction()
        right = self._unit(self._cross(course, (0.0, 1.0, 0.0)))
        back, lift, side = self.shoulder_offset
        eye = tuple(rider[axis] - course[axis] * back + (0.0, 1.0, 0.0)[axis] * lift
                    + right[axis] * side for axis in range(3))
        target = tuple(rider[axis] + course[axis] * self.shoulder_lead for axis in range(3))
        return eye, (target[0], target[1] - self.glide_look_down, target[2])

    def _winter_shift(self):
        if not self._gliding():
            return (0.0, 0.0, 0.0)
        origin = self._glide_origin()
        course = self._glide_direction()
        right = self._unit(self._cross(course, (0.0, 1.0, 0.0)))
        middle = self.flatty_offset[0] / 2.0
        return (origin[0] + course[0] * self.glide_site_ahead + right[0] * self.glide_site_aside - middle,
                origin[1] - self.glide_drop - self.glide_altitude,
                origin[2] + course[2] * self.glide_site_ahead + right[2] * self.glide_site_aside)

    def _city_site(self):
        shift = self._winter_shift()
        ground = self.land.surface_height(self.city_offset[0], self.city_offset[2])
        return (shift[0] + self.city_offset[0],
                shift[1] + ground - self.city_sink,
                shift[2] + self.city_offset[2])

    def _sky_glide_scene(self):
        course = self._glide_direction()
        settle = self._ease(self._clamp01(self._glide_span() / self.glide_level))
        self.santa_ride.x, self.santa_ride.y, self.santa_ride.z = self._glide_position()
        self.city.x, self.city.y, self.city.z = self._city_site()
        self._roof_house()
        self.santa_ride.facing = math.degrees(math.atan2(course[0], course[2]))
        self.santa_ride.pitch = self._dive_pitch() * (1.0 - settle)
        self.eye, self.target = self._glide_view()

    def _bake_surfaces(self):
        self.baked_surfaces["saturn"] = self.saturn._build_surface()
        self.baked_surfaces["mars"] = self.mars._build_surface()

    def _install_surfaces(self):
        for name, planet in (("saturn", self.saturn), ("mars", self.mars)):
            if not planet.ready() and name in self.baked_surfaces:
                planet.attach_surface(self.baked_surfaces.pop(name))

    def _winter_visible(self):
        return self.elapsed < self.nebula_start or self._gliding()

    def _in_cloud(self):
        return self._cloud_approach() > 0.0

    def _nebula_brightness(self):
        if self._gliding():
            return 0.0
        return self._nebula_factor() * (1.0 - self._cloud_approach())

    def _inside_clouds(self):
        if not self._in_flight():
            return False
        centre = (self.earth.x, self.earth.y, self.earth.z)
        rider = (self.santa_ride.x, self.santa_ride.y, self.santa_ride.z)
        gap = math.sqrt(sum((rider[axis] - centre[axis]) ** 2 for axis in range(3)))
        return gap <= self.sky_cloud_shell[1]

    def _in_flight(self):
        return self.elapsed >= self.ride_start

    def _nebula_travel(self):
        return min(self.nebula_travel_cap,
                   max(0.0, self.elapsed - self.nebula_start) * self.nebula_travel_speed)

    def _space_factor(self):
        if self._gliding():
            return 1.0 - self._ease(self._clamp01(self._glide_span() / self.glide_sky_fade))
        if self._in_flight():
            return 1.0
        return self._ease(self._clamp01((self.eye[1] - 28.0) / 24.0))

    def _nebula_factor(self):
        started = self.elapsed - self.ascend_end - self.nebula_delay
        return self._ease(self._clamp01(started / self.nebula_fade))

    def _clamp01(self, value):
        return max(0.0, min(1.0, value))

    def _ease(self, value):
        return value * value * (3.0 - 2.0 * value)

    def _sway_eye(self, moment):
        orbit = math.radians(35.0 * math.sin(moment * 0.25))
        radius = 26.0
        return (math.sin(orbit) * radius, 10.0, math.cos(orbit) * radius)

    def _lerp(self, start, end, factor):
        return tuple(start[axis] + (end[axis] - start[axis]) * factor for axis in range(3))

    def _outside_igloo_view(self, local_time):
        flatty_x, _, flatty_z = self.flatty_offset
        eye = (flatty_x - 12.0 + math.sin(local_time * 0.35) * 4.0,
               8.0,
               flatty_z + 15.0 + math.cos(local_time * 0.35) * 2.0)
        return eye, (flatty_x, 2.5, flatty_z)

    def _snowman_scene(self):
        self.eye = self._sway_eye(self.elapsed)
        self.target = (0.0, 3.0, 0.0)

    def _igloo_transition(self):
        progress = (self.elapsed - self.snowman_end) / self.travel_duration
        eased = progress * progress * (3.0 - 2.0 * progress)
        end_eye, end_target = self._outside_igloo_view(0.0)
        self.eye = self._lerp(self._sway_eye(self.snowman_end), end_eye, eased)
        self.target = self._lerp((0.0, 3.0, 0.0), end_target, eased)

    def _igloo_approach(self):
        self.eye, self.target = self._outside_igloo_view(self.elapsed - self.transition_end)

    def _enter_igloo(self):
        progress = (self.elapsed - self.outside_end) / self.enter_duration
        start_eye, _ = self._outside_igloo_view(self.settle_duration)
        self.eye, self.target = self.igloo.enter_igloo(start_eye, progress)

    def _igloo_inside_view(self):
        start_eye, _ = self._outside_igloo_view(self.settle_duration)
        return self.igloo.enter_igloo(start_eye, 1.0)

    def _igloo_scene(self):
        self.eye, self.target = self._igloo_inside_view()

    def _skyward_target(self, eye, spin):
        yaw = math.radians(-90.0 + spin * 55.0)
        return (eye[0] + math.cos(yaw) * 6.0, eye[1] + 10.0, eye[2] + math.sin(yaw) * 6.0)

    def _hole_position(self):
        return (self.igloo.x, self.igloo.ground_height + self.igloo.base_radius, self.igloo.z)

    def _hole_gaze_view(self, local_time):
        inside_eye, inside_target = self._igloo_inside_view()
        tilt = self._ease(self._clamp01(local_time / self.hole_tilt_duration))
        return inside_eye, self._lerp(inside_target, self._hole_position(), tilt)

    def _ascend_view(self, progress):
        start_eye, _ = self._igloo_inside_view()
        centering = self._ease(self._clamp01(progress / 0.30))
        eye = (start_eye[0] + (self.igloo.x - start_eye[0]) * centering,
               start_eye[1] + (self.ascend_top - start_eye[1]) * progress,
               start_eye[2] + (self.igloo.z - start_eye[2]) * centering)
        skyward = self._skyward_target(eye, progress)
        return eye, self._lerp(self._hole_position(), skyward, self._ease(self._clamp01(progress / 0.22)))

    def _space_view(self, progress):
        eye = (self.igloo.x, self.ascend_top + progress * 16.0, self.igloo.z)
        return eye, self._skyward_target(eye, 1.0 + progress * 1.6)

    def _ascend_scene(self):
        local_time = self.elapsed - self.show_end
        if local_time <= self.hole_gaze_duration:
            self.eye, self.target = self._hole_gaze_view(local_time)
        else:
            rise = (local_time - self.hole_gaze_duration) / self.ascend_duration
            self.eye, self.target = self._ascend_view(self._clamp01(rise))

    def _space_scene(self):
        self.eye, self.target = self._space_view(self._clamp01((self.elapsed - self.ascend_end) / self.space_duration))

    def _roof_house(self):
        if self.roof_house is None:
            town = self.city.town_at(self.city.rows // 2, self.city.columns // 2)
            tallest = None
            for quarter in town.quarters:
                for index, house in enumerate(quarter.houses):
                    if tallest is None or house.total_height > tallest[0].total_height:
                        tallest = (house, quarter, index,
                                   (town.x + quarter.x + house.x, town.z + quarter.z + house.z))
            crowded, quarter, index, spot = tallest
            self.roof_house = House(self.city.x + spot[0], self.city.y, self.city.z + spot[1],
                                    self.landing_floors, windows_per_floor=self.landing_bays,
                                    color=self.landing_color, facing=crowded.facing,
                                    snow_top=self.landing_snow,
                                    chimney_scale=self.landing_chimney_scale,
                                    chimney_width_scale=self.landing_chimney_width_scale)
            self._clear_landing_plot(spot)
        return self.roof_house

    def _clear_landing_plot(self, spot):
        big = self.roof_house
        for town in self.city.towns:
            for quarter in town.quarters:
                hidden = list(quarter.hidden)
                for index, other in enumerate(quarter.houses):
                    across = abs(town.x + quarter.x + other.x - spot[0])
                    along = abs(town.z + quarter.z + other.z - spot[1])
                    if (across < (other.width + big.width) / 2.0 + self.landing_margin
                            and along < (other.depth + big.depth) / 2.0 + self.landing_margin
                            and index not in hidden):
                        hidden.append(index)
                quarter.hidden = tuple(hidden)

    def _chimney_top(self):
        house = self._roof_house()
        return (house.x, house.y + house.roof_peak + house.chimney_rise, house.z)

    def _landing_spot(self):
        house = self._roof_house()
        top = self._chimney_top()
        return (top[0], house.y + house.roof_peak + self.roof_stand_offset,
                top[2] + house.depth * self.sleigh_offset_ratio)

    def _roof_view(self, turn=0.0):
        top = self._chimney_top()
        course = self._glide_direction()
        right = self._unit(self._cross(course, (0.0, 1.0, 0.0)))
        back, lift, side = self.roof_camera_offset
        sweep = math.radians(turn)
        along = -back * math.cos(sweep) - side * math.sin(sweep)
        across = -back * math.sin(sweep) + side * math.cos(sweep)
        eye = (top[0] + course[0] * along + right[0] * across,
               top[1] + lift,
               top[2] + course[2] * along + right[2] * across)
        return eye, top

    def _landing_scene(self):
        settle = self._ease(self._clamp01((self.elapsed - self.glide_end) / self.landing_duration))
        course = self._glide_direction()
        self.santa_ride.x, self.santa_ride.y, self.santa_ride.z = self._lerp(
            self._glide_position(), self._landing_spot(), settle)
        self.santa_ride.facing = math.degrees(math.atan2(course[0], course[2]))
        self.santa_ride.pitch = 0.0
        glide_eye, glide_target = self._glide_view()
        roof_eye, roof_target = self._roof_view(settle * self.landing_turn)
        self.eye = self._lerp(glide_eye, roof_eye, settle)
        self.target = self._lerp(glide_target, roof_target, settle)

    def _on_rooftop(self):
        return self.elapsed > self.landing_end

    def _rooftop_scene(self):
        local = min(self.elapsed, self.rooftop_end) - self.landing_end
        course = self._glide_direction()
        self.santa_ride.x, self.santa_ride.y, self.santa_ride.z = self._landing_spot()
        self.santa_ride.facing = math.degrees(math.atan2(course[0], course[2]))
        self.santa_ride.pitch = 0.0
        self.santa_ride.carry_santa = False
        top = self._chimney_top()
        seat = (self.santa_ride.x, self.santa_ride.y + self.roof_stand_offset, self.santa_ride.z)
        if local <= self.jump_duration:
            hop = self._clamp01(local / self.jump_duration)
            spot = self._lerp(seat, top, hop)
            self.rooftop_santa.x = spot[0]
            self.rooftop_santa.y = spot[1] + math.sin(math.pi * hop) * self.jump_arc
            self.rooftop_santa.z = spot[2]
            self.rooftop_santa.size = self.rooftop_santa_size
        else:
            sink = self._ease(self._clamp01((local - self.jump_duration)
                                            / (self.rooftop_duration - self.jump_duration)))
            self.rooftop_santa.x, self.rooftop_santa.z = top[0], top[2]
            self.rooftop_santa.y = top[1] - sink * self.rooftop_santa_size * 2.6
            self.rooftop_santa.size = self.rooftop_santa_size
        self.rooftop_santa.facing = math.degrees(math.atan2(top[0] - seat[0], top[2] - seat[2]))
        self.eye = self._roof_view(self.landing_turn)[0]
        self.target = (self.rooftop_santa.x, self.rooftop_santa.y, self.rooftop_santa.z)

    def _finish(self):
        self._rooftop_scene()
        if not self.thanks_printed:
            t = Globals.get_duration()
            print("thanks for watching, duration " + str(t))
            self.thanks_printed = True

    def _place_camera(self):
        gluLookAt(self.eye[0], self.eye[1], self.eye[2],
                  self.target[0], self.target[1], self.target[2], 0.0, 1.0, 0.0)

    def _draw(self):
        space_factor = self._space_factor()
        sky = self._lerp(self.sky_color, self.space_color, space_factor)
        glClearColor(sky[0], sky[1], sky[2], 1.0)
        glFogfv(GL_FOG_COLOR, (sky[0], sky[1], sky[2], 1.0))
        if self._gliding():
            glFogf(GL_FOG_END, self.glide_fog_end)
            reach = self.flight_far
        elif self._in_flight():
            glFogf(GL_FOG_END, self.flight_fog_end)
            reach = self.flight_far
        else:
            glFogf(GL_FOG_END, 80.0 + 180.0 * space_factor)
            reach = 220.0
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.1, reach)
        glMatrixMode(GL_MODELVIEW)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self._place_camera()
        self.space_backdrop.draw(self._nebula_brightness(), self.eye, self.target, self._nebula_travel())
        self.stars.draw(space_factor, self.eye)
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.6, 0.0))
        if self._winter_visible():
            glEnable(GL_LIGHT1)
            glow = self.bonfire.glow_intensity()
            glLightfv(GL_LIGHT1, GL_DIFFUSE, (glow, 0.5 * glow, 0.18 * glow, 1.0))
            glPushMatrix()
            glTranslatef(*self._winter_shift())
            glLightfv(GL_LIGHT1, GL_POSITION, self.bonfire.light_position())
            self.land.draw()
            glPushMatrix()
            glTranslatef(*self.flatty_offset)
            self.flatty_land.draw()
            self.igloo_patch.draw()
            glPopMatrix()
            for cloud in self.clouds:
                cloud.draw()
            for tree in self.trees:
                tree.draw()
            self.snowman.draw()
            self.igloo.draw(glow)
            for robin in self.robins:
                robin.draw()
            self.bonfire.draw()
            glPopMatrix()
        else:
            glDisable(GL_LIGHT1)
        if self._gliding():
            self.city.draw()
            if self.roof_house is not None:
                self.roof_house.draw()
            if self._on_rooftop():
                self.rooftop_santa.draw()
            if self._space_factor() > 0.0:
                for _, cloud in self.sky_clouds:
                    cloud.draw()
            self.santa_ride.draw()
        elif self._in_flight():
            approaching = self._in_cloud()
            self.earth.moon_enabled = not approaching
            if not approaching:
                for planet in self.planets:
                    planet.draw()
            elif not self._inside_clouds():
                self.earth.draw()
            shown = self._visible_cloud_count()
            for rank, cloud in self.sky_clouds:
                if rank < shown:
                    cloud.draw()
            self.santa_ride.draw()
        else:
            santa_progress = self._santa_progress()
            if santa_progress >= 0.0:
                self._place_santa(santa_progress)
                self.santa_ride.draw()
        if self._winter_visible():
            glPushMatrix()
            glTranslatef(*self._winter_shift())
            self.snow.draw()
            self.igloo_snow.draw()
            glPopMatrix()

    def on_pause(self):
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass

    def on_start(self):
        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass

    def step(self):
        delta_seconds = self.clock.get_time() / 1000.0
        self.elapsed += delta_seconds
        if self._winter_visible():
            self.snow.update(delta_seconds)
            self.igloo_snow.update(delta_seconds)
            self.bonfire.update(delta_seconds)
            for robin in self.robins:
                robin.update(delta_seconds)
        self.santa_ride.update(delta_seconds)
        self.rooftop_santa.update(delta_seconds)
        for planet in self.planets:
            planet.update(delta_seconds)
        self._install_surfaces()
        self._play_scene()
        self.space_backdrop.update(self.elapsed, self._nebula_brightness())
        self._draw()


def main():
    args = [arg.lower() for arg in sys.argv[1:]]
    windowed = any(arg in ("w", "window", "windowed") for arg in args)
    triggered = any(arg in ("t", "trigger", "triggered") for arg in args)
    WinterDemo(windowed=windowed, triggered=triggered).run()


if __name__ == "__main__":
    main()
