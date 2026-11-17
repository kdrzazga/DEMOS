import math
import os
import random
import sys

import numpy
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.animals.shark import Shark, SharkModel
from lib.sea import Sea
from lib.urban.ruin.ruined_building import Ruin1, Ruin2
from lib.urban.textures import TextureFactory


def smoothstep(edge_start, edge_end, value):
    fraction = min(1.0, max(0.0, (value - edge_start) / (edge_end - edge_start)))
    return fraction * fraction * (3.0 - 2.0 * fraction)


class Flight:

    def __init__(self, sea):
        self.sea = sea
        self.speed = 75.0
        self.distance_flown = 0.0
        self.flight_seconds = 0.0
        self.bank_strength = 1.6
        self.longest_bank = 0.5
        self.climb_follow = 0.6
        self.sample_seconds = 0.05

    def ground_point(self, distance):
        raise NotImplementedError

    def altitude(self, seconds, distance):
        raise NotImplementedError

    def look_down(self, seconds, distance):
        raise NotImplementedError

    def heading(self, distance):
        x, z = self.ground_point(distance)
        ahead_x, ahead_z = self.ground_point(distance + self.speed * self.sample_seconds)
        return math.atan2(ahead_x - x, -(ahead_z - z))

    def update(self, seconds):
        self.flight_seconds += seconds
        self.distance_flown += self.speed * seconds

    def camera(self):
        x, z = self.ground_point(self.distance_flown)
        y = self.altitude(self.flight_seconds, self.distance_flown)
        later_distance = self.distance_flown + self.speed * self.sample_seconds
        yaw = self.heading(self.distance_flown)
        later_yaw = self.heading(later_distance)
        turn = math.atan2(math.sin(later_yaw - yaw), math.cos(later_yaw - yaw)) / self.sample_seconds
        roll = max(-self.longest_bank, min(self.longest_bank, turn * self.bank_strength))
        rise = (self.altitude(self.flight_seconds + self.sample_seconds, later_distance) - y) / self.sample_seconds
        pitch = (math.atan2(rise, self.speed) * self.climb_follow
                 - self.look_down(self.flight_seconds, self.distance_flown))
        return (x, y, z), yaw, pitch, roll


class OpenSeaFlight(Flight):

    def __init__(self, sea):
        super().__init__(sea)
        self.loop_radius = 1800.0
        self.cross_stretch = 0.6
        self.low_clearance = 2.2
        self.high_altitude = 160.0
        self.altitude_period_seconds = 26.0
        self.low_look_down = 0.03
        self.high_look_down = 0.28

    def ground_point(self, distance):
        loop_angle = distance / self.loop_radius
        return (self.loop_radius * math.sin(loop_angle),
                -self.loop_radius * self.cross_stretch * math.sin(2.0 * loop_angle))

    def climb(self, seconds):
        swing = 0.5 - 0.5 * math.cos(2.0 * math.pi * seconds / self.altitude_period_seconds)
        return swing * swing

    def altitude(self, seconds, distance):
        lowest = self.sea.surface_top + self.low_clearance
        return lowest + (self.high_altitude - lowest) * self.climb(seconds)

    def look_down(self, seconds, distance):
        return self.low_look_down + (self.high_look_down - self.low_look_down) * self.climb(seconds)


