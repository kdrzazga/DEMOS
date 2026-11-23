import math

import numpy

from lib.animals.dragon import catmull_rom, normalized


class Carcass:

    def __init__(self, sculptor, generator, origin, heading):
        self.sculptor = sculptor
        self.generator = generator
        self.origin = numpy.asarray(origin, dtype=numpy.float64)
        self.along = numpy.array((math.cos(heading), 0.0, math.sin(heading)))
        self.up = numpy.array((0.0, 1.0, 0.0))
        self.side = numpy.cross(self.along, self.up)
        self.bone = (0.36, 0.33, 0.27)
        self.old_bone = (0.30, 0.27, 0.21)
        self.dried_flesh = (0.20, 0.10, 0.07)
        self.hide = (0.27, 0.17, 0.09)
        self.hoof = (0.035, 0.03, 0.03)
        self.fur = (0.25, 0.24, 0.22)
        self.spine_points = ((-1.0, 0.07, -0.03), (-0.62, 0.12, 0.0), (0.0, 0.13, 0.0), (0.62, 0.12, 0.02),
                             (0.95, 0.10, 0.12), (1.22, 0.07, 0.32))
        self.vertebra_count = 34
        self.rib_count = 13
        self.rib_span = (0.08, 0.7)
        self.broken_rib_chance = 0.3
        self.fur_tuft_count = 28

    def at(self, u, v, w):
        return self.origin + self.along * u + self.up * v + self.side * w

    def toward(self, u, v, w):
        return normalized(self.along * u + self.up * v + self.side * w)

    def build(self):
        self.build_spine()
        self.build_ribs()
        self.build_pelvis()
        self.build_legs()
        self.build_fur_tufts()

    def bone_shade(self):
        generator = self.generator
        if generator.uniform() < 0.2:
            return self.dried_flesh
        return self.bone if generator.uniform() < 0.6 else self.old_bone

    def build_spine(self):
        sculptor = self.sculptor
        local = catmull_rom(self.spine_points, self.vertebra_count)
        tangents = normalized(numpy.gradient(local, axis=0))
        for index, (point, tangent) in enumerate(zip(local, tangents)):
            fraction = index / (self.vertebra_count - 1)
            center = self.at(*point)
            heading = self.toward(*tangent)
            size = 0.016 if fraction < 0.12 else (0.036 if fraction > 0.82 else 0.03)
            sculptor.ellipsoid(center, heading, size * 0.75, size, size, self.bone_shade(), rings=8, segments=10)
            if 0.15 <= fraction < 0.38:
                for vertical in (1.0, -1.0):
                    sculptor.spike(center, self.toward(0.0, vertical, 0.15), 0.06, 0.012, self.bone_shade(),
                                   rings=5, segments=6)
                sculptor.spike(center, self.toward(-0.3, 0.1, -1.0), 0.05, 0.012, self.bone_shade(), rings=5,
                               segments=6)
            elif 0.38 <= fraction <= 0.8:
                withers = math.exp(-((fraction - 0.68) / 0.12) ** 2)
                sculptor.spike(center, self.toward(-0.35, 0.25, -1.0), 0.07 + 0.08 * withers, 0.013,
                               self.bone_shade(), rings=5, segments=6)

    def build_ribs(self):
        generator = self.generator
        sculptor = self.sculptor
        first, last = self.rib_span
        for index in range(self.rib_count):
            fraction = index / (self.rib_count - 1)
            u = first + (last - first) * fraction
            reach = 0.75 + 0.35 * math.sin(math.pi * fraction)
            root = (u, 0.13, 0.0)
            arch = [root, (u + 0.04 * reach, 0.30 * reach, 0.07 * reach), (u + 0.09 * reach, 0.31 * reach, 0.25 * reach),
                    (u + 0.13 * reach, 0.13, 0.38 * reach)]
            if generator.uniform() < self.broken_rib_chance:
                arch = arch[:3]
            sculptor.tube([self.at(*point) for point in arch], ((0.0, 0.012, 0.012), (1.0, 0.007, 0.007)),
                          self.bone_shade(), rings=14, segments=6)
            if generator.uniform() < 0.6:
                fallen = [(u, 0.05, 0.03), (u + 0.07 * reach, 0.03, 0.2 * reach), (u + 0.13 * reach, 0.02, 0.36 * reach)]
                sculptor.tube([self.at(*point) for point in fallen], ((0.0, 0.011, 0.011), (1.0, 0.007, 0.007)),
                              self.old_bone, rings=10, segments=6)

    def build_pelvis(self):
        sculptor = self.sculptor
        sculptor.ellipsoid(self.at(-0.6, 0.2, -0.02), self.toward(-1.0, 0.5, 0.0), 0.15, 0.075, 0.028, self.bone,
                           up_hint=tuple(self.side), rings=14, segments=16)
        sculptor.ellipsoid(self.at(-0.63, 0.05, 0.13), self.toward(-1.0, -0.1, 0.4), 0.15, 0.075, 0.025,
                           self.old_bone, up_hint=tuple(self.up), rings=14, segments=16)
        sculptor.ellipsoid(self.at(-0.84, 0.12, 0.05), self.toward(-1.0, 0.2, 0.3), 0.11, 0.05, 0.03, self.bone,
                           rings=12, segments=14)
        sculptor.ellipsoid(self.at(-0.73, 0.13, 0.12), self.toward(0.0, 0.0, 1.0), 0.04, 0.035, 0.035,
                           self.dried_flesh, rings=8, segments=10)

    def build_legs(self):
        self.long_bone((0.58, 0.09, 0.12), (0.72, 0.07, 0.2), 0.022)
        self.hide_leg(((0.7, 0.07, 0.2), (1.05, 0.05, 0.42), (1.45, 0.04, 0.62)), (1.0, -0.1, 0.45))
        self.long_bone((-0.73, 0.12, 0.13), (-0.42, 0.05, 0.58), 0.026)
        self.hide_leg(((-0.38, 0.05, 0.62), (0.08, 0.04, 0.95), (0.55, 0.04, 1.12)), (0.7, 0.45, 0.4))
        self.long_bone((-0.25, 0.03, 0.4), (0.33, 0.035, 0.47), 0.018)

    def long_bone(self, start, end, radius):
        sculptor = self.sculptor
        start, end = self.at(*start), self.at(*end)
        middle = (start + end) / 2.0 + self.up * 0.01
        sculptor.tube((start, middle, end), ((0.0, radius, radius), (0.5, radius * 0.75, radius * 0.75),
                                             (1.0, radius, radius)), self.bone, rings=12, segments=8)
        direction = normalized(end - start)
        for knob in (start, end):
            sculptor.ellipsoid(knob, direction, radius * 1.4, radius * 1.5, radius * 1.3, self.old_bone, rings=8,
                               segments=10)

    def hide_leg(self, points, hoof_heading):
        sculptor = self.sculptor
        world = [self.at(*point) for point in points]
        sculptor.tube(world, ((0.0, 0.034, 0.034), (0.55, 0.026, 0.026), (0.85, 0.02, 0.02), (1.0, 0.025, 0.025)),
                      self.hide, rings=20, segments=10)
        heading = self.toward(*hoof_heading)
        across = normalized(numpy.cross(heading, self.up))
        base = world[-1]
        for offset in (1.0, -1.0):
            sculptor.ellipsoid(base + heading * 0.045 + across * offset * 0.013, heading, 0.045, 0.016, 0.022,
                               self.hoof, rings=10, segments=10)
            sculptor.spike(base - heading * 0.03 + across * offset * 0.02, normalized(across * offset - heading),
                           0.025, 0.008, self.hoof)

    def build_fur_tufts(self):
        generator = self.generator
        for _ in range(self.fur_tuft_count):
            u = generator.uniform(-1.3, 1.6)
            w = generator.uniform(-0.6, 1.4)
            size = generator.uniform(0.03, 0.08)
            self.sculptor.ellipsoid(self.at(u, 0.01, w), self.toward(generator.normal(), 0.0, generator.normal()),
                                    size, size * 0.6, size * 0.2, self.fur, up_hint=tuple(self.up), rings=6,
                                    segments=8)
