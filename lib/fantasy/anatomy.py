import math

import numpy

from lib.animals.dragon import unit_or_fallback


def smoothstep(values):
    values = numpy.clip(values, 0.0, 1.0)
    return values * values * (3.0 - 2.0 * values)


def rounded_block(lateral, height, center, half_size, roundness=3.0, edge_power=4.0):
    across = numpy.abs((lateral - center[0]) / half_size[0])
    upward = numpy.abs((height - center[1]) / half_size[1])
    distance = (across ** roundness + upward ** roundness) ** (1.0 / roundness)
    return numpy.sqrt(numpy.clip(1.0 - distance ** edge_power, 0.0, 1.0))


def slanted_bulge(lateral, height, center, direction, half_length, half_width):
    direction = numpy.asarray(direction, dtype=numpy.float64)
    direction = direction / numpy.linalg.norm(direction)
    offset_lateral, offset_height = lateral - center[0], height - center[1]
    along = offset_lateral * direction[0] + offset_height * direction[1]
    across = -offset_lateral * direction[1] + offset_height * direction[0]
    return numpy.sqrt(numpy.clip(1.0 - (along / half_length) ** 2 - (across / half_width) ** 2, 0.0, 1.0))


def segment_distance(lateral, height, start, end):
    start, end = numpy.asarray(start, dtype=numpy.float64), numpy.asarray(end, dtype=numpy.float64)
    span = end - start
    fraction = numpy.clip(((lateral - start[0]) * span[0] + (height - start[1]) * span[1]) / span.dot(span), 0.0, 1.0)
    return numpy.hypot(lateral - start[0] - fraction * span[0], height - start[1] - fraction * span[1])


