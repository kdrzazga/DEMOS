import colorsys
import math
import random

import numpy as np
from OpenGL.GL import *

from lib.vector3 import Vector3

PALETTE_CHANNELS = ("cap", "rim", "gill", "spot", "stem", "glow")


class CameraBasis:
    def __init__(self, right, up):
        self.right = right
        self.up = up

    @classmethod
    def from_modelview(cls):
        matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        return cls(Vector3(matrix[0][0], matrix[1][0], matrix[2][0]),
                   Vector3(matrix[0][1], matrix[1][1], matrix[2][1]))


class GlowSprite:
    def __init__(self, segments):
        self.ring = [(math.cos(math.tau * index / segments), math.sin(math.tau * index / segments))
                     for index in range(segments + 1)]
        self.core = 0.3
        self.core_falloff = 0.45

    def draw(self, center, radius, color, alpha, camera):
        self.emit(center, camera.right * radius, camera.up * radius, color, alpha)

    def draw_flat(self, center, radius, color, alpha):
        self.emit(center, Vector3(radius, 0.0, 0.0), Vector3(0.0, 0.0, radius), color, alpha)

    def emit(self, center, axis_a, axis_b, color, alpha):
        red, green, blue = color
        core_alpha = alpha * self.core_falloff
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(red, green, blue, alpha)
        glVertex3f(*center)
        glColor4f(red, green, blue, core_alpha)
        for cosine, sine in self.ring:
            glVertex3f(*self.offset(center, axis_a, axis_b, cosine * self.core, sine * self.core))
        glEnd()
        glBegin(GL_QUAD_STRIP)
        for cosine, sine in self.ring:
            glColor4f(red, green, blue, core_alpha)
            glVertex3f(*self.offset(center, axis_a, axis_b, cosine * self.core, sine * self.core))
            glColor4f(red, green, blue, 0.0)
            glVertex3f(*self.offset(center, axis_a, axis_b, cosine, sine))
        glEnd()

    def offset(self, center, axis_a, axis_b, along_a, along_b):
        return center + axis_a * along_a + axis_b * along_b


class ColorMesh:
    def __init__(self, primitive):
        self.primitive = primitive
        self.positions = []
        self.weight_rows = []
        self.bias_rows = []
        self.indices = []
        self.position_array = None
        self.weight_array = None
        self.bias_array = None
        self.index_array = None
        self.color_array = None

    @staticmethod
    def weights(**amounts):
        row = np.zeros(len(PALETTE_CHANNELS), dtype=np.float32)
        for name, amount in amounts.items():
            row[PALETTE_CHANNELS.index(name)] = amount
        return row

    def vertex(self, position, weights, bias=(0.0, 0.0, 0.0)):
        self.positions.append(tuple(position))
        self.weight_rows.append(weights)
        self.bias_rows.append(tuple(bias))
        return len(self.positions) - 1

    def band(self, inner, outer):
        for index in range(len(inner) - 1):
            self.indices.extend((inner[index], inner[index + 1], outer[index + 1],
                                 inner[index], outer[index + 1], outer[index]))

    def fan(self, center, ring):
        for index in range(len(ring) - 1):
            self.indices.extend((center, ring[index], ring[index + 1]))

    def path(self, points):
        for index in range(len(points) - 1):
            self.indices.extend((points[index], points[index + 1]))

    def seal(self):
        self.position_array = np.array(self.positions, dtype=np.float32).reshape(-1, 3)
        self.weight_array = np.array(self.weight_rows, dtype=np.float32).reshape(-1, len(PALETTE_CHANNELS))
        self.bias_array = np.array(self.bias_rows, dtype=np.float32).reshape(-1, 3)
        self.index_array = np.array(self.indices, dtype=np.uint32)
        self.positions = self.weight_rows = self.bias_rows = self.indices = None
        return self

    def recolor(self, matrix):
        colors = np.clip(self.weight_array @ matrix + self.bias_array, 0.0, 1.0)
        self.color_array = np.ascontiguousarray(colors, dtype=np.float32)

    def draw(self):
        if len(self.index_array) == 0:
            return
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.position_array)
        glColorPointer(3, GL_FLOAT, 0, self.color_array)
        glDrawElements(self.primitive, len(self.index_array), GL_UNSIGNED_INT, self.index_array)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)


