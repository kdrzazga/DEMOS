import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, StatueMesh, normalized


def camera_axes():
    modelview = numpy.asarray(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=numpy.float64).reshape(4, 4)
    return normalized(modelview[:3, 0]), normalized(modelview[:3, 1])


def glow_disc(center, radius, core_color, core_alpha, rim_color, right, up, segments=20):
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*core_color, core_alpha)
    glVertex3f(*center)
    glColor4f(*rim_color, 0.0)
    for step in range(segments + 1):
        angle = 2.0 * math.pi * step / segments
        glVertex3f(*(center + (right * math.cos(angle) + up * math.sin(angle)) * radius))
    glEnd()


class Particles:

    def __init__(self, capacity, hot, cool, gravity, drag, point_size):
        self.capacity = capacity
        self.hot = numpy.asarray(hot, dtype=numpy.float32)
        self.cool = numpy.asarray(cool, dtype=numpy.float32)
        self.gravity = gravity
        self.drag = drag
        self.point_size = point_size
        self.positions = numpy.zeros((capacity, 3), dtype=numpy.float32)
        self.velocities = numpy.zeros((capacity, 3), dtype=numpy.float32)
        self.ages = numpy.ones(capacity, dtype=numpy.float32)
        self.lives = numpy.ones(capacity, dtype=numpy.float32)
        self.colors = numpy.zeros((capacity, 4), dtype=numpy.float32)
        self.next_slot = 0

    def emit(self, positions, velocities, lives):
        for position, velocity, life in zip(positions, velocities, lives):
            slot = self.next_slot
            self.positions[slot] = position
            self.velocities[slot] = velocity
            self.ages[slot] = 0.0
            self.lives[slot] = life
            self.next_slot = (slot + 1) % self.capacity

    def clear(self):
        self.ages[:] = self.lives

    def update(self, seconds):
        self.ages += seconds
        self.velocities *= max(0.0, 1.0 - self.drag * seconds)
        self.velocities[:, 1] -= self.gravity * seconds
        self.positions += self.velocities * seconds
        fade = numpy.clip(1.0 - self.ages / self.lives, 0.0, 1.0)
        self.colors[:, :3] = self.cool + (self.hot - self.cool) * fade[:, None]
        self.colors[:, 3] = fade

    def render(self):
        glPointSize(self.point_size)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        glColorPointer(4, GL_FLOAT, 0, self.colors)
        glDrawArrays(GL_POINTS, 0, self.capacity)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)