class MuscleRelief:

    def __init__(self, anchor=(0.0, 0.0, 0.0), axis=(0.0, 1.0, 0.0), anchor_height=0.0, lateral_scale=1.0,
                 vertical_scale=1.0, texture=None):
        self.anchor = numpy.asarray(anchor, dtype=numpy.float64)
        self.axis = numpy.asarray(axis, dtype=numpy.float64) / numpy.linalg.norm(axis)
        self.anchor_height = anchor_height
        self.lateral_scale = lateral_scale
        self.vertical_scale = vertical_scale
        self.texture = texture
        self.ring_count = 120
        self.segment_count = 128
        self.front_falloff = 0.35
        self.pec_thickness = 0.052
        self.pec_crease_height = 1.32
        self.pec_crease_start = 0.07
        self.pec_crease_rise = 2.2
        self.pec_crease_power = 1.6
        self.pec_shelf = 0.16
        self.clavicle_height = 1.58
        self.clavicle_drop = 0.10
        self.sternum_half_width = 0.008
        self.sternum_blend = 0.03
        self.pec_outer_edge = 0.20
        self.pec_outer_blend = 0.08
        self.ab_rows = ((1.255, 0.040), (1.165, 0.042), (1.075, 0.043), (0.988, 0.036))
        self.ab_column_center = 0.049
        self.ab_column_half_width = 0.036
        self.ab_column_narrowing = 0.08
        self.ab_thickness = 0.008
        self.ab_edge_power = 2.0
        self.ab_region = (0.095, 0.95, 1.30)
        self.oblique_center = (0.122, 1.06)
        self.oblique_radii = (0.035, 0.12)
        self.oblique_thickness = 0.018
        self.serratus_heights = (1.37, 1.315, 1.26)
        self.serratus_lateral = 0.19
        self.serratus_direction = (-0.75, -0.55)
        self.serratus_half_length = 0.034
        self.serratus_half_width = 0.012
        self.serratus_thickness = 0.011
        self.navel = (0.0, 0.945)
        self.navel_radius = 0.012
        self.navel_depth = 0.009
        self.groin_line = ((0.16, 1.0), (0.05, 0.84))
        self.groin_width = 0.013
        self.groin_depth = 0.008
        self.lower_belly = (0.0, 0.90, 0.07, 0.06, 0.008)
        self.crease_darkening = 0.38
        self.groove_darkening = 0.12

    def count_around(self, widths, heights):
        return self.segment_count

    def segments(self, widths, heights):
        if self.texture is None:
            return self.segment_count
        return max(self.segment_count, self.texture.segments(widths, heights))

    def rings(self, length):
        if self.texture is None:
            return self.ring_count
        return max(self.ring_count, self.texture.rings(length))

    def pec_crease(self, lateral):
        return self.pec_crease_height + self.pec_crease_rise * numpy.clip(lateral - self.pec_crease_start, 0.0,
                                                                          None) ** self.pec_crease_power

    def pec_masks(self, lateral):
        inner = smoothstep((lateral - self.sternum_half_width) / self.sternum_blend)
        outer = 1.0 - smoothstep((lateral - self.pec_outer_edge) / self.pec_outer_blend)
        return inner, outer

    def pecs(self, lateral, height):
        crease = self.pec_crease(lateral)
        top = self.clavicle_height - self.clavicle_drop * lateral / 0.25
        upward = (height - crease) / numpy.maximum(top - crease, 1e-3)
        shelf = numpy.sin(numpy.clip(upward / self.pec_shelf, 0.0, 1.0) * math.pi / 2.0) ** 0.7
        taper = numpy.clip(1.0 - upward, 0.0, 1.0) ** 0.6
        fullness = 0.75 + 0.25 * numpy.sin(math.pi * numpy.clip(lateral / 0.22, 0.0, 1.0))
        inner, outer = self.pec_masks(lateral)
        return shelf * taper * fullness * inner * outer

    def abdominals(self, lateral, height):
        value = numpy.zeros_like(lateral)
        for row_height, half_height in self.ab_rows:
            narrowing = 1.0 - self.ab_column_narrowing * (self.ab_rows[0][0] - row_height) / 0.27
            block = rounded_block(lateral, height, (self.ab_column_center * narrowing, row_height),
                                  (self.ab_column_half_width * narrowing, half_height),
                                  edge_power=self.ab_edge_power)
            value = numpy.maximum(value, block)
        return value

    def obliques(self, lateral, height):
        offset_lateral = (lateral - self.oblique_center[0]) / self.oblique_radii[0]
        offset_height = (height - self.oblique_center[1]) / self.oblique_radii[1]
        return numpy.sqrt(numpy.clip(1.0 - offset_lateral ** 2 - offset_height ** 2, 0.0, 1.0))

    def serratus(self, lateral, height):
        value = numpy.zeros_like(lateral)
        for finger_height in self.serratus_heights:
            value = numpy.maximum(value, slanted_bulge(lateral, height, (self.serratus_lateral, finger_height),
                                                       self.serratus_direction, self.serratus_half_length,
                                                       self.serratus_half_width))
        return value

    def dents(self, lateral, height):
        navel = self.navel_depth * numpy.exp(-((lateral - self.navel[0]) ** 2 + (height - self.navel[1]) ** 2)
                                             / self.navel_radius ** 2)
        groin_distance = segment_distance(lateral, height, *self.groin_line)
        groin = self.groin_depth * numpy.exp(-(groin_distance / self.groin_width) ** 2)
        return navel, groin

    def lower_belly_bulge(self, lateral, height):
        center_lateral, center_height, half_width, half_height, thickness = self.lower_belly
        return thickness * numpy.sqrt(numpy.clip(1.0 - ((lateral - center_lateral) / half_width) ** 2
                                                 - ((height - center_height) / half_height) ** 2, 0.0, 1.0))

    def local_coordinates(self, grid, widths, around):
        lateral = numpy.abs(widths[:, None] * numpy.sin(around)[None, :]) / self.lateral_scale
        height = self.anchor_height + ((grid - self.anchor) @ self.axis) / self.vertical_scale
        return lateral, height

    def displace(self, grid, centers, widths, heights, around):
        lateral, height = self.local_coordinates(grid, widths, around)
        frontness = smoothstep(numpy.cos(around)[None, :] / self.front_falloff)
        pecs = self.pecs(lateral, height)
        abdominals = self.abdominals(lateral, height)
        navel, groin = self.dents(lateral, height)
        relief = (self.pec_thickness * pecs + self.ab_thickness * abdominals
                  + self.oblique_thickness * self.obliques(lateral, height)
                  + self.serratus_thickness * self.serratus(lateral, height)
                  + self.lower_belly_bulge(lateral, height) - navel - groin)
        relief = relief * frontness * self.lateral_scale
        inner, outer = self.pec_masks(lateral)
        crease_shadow = numpy.exp(-((height - self.pec_crease(lateral) + 0.012) / 0.016) ** 2) * outer
        sternum_shadow = (1.0 - inner) * smoothstep((height - self.pec_crease_height) / 0.04) * (
                1.0 - smoothstep((height - self.clavicle_height + 0.06) / 0.04))
        ab_limit, ab_bottom, ab_top = self.ab_region
        ab_area = ((1.0 - smoothstep((lateral - ab_limit) / 0.02)) * smoothstep((height - ab_bottom) / 0.02)
                   * (1.0 - smoothstep((height - ab_top) / 0.02)))
        grooves = ab_area * (1.0 - abdominals) + groin / self.groin_depth * 0.6 + navel / self.navel_depth
        shade = 1.0 - frontness * (self.crease_darkening * numpy.maximum(crease_shadow, sternum_shadow)
                                   + self.groove_darkening * numpy.clip(grooves, 0.0, 1.0))
        outward = unit_or_fallback(grid - centers[:, None, :], numpy.zeros(3))
        grid = grid + outward * relief[..., None]
        if self.texture is not None:
            grid, texture_shade = self.texture.displace(grid, centers, widths, heights, around)
            shade = shade * texture_shade
        return grid, shade


