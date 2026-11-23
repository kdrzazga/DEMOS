import math
import random

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, StatueMesh, mottling, normalized, surface_normals, unit_or_fallback
from lib.fantasy.anatomy import smoothstep
from lib.fantasy.carcass import Carcass
from lib.fantasy.scenes.bridge import Embers, SineNoise, slab_sweep
from lib.fantasy.scenes.tower import CameraFlight
from lib.fantasy.troll import StoneLumps
from lib.specialFX.rain import Rain


def grid_triangles(rows, columns):
    row = numpy.arange(rows - 1)[:, None]
    column = numpy.arange(columns - 1)[None, :]
    corner = row * columns + column
    quads = numpy.stack((corner, corner + columns, corner + 1, corner + 1, corner + columns, corner + columns + 1),
                        axis=-1)
    return numpy.ascontiguousarray(quads.reshape(-1).astype(numpy.uint32))


def flat_arrays(*arrays):
    return tuple(numpy.ascontiguousarray(array.reshape(-1, array.shape[-1]).astype(numpy.float32))
                 for array in arrays)


class LavaLake:

    def __init__(self, center, radii, level, generator):
        self.center = numpy.asarray(center, dtype=numpy.float64)
        self.radii = numpy.asarray(radii, dtype=numpy.float64)
        self.level = level
        self.crust_noise = SineNoise(generator, 5, 2.0, 2)
        self.swirl_noise = SineNoise(generator, 3, 0.8, 2)
        self.crust = numpy.array((0.10, 0.015, 0.005))
        self.hot = numpy.array((1.0, 0.36, 0.04))
        self.white_hot = numpy.array((1.0, 0.86, 0.42))
        self.churn_speed = 0.3
        self.circulation_speed = 0.05
        self.crack_sharpness = 0.07
        self.overlap = 1.06
        rings, segments = 40, 120
        self.reach = numpy.linspace(0.0, self.overlap, rings)[:, None] * numpy.ones((1, segments + 1))
        self.angle = numpy.linspace(0.0, 2.0 * math.pi, segments + 1)[None, :] * numpy.ones((rings, 1))
        x, z = self.surface_point(self.reach, self.angle)
        positions = numpy.stack((x, numpy.full_like(x, level), z), axis=-1)
        self.positions, = flat_arrays(positions)
        self.indices = grid_triangles(rings, segments + 1)
        self.colors = numpy.zeros_like(self.positions)
        self.edge_cooling = smoothstep((self.reach - 0.7) / 0.32)
        self.paint(0.0)

    def shoreline(self, angle):
        return 1.0 + 0.12 * numpy.sin(3.0 * angle + 1.0) + 0.07 * numpy.sin(5.0 * angle + 2.0)

    def surface_point(self, reach, angle):
        scale = reach * self.shoreline(angle)
        return (self.center[0] + self.radii[0] * scale * numpy.cos(angle),
                self.center[1] + self.radii[1] * scale * numpy.sin(angle))

    def reach_at(self, x, z):
        dx = (x - self.center[0]) / self.radii[0]
        dz = (z - self.center[1]) / self.radii[1]
        return numpy.hypot(dx, dz) / self.shoreline(numpy.arctan2(dz, dx))

    def paint(self, seconds):
        turning = self.angle + self.circulation_speed * seconds * (1.2 - self.reach)
        x = self.reach * numpy.cos(turning) * self.radii[0]
        z = self.reach * numpy.sin(turning) * self.radii[1]
        swirl = self.swirl_noise(x * 0.8, z * 0.8, drift=seconds * self.churn_speed)
        crust = self.crust_noise(x * 1.1 + swirl * 0.6, z * 1.1, drift=seconds * self.churn_speed)
        heat = numpy.clip(smoothstep((crust + 0.15) / 0.7) * (1.0 - 0.8 * self.edge_cooling), 0.0, 1.0)
        cracks = numpy.exp(-(crust / self.crack_sharpness) ** 2) * (1.0 - self.edge_cooling)
        colors = self.crust * (1.0 - heat[..., None]) + self.hot * heat[..., None]
        colors = colors + (self.white_hot - colors) * numpy.clip(cracks * 0.7, 0.0, 1.0)[..., None]
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


class LakeEmbers(Embers):

    def respawn(self, mask):
        lake = self.scene
        count = int(mask.sum())
        reach = numpy.sqrt(self.generator.uniform(0.0, 1.0, count)) * 0.85
        angle = self.generator.uniform(0.0, 2.0 * math.pi, count)
        x, z = lake.surface_point(reach, angle)
        self.positions[mask, 0] = x
        self.positions[mask, 1] = lake.level + 0.02
        self.positions[mask, 2] = z
        self.velocities[mask, 0] = self.generator.normal(0.0, self.drift, count)
        self.velocities[mask, 1] = self.generator.uniform(*self.rise, count)
        self.velocities[mask, 2] = self.generator.normal(0.0, self.drift, count)
        self.ages[mask] = 0.0
        self.lives[mask] = self.generator.uniform(*self.life, count)