class ThrowingTarget:

    def __init__(self, center, radius):
        self.center = numpy.asarray(center, dtype=numpy.float64)
        self.radius = radius
        self.thickness = 0.04
        self.wood = (0.30, 0.21, 0.13)
        self.straw = numpy.array((0.62, 0.52, 0.30))
        self.ring = numpy.array((0.55, 0.12, 0.08))
        self.bullseye = numpy.array((0.80, 0.62, 0.15))
        self.scorch_radius = 0.09
        self.scorch_strength = 0.65
        self.post = self.build_post()
        self.board = self.build_board()
        self.unburnt = self.board[2].copy()

    def build_post(self):
        mesh = StatueMesh()
        sculptor = Sculptor(mesh)
        x, y, z = self.center
        back = z + self.thickness * 2.0
        for side in (1.0, -1.0):
            sculptor.tube(((x + side * self.radius * 0.7, -0.05, back + 0.12), (x + side * self.radius * 0.45,
                                                                                y * 0.5, back + 0.05),
                           (x + side * self.radius * 0.25, y + self.radius * 0.6, back)),
                          ((0.0, 0.022, 0.022), (1.0, 0.018, 0.018)), self.wood, rings=10, segments=8)
        sculptor.tube(((x - self.radius * 0.6, y - self.radius * 0.8, back), (x, y - self.radius * 0.82, back),
                       (x + self.radius * 0.6, y - self.radius * 0.8, back)),
                      ((0.0, 0.015, 0.015), (1.0, 0.015, 0.015)), self.wood, rings=8, segments=8)
        return mesh.arrays()

    def build_board(self):
        mesh = StatueMesh()
        Sculptor(mesh).ellipsoid(self.center + (0.0, 0.0, self.thickness), (0.0, 0.0, 1.0), self.thickness,
                                 self.radius, self.radius, tuple(self.straw), up_hint=(0.0, 1.0, 0.0), rings=10,
                                 segments=40)
        positions, normals, colors, indices = mesh.arrays()
        distance = numpy.linalg.norm(positions[:, :2] - self.center[:2], axis=1) / self.radius
        band = (numpy.floor(distance * 5.0).astype(int) % 2 == 1)[:, None]
        painted = numpy.where(band, self.ring, self.straw)
        painted = numpy.where((distance < 0.2)[:, None], self.bullseye, painted)
        mottle = colors[:, :1] / self.straw[0]
        colors[:] = painted * mottle
        return positions, normals, colors, indices

    def clear_scorch(self):
        self.board[2][:] = self.unburnt

    def scorch(self, point):
        positions, _, colors, _ = self.board
        distance = numpy.linalg.norm(positions - point, axis=1)
        darkening = self.scorch_strength * numpy.exp(-(distance / self.scorch_radius) ** 2)
        colors *= (1.0 - darkening)[:, None]

    def crossing(self, start, end):
        face = self.center[2]
        if not start[2] < face <= end[2]:
            return None
        point = start + (end - start) * (face - start[2]) / (end[2] - start[2])
        if numpy.linalg.norm(point[:2] - self.center[:2]) > self.radius:
            return None
        return point

    @staticmethod
    def draw(positions, normals, colors, indices):
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

    def render(self):
        self.draw(*self.post)
        self.draw(*self.board)