class MushroomPalette:
    def __init__(self, hue, brightness):
        self.hue = hue % 1.0
        self.brightness = brightness
        self.cap = self.tone(0.0, 0.72, 0.42)
        self.rim = self.tone(-0.015, 0.55, 0.95)
        self.gill = self.tone(0.01, 0.5, 1.0)
        self.spot = self.tone(0.02, 0.16, 1.0)
        self.stem = self.tone(0.0, 0.45, 0.62)
        self.glow = self.tone(0.0, 0.65, 1.0)

    def tone(self, hue_shift, saturation, value):
        return Vector3(*colorsys.hsv_to_rgb((self.hue + hue_shift) % 1.0, saturation, min(1.0, value * self.brightness)))

    def key(self):
        return self.hue, self.brightness

    def matrix(self):
        return np.array([tuple(getattr(self, channel)) for channel in PALETTE_CHANNELS], dtype=np.float32)

    def shifted(self, hue_shift, brightness_scale):
        return MushroomPalette(self.hue + hue_shift, self.brightness * brightness_scale)

    def blend(self, other, amount):
        hue_step = (other.hue - self.hue + 0.5) % 1.0 - 0.5
        return MushroomPalette(self.hue + hue_step * amount,
                               self.brightness + (other.brightness - self.brightness) * amount)

    @classmethod
    def violet(cls):
        return cls(0.76, 1.0)

    @classmethod
    def cyan(cls):
        return cls(0.51, 1.0)

    @classmethod
    def reddish(cls):
        return cls(0.985, 1.0)

    @classmethod
    def yellowish(cls):
        return cls(0.12, 1.0)

    @classmethod
    def named(cls, name):
        return getattr(cls, name)()

    @classmethod
    def presets(cls):
        return [cls.violet(), cls.cyan(), cls.reddish(), cls.yellowish()]


class PaletteVariation:
    def __init__(self, generator):
        self.hue_shift = generator.uniform(-0.03, 0.03)
        self.brightness_scale = generator.uniform(0.82, 1.12)

    def apply(self, palette):
        return palette.shifted(self.hue_shift, self.brightness_scale)


class PaletteTransition:
    def __init__(self, palette):
        self.source = palette
        self.target = palette
        self.current = palette
        self.duration = 1.0
        self.elapsed = 1.0

    def retarget(self, palette, duration):
        self.source = self.current
        self.target = palette
        self.duration = duration
        self.elapsed = 0.0

    def update(self, delta):
        if self.elapsed >= self.duration:
            return
        self.elapsed = min(self.duration, self.elapsed + delta)
        progress = self.elapsed / self.duration
        eased = progress * progress * (3.0 - 2.0 * progress)
        self.current = self.target if progress >= 1.0 else self.source.blend(self.target, eased)


class MushroomShape:
    def __init__(self, cap_radius, cap_height, stem_height, stem_radius):
        self.cap_radius = cap_radius
        self.cap_height = cap_height
        self.stem_height = stem_height
        self.stem_radius = stem_radius
        self.cap_sweep = 1.75
        self.gill_rise = 0.35
        self.stem_bend = 0.06 * stem_height
        self.base_swell = 1.4
        self.top_taper = 0.8
        self.rim_wobble = 0.035
        self.spot_density = 14.0

    @classmethod
    def random(cls, generator, scale):
        cap_radius = generator.uniform(0.6, 1.1) * scale
        shape = cls(cap_radius,
                    cap_radius * generator.uniform(0.45, 0.9),
                    scale * generator.uniform(1.0, 2.6),
                    cap_radius * generator.uniform(0.11, 0.18))
        shape.cap_sweep = generator.uniform(1.45, 1.95)
        shape.stem_bend = shape.stem_height * generator.uniform(-0.08, 0.08)
        return shape


