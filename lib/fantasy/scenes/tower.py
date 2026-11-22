import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, StatueMesh, mottling, normalized, surface_normals, unit_or_fallback
from lib.fantasy.anatomy import smoothstep
from lib.fantasy.scenes.bridge import Embers, LavaRiver, SineNoise
from lib.fantasy.tower import DarkTower
from lib.fantasy.troll import StoneLumps


class CameraFlight:

    def __init__(self, keyframes):
        self.keyframes = keyframes
        self.duration = keyframes[-1][0]

    def segment(self, seconds):
        times = [time for time, _, _ in self.keyframes]
        index = min(max(int(numpy.searchsorted(times, seconds, side="right")) - 1, 0), len(times) - 2)
        span = times[index + 1] - times[index]
        return index, 0.0 if span <= 0.0 else min(max((seconds - times[index]) / span, 0.0), 1.0)

    def spline(self, slot, index, local):
        last = len(self.keyframes) - 1
        before, start, end, after = (numpy.asarray(self.keyframes[min(max(index + step, 0), last)][slot],
                                                   dtype=numpy.float64) for step in (-1, 0, 1, 2))
        if numpy.allclose(start, end):
            return start
        return 0.5 * (2.0 * start + (end - before) * local
                      + (2.0 * before - 5.0 * start + 4.0 * end - after) * local ** 2
                      + (3.0 * start - before - 3.0 * end + after) * local ** 3)

    def view(self, seconds):
        index, local = self.segment(seconds % self.duration)
        return tuple(self.spline(1, index, local)), tuple(self.spline(2, index, local))


