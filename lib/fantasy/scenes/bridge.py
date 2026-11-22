import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, StatueMesh, catmull_rom, mottling, normalized, surface_normals, \
    unit_or_fallback
from lib.fantasy.anatomy import smoothstep
from lib.fantasy.troll import StoneLumps, Troll


class SineNoise:

    def __init__(self, generator, octaves, base_frequency, dimensions):
        self.waves = []
        for octave in range(octaves):
            direction = generator.normal(size=dimensions)
            direction /= numpy.linalg.norm(direction)
            frequency = base_frequency * 2.0 ** octave * generator.uniform(0.8, 1.25)
            self.waves.append((direction * frequency, generator.uniform(0.0, 2.0 * math.pi), 0.55 ** octave))
        self.total_amplitude = sum(amplitude for _, _, amplitude in self.waves)

    def __call__(self, *coordinates, drift=0.0):
        value = 0.0
        for index, (direction, phase, amplitude) in enumerate(self.waves):
            projection = sum(component * coordinate for component, coordinate in zip(direction, coordinates))
            value = value + amplitude * numpy.sin(projection + phase + drift * (1.0 + 0.37 * index))
        return value / self.total_amplitude


def slab_sweep(mesh, centers, up_hint, half_widths, half_heights, color, roughness=0.0, boxiness=8.0, segments=20,
               noise=None):
    centers = numpy.asarray(centers, dtype=numpy.float64)
    count = len(centers)
    half_widths = numpy.broadcast_to(numpy.asarray(half_widths, dtype=numpy.float64), (count,))
    half_heights = numpy.broadcast_to(numpy.asarray(half_heights, dtype=numpy.float64), (count,))
    tangents = normalized(numpy.gradient(centers, axis=0))
    sides = normalized(numpy.cross(tangents, numpy.asarray(up_hint, dtype=numpy.float64)))
    ups = numpy.cross(sides, tangents)
    closed = 1e-4
    centers = numpy.vstack((centers[:1], centers, centers[-1:]))
    sides = numpy.vstack((sides[:1], sides, sides[-1:]))
    ups = numpy.vstack((ups[:1], ups, ups[-1:]))
    half_widths = numpy.concatenate(((half_widths[0] * closed,), half_widths, (half_widths[-1] * closed,)))
    half_heights = numpy.concatenate(((half_heights[0] * closed,), half_heights, (half_heights[-1] * closed,)))
    around = numpy.linspace(0.0, 2.0 * math.pi, segments + 1)
    cosine, sine = numpy.cos(around), numpy.sin(around)
    across = numpy.sign(cosine) * numpy.abs(cosine) ** (2.0 / boxiness)
    upward = numpy.sign(sine) * numpy.abs(sine) ** (2.0 / boxiness)
    grid = (centers[:, None, :] + sides[:, None, :] * (half_widths[:, None] * across[None, :])[..., None]
            + ups[:, None, :] * (half_heights[:, None] * upward[None, :])[..., None])
    if roughness > 0.0 and noise is not None:
        outward = unit_or_fallback(grid - centers[:, None, :], numpy.zeros(3))
        bumps = noise(grid[..., 0] * 9.0, grid[..., 1] * 9.0, grid[..., 2] * 9.0)
        thickness = numpy.minimum(half_widths, half_heights)[:, None]
        grid = grid + outward * (roughness * thickness * bumps)[..., None]
    normals = unit_or_fallback(surface_normals(grid, centers[:, None, :], True), numpy.array((0.0, 1.0, 0.0)))
    colors = numpy.asarray(color) * mottling(grid, 0.18)[..., None]
    mesh.add_grid(grid, normals, colors)