class Fireballs:

    def __init__(self, target, seed=23):
        self.target = target
        self.generator = numpy.random.default_rng(seed)
        self.speed = 5.0
        self.max_range = 8.0
        self.radius = 0.08
        self.glow_radius = 0.26
        self.core_color = (1.0, 0.95, 0.70)
        self.flame_color = (1.0, 0.50, 0.10)
        self.ember_color = (0.85, 0.18, 0.03)
        self.light_color = numpy.array((1.0, 0.55, 0.20))
        self.trail_rate = 220.0
        self.explosion_seconds = 0.65
        self.blast_radius = 1.0
        self.spark_count = 120
        self.spark_speed = (1.2, 4.0)
        self.smoke_count = 12
        self.smoke_seconds = (0.9, 1.6)
        self.smoke_color = (0.10, 0.09, 0.08)
        self.flying = []
        self.explosions = []
        self.smoke = []
        self.trail = Particles(400, (1.0, 0.75, 0.25), (0.6, 0.08, 0.02), -0.4, 2.0, 6.0)
        self.sparks = Particles(400, (1.0, 0.85, 0.45), (0.8, 0.15, 0.02), 3.5, 1.2, 4.0)
        self.seconds = 0.0

    def clear(self):
        self.flying = []
        self.explosions = []
        self.smoke = []
        self.trail.clear()
        self.sparks.clear()

    def throw(self, origin, direction):
        self.flying.append([numpy.asarray(origin, dtype=numpy.float64), normalized(direction), 0.0, 0.0])

    def explode(self, point):
        generator = self.generator
        self.explosions.append([0.0, point])
        directions = normalized(generator.normal(size=(self.spark_count, 3)) + (0.0, 0.4, -0.5))
        speeds = generator.uniform(*self.spark_speed, self.spark_count)[:, None]
        self.sparks.emit(numpy.repeat(point[None, :], self.spark_count, axis=0), directions * speeds,
                         generator.uniform(0.3, 0.8, self.spark_count))
        for _ in range(self.smoke_count):
            drift = generator.normal(0.0, 0.12, 3) + (0.0, 0.25, -0.1)
            self.smoke.append([0.0, generator.uniform(*self.smoke_seconds), point + generator.normal(0.0, 0.04, 3),
                               drift, generator.uniform(0.14, 0.26)])
        self.target.scorch(point)

    def update(self, seconds):
        self.seconds += seconds
        generator = self.generator
        still_flying = []
        for fireball in self.flying:
            start, direction, travelled, owed_trail = fireball
            end = start + direction * self.speed * seconds
            travelled += self.speed * seconds
            owed_trail += self.trail_rate * seconds
            emitted = int(owed_trail)
            if emitted:
                along = generator.uniform(0.0, 1.0, (emitted, 1))
                self.trail.emit(start + (end - start) * along + generator.normal(0.0, self.radius * 0.4, (emitted, 3)),
                                generator.normal(0.0, 0.15, (emitted, 3)) - direction * 0.4,
                                generator.uniform(0.15, 0.35, emitted))
            hit = self.target.crossing(start, end)
            if hit is not None:
                self.explode(hit)
            elif end[1] <= 0.0 or travelled > self.max_range:
                self.explode(end)
            else:
                still_flying.append([end, direction, travelled, owed_trail - emitted])
        self.flying = still_flying
        for explosion in self.explosions:
            explosion[0] += seconds
        self.explosions = [explosion for explosion in self.explosions if explosion[0] < self.explosion_seconds]
        for puff in self.smoke:
            puff[0] += seconds
            puff[2] = puff[2] + puff[3] * seconds
        self.smoke = [puff for puff in self.smoke if puff[0] < puff[1]]
        self.trail.update(seconds)
        self.sparks.update(seconds)

    def flicker(self, offset):
        return 1.0 + 0.15 * math.sin(self.seconds * 37.0 + offset) + 0.08 * math.sin(self.seconds * 61.0 + offset)

    def brightest(self, held):
        sources = [(position, 0.6 * charge) for position, charge in held if charge > 0.05]
        sources += [(fireball[0], 1.0) for fireball in self.flying]
        sources += [(point, 2.5 * (1.0 - age / self.explosion_seconds) ** 2 * 1.6) for age, point in self.explosions]
        return max(sources, key=lambda source: source[1], default=None)

    def place_light(self, light, held, attenuation):
        source = self.brightest(held)
        if source is None:
            glDisable(light)
            return
        position, strength = source
        constant, linear, quadratic = attenuation
        color = (*(self.light_color * strength), 1.0)
        glEnable(light)
        glLightfv(light, GL_POSITION, (*position, 1.0))
        glLightfv(light, GL_DIFFUSE, color)
        glLightfv(light, GL_SPECULAR, color)
        glLightfv(light, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightf(light, GL_CONSTANT_ATTENUATION, constant)
        glLightf(light, GL_LINEAR_ATTENUATION, linear)
        glLightf(light, GL_QUADRATIC_ATTENUATION, quadratic)

    def draw_fireball(self, center, size, offset, right, up):
        flicker = self.flicker(offset)
        glow_disc(center, self.glow_radius * size * flicker, self.flame_color, 0.55, self.ember_color, right, up)
        glow_disc(center, self.radius * size * flicker, self.core_color, 1.0, self.flame_color, right, up)

    def render(self, held):
        right, up = camera_axes()
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_CURRENT_BIT | GL_POINT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for age, life, center, _, size in self.smoke:
            progress = age / life
            glow_disc(center, size * (1.0 + 2.5 * progress), self.smoke_color, 0.55 * (1.0 - progress),
                      self.smoke_color, right, up, 14)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_POINT_SMOOTH)
        self.trail.render()
        self.sparks.render()
        for number, (position, charge) in enumerate(held):
            if charge > 0.05:
                self.draw_fireball(numpy.asarray(position), charge, number * 2.1, right, up)
        for number, fireball in enumerate(self.flying):
            self.draw_fireball(fireball[0], 1.0, 5.0 + number * 1.3, right, up)
        for age, point in self.explosions:
            progress = age / self.explosion_seconds
            radius = self.blast_radius * (0.25 + 0.75 * math.sqrt(progress))
            glow_disc(point, radius, self.flame_color, 0.9 * (1.0 - progress), self.ember_color, right, up, 28)
            glow_disc(point, radius * 0.45, self.core_color, (1.0 - progress) ** 2, self.flame_color, right, up)
        glPopAttrib()