class SwampWater:

    def __init__(self, extent, step, level, moon_direction, generator):
        self.level = level
        self.ripple_noise = SineNoise(generator, 4, 3.0, 2)
        self.deep = numpy.array((0.035, 0.04, 0.05))
        self.sheen = numpy.array((0.30, 0.34, 0.42))
        self.opacity = 0.9
        self.ripple_speed = 0.4
        (low_x, high_x), (low_z, high_z) = extent
        xs = numpy.arange(low_x, high_x + 1e-6, step)
        zs = numpy.arange(low_z, high_z + 1e-6, step)
        self.z, self.x = numpy.meshgrid(zs, xs, indexing="ij")
        positions = numpy.stack((self.x, numpy.full_like(self.x, level), self.z), axis=-1)
        self.positions, = flat_arrays(positions)
        self.indices = grid_triangles(*self.x.shape)
        toward_moon = normalized(numpy.asarray((moon_direction[0], 0.0, moon_direction[2])))
        along_moon = self.x * toward_moon[0] + self.z * toward_moon[2]
        self.moon_path = numpy.exp(-((self.x * toward_moon[2] - self.z * toward_moon[0]) / 3.5) ** 2)
        self.reflection = 0.25 + 0.75 * smoothstep((along_moon + 4.0) / 16.0)
        self.colors = numpy.zeros((len(self.positions), 4), dtype=numpy.float32)
        self.paint(0.0)

    def paint(self, seconds):
        ripple = self.ripple_noise(self.x, self.z, drift=seconds * self.ripple_speed)
        glint = self.reflection * (0.35 + 0.25 * ripple) + 0.45 * self.moon_path * self.reflection * (ripple > 0.2)
        colors = self.deep + (self.sheen - self.deep) * numpy.clip(glint, 0.0, 1.0)[..., None]
        self.colors[:, :3] = colors.reshape(-1, 3)
        self.colors[:, 3] = self.opacity

    def render(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        glColorPointer(4, GL_FLOAT, 0, self.colors)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


class NightSky:

    def __init__(self, moon_direction, generator):
        self.moon_direction = normalized(moon_direction)
        self.radius = 40.0
        self.moon_distance = 36.0
        self.moon_radius = 2.0
        self.moon_halo_radius = 7.5
        self.moon_color = numpy.array((0.86, 0.91, 1.0))
        self.moon_halo_color = (0.45, 0.56, 0.80)
        self.zenith = numpy.array((0.02, 0.022, 0.035))
        self.horizon = numpy.array((0.10, 0.11, 0.14))
        self.glow = numpy.array((0.30, 0.36, 0.50))
        self.cloud_shadow = 0.45
        self.cloud_noise = SineNoise(generator, 5, 2.2, 2)
        self.moon_noise = SineNoise(generator, 5, 3.0, 2)
        self.star_count = 350
        self.dome = self.build_dome()
        self.moon = self.build_moon()
        self.stars = self.build_stars(generator)

    def build_dome(self):
        elevation = numpy.radians(numpy.linspace(-12.0, 90.0, 40))[:, None]
        azimuth = numpy.linspace(0.0, 2.0 * math.pi, 97)[None, :]
        directions = numpy.stack((numpy.cos(elevation) * numpy.cos(azimuth),
                                  numpy.sin(elevation) * numpy.ones_like(azimuth),
                                  numpy.cos(elevation) * numpy.sin(azimuth)), axis=-1)
        height = numpy.clip(directions[..., 1], 0.0, 1.0)
        colors = self.horizon + (self.zenith - self.horizon) * (height ** 0.6)[..., None]
        toward_moon = numpy.clip(numpy.sum(directions * self.moon_direction, axis=-1), 0.0, 1.0)
        colors = colors + self.glow * (0.65 * toward_moon ** 6 + 0.35 * toward_moon ** 40)[..., None]
        streaks = self.cloud_noise(directions[..., 0] / (height + 0.25) * 1.4, directions[..., 2] / (height + 0.25) * 3.0)
        clouds = smoothstep((streaks + 0.05) / 0.5) * smoothstep((height - 0.02) / 0.1)
        colors = colors * (1.0 - self.cloud_shadow * clouds[..., None]) + self.glow * (
                0.25 * clouds * toward_moon ** 4)[..., None]
        positions, colors = flat_arrays(directions * self.radius, colors)
        return positions, colors, grid_triangles(*directions.shape[:2])

    def moon_axes(self):
        toward_viewer = -self.moon_direction
        across = normalized(numpy.cross((0.0, 1.0, 0.0), toward_viewer))
        upward = numpy.cross(toward_viewer, across)
        return self.moon_direction * self.moon_distance, across, upward

    def build_moon(self):
        center, across, upward = self.moon_axes()
        radius = numpy.linspace(0.0, 1.0, 24)[:, None]
        angle = numpy.linspace(0.0, 2.0 * math.pi, 65)[None, :]
        u, v = radius * numpy.cos(angle), radius * numpy.sin(angle)
        grid = center + (across * u[..., None] + upward * v[..., None]) * self.moon_radius
        maria = smoothstep((self.moon_noise(u * 1.3 + 0.4, v * 1.3 - 0.2) + 0.1) / 0.5)
        craters = 0.5 + 0.5 * self.moon_noise(u * 4.0, v * 4.0)
        limb = 1.0 - 0.25 * radius ** 3
        shade = (0.78 + 0.22 * (1.0 - maria) - 0.08 * craters) * limb
        positions, colors = flat_arrays(grid, self.moon_color * shade[..., None])
        return positions, colors, grid_triangles(*grid.shape[:2])

    def build_stars(self, generator):
        directions = generator.normal(size=(self.star_count, 3))
        directions[:, 1] = numpy.abs(directions[:, 1]) + 0.35
        directions = normalized(directions)
        away_from_moon = 1.0 - smoothstep((directions @ self.moon_direction - 0.8) / 0.15)
        brightness = generator.uniform(0.15, 0.6, self.star_count) * away_from_moon
        colors = numpy.stack((brightness * 0.9, brightness * 0.95, brightness), axis=-1)
        return flat_arrays(directions * (self.radius - 1.0), colors)

    @staticmethod
    def eye():
        modelview = numpy.asarray(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=numpy.float64).reshape(4, 4)
        return -modelview[:3, :3] @ modelview[3, :3]

    def render(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDepthMask(GL_FALSE)
        glPushMatrix()
        glTranslatef(*self.eye())
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        positions, colors, indices = self.dome
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        positions, colors = self.stars
        glPointSize(1.5)
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
        positions, colors, indices = self.moon
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()
        glDepthMask(GL_TRUE)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)


class Crows:

    def __init__(self, center, generator, count=7):
        self.center = numpy.asarray(center, dtype=numpy.float64)
        self.color = (0.02, 0.02, 0.025)
        self.span = 0.13
        self.orbit_radii = generator.uniform(1.2, 3.4, count)
        self.heights = generator.uniform(-0.6, 1.4, count)
        self.angular_speeds = generator.uniform(0.25, 0.55, count) * generator.choice((-1.0, 1.0), count)
        self.phases = generator.uniform(0.0, 2.0 * math.pi, count)
        self.flap_rates = generator.uniform(2.5, 4.0, count)
        self.glide_rates = generator.uniform(0.15, 0.35, count)
        self.seconds = 0.0

    def update(self, seconds):
        self.seconds += seconds

    def render(self):
        glDisable(GL_LIGHTING)
        glColor3f(*self.color)
        glBegin(GL_TRIANGLES)
        for radius, height, speed, phase, flap_rate, glide_rate in zip(
                self.orbit_radii, self.heights, self.angular_speeds, self.phases, self.flap_rates,
                self.glide_rates):
            angle = phase + speed * self.seconds
            bob = 0.15 * math.sin(self.seconds * 0.7 + phase)
            body = self.center + (radius * math.cos(angle), height + bob, radius * math.sin(angle))
            heading = normalized(numpy.array((-math.sin(angle), 0.0, math.cos(angle)))) * math.copysign(1.0, speed)
            side = numpy.cross(heading, (0.0, 1.0, 0.0))
            gliding = math.sin(self.seconds * glide_rate * 2.0 * math.pi + phase) > 0.3
            flap = 0.15 if gliding else math.sin(self.seconds * flap_rate * 2.0 * math.pi + phase)
            lift = numpy.array((0.0, flap * self.span * 0.6, 0.0))
            nose = body + heading * self.span * 0.35
            tail = body - heading * self.span * 0.45
            for direction in (1.0, -1.0):
                tip = body + side * direction * self.span - heading * self.span * 0.15 + lift
                glVertex3f(*nose)
                glVertex3f(*tail)
                glVertex3f(*tip)
        glEnd()
        glEnable(GL_LIGHTING)


class DeadTreeGrower:

    def __init__(self, sculptor, generator, bark, moss=None):
        self.sculptor = sculptor
        self.generator = generator
        self.bark = bark
        self.moss = moss
        self.gnarl = 0.18
        self.upward_pull = 0.35
        self.moss_chance = 0.55
        self.trunk_taper = 0.55

    def trunk(self, base, height, radius, depth, roots=5):
        generator = self.generator
        base = numpy.asarray(base, dtype=numpy.float64)
        for _ in range(roots):
            angle = generator.uniform(0.0, 2.0 * math.pi)
            outward = numpy.array((math.cos(angle), 0.0, math.sin(angle)))
            reach = radius * generator.uniform(3.0, 5.5)
            self.sculptor.tube((base + (0.0, radius * 1.4, 0.0), base + outward * reach * 0.45 + (0.0, radius * 0.3, 0.0),
                                base + outward * reach + (0.0, -radius * 0.6, 0.0)),
                               ((0.0, radius * 0.6, radius * 0.5), (1.0, radius * 0.08, radius * 0.08)), self.bark,
                               rings=10, segments=8, mottle=0.12)
        lean = normalized((generator.normal(0.0, 0.12), 1.0, generator.normal(0.0, 0.12)))
        self.branch(base - (0.0, radius * 0.5, 0.0), lean, height, radius, depth, flare=True)

    def branch(self, base, direction, length, radius, depth, flare=False):
        generator = self.generator
        points = [numpy.asarray(base, dtype=numpy.float64)]
        heading = normalized(direction)
        for _ in range(3):
            heading = normalized(heading + generator.normal(0.0, self.gnarl, 3) + (0.0, self.upward_pull * 0.3, 0.0))
            points.append(points[-1] + heading * length / 3.0)
        profile = ((0.0, radius * 1.7, radius * 1.7), (0.12, radius, radius),
                   (1.0, radius * self.trunk_taper, radius * self.trunk_taper)) \
            if flare else ((0.0, radius, radius), (1.0, radius * 0.3, radius * 0.3))
        self.sculptor.tube(points, profile, self.bark, rings=12 if depth else 7, segments=10 if depth > 1 else 6,
                           cap_start=False, mottle=0.12)
        if self.moss is not None and depth <= 1 and generator.uniform() < self.moss_chance:
            self.hang_moss(points)
        if depth == 0:
            return
        children = int(generator.integers(2, 4))
        for _ in range(children):
            fraction = generator.uniform(0.45, 0.95)
            segment = min(int(fraction * 3.0), 2)
            local = fraction * 3.0 - segment
            fork = points[segment] + (points[segment + 1] - points[segment]) * local
            sideways = generator.normal(0.0, 1.0, 3) * (1.0, 0.0, 1.0)
            spread = normalized(heading * 0.6 + normalized(sideways) * 0.8 + (0.0, self.upward_pull, 0.0))
            self.branch(fork, spread, length * generator.uniform(0.45, 0.7), radius * generator.uniform(0.45, 0.6),
                        depth - 1)

    def hang_moss(self, points):
        generator = self.generator
        for _ in range(int(generator.integers(2, 6))):
            index = int(generator.integers(1, len(points)))
            anchor = points[index - 1] + (points[index] - points[index - 1]) * generator.uniform(0.0, 1.0)
            self.sculptor.spike(anchor, (generator.normal(0.0, 0.08), -1.0, generator.normal(0.0, 0.08)),
                                generator.uniform(0.15, 0.6), generator.uniform(0.008, 0.02), self.moss,
                                curl=(generator.normal(0.0, 0.1), 0.0, generator.normal(0.0, 0.1)), rings=6,
                                segments=5)


class DeadLandScene:

    def __init__(self, seed=17):
        self.generator = numpy.random.default_rng(seed)
        self.acting = True
        self.talking = False
        self.seconds = 0.0
        self.terrain_extent = ((-186.0, 26.0), (-24.0, 10.0))
        self.terrain_step = 0.2
        self.water_level = 0.0
        self.swamp_edge = -1.0
        self.swamp_blend = 4.0
        self.swamp_far_edge = -24.0
        self.swamp_far_blend = 3.0
        self.forest_edge = -160.0
        self.forest_blend = 3.0
        self.forest_span = (-180.0, -161.0)
        self.land_end = (-180.0, 17.0)
        self.carcass_spot = (-88.0, -1.0)
        self.carcass_heading = 0.35
        self.carcass_clearing = 2.2
        self.carcass_ground = 0.32
        self.forest_tree_count = 24
        self.forest_stump_count = 6
        self.forest_log_count = 9
        self.barren_rock_count = 70
        self.carcass_leaf_count = 2200
        self.forest_leaf_count = 4500
        self.leaf_colors = ((0.13, 0.08, 0.05), (0.10, 0.065, 0.04), (0.16, 0.11, 0.07), (0.08, 0.06, 0.045),
                            (0.18, 0.15, 0.12), (0.12, 0.05, 0.035))
        self.wet_darkening = 0.7
        self.rain_drop_count = 5000
        self.rain_color = (0.55, 0.6, 0.7, 0.22)
        self.lake_center = (11.0, -3.0)
        self.lake_radii = (3.4, 2.6)
        self.lake_level = 0.1
        self.hero_tree_spot = (-1.5, -2.2)
        self.ruins_spot = (-7.5, -15.0)
        self.mountain_line = -31.0
        self.mountain_span = (-210.0, 50.0)
        self.ground_color = (0.11, 0.10, 0.095)
        self.mud_color = (0.07, 0.065, 0.06)
        self.scorched_color = (0.045, 0.035, 0.03)
        self.rock_color = (0.17, 0.165, 0.16)
        self.bark_color = (0.075, 0.07, 0.068)
        self.swamp_bark_color = (0.09, 0.08, 0.07)
        self.moss_color = (0.13, 0.14, 0.11)
        self.thorn_color = (0.10, 0.095, 0.09)
        self.ruin_color = (0.10, 0.10, 0.11)
        self.mountain_color = (0.09, 0.095, 0.11)
        self.moon_direction = normalized((0.3, 0.36, -1.0))
        self.moonlight_color = (0.40, 0.46, 0.62, 1.0)
        self.moonlight_specular = (0.20, 0.24, 0.32, 1.0)
        self.ambient = (0.05, 0.05, 0.06, 1.0)
        self.lava_light_color = numpy.array((1.0, 0.42, 0.12))
        self.lava_light_strength = 1.7
        self.lava_light_height = 0.6
        self.lava_light_spots = ((0.0, 0.0), (0.55, 0.3), (0.55, 2.4), (0.55, 4.4))
        self.lava_light_attenuation = (0.25, 0.18, 0.09)
        self.flicker_rates = self.generator.uniform(5.0, 11.0, len(self.lava_light_spots))
        self.flicker_phases = self.generator.uniform(0.0, 2.0 * math.pi, len(self.lava_light_spots))
        self.fog_color = (0.085, 0.09, 0.115, 1.0)
        self.fog_density = 0.034
        self.rock_count = 70
        self.swamp_tree_count = 8
        self.stump_count = 9
        self.thorn_bush_count = 22
        self.fallen_branch_count = 10
        self.ground_noise = SineNoise(self.generator, 5, 0.35, 2)
        self.detail_noise = SineNoise(self.generator, 4, 1.6, 2)
        self.stone_noise = SineNoise(self.generator, 4, 1.0, 3)
        self.ridge_noise = SineNoise(self.generator, 5, 1.0, 1)
        self.lake = LavaLake(self.lake_center, self.lake_radii, self.lake_level, self.generator)
        self.flight = CameraFlight(self.flight_keyframes())
        self.camera_path = numpy.array([self.flight.view(time)[0] for time in numpy.linspace(0.0, self.flight.duration,
                                                                                               400)])
        self.terrain = self.build_terrain()
        self.mesh = StatueMesh()
        self.sculptor = Sculptor(self.mesh)
        self.build_mountains()
        self.build_ruins()
        self.build_hero_tree()
        self.build_swamp_trees()
        self.build_stumps()
        self.build_thorn_bushes()
        self.build_fallen_branches()
        self.build_rocks()
        self.build_carcass()
        self.build_dead_forest()
        self.build_barren_rocks()
        self.scatter_leaves(self.carcass_spot, 2.8, self.carcass_leaf_count)
        self.scatter_leaves(((self.forest_span[0] + self.forest_span[1]) / 2.0, -3.0), 11.0, self.forest_leaf_count,
                            uniform=True)
        self.scenery = self.mesh.arrays()
        self.waters = [SwampWater(extent, 0.25, self.water_level, self.moon_direction, self.generator)
                       for extent in (((self.swamp_far_edge - 2.0, 0.5), (-16.0, 8.0)),
                                      ((self.forest_span[0], self.forest_edge + 1.0), (-16.0, 8.0)))]
        self.rain = Rain(self.rain_drop_count, (self.forest_span[0] - 1.0, -0.5, -15.0),
                         (self.forest_span[1] + 1.5, 8.0, 7.0), random.Random(seed))
        self.rain.color = self.rain_color
        self.sky = NightSky(self.moon_direction, self.generator)
        self.embers = LakeEmbers(self.lake, 260)
        tree_x, tree_z = self.hero_tree_spot
        self.crows = Crows((tree_x, float(self.ground_height(tree_x, tree_z)) + 4.6, tree_z), self.generator)
        carcass_x, carcass_z = self.carcass_spot
        self.carrion_crows = Crows((carcass_x, self.carcass_ground + 2.6, carcass_z), self.generator, 5)

    def swampiness(self, x):
        x = numpy.asarray(x)
        return (smoothstep((self.swamp_edge - x) / self.swamp_blend)
                * smoothstep((x - self.swamp_far_edge) / self.swamp_far_blend))

    def wetness(self, x):
        return smoothstep((self.forest_edge - numpy.asarray(x)) / self.forest_blend)

    def carcass_flattening(self, x, z):
        carcass_x, carcass_z = self.carcass_spot
        distance = numpy.hypot(x - carcass_x, z - carcass_z)
        return 1.0 - smoothstep((distance - self.carcass_clearing * 0.6) / (self.carcass_clearing * 0.6))

    def ground_height(self, x, z):
        x = numpy.asarray(x, dtype=numpy.float64)
        z = numpy.asarray(z, dtype=numpy.float64)
        rolling = self.ground_noise(x, z)
        detail = self.detail_noise(x, z)
        dry = 0.36 + 0.24 * rolling + 0.06 * detail
        swamp = -0.05 + 0.2 * rolling + 0.1 * detail
        soaked = 0.1 + 0.2 * rolling + 0.08 * detail
        swampiness = self.swampiness(x)
        wetness = self.wetness(x)
        height = dry * (1.0 - swampiness) + swamp * swampiness
        height = height * (1.0 - wetness) + soaked * wetness
        flattening = self.carcass_flattening(x, z)
        height = height * (1.0 - flattening) + (self.carcass_ground + 0.03 * detail) * flattening
        left_end, right_end = self.land_end
        height = height + 0.12 * numpy.clip(-z - 10.0, 0.0, None) ** 1.3 + 0.08 * numpy.clip(
            x - right_end, 0.0, None) ** 1.3 + 0.08 * numpy.clip(left_end - x, 0.0, None) ** 1.3
        reach = self.lake.reach_at(x, z)
        basin = 1.0 - smoothstep((reach - 0.9) / 0.25)
        rim = 0.2 * numpy.exp(-((reach - 1.2) / 0.2) ** 2)
        return height * (1.0 - basin) + (self.lake_level - 0.3) * basin + rim

    def build_terrain(self):
        (low_x, high_x), (low_z, high_z) = self.terrain_extent
        xs = numpy.arange(low_x, high_x + 1e-6, self.terrain_step)
        zs = numpy.arange(low_z, high_z + 1e-6, self.terrain_step)
        z, x = numpy.meshgrid(zs, xs, indexing="ij")
        grid = numpy.stack((x, self.ground_height(x, z), z), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, grid - (0.0, 1.0, 0.0), False), numpy.array((0.0, 1.0, 0.0)))
        swampiness = self.swampiness(x)[..., None]
        scorch = (1.0 - smoothstep((self.lake.reach_at(x, z) - 1.0) / 0.8))[..., None]
        colors = numpy.asarray(self.ground_color) * (1.0 - swampiness) + numpy.asarray(self.mud_color) * swampiness
        colors = colors * (1.0 - scorch) + numpy.asarray(self.scorched_color) * scorch
        colors = colors * (1.0 - (1.0 - self.wet_darkening) * self.wetness(x))[..., None]
        cracks = numpy.abs(self.detail_noise(x * 2.7, z * 2.7)) < 0.05
        colors = colors * mottling(grid * 0.6, 0.3)[..., None] * numpy.where(cracks, 0.6, 1.0)[..., None]
        mesh = StatueMesh()
        mesh.add_grid(grid, normals, colors)
        return mesh.arrays()

    def clear_of_camera(self, x, z, clearance):
        distances = numpy.hypot(self.camera_path[:, 0] - x, self.camera_path[:, 2] - z)
        return float(distances.min()) > clearance

    def open_ground(self, x, z, margin):
        tree_x, tree_z = self.hero_tree_spot
        carcass_x, carcass_z = self.carcass_spot
        return (float(self.lake.reach_at(x, z)) > 1.35 + margin / 3.0 and math.hypot(x - tree_x, z - tree_z) > 1.2
                and math.hypot(x - carcass_x, z - carcass_z) > self.carcass_clearing + margin
                and self.clear_of_camera(x, z, 0.9 + margin))

    def random_spot(self, x_range, z_range, margin, accept=None):
        generator = self.generator
        while True:
            x = generator.uniform(*x_range)
            z = generator.uniform(*z_range)
            if self.open_ground(x, z, margin) and (accept is None or accept(x, z)):
                return x, z

    def build_mountains(self):
        generator = self.generator
        for line, peak, base, wiggle, offset in ((self.mountain_line, 7.5, 2.5, 0.22, 0.0),
                                                 (self.mountain_line + 6.0, 3.2, 1.2, 0.35, 1.7)):
            x = numpy.linspace(*self.mountain_span, 1600)
            rise = numpy.linspace(0.0, 1.0, 14)[:, None]
            ridge = 1.0 - numpy.abs(numpy.sin(x * wiggle + offset))
            noise = 0.5 + 0.5 * self.ridge_noise(x * 0.1 + offset)
            heights = base + (peak - base) * noise * (0.45 + 0.55 * ridge ** 2) + 0.4 * self.ridge_noise(
                x * 0.55 + offset)
            depth = line + 2.5 * self.ridge_noise(x * 0.16 + offset + 3.0)
            spread = depth[None, :] + (1.0 - rise) * heights[None, :] * 0.9
            grid = numpy.stack((numpy.broadcast_to(x, spread.shape), -1.5 + rise * (heights[None, :] + 1.5), spread),
                               axis=-1)
            behind = numpy.stack((x, numpy.full_like(x, -3.0), depth - 6.0), axis=-1)[None, :, :]
            normals = unit_or_fallback(surface_normals(grid, behind, False), numpy.array((0.0, 1.0, 0.0)))
            colors = numpy.asarray(self.mountain_color) * mottling(grid * 0.2, 0.25)[..., None] * (
                    0.8 + 0.2 * generator.uniform())
            self.mesh.add_grid(grid, normals, colors)

    def build_ruins(self):
        generator = self.generator
        ruin_x, ruin_z = self.ruins_spot
        for offset_x, offset_z, height, radius in ((0.0, 0.0, 4.2, 0.32), (-1.3, 0.6, 2.4, 0.26),
                                                   (1.2, -0.4, 2.9, 0.22), (2.6, 0.9, 1.5, 0.3)):
            x, z = ruin_x + offset_x, ruin_z + offset_z
            ground = float(self.ground_height(x, z)) - 0.2
            self.sculptor.tube(((x, ground, z), (x, ground + height * 0.5, z), (x, ground + height, z)),
                               ((0.0, radius * 1.4, radius * 1.4), (0.75, radius, radius), (1.0, 0.0, 0.0)),
                               self.ruin_color, rings=14, segments=10, mottle=0.1)
            for side in (-1.0, 1.0):
                self.sculptor.spike((x + side * radius * 0.8, ground + height * 0.62, z), (side * 0.35, 1.0, 0.0),
                                    height * 0.22, radius * 0.35, self.ruin_color)
        wall = numpy.linspace((ruin_x - 2.2, 0.0, ruin_z + 0.8), (ruin_x + 3.2, 0.0, ruin_z + 0.6), 30)
        wall[:, 1] = self.ground_height(wall[:, 0], wall[:, 2]) + 0.4
        crumbling = 0.5 + 0.35 * numpy.abs(numpy.sin(wall[:, 0] * 2.3)) + generator.uniform(0.0, 0.2, len(wall))
        slab_sweep(self.mesh, wall, (0.0, 1.0, 0.0), 0.15, crumbling, self.ruin_color, roughness=0.3, segments=16,
                   noise=self.stone_noise)

    def build_hero_tree(self):
        grower = DeadTreeGrower(self.sculptor, self.generator, self.bark_color)
        grower.upward_pull = 0.55
        grower.gnarl = 0.22
        x, z = self.hero_tree_spot
        grower.trunk((x, float(self.ground_height(x, z)), z), 3.0, 0.34, 4, roots=7)

    def build_swamp_trees(self):
        grower = DeadTreeGrower(self.sculptor, self.generator, self.swamp_bark_color, self.moss_color)
        grower.upward_pull = 0.1
        grower.gnarl = 0.3
        for _ in range(self.swamp_tree_count):
            x, z = self.random_spot((-18.0, -3.5), (-13.0, 4.0), 0.6)
            height = self.generator.uniform(1.4, 2.6)
            grower.trunk((x, float(self.ground_height(x, z)), z), height, 0.13 * height, 3, roots=4)

    def build_stumps(self):
        for _ in range(self.stump_count):
            x, z = self.random_spot((-17.0, 16.0), (-12.0, 5.0), 0.3)
            self.stump(x, z)

    def stump(self, x, z):
        generator = self.generator
        height = generator.uniform(0.5, 1.5)
        radius = generator.uniform(0.09, 0.2)
        ground = float(self.ground_height(x, z))
        lean = normalized((generator.normal(0.0, 0.15), 1.0, generator.normal(0.0, 0.15)))
        top = numpy.array((x, ground, z)) + lean * height
        self.sculptor.tube(((x, ground - 0.15, z), (x, ground, z) + lean * height * 0.5, top),
                           ((0.0, radius * 1.6, radius * 1.6), (0.2, radius, radius), (1.0, radius * 0.85,
                                                                                     radius * 0.85)),
                           self.swamp_bark_color, rings=12, segments=10, cap_end=True, mottle=0.12)
        for _ in range(int(generator.integers(3, 6))):
            angle = generator.uniform(0.0, 2.0 * math.pi)
            outward = numpy.array((math.cos(angle), 0.0, math.sin(angle)))
            rim = top + outward * radius * 0.6 - lean * 0.05
            self.sculptor.spike(rim, lean + outward * 0.25, generator.uniform(0.12, 0.45) * height, radius * 0.35,
                                self.swamp_bark_color)

    def build_thorn_bushes(self):
        generator = self.generator
        for _ in range(self.thorn_bush_count):
            x, z = self.random_spot((-4.0, 18.0), (-11.0, 6.0), 0.2, lambda x, z: self.swampiness(x) < 0.5)
            ground = float(self.ground_height(x, z))
            size = generator.uniform(0.35, 0.9)
            for _ in range(int(generator.integers(12, 22))):
                angle = generator.uniform(0.0, 2.0 * math.pi)
                tilt = generator.uniform(0.2, 1.3)
                direction = (math.cos(angle) * tilt, 1.0, math.sin(angle) * tilt)
                self.sculptor.spike((x, ground - 0.02, z), direction, size * generator.uniform(0.5, 1.0),
                                    generator.uniform(0.004, 0.009), self.thorn_color,
                                    curl=generator.normal(0.0, 0.15, 3), rings=6, segments=4)

    def build_fallen_branches(self):
        for _ in range(self.fallen_branch_count):
            x, z = self.random_spot((-6.0, 17.0), (-10.0, 6.0), 0.2)
            self.fallen_branch(x, z, self.generator.uniform(0.6, 1.6), 0.05)

    def fallen_branch(self, x, z, length, radius):
        generator = self.generator
        angle = generator.uniform(0.0, 2.0 * math.pi)
        along = numpy.array((math.cos(angle), 0.0, math.sin(angle)))
        points = [numpy.array((x, 0.0, z)) + along * length * fraction
                  + numpy.array((generator.normal(0.0, 0.06), 0.0, generator.normal(0.0, 0.06)))
                  for fraction in (0.0, 0.35, 0.7, 1.0)]
        for point in points:
            point[1] = float(self.ground_height(point[0], point[2])) + radius * 0.6
        self.sculptor.tube(points, ((0.0, radius, radius), (1.0, radius * 0.3, radius * 0.3)), self.bark_color,
                           rings=10, segments=6, mottle=0.12)

    def build_rocks(self):
        for _ in range(self.rock_count):
            x, z = self.random_spot((-19.0, 19.0), (-14.0, 7.0), 0.4)
            self.rock(x, z)

    def rock(self, x, z):
        generator = self.generator
        size = generator.uniform(0.1, 0.5)
        ground = float(self.ground_height(x, z))
        shade = generator.uniform(0.75, 1.15)
        self.sculptor.ellipsoid((x, ground + size * 0.15, z),
                                (generator.normal(), generator.uniform(-0.3, 0.3), generator.normal()), size,
                                size * generator.uniform(0.6, 0.95), size * generator.uniform(0.4, 0.75),
                                tuple(numpy.asarray(self.rock_color) * shade), up_hint=(0.0, 1.0, 0.0),
                                scales=StoneLumps(size * 0.45, 0.35))

    def build_carcass(self):
        x, z = self.carcass_spot
        Carcass(self.sculptor, self.generator, (x, self.carcass_ground, z), self.carcass_heading).build()

    def build_dead_forest(self):
        generator = self.generator
        grower = DeadTreeGrower(self.sculptor, generator, self.bark_color)
        grower.upward_pull = 0.45
        grower.gnarl = 0.25
        for _ in range(self.forest_tree_count):
            x, z = self.random_spot(self.forest_span, (-14.0, 6.0), 0.5)
            height = generator.uniform(2.2, 4.0)
            grower.trunk((x, float(self.ground_height(x, z)), z), height, 0.1 * height, 3, roots=5)
        for _ in range(self.forest_stump_count):
            x, z = self.random_spot(self.forest_span, (-12.0, 5.0), 0.3)
            self.stump(x, z)
        for _ in range(self.forest_log_count):
            x, z = self.random_spot(self.forest_span, (-12.0, 5.0), 0.4)
            self.fallen_branch(x, z, generator.uniform(1.5, 3.2), generator.uniform(0.08, 0.16))

    def build_barren_rocks(self):
        for _ in range(self.barren_rock_count):
            x, z = self.random_spot((self.forest_edge, self.swamp_far_edge), (-13.0, 7.0), 0.4)
            self.rock(x, z)

    def scatter_leaves(self, center, radius, count, uniform=False):
        generator = self.generator
        distance = radius * generator.uniform(0.0, 1.0, count) ** (0.5 if uniform else 0.9)
        angle = generator.uniform(0.0, 2.0 * math.pi, count)
        x = center[0] + distance * numpy.cos(angle)
        z = center[1] + distance * numpy.sin(angle)
        ground = self.ground_height(x, z) + generator.uniform(0.008, 0.03, count)
        spin = generator.uniform(0.0, 2.0 * math.pi, count)
        size = generator.uniform(0.035, 0.08, count)
        tilt = generator.normal(0.0, 0.25, count)
        lengthwise = numpy.stack((numpy.cos(spin), tilt, numpy.sin(spin)), axis=-1) * size[:, None]
        crosswise = numpy.stack((-numpy.sin(spin), numpy.zeros(count), numpy.cos(spin)), axis=-1) * size[:, None]
        centers = numpy.stack((x, ground, z), axis=-1)
        corners = numpy.stack((centers + lengthwise, centers + crosswise * 0.45, centers - lengthwise * 0.8,
                               centers - crosswise * 0.45), axis=1)
        palette = numpy.asarray(self.leaf_colors)
        colors = palette[generator.integers(0, len(palette), count)] * generator.uniform(0.75, 1.15, count)[:, None]
        normals = numpy.broadcast_to((0.0, 1.0, 0.0), corners.shape)
        first = self.mesh.add_vertices(corners, normals, numpy.repeat(colors, 4, axis=0))
        quads = first + numpy.arange(count)[:, None] * 4 + numpy.array((0, 1, 2, 0, 2, 3))[None, :]
        self.mesh.indices.append(quads.reshape(-1).astype(numpy.uint32))

    def flight_keyframes(self):
        lake = (self.lake_center[0], 0.2, self.lake_center[1])
        tree = (self.hero_tree_spot[0], 2.4, self.hero_tree_spot[1])
        crown = (self.hero_tree_spot[0], 3.6, self.hero_tree_spot[1])
        carcass_x, carcass_z = self.carcass_spot
        carcass = (carcass_x, self.carcass_ground + 0.1, carcass_z)
        forest = self.forest_edge
        start = ((0.0, 2.6, 11.0), (0.0, 1.4, -6.0))
        return [(0.0, *start),
                (6.0, (-6.0, 1.9, 7.5), (-8.0, 0.4, -4.0)),
                (12.0, (-11.0, 0.9, 3.0), (-7.0, 0.8, -10.0)),
                (18.0, (-18.0, 1.6, 4.0), (-26.0, 0.8, -3.0)),
                (25.0, (-28.0, 1.8, 4.0), (-40.0, 0.8, -2.0)),
                (33.0, (-50.0, 2.0, 4.5), (-62.0, 0.8, -2.0)),
                (41.0, (carcass_x + 16.0, 1.9, 4.0), carcass),
                (47.0, (carcass_x + 5.0, 1.8, 3.5), carcass),
                (52.0, (carcass_x + 1.3, 1.25, carcass_z + 1.5), carcass),
                (57.0, (carcass_x - 1.4, 1.0, carcass_z + 1.4), carcass),
                (64.0, (carcass_x - 10.0, 1.8, 4.0), (carcass_x - 22.0, 0.8, -2.0)),
                (72.0, ((carcass_x + forest) / 2.0, 2.0, 4.5), ((carcass_x + forest) / 2.0 - 15.0, 1.0, -2.0)),
                (80.0, (forest + 8.0, 1.8, 3.5), (forest - 6.0, 1.5, -3.0)),
                (86.0, (forest - 2.5, 1.3, 2.8), (forest - 10.0, 2.0, -4.0)),
                (92.0, (forest - 9.0, 1.6, 1.0), (forest - 13.0, 2.6, -6.0)),
                (97.0, (forest - 5.0, 2.2, 4.5), (forest + 2.0, 1.2, -4.0)),
                (105.0, (forest + 25.0, 3.5, 7.0), (forest + 45.0, 2.0, -2.0)),
                (113.0, (carcass_x - 2.0, 3.5, 7.0), (carcass_x + 18.0, 2.0, -2.0)),
                (121.0, (-50.0, 3.2, 7.0), (-30.0, 1.5, -2.0)),
                (129.0, (-24.0, 3.0, 7.0), tree),
                (135.0, (0.8, 0.9, 1.4), crown),
                (141.0, (4.5, 1.9, 3.5), lake),
                (147.0, (8.0, 1.5, 2.2), lake),
                (153.0, (14.0, 2.6, 3.5), (2.0, 1.2, -7.0)),
                (159.0, *start)]

    def camera_view(self):
        return self.flight.view(self.seconds)

    def restart(self):
        self.seconds = 0.0

    def update(self, seconds):
        self.seconds += seconds
        self.lake.paint(self.seconds)
        for water in self.waters:
            water.paint(self.seconds)
        self.embers.update(seconds)
        self.crows.update(seconds)
        self.carrion_crows.update(seconds)
        self.rain.update(seconds)

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
        for number, ((reach, angle), strength) in enumerate(zip(self.lava_light_spots, self.lava_light_strengths())):
            light = GL_LIGHT1 + number
            x, z = self.lake.surface_point(reach, angle)
            color = (*(self.lava_light_color * strength), 1.0)
            glEnable(light)
            glLightfv(light, GL_POSITION, (float(x), self.lake_level + self.lava_light_height, float(z), 1.0))
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

    def render(self):
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT | GL_FOG_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT
                     | GL_POINT_BIT | GL_CURRENT_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.06, 0.06, 0.08, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 12.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))
        self.setup_lights()
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, self.fog_color)
        self.sky.render()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        self.draw(*self.terrain)
        self.draw(*self.scenery)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.lake.render()
        for water in self.waters:
            water.render()
        self.crows.render()
        self.carrion_crows.render()
        self.embers.render()
        self.rain.draw()
        glPopAttrib()