class DiveFlight(Flight):

    def __init__(self, sea):
        super().__init__(sea)
        self.speed = 24.0
        self.loop_radius = 96.0
        self.cruise_altitude = 16.0
        self.dive_altitude = -30.0
        self.dive_window = (0.22, 0.38, 0.80, 0.94)
        self.cruise_look_down = 0.22
        self.dive_look_down = 0.05
        self.bank_strength = 1.2
        self.descent_recovery = 25.0
        self.descents = []

    def add_descent(self, center_distance, half_length, drop):
        self.descents.append((center_distance, half_length, drop))

    def descended(self, distance):
        total = 0.0
        for center_distance, half_length, drop in self.descents:
            apart = (distance - center_distance + self.loop_length / 2.0) % self.loop_length - self.loop_length / 2.0
            total += drop * (smoothstep(-half_length, half_length, apart)
                             - smoothstep(half_length, half_length + self.descent_recovery, apart))
        return total

    @property
    def loop_length(self):
        return 2.0 * math.pi * self.loop_radius

    def ground_point(self, distance):
        loop_angle = distance / self.loop_radius
        return self.loop_radius * math.sin(loop_angle), -self.loop_radius * math.cos(loop_angle)

    def submersion(self, distance):
        fraction = (distance / self.loop_length) % 1.0
        dive_start, dive_bottom, rise_start, rise_end = self.dive_window
        return smoothstep(dive_start, dive_bottom, fraction) - smoothstep(rise_start, rise_end, fraction)

    def altitude(self, seconds, distance):
        return (self.cruise_altitude + (self.dive_altitude - self.cruise_altitude) * self.submersion(distance)
                - self.descended(distance))

    def look_down(self, seconds, distance):
        return self.cruise_look_down + (self.dive_look_down - self.cruise_look_down) * self.submersion(distance)


class ConcreteTexture:

    def __init__(self, seed):
        self.size = 128
        self.blotch_grids = (4, 8, 16, 32)
        self.blotch_weights = (0.45, 0.3, 0.15, 0.1)
        self.speckle_strength = 0.08
        self.base_gray = 205.0
        self.contrast = 90.0
        self.generator = numpy.random.default_rng(seed)

    def wrapped_noise(self, grid):
        cells = self.generator.random((grid, grid))
        tiled = numpy.tile(cells, (3, 3))
        gray = (tiled * 255.0).astype(numpy.uint8)
        small = pygame.surfarray.make_surface(numpy.repeat(gray[:, :, None], 3, axis=2))
        large = pygame.transform.smoothscale(small, (self.size * 3, self.size * 3))
        return pygame.surfarray.array3d(large)[self.size:self.size * 2, self.size:self.size * 2, 0] / 255.0

    def surface(self):
        blotches = sum(weight * self.wrapped_noise(grid) for grid, weight in zip(self.blotch_grids, self.blotch_weights))
        speckle = self.generator.random((self.size, self.size)) * self.speckle_strength
        gray = numpy.clip(self.base_gray + (blotches - 0.5 + speckle) * self.contrast, 0, 255).astype(numpy.uint8)
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        surface.blit(pygame.surfarray.make_surface(numpy.repeat(gray[:, :, None], 3, axis=2)), (0, 0))
        return surface