class TowerScene:

    def __init__(self, seed=8):
        self.generator = numpy.random.default_rng(seed)
        self.acting = True
        self.talking = False
        self.seconds = 0.0
        self.river_start = -12.0
        self.river_end = 10.0
        self.rapids_center = 100.0
        self.rapids_length = 1.0
        self.terrain_extent = ((-10.0, 9.0), (-12.0, 10.0))
        self.terrain_step = 0.15
        self.plateau_radius = 2.2
        self.rock_count = 60
        self.tree_count = 7
        self.star_count = 500
        self.ground_color = (0.12, 0.12, 0.13)
        self.scorched_color = (0.05, 0.04, 0.04)
        self.rock_color = (0.16, 0.16, 0.17)
        self.tree_color = (0.06, 0.06, 0.065)
        self.moon_direction = normalized((-0.7, 0.32, -0.62))
        self.moon_distance = 36.0
        self.moon_radius = 2.2
        self.moon_halo_radius = 7.0
        self.moon_color = numpy.array((0.86, 0.91, 1.0))
        self.moon_halo_color = (0.45, 0.58, 0.85)
        self.moonlight_color = (0.42, 0.52, 0.78, 1.0)
        self.moonlight_specular = (0.25, 0.32, 0.45, 1.0)
        self.ambient = (0.03, 0.035, 0.05, 1.0)
        self.lava_light_color = numpy.array((1.0, 0.42, 0.12))
        self.lava_light_strength = 1.6
        self.lava_light_height = 0.55
        self.lava_light_depths = (-8.0, -4.5, -1.8, 0.8, 3.5, 7.0)
        self.lava_light_attenuation = (0.25, 0.22, 0.12)
        self.flicker_rates = self.generator.uniform(5.0, 11.0, len(self.lava_light_depths))
        self.flicker_phases = self.generator.uniform(0.0, 2.0 * math.pi, len(self.lava_light_depths))
        self.fog_color = (0.03, 0.035, 0.06, 1.0)
        self.fog_density = 0.028
        self.ground_noise = SineNoise(self.generator, 5, 0.5, 2)
        self.moon_noise = SineNoise(self.generator, 5, 3.0, 2)
        self.tower = DarkTower()
        self.terrain = self.build_terrain()
        self.mesh = StatueMesh()
        self.sculptor = Sculptor(self.mesh)
        self.build_rocks()
        self.build_trees()
        self.scenery = self.mesh.arrays()
        self.stars = self.build_stars()
        self.moon = self.build_moon()
        self.lava = LavaRiver(self)
        self.embers = Embers(self, 450)
        self.flight = CameraFlight(self.flight_keyframes())

    def river_center(self, depth):
        return 3.2 + 0.35 * numpy.sin(0.35 * numpy.asarray(depth) + 0.5)

    def lava_half_width(self, depth):
        return 0.9 + 0.15 * numpy.sin(0.4 * numpy.asarray(depth) + 1.0)

    def lava_level(self, depth):
        return numpy.full(numpy.shape(depth), -0.25) if numpy.ndim(depth) else -0.25

    def ground_height(self, x, depth):
        distance = numpy.abs(x - self.river_center(depth))
        bank = smoothstep((distance - 0.85 * self.lava_half_width(depth)) / 1.6)
        height = (-0.55 + 0.55 * bank + 0.25 * bank * self.ground_noise(x * 0.6, depth * 0.6)
                  + 0.06 * numpy.clip(distance - 4.0, 0.0, None) * self.ground_noise(depth * 0.3, x * 0.3))
        plateau = smoothstep((self.plateau_radius - numpy.hypot(x, depth)) / 0.8)
        return height * (1.0 - plateau)

    def build_terrain(self):
        (left, right), (back, front) = self.terrain_extent
        xs = numpy.arange(left, right + 1e-6, self.terrain_step)
        depths = numpy.arange(back, front + 1e-6, self.terrain_step)
        depth, x = numpy.meshgrid(depths, xs, indexing="ij")
        grid = numpy.stack((x, self.ground_height(x, depth), depth), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, grid - (0.0, 1.0, 0.0), False), numpy.array((0.0, 1.0, 0.0)))
        distance = numpy.abs(x - self.river_center(depth)) - self.lava_half_width(depth)
        scorch = (1.0 - smoothstep(distance / 1.1))[..., None]
        colors = numpy.asarray(self.ground_color) * (1.0 - scorch) + numpy.asarray(self.scorched_color) * scorch
        colors = colors * mottling(grid * 0.5, 0.3)[..., None]
        mesh = StatueMesh()
        mesh.add_grid(grid, normals, colors)
        return mesh.arrays()

    def open_ground(self, x, depth, margin):
        clear_of_lava = abs(x - float(self.river_center(depth))) > float(self.lava_half_width(depth)) + margin
        return clear_of_lava and math.hypot(x, depth) > self.plateau_radius - 0.6 + margin

    def build_rocks(self):
        generator = self.generator
        (left, right), (back, front) = self.terrain_extent
        placed = 0
        while placed < self.rock_count:
            x, depth = generator.uniform(left + 1.0, right - 1.0), generator.uniform(back + 1.0, front - 1.0)
            if not self.open_ground(x, depth, 0.15):
                continue
            size = generator.uniform(0.1, 0.5)
            ground = float(self.ground_height(x, depth))
            axis = (generator.normal(), generator.uniform(-0.3, 0.3), generator.normal())
            shade = generator.uniform(0.75, 1.15)
            width, height = size * generator.uniform(0.6, 0.95), size * generator.uniform(0.45, 0.8)
            self.sculptor.ellipsoid((x, ground + size * 0.2, depth), axis, size, width, height,
                                    tuple(numpy.asarray(self.rock_color) * shade), up_hint=(0.0, 1.0, 0.0),
                                    scales=StoneLumps(size * 0.45, 0.35))
            placed += 1

    def build_trees(self):
        generator = self.generator
        (left, right), (back, front) = self.terrain_extent
        placed = 0
        while placed < self.tree_count:
            x, depth = generator.uniform(left + 1.0, right - 1.0), generator.uniform(back + 1.0, front - 2.0)
            if not self.open_ground(x, depth, 1.2):
                continue
            base = numpy.array((x, float(self.ground_height(x, depth)) - 0.05, depth))
            height = generator.uniform(1.6, 3.0)
            self.grow_branch(base, normalized((generator.normal(0.0, 0.15), 1.0, generator.normal(0.0, 0.15))),
                             height, 0.03 * height, 3)
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
        directions[:, 1] = numpy.abs(directions[:, 1]) + 0.1
        directions /= numpy.linalg.norm(directions, axis=1, keepdims=True)
        brightness = generator.uniform(0.2, 0.75, self.star_count)
        colors = numpy.stack((brightness * 0.9, brightness * 0.95, brightness), axis=-1)
        return (numpy.ascontiguousarray((directions * 40.0).astype(numpy.float32)),
                numpy.ascontiguousarray(colors.astype(numpy.float32)))

    def moon_axes(self):
        toward_viewer = -self.moon_direction
        across = normalized(numpy.cross((0.0, 1.0, 0.0), toward_viewer))
        upward = numpy.cross(toward_viewer, across)
        return self.moon_direction * self.moon_distance, across, upward

    def build_moon(self):
        center, across, upward = self.moon_axes()
        rings, segments = 24, 64
        radius = numpy.linspace(0.0, 1.0, rings)[:, None]
        angle = numpy.linspace(0.0, 2.0 * math.pi, segments + 1)[None, :]
        u, v = radius * numpy.cos(angle), radius * numpy.sin(angle)
        grid = center + (across * u[..., None] + upward * v[..., None]) * self.moon_radius
        maria = smoothstep((self.moon_noise(u * 1.3 + 0.4, v * 1.3 - 0.2) + 0.1) / 0.5)
        craters = 0.5 + 0.5 * self.moon_noise(u * 4.0, v * 4.0)
        limb = 1.0 - 0.25 * radius ** 3
        shade = (0.78 + 0.22 * (1.0 - maria) - 0.08 * craters) * limb
        colors = self.moon_color * shade[..., None]
        rows, columns = grid.shape[:2]
        row = numpy.arange(rows - 1)[:, None]
        column = numpy.arange(columns - 1)[None, :]
        corner = row * columns + column
        quads = numpy.stack((corner, corner + columns, corner + 1, corner + 1, corner + columns, corner + columns + 1),
                            axis=-1)
        return (numpy.ascontiguousarray(grid.reshape(-1, 3).astype(numpy.float32)),
                numpy.ascontiguousarray(colors.reshape(-1, 3).astype(numpy.float32)),
                numpy.ascontiguousarray(quads.reshape(-1).astype(numpy.uint32)))

    def flight_keyframes(self):
        window, outward = self.tower.model.window_center()
        moon = self.moon_direction * 14.0
        tower_middle = (0.0, 2.6, 0.0)
        lava_watch = (5.4, 1.0, 1.6)
        return [(0.0, (0.5, 2.2, 8.5), tower_middle),
                (4.0, (-5.8, 2.8, 5.8), tower_middle),
                (8.0, (-7.2, 3.4, -1.5), (0.0, 2.8, 0.0)),
                (12.0, (-2.0, 2.6, -7.5), (0.0, 3.0, 0.0)),
                (16.0, lava_watch, tuple(numpy.asarray(lava_watch) + moon)),
                (20.0, (5.1, 1.1, 0.8), tuple(numpy.asarray((5.1, 1.1, 0.8)) + moon)),
                (24.0, (4.7, 1.4, 6.5), (3.1, -0.25, -2.0)),
                (28.0, (2.2, 1.7, 4.2), (3.4, -0.25, -0.5)),
                (32.0, (1.4, 3.5, 3.6), tuple(window)),
                (35.0, tuple(window + outward * 0.7 + (0.0, 0.05, 0.0)), tuple(window)),
                (37.5, tuple(window + outward * 0.38 + (0.0, 0.02, 0.0)), tuple(window - outward * 0.3)),
                (39.5, tuple(window + outward * 0.24), tuple(window - outward * 0.5)),
                (42.5, tuple(window + outward * 0.24), tuple(window - outward * 0.5)),
                (46.0, (1.2, 3.0, 5.5), tower_middle),
                (50.0, (0.5, 2.2, 8.5), tower_middle)]

    def camera_view(self):
        return self.flight.view(self.seconds)

    def restart(self):
        self.seconds = 0.0

    def update(self, seconds):
        self.seconds += seconds
        self.tower.update(seconds)
        self.lava.paint(self.seconds)
        self.embers.update(seconds)

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
        glLightfv(GL_LIGHT0, GL_POSITION, (*self.moon_direction, 0.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, self.moonlight_color)
        glLightfv(GL_LIGHT0, GL_SPECULAR, self.moonlight_specular)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        constant, linear, quadratic = self.lava_light_attenuation
        for number, (depth, strength) in enumerate(zip(self.lava_light_depths, self.lava_light_strengths())):
            light = GL_LIGHT1 + number
            glEnable(light)
            color = (*(self.lava_light_color * strength), 1.0)
            glLightfv(light, GL_POSITION, (float(self.river_center(depth)), self.lava_level(depth)
                                           + self.lava_light_height, depth, 1.0))
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

    def render_sky(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDepthMask(GL_FALSE)
        positions, colors = self.stars
        glPointSize(1.5)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawArrays(GL_POINTS, 0, len(positions))
        center, across, upward = self.moon_axes()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*self.moon_halo_color, 0.35)
        glVertex3f(*center)
        glColor4f(*self.moon_halo_color, 0.0)
        for step in range(65):
            angle = 2.0 * math.pi * step / 64
            glVertex3f(*(center + (across * math.cos(angle) + upward * math.sin(angle)) * self.moon_halo_radius))
        glEnd()
        glDisable(GL_BLEND)
        moon_positions, moon_colors, moon_indices = self.moon
        glVertexPointer(3, GL_FLOAT, 0, moon_positions)
        glColorPointer(3, GL_FLOAT, 0, moon_colors)
        glDrawElements(GL_TRIANGLES, len(moon_indices), GL_UNSIGNED_INT, moon_indices)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDepthMask(GL_TRUE)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)

    def render(self):
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT | GL_FOG_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT
                     | GL_POINT_BIT | GL_CURRENT_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.08, 0.08, 0.1, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 12.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))
        self.setup_lights()
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, self.fog_color)
        self.render_sky()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        self.draw(*self.terrain)
        self.draw(*self.scenery)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.tower.render()
        self.lava.render()
        self.embers.render()
        glPopAttrib()