class MushroomGeometry:
    def __init__(self, shape, generator):
        self.shape = shape
        self.wobble_lobes = (3, 5, 7)
        self.wobble_phases = [generator.uniform(0.0, math.tau) for _ in self.wobble_lobes]
        self.lift = shape.gill_rise * shape.cap_height
        self.epsilon = 1e-3

    def stem_center(self, height_fraction):
        return Vector3(self.shape.stem_bend * height_fraction * height_fraction,
                       self.shape.stem_height * height_fraction,
                       0.0)

    def stem_radius(self, height_fraction):
        shape = self.shape
        swell = 1.0 + (shape.base_swell - 1.0) * (1.0 - height_fraction) ** 4
        taper = 1.0 - (1.0 - shape.top_taper) * height_fraction
        return shape.stem_radius * swell * taper

    def stem_point(self, height_fraction, theta):
        center = self.stem_center(height_fraction)
        radius = self.stem_radius(height_fraction)
        return center + Vector3(radius * math.cos(theta), 0.0, radius * math.sin(theta))

    def cap_tilt(self):
        return math.degrees(math.atan2(2.0 * self.shape.stem_bend, self.shape.stem_height))

    def wobble(self, theta):
        waves = sum(math.sin(lobes * theta + phase) for lobes, phase in zip(self.wobble_lobes, self.wobble_phases))
        return self.shape.rim_wobble * waves / len(self.wobble_lobes)

    def cap_point(self, phi, theta):
        shape = self.shape
        rim_cosine = math.cos(shape.cap_sweep)
        radius = shape.cap_radius * math.sin(phi) * (1.0 + self.wobble(theta) * phi / shape.cap_sweep)
        height = shape.cap_height * (math.cos(phi) - rim_cosine) / (1.0 - rim_cosine)
        return Vector3(radius * math.cos(theta), height - self.lift, radius * math.sin(theta))

    def cap_normal(self, phi, theta):
        phi = max(phi, 0.02)
        point = self.cap_point(phi, theta)
        along_phi = self.cap_point(phi + self.epsilon, theta) - point
        along_theta = self.cap_point(phi, theta + self.epsilon) - point
        return along_theta.cross(along_phi).normalized()

    def cap_tangent(self, phi, theta):
        phi = max(phi, 0.02)
        return (self.cap_point(phi, theta + self.epsilon) - self.cap_point(phi, theta)).normalized()

    def under_point(self, spread, theta):
        rim = self.cap_point(self.shape.cap_sweep, theta)
        inner = self.stem_radius(1.0) * 1.1
        radius = inner + (math.hypot(rim.x, rim.z) - inner) * spread
        height = rim.y * spread + self.shape.cap_height * 0.12 * math.sin(math.pi * spread)
        return Vector3(radius * math.cos(theta), height, radius * math.sin(theta))