class Jaw:

    def __init__(self, hinge, lip_front, half_width, chin, max_degrees):
        self.hinge = numpy.asarray(hinge, dtype=numpy.float64)
        self.lip_front = numpy.asarray(lip_front, dtype=numpy.float64)
        self.half_width = half_width
        self.chin = numpy.asarray(chin, dtype=numpy.float64)
        self.max_degrees = max_degrees
        self.behind_hinge_margin = 0.01

    def mouth_line_height(self, depth):
        slope = (self.lip_front[1] - self.hinge[1]) / (self.lip_front[2] - self.hinge[2])
        return self.hinge[1] + (depth - self.hinge[2]) * slope

    def claims(self, positions):
        below_lips = positions[:, 1] < self.mouth_line_height(positions[:, 2])
        ahead_of_hinge = positions[:, 2] > self.hinge[2] - self.behind_hinge_margin
        narrow = numpy.abs(positions[:, 0]) < self.half_width
        return below_lips & ahead_of_hinge & narrow


class Speech:

    def __init__(self, seed=5):
        self.generator = numpy.random.default_rng(seed)
        self.word_count = 24
        self.syllables_per_word = (1, 4)
        self.syllable_seconds = (0.12, 0.24)
        self.syllable_openness = (0.35, 1.0)
        self.word_gap_seconds = (0.05, 0.25)
        self.words_per_sentence = (3, 7)
        self.sentence_gap_seconds = (0.6, 1.1)
        self.syllables = []
        self.duration = 0.0
        self.compose()
        self.starts = numpy.array([start for start, _, _ in self.syllables])

    def compose(self):
        generator = self.generator
        clock = 0.0
        words_left = int(generator.integers(*self.words_per_sentence))
        for _ in range(self.word_count):
            for _ in range(int(generator.integers(self.syllables_per_word[0], self.syllables_per_word[1] + 1))):
                length = generator.uniform(*self.syllable_seconds)
                self.syllables.append((clock, length, generator.uniform(*self.syllable_openness)))
                clock += length
            words_left -= 1
            if words_left == 0:
                clock += generator.uniform(*self.sentence_gap_seconds)
                words_left = int(generator.integers(*self.words_per_sentence))
            else:
                clock += generator.uniform(*self.word_gap_seconds)
        self.duration = clock + self.sentence_gap_seconds[0]

    def openness(self, seconds):
        seconds = seconds % self.duration
        index = int(numpy.searchsorted(self.starts, seconds, side="right")) - 1
        if index < 0:
            return 0.0
        start, length, openness = self.syllables[index]
        progress = (seconds - start) / length
        if progress >= 1.0:
            return 0.0
        return openness * math.sin(math.pi * progress) ** 2


class HairGrower:

    def __init__(self, generator, colliders, step, jitter, fall=(0.0, -1.0, 0.0), floor=0.015):
        self.generator = generator
        self.colliders = [(numpy.asarray(center, dtype=numpy.float64), radius) for center, radius in colliders]
        self.step = step
        self.jitter = jitter
        self.fall = numpy.asarray(fall, dtype=numpy.float64)
        self.floor = floor

    def collided(self, point):
        for center, radius in self.colliders:
            offset = point - center
            distance = float(numpy.linalg.norm(offset))
            if distance < radius:
                point = center + offset / max(distance, 1e-6) * radius
        point[1] = max(point[1], self.floor)
        return point

    def grown(self, root, heading, steps, gravity):
        points = [numpy.asarray(root, dtype=numpy.float64)]
        heading = numpy.asarray(heading, dtype=numpy.float64)
        heading = heading / numpy.linalg.norm(heading)
        for _ in range(steps):
            heading = heading + self.fall * gravity + self.generator.normal(0.0, self.jitter, 3)
            heading = heading / numpy.linalg.norm(heading)
            points.append(self.collided(points[-1] + heading * self.step))
        return numpy.array(points)