class LavaRiver:

    def __init__(self, scene):
        self.scene = scene
        generator = numpy.random.default_rng(31)
        self.crust_noise = SineNoise(generator, 5, 2.2, 2)
        self.swirl_noise = SineNoise(generator, 3, 0.9, 2)
        self.crust = numpy.array((0.10, 0.015, 0.005))
        self.hot = numpy.array((1.0, 0.36, 0.04))
        self.white_hot = numpy.array((1.0, 0.86, 0.42))
        self.flow_speed = 0.22
        self.churn_speed = 0.35
        self.crack_sharpness = 0.07
        self.width_scale = 1.6
        along = numpy.linspace(scene.river_start, scene.river_end, 230)
        across = numpy.linspace(-1.0, 1.0, 44)
        self.along, self.across = numpy.meshgrid(along, across, indexing="ij")
        center = scene.river_center(self.along)
        half_width = scene.lava_half_width(self.along) * self.width_scale
        positions = numpy.stack((center + self.across * half_width, scene.lava_level(self.along),
                                 self.along), axis=-1)
        rows, columns = self.along.shape
        row = numpy.arange(rows - 1)[:, None]
        column = numpy.arange(columns - 1)[None, :]
        corner = row * columns + column
        quads = numpy.stack((corner, corner + columns, corner + 1, corner + 1, corner + columns, corner + columns + 1),
                            axis=-1)
        self.positions = numpy.ascontiguousarray(positions.reshape(-1, 3).astype(numpy.float32))
        self.indices = numpy.ascontiguousarray(quads.reshape(-1).astype(numpy.uint32))
        self.colors = numpy.zeros_like(self.positions)
        self.rapids = numpy.exp(-((self.along - scene.rapids_center) / scene.rapids_length) ** 2)
        self.edge_cooling = smoothstep((numpy.abs(self.across) * self.width_scale - 0.75) / 0.5)
        self.paint(0.0)

    def paint(self, seconds):
        flowing = self.along - self.flow_speed * seconds * (1.0 + 2.5 * self.rapids)
        swirl = self.swirl_noise(flowing * 0.8, self.across * 1.5, drift=seconds * self.churn_speed)
        crust = self.crust_noise(flowing * 1.3 + swirl * 0.6, self.across * 2.2, drift=seconds * self.churn_speed)
        heat = smoothstep((crust + 0.15) / 0.7) * (1.0 - 0.75 * self.edge_cooling) + 0.6 * self.rapids
        cracks = numpy.exp(-(crust / self.crack_sharpness) ** 2) * (1.0 - self.edge_cooling)
        heat = numpy.clip(heat, 0.0, 1.0)[..., None]
        colors = self.crust * (1.0 - heat) + self.hot * heat
        colors = colors + (self.white_hot - colors) * numpy.clip(cracks * 0.7 + self.rapids * heat[..., 0] * 0.5,
                                                                 0.0, 1.0)[..., None]
        self.colors[:] = colors.reshape(-1, 3)

    def render(self):
        glDisable(GL_LIGHTING)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        glColorPointer(3, GL_FLOAT, 0, self.colors)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glEnable(GL_LIGHTING)