class FloodedCity:

    def __init__(self, sea, flight, concrete_texture):
        self.sea = sea
        self.flight = flight
        self.concrete_texture = concrete_texture
        self.generator = random.Random(7)
        self.base_level = -sea.seabed_depth - 6.0
        self.lot_spacing = 38.0
        self.lots_per_side = 7
        self.empty_lot_chance = 0.2
        self.lane_half_width = 9.0
        self.footprint_span = (12.0, 22.0)
        self.top_above_water_span = (-16.0, 12.0)
        self.skeleton_chance = 0.4
        self.textured_chance = 0.6
        self.lean_degrees = 4.0
        self.path_building_plans = ((0.50, Ruin1, (17.0, 16.0), 74.0, 1000, 1),
                                    (0.62, Ruin2, (19.0, 18.0), 72.0, 2000, 0),
                                    (0.74, Ruin1, (16.0, 18.0), 74.0, 3000, 1))
        self.passage_level_span = (50.5, 66.0)
        self.preferred_passage_level = 58.0
        self.seed_attempts = 600
        self.path_building_clearance = 3.0
        self.floor_hole_half_sizes = (1.6, 3.5)
        self.ruins = []
        self.path_buildings = []
        self.obstacles = []
        for plan in self.path_building_plans:
            self.place_on_path(*plan)
        self.place_on_lots()

    def lot_centers(self):
        half = (self.lots_per_side - 1) / 2.0
        for row in range(self.lots_per_side):
            for column in range(self.lots_per_side):
                yield (column - half) * self.lot_spacing, (row - half) * self.lot_spacing

    def blocks_lane(self, x, z, footprint):
        reach = math.hypot(*footprint) / 2.0
        if abs(math.hypot(x, z) - self.flight.loop_radius) < self.lane_half_width + reach:
            return True
        return any(math.hypot(x - path_x, z - path_z) < reach + path_reach + self.path_building_clearance
                   for path_x, path_z, path_reach in self.path_buildings)

    def place_on_lots(self):
        for index, (x, z) in enumerate(self.lot_centers()):
            footprint = (self.generator.uniform(*self.footprint_span), self.generator.uniform(*self.footprint_span))
            if self.generator.random() < self.empty_lot_chance or self.blocks_lane(x, z, footprint):
                continue
            height = -self.base_level + self.generator.uniform(*self.top_above_water_span)
            texture = self.concrete_texture if self.generator.random() < self.textured_chance else None
            ruin_kind = Ruin2 if self.generator.random() < self.skeleton_chance else Ruin1
            ruin = ruin_kind(footprint, height, texture=texture, seed=index)
            facing = self.generator.choice((0.0, 90.0, 180.0, 270.0)) + self.generator.uniform(-6.0, 6.0)
            lean = (self.generator.uniform(-self.lean_degrees, self.lean_degrees),
                    self.generator.uniform(-self.lean_degrees, self.lean_degrees))
            self.ruins.append((x, self.base_level, z, facing, lean, ruin))

    def passage_score(self, passage):
        across, entry_level, _ = passage
        return abs(entry_level - self.preferred_passage_level) + 0.5 * abs(across)

    def ruin_with_passage(self, ruin_kind, footprint, height, first_seed, storeys_down):
        lowest, highest = self.passage_level_span
        texture = self.concrete_texture if ruin_kind is Ruin1 else None
        for seed in range(first_seed, first_seed + self.seed_attempts):
            ruin = ruin_kind(footprint, height, texture=texture, seed=seed)
            passages = [passage for passage in ruin.passages(storeys_down) if lowest <= passage[1] <= highest]
            if passages:
                return ruin, min(passages, key=self.passage_score)
        raise RuntimeError(f"no {ruin_kind.__name__} with a passage between {lowest} and {highest} m")

    def place_on_path(self, loop_fraction, ruin_kind, footprint, height, first_seed, storeys_down):
        ruin, (across, level, exit_level) = self.ruin_with_passage(ruin_kind, footprint, height, first_seed,
                                                                   storeys_down)
        radius = self.flight.loop_radius
        angle = 2.0 * math.pi * loop_fraction
        half_angle = math.asin(ruin.depth / 2.0 / radius)
        if exit_level < level:
            ruin.add_holed_floor(ruin.storey_below(level), (across, 0.0), self.floor_hole_half_sizes)
            self.flight.add_descent(loop_fraction * self.flight.loop_length, radius * half_angle, level - exit_level)
        chord_middle = radius * math.cos(half_angle)
        facing = math.atan2(-math.cos(angle), -math.sin(angle))
        across_x, across_z = math.cos(facing), -math.sin(facing)
        x = chord_middle * math.sin(angle) - across * across_x
        z = -chord_middle * math.cos(angle) - across * across_z
        base = self.flight.dive_altitude - level
        reach = math.hypot(ruin.width, ruin.depth) / 2.0
        self.ruins.append((x, base, z, math.degrees(facing), (0.0, 0.0), ruin))
        self.path_buildings.append((x, z, reach))
        self.obstacles.append((angle, reach / radius, base + ruin.highest_top))

    def draw(self):
        for x, base, z, facing, (lean_x, lean_z), ruin in self.ruins:
            glPushMatrix()
            glTranslatef(x, base, z)
            glRotatef(facing, 0.0, 1.0, 0.0)
            glRotatef(lean_x, 1.0, 0.0, 0.0)
            glRotatef(lean_z, 0.0, 0.0, 1.0)
            ruin.render()
            glPopMatrix()