class Mushroom:
    def __init__(self, x, z, shape, palette, seed):
        generator = random.Random(seed)
        self.x = x
        self.z = z
        self.ground = 0.0
        self.shape = shape
        self.palette = palette
        self.geometry = MushroomGeometry(shape, generator)
        self.yaw = generator.uniform(0.0, 360.0)
        self.sway_axis = generator.uniform(0.0, math.tau)
        self.sway_angle = generator.uniform(0.5, 1.4)
        self.sway_speed = generator.uniform(0.35, 0.7)
        self.sway_phase = generator.uniform(0.0, math.tau)
        self.pulse_speed = generator.uniform(0.5, 1.1)
        self.pulse_phase = generator.uniform(0.0, math.tau)
        self.cap_slices = 56
        self.cap_rings = 16
        self.under_rings = 6
        self.stem_slices = 18
        self.stem_rings = 14
        self.gill_count = min(140, int(50 + 40 * shape.cap_radius))
        self.gill_steps = 5
        self.spot_sides = 7
        self.halo_scale = 2.4
        self.halo_alpha = 0.14
        self.under_glow_alpha = 0.22
        self.light = self.turned(Vector3(-0.35, 0.85, 0.4).normalized(), -self.yaw)
        self.cap_ridges = self.ridge_noise(generator, self.cap_slices)
        self.stem_streaks = self.ridge_noise(generator, self.stem_slices)
        self.spots = self.scatter_spots(generator)
        self.sprite = GlowSprite(20)
        self.body = None
        self.glow = None

    def ridge_noise(self, generator, count):
        raw = [generator.uniform(-1.0, 1.0) for _ in range(count)]
        return [(raw[index - 1] + 2.0 * raw[index] + raw[(index + 1) % count]) / 4.0 for index in range(count)]

    def scatter_spots(self, generator):
        shape = self.shape
        count = min(160, int(shape.spot_density * shape.cap_radius ** 2 * 2.0) + 4)
        rim_cosine = math.cos(shape.cap_sweep * 0.96)
        spots = []
        for _ in range(count):
            phi = math.acos(1.0 - generator.random() * (1.0 - rim_cosine))
            theta = generator.uniform(0.0, math.tau)
            size = shape.cap_radius * generator.uniform(0.02, 0.055) * (1.3 - 0.6 * phi / shape.cap_sweep)
            spots.append((phi, theta, size))
        return spots

    def turned(self, vector, degrees):
        angle = math.radians(degrees)
        cosine, sine = math.cos(angle), math.sin(angle)
        return Vector3(vector.x * cosine + vector.z * sine, vector.y, -vector.x * sine + vector.z * cosine)

    def to_world(self, local):
        return Vector3(self.x, self.ground, self.z) + self.turned(local, self.yaw)

    def cap_to_stem(self, point):
        angle = math.radians(-self.geometry.cap_tilt())
        cosine, sine = math.cos(angle), math.sin(angle)
        tilted = Vector3(point.x * cosine - point.y * sine, point.x * sine + point.y * cosine, point.z)
        return tilted + self.geometry.stem_center(1.0)

    def cap_center(self):
        return self.to_world(self.geometry.stem_center(1.0) + Vector3(0.0, self.shape.cap_height * 0.25, 0.0))

    def gill_center(self):
        return self.to_world(self.geometry.stem_center(1.0) - Vector3(0.0, self.geometry.lift * 0.5, 0.0))

    def cap_span(self):
        bottom = self.ground + self.shape.stem_height - self.geometry.lift
        return bottom, bottom + self.shape.cap_height

    def stem_top(self):
        return self.ground + self.shape.stem_height

    def slice_index(self, theta, slices):
        return int(round(theta / math.tau * slices)) % slices

    def cap_angles(self):
        return [math.tau * index / self.cap_slices for index in range(self.cap_slices + 1)]

    def cap_top_weights(self, phi, theta):
        normal = self.geometry.cap_normal(phi, theta)
        lambert = max(0.0, normal.dot(self.light))
        edge = (phi / self.shape.cap_sweep) ** 3
        ridge = self.cap_ridges[self.slice_index(theta, self.cap_slices)]
        return ColorMesh.weights(cap=(0.3 + 0.8 * lambert) * (0.85 + 0.15 * ridge),
                                 rim=0.55 * edge,
                                 spot=0.15 * lambert ** 8)

    def under_weights(self, spread, theta):
        ridge = self.cap_ridges[self.slice_index(theta, self.cap_slices)]
        light = 0.35 + 0.55 * math.sin(math.pi * min(1.0, spread * 1.1)) ** 0.6
        return ColorMesh.weights(gill=light * (0.85 + 0.15 * ridge))

    def stem_weights(self, height_fraction, slice_index):
        theta = math.tau * slice_index / self.stem_slices
        side = max(0.0, Vector3(math.cos(theta), 0.0, math.sin(theta)).dot(self.light))
        streak = self.stem_streaks[slice_index % self.stem_slices]
        return ColorMesh.weights(
            stem=(0.18 + 0.82 * height_fraction ** 1.4) * (0.75 + 0.25 * side) * (0.85 + 0.15 * streak),
            gill=0.35 * max(0.0, (height_fraction - 0.75) / 0.25) ** 2)

    def prepare(self):
        if self.body is None:
            self.body = self.build_body()
            self.glow = self.build_glow()
            self.recolor()

    def tint(self, palette):
        if palette.key() == self.palette.key():
            return
        self.palette = palette
        if self.body is not None:
            self.recolor()

    def recolor(self):
        matrix = self.palette.matrix()
        self.body.recolor(matrix)
        self.glow.recolor(matrix)

    def build_body(self):
        mesh = ColorMesh(GL_TRIANGLES)
        self.add_stem(mesh)
        self.add_cap_top(mesh)
        self.add_cap_under(mesh)
        self.add_spots(mesh)
        return mesh.seal()

    def build_glow(self):
        mesh = ColorMesh(GL_LINES)
        self.add_gills(mesh)
        self.add_rim(mesh)
        return mesh.seal()

    def add_stem(self, mesh):
        rings = []
        for ring in range(self.stem_rings + 1):
            fraction = ring / self.stem_rings
            rings.append([mesh.vertex(self.geometry.stem_point(fraction, math.tau * slice_index / self.stem_slices),
                                      self.stem_weights(fraction, slice_index))
                          for slice_index in range(self.stem_slices + 1)])
        for lower, upper in zip(rings, rings[1:]):
            mesh.band(lower, upper)

    def add_cap_top(self, mesh):
        rings = []
        for ring in range(self.cap_rings + 1):
            phi = self.shape.cap_sweep * ring / self.cap_rings
            rings.append([mesh.vertex(self.cap_to_stem(self.geometry.cap_point(phi, theta)),
                                      self.cap_top_weights(phi, theta))
                          for theta in self.cap_angles()])
        for inner, outer in zip(rings, rings[1:]):
            mesh.band(inner, outer)

    def add_cap_under(self, mesh):
        rings = []
        for ring in range(self.under_rings + 1):
            spread = ring / self.under_rings
            rings.append([mesh.vertex(self.cap_to_stem(self.geometry.under_point(spread, theta)),
                                      self.under_weights(spread, theta))
                          for theta in self.cap_angles()])
        for inner, outer in zip(rings, rings[1:]):
            mesh.band(inner, outer)

    def add_spots(self, mesh):
        geometry = self.geometry
        for phi, theta, size in self.spots:
            point = geometry.cap_point(phi, theta)
            normal = geometry.cap_normal(phi, theta)
            tangent = geometry.cap_tangent(phi, theta)
            bitangent = normal.cross(tangent)
            edge_weights = ColorMesh.weights(spot=0.6) + self.cap_top_weights(phi, theta) * 0.4
            center = mesh.vertex(self.cap_to_stem(point + normal * (size * 0.45)), ColorMesh.weights(spot=1.0))
            base = point + normal * (size * 0.05)
            ring = []
            for side in range(self.spot_sides + 1):
                angle = math.tau * side / self.spot_sides
                spread = tangent * (math.cos(angle) * size) + bitangent * (math.sin(angle) * size)
                ring.append(mesh.vertex(self.cap_to_stem(base + spread), edge_weights))
            mesh.fan(center, ring)

    def add_gills(self, mesh):
        drop = Vector3(0.0, -0.004 * self.shape.cap_radius, 0.0)
        for gill in range(self.gill_count):
            theta = math.tau * gill / self.gill_count
            start = 0.1 if gill % 2 == 0 else 0.45
            points = []
            for step in range(self.gill_steps + 1):
                spread = start + (0.98 - start) * step / self.gill_steps
                points.append(mesh.vertex(self.cap_to_stem(self.geometry.under_point(spread, theta) + drop),
                                          ColorMesh.weights(gill=0.25 + 0.3 * math.sin(math.pi * spread))))
            mesh.path(points)

    def add_rim(self, mesh):
        mesh.path([mesh.vertex(self.cap_to_stem(self.geometry.cap_point(self.shape.cap_sweep, theta)),
                               ColorMesh.weights(rim=0.45))
                   for theta in self.cap_angles()])

    def place(self, elapsed):
        glTranslatef(self.x, self.ground, self.z)
        glRotatef(self.sway_angle * math.sin(elapsed * self.sway_speed + self.sway_phase),
                  math.cos(self.sway_axis), 0.0, math.sin(self.sway_axis))
        glRotatef(self.yaw, 0.0, 1.0, 0.0)

    def glow_strength(self, elapsed):
        return 0.75 + 0.25 * math.sin(elapsed * self.pulse_speed + self.pulse_phase)

    def draw_body(self, elapsed):
        self.prepare()
        glPushMatrix()
        self.place(elapsed)
        self.body.draw()
        glPopMatrix()

    def draw_glow(self, elapsed, camera):
        self.prepare()
        strength = self.glow_strength(elapsed)
        glBlendFunc(GL_ONE, GL_ONE)
        glPushMatrix()
        self.place(elapsed)
        self.glow.draw()
        glPopMatrix()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        self.sprite.draw(self.cap_center(), self.shape.cap_radius * self.halo_scale,
                         self.palette.glow, self.halo_alpha * strength, camera)
        self.sprite.draw(self.gill_center(), self.shape.cap_radius * 1.2,
                         self.palette.gill, self.under_glow_alpha * strength, camera)

    def draw_ground_glow(self, elapsed):
        self.sprite.draw_flat(Vector3(self.x, self.ground + 0.02, self.z), self.shape.cap_radius * 1.8,
                              self.palette.glow, 0.12 * self.glow_strength(elapsed))

    def draw(self, elapsed):
        camera = CameraBasis.from_modelview()
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        self.draw_body(elapsed)
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        self.draw_glow(elapsed, camera)
        glPopAttrib()