class Embers:

    def __init__(self, scene, count=320):
        self.scene = scene
        self.generator = numpy.random.default_rng(41)
        self.count = count
        self.rise = (0.25, 0.8)
        self.drift = 0.12
        self.life = (1.2, 3.2)
        self.point_size = 3.0
        self.hot = numpy.array((1.0, 0.75, 0.3))
        self.cool = numpy.array((0.8, 0.15, 0.02))
        self.positions = numpy.zeros((count, 3), dtype=numpy.float32)
        self.velocities = numpy.zeros((count, 3), dtype=numpy.float32)
        self.ages = numpy.zeros(count, dtype=numpy.float32)
        self.lives = numpy.ones(count, dtype=numpy.float32)
        self.colors = numpy.zeros((count, 4), dtype=numpy.float32)
        self.respawn(numpy.ones(count, dtype=bool))
        self.ages[:] = self.generator.uniform(0.0, 1.0, count) * self.lives

    def respawn(self, mask):
        generator = self.generator
        scene = self.scene
        count = int(mask.sum())
        along = generator.uniform(scene.river_start + 1.0, scene.river_end - 0.5, count)
        across = generator.uniform(-0.8, 0.8, count)
        self.positions[mask, 0] = scene.river_center(along) + across * scene.lava_half_width(along)
        self.positions[mask, 1] = scene.lava_level(along) + 0.02
        self.positions[mask, 2] = along
        self.velocities[mask, 0] = generator.normal(0.0, self.drift, count)
        self.velocities[mask, 1] = generator.uniform(*self.rise, count)
        self.velocities[mask, 2] = generator.normal(0.05, self.drift, count)
        self.ages[mask] = 0.0
        self.lives[mask] = generator.uniform(*self.life, count)

    def update(self, seconds):
        self.ages += seconds
        self.velocities[:, 0] += self.generator.normal(0.0, 0.3, self.count).astype(numpy.float32) * seconds
        self.positions += self.velocities * seconds
        self.respawn(self.ages >= self.lives)
        fade = numpy.clip(1.0 - self.ages / self.lives, 0.0, 1.0)
        self.colors[:, :3] = self.cool + (self.hot - self.cool) * fade[:, None]
        self.colors[:, 3] = fade

    def render(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glPointSize(self.point_size)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        glColorPointer(4, GL_FLOAT, 0, self.colors)
        glDrawArrays(GL_POINTS, 0, self.count)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


class LavaBridgeScene:

    def __init__(self, seed=3):
        self.generator = numpy.random.default_rng(seed)
        self.seconds = 0.0
        self.river_start = -7.0
        self.river_end = 4.5
        self.rapids_center = 1.5
        self.rapids_length = 0.35
        self.terrain_extent = (-6.0, 6.0)
        self.terrain_step = 0.1
        self.deck_span = (-2.9, 3.3)
        self.deck_top = 1.32
        self.deck_thickness = 0.14
        self.deck_half_width = 0.45
        self.deck_sag = 0.04
        self.pier_x = 0.45
        self.post_x = -1.25
        self.arch_points = ((1.10, -0.05, 0.0), (1.30, 0.70, 0.0), (1.75, 1.10, 0.0), (2.30, 1.19, 0.0),
                            (2.80, 1.25, 0.0))
        self.rock_count = 90
        self.approach_half_width = 0.7
        self.approach_overlap = 0.6
        self.tree_count = 9
        self.drip_count = 150
        self.star_count = 400
        self.ground_color = (0.14, 0.12, 0.11)
        self.scorched_color = (0.06, 0.045, 0.04)
        self.stone_color = (0.27, 0.25, 0.21)
        self.wood_color = (0.17, 0.13, 0.10)
        self.moss_color = (0.11, 0.12, 0.09)
        self.rock_color = (0.17, 0.16, 0.15)
        self.tree_color = (0.07, 0.06, 0.06)
        self.moonlight_direction = (-0.3, 0.8, -0.5, 0.0)
        self.moonlight_color = (0.09, 0.10, 0.16, 1.0)
        self.ambient = (0.025, 0.02, 0.025, 1.0)
        self.lava_light_color = numpy.array((1.0, 0.42, 0.12))
        self.lava_light_strength = 1.35
        self.lava_light_height = 0.45
        self.lava_light_depths = (-4.2, -2.4, -0.9, 0.5, 1.8, 3.4)
        self.lava_light_attenuation = (0.25, 0.35, 0.25)
        self.flicker_rates = self.generator.uniform(5.0, 11.0, len(self.lava_light_depths))
        self.flicker_phases = self.generator.uniform(0.0, 2.0 * math.pi, len(self.lava_light_depths))
        self.fog_color = (0.02, 0.012, 0.012, 1.0)
        self.fog_density = 0.045
        self.specular = (0.12, 0.08, 0.06, 1.0)
        self.shininess = 12.0
        self.ground_noise = SineNoise(self.generator, 5, 0.9, 2)
        self.stone_noise = SineNoise(self.generator, 4, 1.0, 3)
        self.terrain = self.build_terrain()
        self.mesh = StatueMesh()
        self.sculptor = Sculptor(self.mesh)
        self.build_bridge()
        self.build_rocks()
        self.build_trees()
        self.structures = self.mesh.arrays()
        self.stars = self.build_stars()
        self.lava = LavaRiver(self)
        self.embers = Embers(self)
        self.troll_height = 1.1
        self.troll_spot = 1.6
        self.troll = Troll(self.troll_height)
        self.troll.position = (self.troll_spot, self.deck_surface(self.troll_spot), 0.0)
        self.troll.yaw = -math.pi / 2.0

    @property
    def acting(self):
        return self.troll.acting

    @acting.setter
    def acting(self, value):
        self.troll.acting = value

    @property
    def talking(self):
        return self.troll.talking

    @talking.setter
    def talking(self, value):
        self.troll.talking = value

    def deck_surface(self, x):
        middle = (self.deck_span[0] + self.deck_span[1]) / 2.0
        reach = (self.deck_span[1] - self.deck_span[0]) / 2.0
        return self.deck_top - self.deck_sag * (1.0 - ((x - middle) / reach) ** 2)

    def river_center(self, depth):
        return 0.25 + 0.18 * depth + 0.15 * numpy.sin(0.7 * depth)

    def lava_half_width(self, depth):
        return 0.75 + 0.12 * numpy.sin(0.5 * depth + 1.0)

    def lava_level(self, depth):
        return 0.22 - 0.14 * smoothstep((numpy.asarray(depth) - self.rapids_center + 0.3) / 0.6)

    def ground_height(self, x, depth):
        distance = numpy.abs(x - self.river_center(depth))
        bank = smoothstep((distance - 0.85 * self.lava_half_width(depth)) / 1.4)
        rough = self.ground_noise(x, depth)
        return -0.15 + 1.45 * bank ** 1.1 + 0.14 * bank * rough + 0.18 * numpy.clip(distance - 2.6, 0.0, None)

    def build_terrain(self):
        low, high = self.terrain_extent
        xs = numpy.arange(low, high + 1e-6, self.terrain_step)
        depths = numpy.arange(self.river_start, self.river_end + 1e-6, self.terrain_step)
        depth, x = numpy.meshgrid(depths, xs, indexing="ij")
        height = self.ground_height(x, depth)
        grid = numpy.stack((x, height, depth), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, grid - (0.0, 1.0, 0.0), False), numpy.array((0.0, 1.0, 0.0)))
        distance = numpy.abs(x - self.river_center(depth)) - self.lava_half_width(depth)
        scorch = 1.0 - smoothstep(distance / 0.9)
        colors = (numpy.asarray(self.ground_color) * (1.0 - scorch[..., None])
                  + numpy.asarray(self.scorched_color) * scorch[..., None])
        colors = colors * mottling(grid * 0.6, 0.3)[..., None]
        mesh = StatueMesh()
        mesh.add_grid(grid, normals, colors)
        return mesh.arrays()

    def build_bridge(self):
        span = numpy.linspace(*self.deck_span, 140)
        middle = (self.deck_span[0] + self.deck_span[1]) / 2.0
        reach = (self.deck_span[1] - self.deck_span[0]) / 2.0
        sag = self.deck_sag * (1.0 - ((span - middle) / reach) ** 2)
        centers = numpy.stack((span, self.deck_top - self.deck_thickness / 2.0 - sag, numpy.zeros_like(span)), -1)
        chipped = self.deck_half_width * (1.0 + 0.06 * self.stone_noise(span * 3.0, span * 0.0, span * 1.7))
        slab_sweep(self.mesh, centers, (0.0, 0.0, -1.0), self.deck_thickness / 2.0, chipped, self.stone_color,
                   roughness=0.25, boxiness=10.0, segments=40, noise=self.stone_noise)
        deck_bottom = self.deck_top - self.deck_thickness
        pier = ((self.pier_x, -0.25, 0.0), (self.pier_x, deck_bottom - 0.12, 0.0))
        slab_sweep(self.mesh, numpy.linspace(*pier, 12), (0.0, 0.0, 1.0), 0.2, 0.34, self.stone_color,
                   roughness=0.35, segments=28, noise=self.stone_noise)
        self.beam((self.pier_x, deck_bottom - 0.06, -0.62), (self.pier_x, deck_bottom - 0.06, 0.62), 0.07, 0.06)
        for side in (-1.0, 1.0):
            depth = side * 0.34
            ground = float(self.ground_height(self.post_x, depth))
            self.beam((self.post_x, ground - 0.1, depth), (self.post_x, deck_bottom, depth), 0.06, 0.06)
            self.beam((self.post_x - 0.55, deck_bottom - 0.02, depth), (self.post_x, ground + 0.25, depth), 0.035,
                      0.035)
            self.beam((self.post_x + 0.6, deck_bottom - 0.02, depth), (self.post_x, ground + 0.25, depth), 0.035,
                      0.035)
        self.beam((self.post_x, deck_bottom - 0.05, -0.55), (self.post_x, deck_bottom - 0.05, 0.55), 0.06, 0.05)
        for start, end in (((-2.6, deck_bottom - 0.05, 0.3), (2.9, deck_bottom - 0.05, 0.3)),
                           ((-2.6, deck_bottom - 0.05, -0.3), (2.9, deck_bottom - 0.05, -0.3))):
            self.beam(start, end, 0.05, 0.05, samples=60)
        arch = numpy.asarray(self.arch_points)
        slab_sweep(self.mesh, catmull_rom(arch, 50), (0.0, 0.0, 1.0), 0.09, 0.36, self.stone_color, roughness=0.3,
                   segments=24, noise=self.stone_noise)
        self.add_drips(deck_bottom)

    def beam(self, start, end, half_width, half_height, samples=10):
        centers = numpy.linspace(start, end, samples)
        direction = normalized(numpy.asarray(end) - numpy.asarray(start))
        up_hint = (0.0, 1.0, 0.0) if abs(direction[1]) < 0.9 else (0.0, 0.0, 1.0)
        slab_sweep(self.mesh, centers, up_hint, half_width, half_height, self.wood_color, roughness=0.15,
                   boxiness=6.0, segments=16, noise=self.stone_noise)

    def add_drips(self, deck_bottom):
        generator = self.generator
        for _ in range(self.drip_count):
            x = generator.uniform(self.deck_span[0] + 0.4, self.deck_span[1] - 0.4)
            side = generator.choice((-1.0, 1.0))
            base = (x, deck_bottom + 0.02, side * (self.deck_half_width - generator.uniform(0.0, 0.05)))
            length = generator.uniform(0.04, 0.38) * generator.uniform(0.4, 1.0)
            self.sculptor.spike(base, (generator.normal(0.0, 0.08), -1.0, side * 0.08), length,
                                generator.uniform(0.008, 0.02), self.moss_color, rings=6, segments=6)

    def build_rocks(self):
        generator = self.generator
        placed = 0
        while placed < self.rock_count:
            depth = generator.uniform(self.river_start + 0.5, self.river_end - 0.3)
            x = generator.uniform(*self.terrain_extent)
            distance = abs(x - float(self.river_center(depth)))
            if distance < float(self.lava_half_width(depth)) + 0.1 or distance > 4.0:
                continue
            size = generator.uniform(0.08, 0.42) * (1.2 - 0.25 * min(distance, 3.0) / 3.0)
            ground = float(self.ground_height(x, depth))
            axis = (generator.normal(), generator.uniform(-0.3, 0.3), generator.normal())
            shade = generator.uniform(0.75, 1.15)
            width = size * generator.uniform(0.6, 0.95)
            height = size * generator.uniform(0.45, 0.8)
            placed += 1
            if self.blocks_bridge_approach(x, depth, size):
                continue
            self.sculptor.ellipsoid((x, ground + size * 0.25, depth), axis, size, width, height,
                                    tuple(numpy.asarray(self.rock_color) * shade), up_hint=(0.0, 1.0, 0.0),
                                    scales=StoneLumps(size * 0.45, 0.35))

    def blocks_bridge_approach(self, x, depth, size):
        near_end, far_end = self.deck_span
        beyond_deck = x - size < near_end + self.approach_overlap or x + size > far_end - self.approach_overlap
        return beyond_deck and abs(depth) - size < self.approach_half_width

    def build_trees(self):
        generator = self.generator
        placed = 0
        while placed < self.tree_count:
            depth = generator.uniform(self.river_start + 0.5, -1.2)
            x = generator.uniform(*self.terrain_extent)
            if abs(x - float(self.river_center(depth))) < 2.0:
                continue
            base = numpy.array((x, float(self.ground_height(x, depth)) - 0.05, depth))
            height = generator.uniform(1.4, 2.6)
            self.grow_branch(base, normalized((generator.normal(0.0, 0.15), 1.0, generator.normal(0.0, 0.15))),
                             height, 0.06 * height / 2.0, 3)
            placed += 1

    def grow_branch(self, base, direction, length, radius, depth):
        generator = self.generator
        bend = normalized(direction + generator.normal(0.0, 0.25, 3) * numpy.array((1.0, 0.3, 1.0)))
        middle = base + direction * length * 0.5 + bend * length * 0.08
        tip = base + bend * length
        self.sculptor.tube((base, middle, tip), ((0.0, radius, radius), (1.0, radius * 0.3, radius * 0.3)),
                           self.tree_color, rings=8, segments=6, cap_start=False, mottle=0.1)
        if depth == 0:
            return
        for _ in range(int(generator.integers(2, 4))):
            fork = base + (tip - base) * generator.uniform(0.45, 0.9)
            spread = normalized(bend + generator.normal(0.0, 0.8, 3) * numpy.array((1.0, 0.4, 1.0)))
            self.grow_branch(fork, spread, length * generator.uniform(0.35, 0.6), radius * 0.5, depth - 1)

    def build_stars(self):
        generator = self.generator
        directions = generator.normal(size=(self.star_count, 3))
        directions[:, 1] = numpy.abs(directions[:, 1]) + 0.15
        directions /= numpy.linalg.norm(directions, axis=1, keepdims=True)
        positions = (directions * 40.0).astype(numpy.float32)
        brightness = generator.uniform(0.15, 0.6, self.star_count)
        colors = numpy.stack((brightness, brightness * 0.95, brightness * 1.1), axis=-1).astype(numpy.float32)
        return numpy.ascontiguousarray(positions), numpy.ascontiguousarray(numpy.clip(colors, 0.0, 1.0))

    def restart(self):
        self.seconds = 0.0
        self.troll.restart()

    def update(self, seconds):
        self.seconds += seconds
        self.lava.paint(self.seconds)
        self.embers.update(seconds)
        self.troll.update(seconds)

    def focus(self):
        return 0.0, 0.0

    def lava_light_strengths(self):
        flicker = numpy.sin(self.seconds * self.flicker_rates + self.flicker_phases)
        return self.lava_light_strength * (1.0 + 0.12 * flicker + 0.05 * numpy.sin(self.seconds * 23.0
                                                                                  + self.flicker_phases))

    def setup_lights(self):
        for light in range(8):
            glDisable(GL_LIGHT0 + light)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, self.moonlight_direction)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, self.moonlight_color)
        glLightfv(GL_LIGHT0, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
        constant, linear, quadratic = self.lava_light_attenuation
        for number, (depth, strength) in enumerate(zip(self.lava_light_depths, self.lava_light_strengths())):
            light = GL_LIGHT1 + number
            glEnable(light)
            position = (float(self.river_center(depth)), float(self.lava_level(depth)) + self.lava_light_height, depth,
                        1.0)
            color = (*(self.lava_light_color * strength), 1.0)
            glLightfv(light, GL_POSITION, position)
            glLightfv(light, GL_DIFFUSE, color)
            glLightfv(light, GL_SPECULAR, color)
            glLightfv(light, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
            glLightf(light, GL_CONSTANT_ATTENUATION, constant)
            glLightf(light, GL_LINEAR_ATTENUATION, linear)
            glLightf(light, GL_QUADRATIC_ATTENUATION, quadratic)

    @staticmethod
    def draw(positions, normals, colors, indices):
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

    def render_stars(self):
        positions, colors = self.stars
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glPointSize(1.5)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawArrays(GL_POINTS, 0, len(positions))
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)

    def render(self):
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT | GL_FOG_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT
                     | GL_POINT_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.shininess)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))
        self.setup_lights()
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, self.fog_color)
        self.render_stars()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        self.draw(*self.terrain)
        self.draw(*self.structures)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.lava.render()
        self.troll.render()
        self.embers.render()
        glPopAttrib()