class SharkSwimmer:

    def __init__(self, shark, lane_radius, lane_offset, depth, clockwise, angle, speed, weave, bob_height, bob_period,
                 bob_phase, obstacles):
        self.shark = shark
        self.lane_radius = lane_radius
        self.lane_offset = lane_offset
        self.depth = depth
        self.direction = -1.0 if clockwise else 1.0
        self.start_angle = angle
        self.speed = speed
        self.weave_amplitude, self.weave_wavelength, self.weave_phase = weave
        self.bob_height = bob_height
        self.bob_period = bob_period
        self.bob_phase = bob_phase
        self.obstacles = obstacles
        self.obstacle_ramp = 30.0
        self.obstacle_clearance = 2.0 + shark.length * 0.3
        self.look_ahead_seconds = 0.05
        self.seconds = 0.0
        self.travelled = 0.0

    def over_obstacles(self, angle, level):
        for obstacle_angle, half_span, top in self.obstacles:
            apart = abs(math.atan2(math.sin(angle - obstacle_angle), math.cos(angle - obstacle_angle)))
            lift = 1.0 - smoothstep(half_span, half_span + self.obstacle_ramp / self.lane_radius, apart)
            level += (max(level, top + self.obstacle_clearance) - level) * lift
        return level

    def position_at(self, travelled, seconds):
        angle = self.start_angle + self.direction * travelled / self.lane_radius
        weave_angle = 2.0 * math.pi * travelled / self.weave_wavelength + self.weave_phase
        radius = self.lane_radius + self.lane_offset + self.direction * self.weave_amplitude * math.sin(weave_angle)
        bobbing = self.depth + self.bob_height * math.sin(2.0 * math.pi * seconds / self.bob_period + self.bob_phase)
        return radius * math.sin(angle), self.over_obstacles(angle, bobbing), -radius * math.cos(angle)

    def update(self, seconds):
        self.seconds += seconds
        self.travelled += self.speed * seconds
        here = self.position_at(self.travelled, self.seconds)
        ahead = self.position_at(self.travelled + self.speed * self.look_ahead_seconds,
                                 self.seconds + self.look_ahead_seconds)
        self.shark.position = here
        self.shark.swim_toward(tuple(later - now for later, now in zip(ahead, here)))
        self.shark.update(seconds)


class SharkShoal:

    def __init__(self, flight, obstacles):
        self.obstacles = obstacles
        self.generator = random.Random(23)
        self.count = 60
        self.smallest_length = 2.0
        self.size_ratio = 3.0
        self.depth_span = (-44.0, -7.0)
        self.body_lengths_per_second = (0.45, 0.8)
        self.lane_radius = flight.loop_radius
        self.lane_spread = 2.0
        self.weave_amplitude_span = (2.5, 4.5)
        self.weave_wavelength_span = (25.0, 50.0)
        self.bob_height_span = (0.5, 3.0)
        self.bob_period_span = (14.0, 28.0)
        self.model = SharkModel()
        self.swimmers = [self.make_swimmer(length, index % 3) for index, length in enumerate(self.shuffled_lengths())]

    def shuffled_lengths(self):
        largest_length = self.smallest_length * self.size_ratio
        step = (largest_length - self.smallest_length) / (self.count - 1)
        lengths = [self.smallest_length + step * index for index in range(self.count)]
        self.generator.shuffle(lengths)
        return lengths

    def weave_for(self, third):
        if third == 0:
            return 0.0, 1.0, 0.0
        first_turn = 0.0 if third == 1 else math.pi
        return (self.generator.uniform(*self.weave_amplitude_span), self.generator.uniform(*self.weave_wavelength_span),
                first_turn)

    def make_swimmer(self, length, third):
        return SharkSwimmer(Shark(length, self.model),
                            self.lane_radius,
                            self.generator.uniform(-self.lane_spread, self.lane_spread),
                            self.generator.uniform(*self.depth_span),
                            self.generator.random() < 0.5,
                            self.generator.uniform(0.0, 2.0 * math.pi),
                            length * self.generator.uniform(*self.body_lengths_per_second),
                            self.weave_for(third),
                            self.generator.uniform(*self.bob_height_span),
                            self.generator.uniform(*self.bob_period_span),
                            self.generator.uniform(0.0, 2.0 * math.pi),
                            self.obstacles)

    def update(self, seconds):
        for swimmer in self.swimmers:
            swimmer.update(seconds)

    def draw(self):
        for swimmer in self.swimmers:
            swimmer.shark.render()


class SeaTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.longest_frame_seconds = 0.1
        self.speed_step = 1.25
        self.sun_azimuth_step = 10.0
        self.sun_elevation_step = 2.0
        self.caption = ("Sea / {} - {:.0f} fps, {:.0f} m/s, altitude {:.1f} m, sun {:.0f}/{:.0f} deg  "
                        "(SPACE switch scene, UP/DOWN speed, LEFT/RIGHT sun azimuth, PGUP/PGDN sun elevation, "
                        "P pause, ESC quit)")
        self.caption_refresh_seconds = 0.5
        self.seconds_since_caption = 0.0
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.sea = Sea(self.window_size)
        self.open_sea_flight = OpenSeaFlight(self.sea)
        self.dive_flight = DiveFlight(self.sea)
        concrete_texture = TextureFactory().upload(ConcreteTexture(seed=11).surface())
        self.flooded_city = FloodedCity(self.sea, self.dive_flight, concrete_texture)
        self.shark_shoal = SharkShoal(self.dive_flight, self.flooded_city.obstacles)
        self.shark_shoal.update(0.0)
        self.scenes = (("open sea", self.open_sea_flight, None),
                       ("flooded city", self.dive_flight, self.draw_flooded_city))
        self.scene_index = 0
        self.paused = False
        self.running = True
        self.show_caption()

    def draw_flooded_city(self):
        self.flooded_city.draw()
        self.shark_shoal.draw()

    @property
    def scene(self):
        return self.scenes[self.scene_index]

    def show_caption(self):
        name, flight, _ = self.scene
        eye, _, _, _ = flight.camera()
        pygame.display.set_caption(self.caption.format(name, self.clock.get_fps(), flight.speed, eye[1],
                                                       self.sea.sun_azimuth_degrees, self.sea.sun_elevation_degrees))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        _, flight, _ = self.scene
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.scene_index = (self.scene_index + 1) % len(self.scenes)
        elif key == pygame.K_p:
            self.paused = not self.paused
        elif key == pygame.K_UP:
            flight.speed *= self.speed_step
        elif key == pygame.K_DOWN:
            flight.speed /= self.speed_step
        elif key == pygame.K_LEFT:
            self.sea.sun_azimuth_degrees = (self.sea.sun_azimuth_degrees - self.sun_azimuth_step) % 360.0
        elif key == pygame.K_RIGHT:
            self.sea.sun_azimuth_degrees = (self.sea.sun_azimuth_degrees + self.sun_azimuth_step) % 360.0
        elif key == pygame.K_PAGEUP:
            self.sea.sun_elevation_degrees = min(89.0, self.sea.sun_elevation_degrees + self.sun_elevation_step)
        elif key == pygame.K_PAGEDOWN:
            self.sea.sun_elevation_degrees = max(1.0, self.sea.sun_elevation_degrees - self.sun_elevation_step)
        self.show_caption()

    def update(self, seconds):
        if not self.paused:
            step = min(seconds, self.longest_frame_seconds)
            self.sea.update(step)
            self.scene[1].update(step)
            if self.scene[1] is self.dive_flight:
                self.shark_shoal.update(step)
        self.seconds_since_caption += seconds
        if self.seconds_since_caption >= self.caption_refresh_seconds:
            self.seconds_since_caption = 0.0
            self.show_caption()

    def draw(self):
        _, flight, draw_scene = self.scene
        glClear(GL_COLOR_BUFFER_BIT)
        self.sea.render(*flight.camera(), draw_scene=draw_scene)
        pygame.display.flip()

    def run(self):
        while self.running:
            seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.handle_events()
            self.update(seconds)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    SeaTest().run()
