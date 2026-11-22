import math
import os

import numpy
import pygame
from OpenGL.GL import *

from lib import Globals
from lib.animals.shark import hermite_profile, quadratic_curve


def normalized(vectors):
    vectors = numpy.asarray(vectors, dtype=numpy.float64)
    lengths = numpy.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / numpy.maximum(lengths, 1e-12)


def catmull_rom(points, count):
    points = numpy.asarray(points, dtype=numpy.float64)
    padded = numpy.vstack((2.0 * points[0] - points[1], points, 2.0 * points[-1] - points[-2]))
    spans = len(points) - 1
    position = numpy.linspace(0.0, spans, count)
    segment = numpy.minimum(numpy.floor(position).astype(int), spans - 1)
    local = (position - segment)[:, None]
    before, start, end, after = padded[segment], padded[segment + 1], padded[segment + 2], padded[segment + 3]
    return 0.5 * (2.0 * start + (end - before) * local
                  + (2.0 * before - 5.0 * start + 4.0 * end - after) * local ** 2
                  + (3.0 * start - before - 3.0 * end + after) * local ** 3)


def mottling(positions, strength):
    x, y, z = positions[..., 0], positions[..., 1], positions[..., 2]
    wave = (0.5 * numpy.sin(x * 37.0 + y * 11.0) * numpy.sin(y * 29.0 - z * 17.0)
            + 0.3 * numpy.sin(z * 53.0 + x * 23.0 + y * 7.0)
            + 0.2 * numpy.sin(x * 97.0 + y * 83.0 + z * 71.0))
    return 1.0 + strength * wave


def surface_normals(grid, inside, wrap_columns):
    along = numpy.gradient(grid, axis=0)
    if wrap_columns:
        ring = grid[:, :-1]
        across = numpy.roll(ring, -1, axis=1) - numpy.roll(ring, 1, axis=1)
        across = numpy.concatenate((across, across[:, :1]), axis=1)
    else:
        across = numpy.gradient(grid, axis=1)
    normals = numpy.cross(along, across)
    flip = numpy.sum(normals * (grid - inside), axis=-1) < 0.0
    normals[flip] = -normals[flip]
    return normals


def unit_or_fallback(normals, fallback):
    lengths = numpy.linalg.norm(normals, axis=-1, keepdims=True)
    fallback = numpy.broadcast_to(fallback, normals.shape)
    return numpy.where(lengths > 1e-12, normals / numpy.maximum(lengths, 1e-12), fallback)


class StatueMesh:

    def __init__(self):
        self.positions = []
        self.normals = []
        self.colors = []
        self.indices = []
        self.vertex_count = 0

    def add_vertices(self, positions, normals, colors):
        first = self.vertex_count
        positions = numpy.asarray(positions, dtype=numpy.float32).reshape(-1, 3)
        self.positions.append(positions)
        self.normals.append(numpy.asarray(normals, dtype=numpy.float32).reshape(-1, 3))
        colors = numpy.asarray(colors, dtype=numpy.float32).reshape(-1, 3)
        self.colors.append(numpy.broadcast_to(colors, positions.shape))
        self.vertex_count += len(positions)
        return first

    def add_grid(self, grid, normals, colors):
        rows, columns = grid.shape[:2]
        colors = numpy.broadcast_to(numpy.asarray(colors, dtype=numpy.float64), grid.shape)
        first = self.add_vertices(grid, normals, colors)
        row = numpy.arange(rows - 1)[:, None]
        column = numpy.arange(columns - 1)[None, :]
        corner = first + row * columns + column
        quads = numpy.stack((corner, corner + columns, corner + 1, corner + 1, corner + columns, corner + columns + 1),
                            axis=-1)
        self.indices.append(quads.reshape(-1).astype(numpy.uint32))

    def add_quad(self, corners, normals, color):
        first = self.add_vertices(corners, normals, color)
        self.indices.append(numpy.array((0, 1, 2, 0, 2, 3), dtype=numpy.uint32) + first)

    def arrays(self):
        return (numpy.ascontiguousarray(numpy.concatenate(self.positions)),
                numpy.ascontiguousarray(numpy.concatenate(self.normals)),
                numpy.ascontiguousarray(numpy.concatenate(self.colors)),
                numpy.ascontiguousarray(numpy.concatenate(self.indices)))


class Scales:

    def __init__(self, size, flow):
        self.size = size
        self.flow = flow
        self.relief = 0.32
        self.groove_darkening = 0.3
        self.edge_scallop = 0.45
        self.vertices_per_scale = 4
        self.shingle_power = 0.75

    def count_around(self, widths, heights):
        radii = (numpy.asarray(widths) + numpy.asarray(heights)) / 2.0
        radii = radii[radii > 0.0]
        median_radius = float(numpy.median(radii)) if len(radii) else self.size
        return max(4, round(2.0 * math.pi * median_radius / self.size))

    def segments(self, widths, heights):
        return self.count_around(widths, heights) * self.vertices_per_scale

    def rings(self, length):
        return math.ceil(length / self.size * self.vertices_per_scale) + 1

    def displace(self, grid, centers, widths, heights, around):
        steps = numpy.linalg.norm(numpy.diff(centers, axis=0), axis=-1)
        distance = numpy.concatenate(((0.0,), numpy.cumsum(steps)))
        rows = distance / self.size
        stagger = 0.5 * (numpy.floor(rows) % 2.0)
        columns = around[None, :] / (2.0 * math.pi) * self.count_around(widths, heights) + stagger[:, None]
        toward_edge = numpy.broadcast_to((rows % 1.0)[:, None], columns.shape)
        if self.flow < 0.0:
            toward_edge = 1.0 - toward_edge
        sideways = 2.0 * (columns % 1.0 - 0.5)
        free_edge = 1.0 - self.edge_scallop * sideways * sideways
        lift = numpy.where(toward_edge < free_edge,
                           (numpy.clip(toward_edge / free_edge, 0.0, 1.0)) ** self.shingle_power, 0.0)
        thickness = numpy.clip((widths + heights) / (4.0 * self.size), 0.0, 1.0)[:, None]
        outward = unit_or_fallback(grid - centers[:, None, :], numpy.zeros(3))
        shade = 1.0 - self.groove_darkening * (1.0 - lift) * thickness
        return grid + outward * (self.relief * self.size * lift * thickness)[..., None], shade


class MouthLining:

    def __init__(self, facing_angle):
        self.facing_angle = facing_angle
        self.spread = 1.25
        self.soft_edge = 0.35
        self.deep_color = numpy.array((0.28, 0.04, 0.04))
        self.lip_color = numpy.array((0.78, 0.30, 0.26))

    def weight(self, around, ring_count):
        apart = numpy.abs(numpy.angle(numpy.exp(1j * (around - self.facing_angle))))
        band = 1.0 - numpy.clip((apart - (self.spread - self.soft_edge)) / self.soft_edge, 0.0, 1.0)
        return numpy.broadcast_to(band[None, :], (ring_count, len(around))).copy()

    def colors(self, ring_count):
        along = numpy.linspace(0.0, 1.0, ring_count)[:, None] ** 0.8
        return self.deep_color + (self.lip_color - self.deep_color) * along


class Sculptor:

    def __init__(self, mesh):
        self.mesh = mesh
        self.default_mottle = 0.05
        self.dome_rings = 5
        self.dome_depth = 0.85

    def sweep(self, centers, widths, heights, color, up_hint=None, segments=20, cap_start=False, cap_end=False,
              mottle=None, scales=None, lining=None):
        centers = numpy.asarray(centers, dtype=numpy.float64)
        widths = numpy.asarray(widths, dtype=numpy.float64)
        heights = numpy.asarray(heights, dtype=numpy.float64)
        tangents = normalized(numpy.gradient(centers, axis=0))
        if up_hint is None:
            overall = normalized(centers[-1] - centers[0])
            up_hint = (1.0, 0.0, 0.0) if abs(overall[1]) > 0.8 else (0.0, 1.0, 0.0)
        sides = normalized(numpy.cross(tangents, numpy.asarray(up_hint, dtype=numpy.float64)))
        ups = numpy.cross(sides, tangents)
        frame = centers, sides, ups, widths, heights
        if cap_start:
            dome = numpy.linspace(1.0, 0.0, self.dome_rings, endpoint=False)
            depth = (widths[0] + heights[0]) / 2.0 * self.dome_depth
            rounding = numpy.sqrt(1.0 - dome * dome)
            centers = numpy.vstack((centers[0] - tangents[0] * (dome * depth)[:, None], centers))
            tangents, sides, ups = (numpy.vstack((numpy.repeat(array[:1], len(dome), axis=0), array))
                                    for array in (tangents, sides, ups))
            widths = numpy.concatenate((widths[0] * rounding, widths))
            heights = numpy.concatenate((heights[0] * rounding, heights))
        if cap_end:
            dome = numpy.linspace(0.0, 1.0, self.dome_rings + 1)[1:]
            depth = (widths[-1] + heights[-1]) / 2.0 * self.dome_depth
            rounding = numpy.sqrt(1.0 - dome * dome)
            centers = numpy.vstack((centers, centers[-1] + tangents[-1] * (dome * depth)[:, None]))
            tangents, sides, ups = (numpy.vstack((array, numpy.repeat(array[-1:], len(dome), axis=0)))
                                    for array in (tangents, sides, ups))
            widths = numpy.concatenate((widths, widths[-1] * rounding))
            heights = numpy.concatenate((heights, heights[-1] * rounding))
        around = numpy.linspace(0.0, 2.0 * math.pi, segments + 1)
        grid = (centers[:, None, :]
                + sides[:, None, :] * (widths[:, None] * numpy.sin(around)[None, :])[..., None]
                + ups[:, None, :] * (heights[:, None] * numpy.cos(around)[None, :])[..., None])
        shade = numpy.ones(grid.shape[:2])
        lining_weight = numpy.zeros(grid.shape[:2]) if lining is None else lining.weight(around, len(centers))
        if scales is not None:
            scaled, scaled_shade = scales.displace(grid, centers, widths, heights, around)
            grid = scaled + (grid - scaled) * lining_weight[..., None]
            shade = scaled_shade + (1.0 - scaled_shade) * lining_weight
        end_sign = numpy.where(numpy.arange(len(centers)) < len(centers) / 2.0, -1.0, 1.0)
        fallback = tangents[:, None, :] * end_sign[:, None, None]
        normals = unit_or_fallback(surface_normals(grid, centers[:, None, :], True), fallback)
        strength = self.default_mottle if mottle is None else mottle
        colors = numpy.asarray(color) * (mottling(grid, strength) * shade)[..., None]
        if lining is not None:
            colors = colors + (lining.colors(len(centers))[:, None, :] - colors) * lining_weight[..., None]
        self.mesh.add_grid(grid, normals, colors)
        return frame

    def tube(self, control_points, profile, color, rings=24, segments=20, up_hint=None, cap_start=True,
             cap_end=True, mottle=None, scales=None, lining=None):
        knots, widths, heights = (numpy.array(column, dtype=numpy.float64) for column in zip(*profile))
        if scales is not None:
            length = float(numpy.linalg.norm(numpy.diff(catmull_rom(control_points, 64), axis=0), axis=-1).sum())
            rings = max(rings, scales.rings(length))
            segments = max(segments, scales.segments(widths, heights))
        centers = catmull_rom(control_points, rings)
        along = numpy.linspace(0.0, 1.0, rings)
        widths = numpy.maximum(hermite_profile(knots, widths, along), 0.0)
        heights = numpy.maximum(hermite_profile(knots, heights, along), 0.0)
        return self.sweep(centers, widths, heights, color, up_hint, segments, cap_start, cap_end, mottle, scales,
                          lining)

    def ellipsoid(self, center, axis, half_length, width, height, color, up_hint=None, rings=16, segments=20,
                  mottle=None, scales=None):
        axis = normalized(axis)
        if scales is not None:
            rings = max(rings, scales.rings(math.pi * half_length))
            segments = max(segments, scales.segments((width,), (height,)))
        spread = -numpy.cos(numpy.linspace(0.0, math.pi, rings))
        centers = numpy.asarray(center, dtype=numpy.float64) + spread[:, None] * axis * half_length
        bulge = numpy.sqrt(numpy.clip(1.0 - spread * spread, 0.0, 1.0))
        return self.sweep(centers, width * bulge, height * bulge, color, up_hint, segments, mottle=mottle,
                          scales=scales)

    def spike(self, base, direction, length, radius, color, curl=(0.0, 0.0, 0.0), rings=7, segments=10):
        base = numpy.asarray(base, dtype=numpy.float64)
        direction = normalized(direction)
        middle = base + direction * length * 0.5 + numpy.asarray(curl, dtype=numpy.float64) * length
        centers = catmull_rom((base, middle, base + direction * length), rings)
        along = numpy.linspace(0.0, 1.0, rings)
        widths = radius * (1.0 - along) ** 1.1
        return self.sweep(centers, widths, widths, color, segments=segments, cap_start=True, mottle=0.02)

    def ridge_spikes(self, frame, first, last, count, length, radius, lean, color):
        centers, sides, ups, widths, heights = frame
        tangents = normalized(numpy.gradient(centers, axis=0))
        for index in numpy.linspace(first * (len(centers) - 1), last * (len(centers) - 1), count).astype(int):
            base = centers[index] + ups[index] * heights[index] * 0.85
            fade = 1.0 - 0.5 * abs(index / (len(centers) - 1) - (first + last) / 2.0) / max(last - first, 1e-6)
            self.spike(base, ups[index] + tangents[index] * lean, length * fade, radius * fade, color)


class StrokeFont:

    def __init__(self):
        self.half_stroke = 0.09
        self.arc_samples = 18
        self.space_advance = 0.42
        self.glyphs = {
            "E": (0.78, (((0.62, 0.91), (0.09, 0.91), (0.09, 0.09), (0.62, 0.09)),
                         ((0.09, 0.5), (0.52, 0.5)))),
            "S": (0.78, (numpy.vstack((self.arc((0.36, 0.705), (0.26, 0.205), 15.0, 270.0),
                                       self.arc((0.36, 0.295), (0.27, 0.205), 90.0, -165.0)[1:])),)),
            "T": (0.74, (((0.0, 0.91), (0.66, 0.91)), ((0.33, 0.91), (0.33, 0.09)))),
            ".": (0.40, (((0.14, 0.09), (0.14, 0.12)),)),
            "2": (0.78, (self.arc((0.36, 0.68), (0.26, 0.23), 160.0, -35.0),
                         ((0.57, 0.548), (0.13, 0.13)),
                         ((0.09, 0.09), (0.64, 0.09)))),
            "0": (0.80, (self.arc((0.37, 0.5), (0.27, 0.41), 90.0, 450.0)[:-1],)),
            "1": (0.72, (((0.36, 0.91), (0.36, 0.09)), ((0.36, 0.91), (0.14, 0.75)), ((0.14, 0.09), (0.58, 0.09)))),
            "4": (0.80, (((0.50, 0.91), (0.50, 0.09)), ((0.50, 0.91), (0.09, 0.33)), ((0.09, 0.33), (0.68, 0.33)))),
        }
        self.closed_glyphs = {"0"}

    def arc(self, center, radii, start_degrees, end_degrees):
        angles = numpy.radians(numpy.linspace(start_degrees, end_degrees, self.arc_samples))
        return numpy.stack((center[0] + radii[0] * numpy.cos(angles), center[1] + radii[1] * numpy.sin(angles)), axis=-1)

    def advance(self, character):
        return self.glyphs[character][0] if character in self.glyphs else self.space_advance

    def strokes(self, character):
        if character not in self.glyphs:
            return ()
        closed = character in self.closed_glyphs
        return tuple((numpy.asarray(points, dtype=numpy.float64), closed) for points in self.glyphs[character][1])

    def outline(self, points, closed):
        if not closed:
            points = points.copy()
            points[0] -= normalized(points[1] - points[0]) * self.half_stroke
            points[-1] += normalized(points[-1] - points[-2]) * self.half_stroke
        following = numpy.roll(points, -1, axis=0)
        directions = normalized(following - points)
        segment_normals = numpy.stack((-directions[:, 1], directions[:, 0]), axis=-1)
        incoming = numpy.roll(segment_normals, 1, axis=0)
        outgoing = segment_normals.copy()
        if not closed:
            outgoing[-1] = segment_normals[-2]
            incoming[0] = segment_normals[0]
        bisectors = normalized(incoming + outgoing)
        stretch = 1.0 / numpy.maximum(numpy.sum(bisectors * outgoing, axis=-1), 0.5)
        offsets = bisectors * (stretch * self.half_stroke)[:, None]
        return points + offsets, points - offsets, segment_normals, directions


class DrumInscription:

    def __init__(self, sculptor, font, text, drum_radius, center_height, letter_height, relief, color):
        self.mesh = sculptor.mesh
        self.font = font
        self.text = text
        self.drum_radius = drum_radius
        self.center_height = center_height
        self.letter_height = letter_height
        self.sunk_depth = 0.003
        self.relief = relief
        self.color = numpy.asarray(color, dtype=numpy.float64)

    def placed(self, along, height, lift):
        angle = along / self.drum_radius
        radius = self.drum_radius + lift
        return numpy.stack((radius * numpy.sin(angle), height, radius * numpy.cos(angle)), axis=-1)

    def outward(self, along):
        angle = along / self.drum_radius
        return numpy.stack((numpy.sin(angle), numpy.zeros_like(angle), numpy.cos(angle)), axis=-1)

    def surface_direction(self, along, flat_direction):
        angle = along / self.drum_radius
        return normalized(numpy.array((flat_direction[0] * math.cos(angle), flat_direction[1],
                                       -flat_direction[0] * math.sin(angle))))

    def carve(self):
        width = sum(self.font.advance(character) for character in self.text) * self.letter_height
        cursor = -width / 2.0
        baseline = self.center_height - self.letter_height / 2.0
        for character in self.text:
            for points, closed in self.font.strokes(character):
                self.raise_stroke(points, closed, cursor, baseline)
            cursor += self.font.advance(character) * self.letter_height

    def raise_stroke(self, points, closed, cursor, baseline):
        left, right, segment_normals, directions = self.font.outline(points, closed)
        left = left * self.letter_height + (cursor, baseline)
        right = right * self.letter_height + (cursor, baseline)
        top, bottom = self.relief, -self.sunk_depth
        segment_count = len(left) if closed else len(left) - 1
        for index in range(segment_count):
            following = (index + 1) % len(left)
            middle_along = (left[index][0] + right[following][0]) / 2.0
            front = self.placed(numpy.array((left[index][0], left[following][0], right[following][0], right[index][0])),
                                numpy.array((left[index][1], left[following][1], right[following][1], right[index][1])),
                                top)
            front_normals = self.outward(numpy.array((left[index][0], left[following][0], right[following][0],
                                                      right[index][0])))
            self.mesh.add_quad(front, front_normals, self.color)
            for edge, sign in ((left, 1.0), (right, -1.0)):
                normal = self.surface_direction(middle_along, segment_normals[index] * sign)
                self.wall(edge[index], edge[following], normal, top, bottom)
        if not closed:
            start_normal = self.surface_direction(left[0][0], -directions[0])
            self.wall(right[0], left[0], start_normal, top, bottom)
            end_normal = self.surface_direction(left[-1][0], directions[-2])
            self.wall(left[-1], right[-1], end_normal, top, bottom)

    def wall(self, start, end, normal, top, bottom):
        along = numpy.array((start[0], end[0], end[0], start[0]))
        height = numpy.array((start[1], end[1], end[1], start[1]))
        lift = numpy.array((bottom, bottom, top, top))
        angle = along / self.drum_radius
        radius = self.drum_radius + lift
        corners = numpy.stack((radius * numpy.sin(angle), height, radius * numpy.cos(angle)), axis=-1)
        self.mesh.add_quad(corners, numpy.tile(normal, (4, 1)), self.color * 0.82)


class DragonModel:

    def __init__(self, seed=14):
        self.generator = numpy.random.default_rng(seed)
        self.clay = (0.74, 0.55, 0.47)
        self.bone_clay = (0.82, 0.64, 0.55)
        self.membrane_clay = (0.70, 0.48, 0.40)
        self.eye_color = (0.22, 0.13, 0.11)
        self.cobble_gray = (0.50, 0.51, 0.53)
        self.drum_gray = (0.33, 0.33, 0.35)
        self.gilding = (0.82, 0.63, 0.30)
        self.caption = "EST. 2014"
        self.plinth_top = 0.322
        self.cobble_count = 24
        self.cobble_groove_width = 0.006
        self.cobble_groove_depth = 0.012
        self.cobble_bulge = 0.006
        self.cobble_profile = ((0.385, 0.0), (0.398, 0.008), (0.405, 0.025), (0.405, 0.05), (0.398, 0.068),
                               (0.385, 0.077), (0.36, 0.08), (0.33, 0.08), (0.28, 0.08))
        self.drum_radius = 0.295
        self.drum_profile = ((0.30, 0.08), (0.31, 0.088), (0.30, 0.096), (0.295, 0.10), (0.295, 0.17),
                             (0.295, 0.245), (0.30, 0.25), (0.31, 0.257), (0.30, 0.265), (0.31, 0.27),
                             (0.325, 0.282), (0.328, 0.298), (0.318, 0.312), (0.30, 0.318), (0.15, self.plinth_top),
                             (0.0, self.plinth_top))
        self.drum_segments = 144
        self.caption_center_height = 0.173
        self.caption_letter_height = 0.045
        self.caption_relief = 0.0075
        self.torso_points = ((0.0, 0.37, -0.17), (0.0, 0.44, -0.11), (0.0, 0.51, -0.03), (0.0, 0.57, 0.03),
                             (0.0, 0.61, 0.06))
        self.torso_profile = ((0.0, 0.05, 0.05), (0.2, 0.11, 0.095), (0.5, 0.12, 0.105), (0.8, 0.09, 0.085),
                              (1.0, 0.06, 0.06))
        self.neck_points = ((0.0, 0.57, 0.05), (0.0, 0.64, 0.08), (0.0, 0.685, 0.13), (0.0, 0.675, 0.18))
        self.neck_profile = ((0.0, 0.065, 0.065), (0.5, 0.05, 0.05), (1.0, 0.04, 0.042))
        self.ember_color = (0.85, 0.22, 0.06)
        self.skull_points = ((0.0, 0.675, 0.165), (0.0, 0.662, 0.23), (0.0, 0.632, 0.30), (0.0, 0.608, 0.35))
        self.skull_profile = ((0.0, 0.044, 0.034), (0.2, 0.048, 0.036), (0.5, 0.034, 0.025), (0.8, 0.024, 0.017),
                              (1.0, 0.010, 0.008))
        self.jaw_points = ((0.0, 0.635, 0.19), (0.0, 0.575, 0.255), (0.0, 0.52, 0.315))
        self.jaw_profile = ((0.0, 0.032, 0.02), (0.6, 0.024, 0.014), (1.0, 0.010, 0.007))
        self.eye_position = (0.041, 0.677, 0.232)
        self.brow_position = (0.03, 0.694, 0.226)
        self.torso_scales = Scales(0.018, -1.0)
        self.neck_scales = Scales(0.0135, -1.0)
        self.head_scales = Scales(0.00975, -1.0)
        self.thigh_scales = Scales(0.0165, -1.0)
        self.limb_scales = Scales(0.01125, 1.0)
        self.paw_scales = Scales(0.00825, 1.0)
        self.tail_scales = Scales(0.0135, 1.0)
        self.upper_tooth_count = 7
        self.lower_tooth_count = 6
        self.crown_center = (0.0, 0.695, 0.165)
        self.crown_spike_count = 9
        self.crown_spread_degrees = 75.0
        self.tail_points = ((0.0, 0.39, -0.17), (0.08, 0.35, -0.25), (0.19, 0.335, -0.22), (0.26, 0.335, -0.10),
                            (0.27, 0.335, 0.04), (0.22, 0.335, 0.17), (0.12, 0.337, 0.25), (0.0, 0.34, 0.27),
                            (-0.06, 0.342, 0.26))
        self.tail_profile = ((0.0, 0.055, 0.05), (0.25, 0.04, 0.035), (0.6, 0.025, 0.022), (1.0, 0.008, 0.007))
        self.wing_shoulder = (0.085, 0.60, -0.05)
        self.wing_elbow = (0.21, 0.73, -0.13)
        self.wing_wrist = (0.15, 0.90, -0.09)
        self.wing_flank = (0.12, 0.47, -0.08)
        self.wing_fingers = (((0.42, 0.93, -0.10), (0.66, 0.62, 0.02)),
                             ((0.40, 0.66, -0.10), (0.55, 0.36, -0.02)),
                             ((0.24, 0.60, -0.10), (0.30, 0.31, -0.05)))
        self.membrane_rows = 28
        self.membrane_columns = 16
        self.membrane_sag = 0.16
        self.membrane_billow = 0.06
        self.membrane_half_thickness = 0.0018
        self.vein_color = (0.58, 0.34, 0.29)
        self.vein_ribs_per_panel = 4
        self.vein_branches_per_rib = 3
        self.vein_rib_radius = (0.0032, 0.0022)
        self.vein_branch_radius = (0.0024, 0.0012)
        self.vein_branch_steps = 7
        self.vein_branch_step = 0.035
        self.vein_branch_turn = 0.45
        self.tail_centerline_samples = 64
        self.wing_text_areas = {-1.0: (-0.38, 0.67, 0.456, 0.312, 52.0), 1.0: (0.38, 0.67, 0.456, 0.312, -52.0)}
        self.wing_text_lift = 0.0036
        self.membrane_sheets = []
        self.mesh = StatueMesh()
        self.sculptor = Sculptor(self.mesh)
        self.rocky_base = self.built(self.build_rocky_base, self.sweep_from_front)
        self.solid_base = self.built(self.build_solid_base, self.bottom_up)
        self.caption_letters = self.built(self.build_caption, self.left_to_right)
        self.body = self.built(self.build_figure)
        self.eyes = self.built(self.build_eyes)
        self.jaw = self.built(self.build_jaw)
        self.jaw_hinge = numpy.asarray(self.jaw_points[0], dtype=numpy.float32)
        self.tail = self.built(self.build_tail)
        self.tail_along, self.tail_sideways = self.tail_bend_frame(self.tail[0])
        self.wings = {}
        self.wing_decals = {}
        for side in (1.0, -1.0):
            self.membrane_sheets = []
            self.wings[side] = self.built(lambda: self.build_wing(side))
            self.wing_decals[side] = self.wing_decal(side)
        self.total_height = max(float(positions[:, 1].max())
                                for positions, _, _, _ in (self.body, self.tail, *self.wings.values()))

    def use_mesh(self, mesh):
        self.mesh = mesh
        self.sculptor.mesh = mesh

    def built(self, builder, triangle_order=None):
        self.use_mesh(StatueMesh())
        builder()
        positions, normals, colors, indices = self.mesh.arrays()
        if triangle_order is not None:
            triangles = indices.reshape(-1, 3)
            order = numpy.argsort(triangle_order(positions[triangles].mean(axis=1)), kind="stable")
            indices = numpy.ascontiguousarray(triangles[order].reshape(-1))
        return positions, normals, colors, indices

    @staticmethod
    def sweep_from_front(centroids):
        return numpy.abs(numpy.arctan2(centroids[:, 0], centroids[:, 2]))

    @staticmethod
    def bottom_up(centroids):
        return centroids[:, 1]

    @staticmethod
    def left_to_right(centroids):
        return centroids[:, 0]

    def wing_decal(self, side):
        center_x, center_y, width, height, baseline_degrees = self.wing_text_areas[side]
        baseline = math.radians(baseline_degrees)
        cosine, sine = math.cos(baseline), math.sin(baseline)
        decal = StatueMesh()
        texture_points = []
        for grid, normals in self.membrane_sheets:
            lifted = grid + normals * self.wing_text_lift
            decal.add_grid(lifted, normals, (1.0, 1.0, 1.0))
            right, up = lifted[..., 0] - center_x, lifted[..., 1] - center_y
            texture_points.append(numpy.stack(((right * cosine + up * sine) / width + 0.5,
                                               (up * cosine - right * sine) / height + 0.5), axis=-1).reshape(-1, 2))
        positions, normals, _, indices = decal.arrays()
        return (positions, normals, numpy.ascontiguousarray(numpy.concatenate(texture_points), dtype=numpy.float32),
                indices)

    def tail_bend_frame(self, positions):
        centerline = catmull_rom(self.tail_points, self.tail_centerline_samples)
        tangents = normalized(numpy.gradient(centerline, axis=0))
        sideways = normalized(numpy.stack((tangents[:, 2], numpy.zeros(len(tangents)), -tangents[:, 0]), axis=-1))
        nearest = numpy.argmin(numpy.linalg.norm(positions[:, None, :] - centerline[None, :, :].astype(numpy.float32),
                                                 axis=-1), axis=1)
        along = (nearest / (len(centerline) - 1)).astype(numpy.float32)
        return along, sideways[nearest].astype(numpy.float32)

    @staticmethod
    def mirrored(point, side):
        return numpy.array((side * point[0], point[1], point[2]), dtype=numpy.float64)

    def lathe(self, profile, segments, inside_height, colors_for, inset_for=None):
        radii, heights = (numpy.array(column, dtype=numpy.float64) for column in zip(*profile))
        angles = numpy.linspace(0.0, 2.0 * math.pi, segments + 1)
        radius = radii[:, None] - (0.0 if inset_for is None else inset_for(angles)[None, :])
        radius = numpy.maximum(radius, 0.0)
        grid = numpy.stack((radius * numpy.sin(angles)[None, :], numpy.repeat(heights[:, None], len(angles), axis=1),
                            radius * numpy.cos(angles)[None, :]), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, numpy.array((0.0, inside_height, 0.0)), True),
                                   numpy.array((0.0, 1.0, 0.0)))
        self.mesh.add_grid(grid, normals, colors_for(grid, angles))

    def cobble_inset(self, angles):
        per_stone = angles / (2.0 * math.pi) * self.cobble_count
        fraction = per_stone % 1.0
        gap = numpy.minimum(fraction, 1.0 - fraction) * 2.0 * math.pi / self.cobble_count * self.cobble_profile[2][0]
        groove = 1.0 - numpy.clip(gap / self.cobble_groove_width, 0.0, 1.0) ** 2
        return groove * self.cobble_groove_depth - numpy.sin(math.pi * fraction) * self.cobble_bulge

    def cobble_colors(self, grid, angles):
        tones = self.generator.uniform(0.82, 1.12, self.cobble_count)
        stone = numpy.floor(angles / (2.0 * math.pi) * self.cobble_count).astype(int) % self.cobble_count
        per_stone = angles / (2.0 * math.pi) * self.cobble_count
        fraction = per_stone % 1.0
        gap = numpy.minimum(fraction, 1.0 - fraction) * 2.0 * math.pi / self.cobble_count * self.cobble_profile[2][0]
        groove_shade = 1.0 - 0.5 * (1.0 - numpy.clip(gap / self.cobble_groove_width, 0.0, 1.0))
        tone = (tones[stone] * groove_shade)[None, :, None]
        return numpy.asarray(self.cobble_gray) * tone * mottling(grid, 0.08)[..., None]

    def drum_colors(self, grid, angles):
        return numpy.asarray(self.drum_gray) * mottling(grid * 1.7, 0.07)[..., None]

    def build_rocky_base(self):
        self.lathe(self.cobble_profile, self.cobble_count * 12, 0.04, self.cobble_colors, self.cobble_inset)

    def build_solid_base(self):
        self.lathe(self.drum_profile, self.drum_segments, 0.2, self.drum_colors)

    def build_caption(self):
        DrumInscription(self.sculptor, StrokeFont(), self.caption, self.drum_radius, self.caption_center_height,
                        self.caption_letter_height, self.caption_relief, self.gilding).carve()

    def build_figure(self):
        self.build_body()
        self.build_head()
        self.build_legs()

    def build_eyes(self):
        for side in (1.0, -1.0):
            self.sculptor.ellipsoid(self.mirrored(self.eye_position, side), (side * -0.55, -0.35, 0.75), 0.014, 0.005,
                                    0.0035, self.ember_color, mottle=0.0)

    def build_body(self):
        torso = self.sculptor.tube(self.torso_points, self.torso_profile, self.clay, rings=30, segments=28,
                                   scales=self.torso_scales)
        self.sculptor.ridge_spikes(torso, 0.15, 0.95, 7, 0.03, 0.009, -0.35, self.bone_clay)
        neck = self.sculptor.tube(self.neck_points, self.neck_profile, self.clay, rings=22, segments=24,
                                  up_hint=(0.0, 1.0, -1.0), scales=self.neck_scales)
        self.sculptor.ridge_spikes(neck, 0.1, 0.8, 4, 0.028, 0.008, -0.4, self.bone_clay)

    def build_head(self):
        sculptor = self.sculptor
        skull = sculptor.tube(self.skull_points, self.skull_profile, self.clay, rings=26, segments=24,
                              up_hint=(0.0, 1.0, 0.0), scales=self.head_scales, lining=MouthLining(math.pi))
        sculptor.spike((0.0, 0.628, 0.318), (0.0, 1.0, 0.35), 0.03, 0.007, self.bone_clay, curl=(0.0, 0.0, -0.2))
        for side in (1.0, -1.0):
            self.add_teeth(skull, 0.42, 0.95, self.upper_tooth_count, side, -1.0)
            sculptor.ellipsoid(self.mirrored(self.brow_position, side), (side * -0.5, -0.4, 0.8), 0.032, 0.017,
                               0.012, self.clay, up_hint=(0.0, 1.0, 0.0))
            sculptor.spike(self.mirrored((0.045, 0.7, 0.21), side), (side * 0.6, 0.7, -0.6), 0.035, 0.007,
                           self.bone_clay)
            for height, length in ((0.655, 0.05), (0.632, 0.042), (0.61, 0.034)):
                sculptor.spike(self.mirrored((0.03, height, 0.185), side), (side * 0.75, -0.1, -0.7), length, 0.008,
                               self.bone_clay, curl=(0.0, 0.0, -0.1))
            sculptor.tube((self.mirrored((0.035, 0.69, 0.162), side), self.mirrored((0.085, 0.745, 0.10), side),
                           self.mirrored((0.10, 0.82, 0.02), side), self.mirrored((0.085, 0.86, -0.04), side)),
                          ((0.0, 0.016, 0.016), (0.5, 0.01, 0.01), (1.0, 0.0, 0.0)), self.bone_clay, rings=18,
                          segments=12, cap_end=False)
        center = numpy.asarray(self.crown_center)
        for spread in numpy.radians(numpy.linspace(-self.crown_spread_degrees, self.crown_spread_degrees,
                                                   self.crown_spike_count)):
            base = center + (math.sin(spread) * 0.042, -0.012 * abs(math.sin(spread)), -0.01)
            length = 0.035 + 0.045 * math.cos(spread) ** 2
            sculptor.spike(base, (math.sin(spread) * 0.7, 1.0, -0.4), length, 0.0105, self.bone_clay,
                           curl=(0.0, 0.0, -0.12))

    def build_jaw(self):
        sculptor = self.sculptor
        jaw = sculptor.tube(self.jaw_points, self.jaw_profile, self.clay, rings=18, segments=20,
                            up_hint=(0.0, 1.0, 0.0), scales=self.head_scales, lining=MouthLining(0.0))
        for side in (1.0, -1.0):
            self.add_teeth(jaw, 0.35, 0.92, self.lower_tooth_count, side, 1.0)
        for offset in (-0.016, 0.0, 0.016):
            sculptor.spike((offset, 0.57, 0.225), (offset * 8.0, -1.0, -0.35), 0.035, 0.006, self.clay)

    def add_teeth(self, frame, first, last, count, side, pointing):
        centers, sides, ups, widths, heights = frame
        tangents = normalized(numpy.gradient(centers, axis=0))
        fang_at = first + (last - first) * 0.78
        for fraction in numpy.linspace(first, last, count):
            index = int(fraction * (len(centers) - 1))
            base = (centers[index] + sides[index] * widths[index] * 0.72 * side
                    - ups[index] * heights[index] * 0.55 * pointing)
            fang = math.exp(-((fraction - fang_at) / 0.08) ** 2)
            length = 0.011 + 0.022 * fang
            direction = ups[index] * pointing + tangents[index] * 0.2 + sides[index] * side * 0.15
            self.sculptor.spike(base, direction, length, 0.0034 + 0.0025 * fang, self.bone_clay,
                                curl=tuple(-tangents[index] * 0.1), rings=6, segments=8)

    def build_legs(self):
        sculptor = self.sculptor
        for side in (1.0, -1.0):
            sculptor.ellipsoid((side * 0.135, 0.43, -0.05), (side * 0.15, 0.3, 1.0), 0.12, 0.072, 0.088, self.clay,
                               up_hint=(0.0, 1.0, 0.0), rings=20, segments=24, mottle=0.09,
                               scales=self.thigh_scales)
            sculptor.tube((self.mirrored((0.15, 0.48, 0.06), side), self.mirrored((0.165, 0.42, 0.02), side),
                           self.mirrored((0.17, 0.36, -0.03), side)),
                          ((0.0, 0.042, 0.042), (1.0, 0.026, 0.026)), self.clay, rings=14, scales=self.limb_scales)
            sculptor.tube((self.mirrored((0.17, 0.36, -0.03), side), self.mirrored((0.17, 0.335, 0.03), side),
                           self.mirrored((0.17, 0.33, 0.07), side)),
                          ((0.0, 0.026, 0.024), (1.0, 0.022, 0.016)), self.clay, rings=12, up_hint=(0.0, 1.0, 0.0),
                          scales=self.paw_scales)
            self.add_digits(self.mirrored((0.17, 0.33, 0.07), side), 0.045, 0.012, side)
            sculptor.tube((self.mirrored((0.075, 0.57, 0.07), side), self.mirrored((0.11, 0.50, 0.11), side),
                           self.mirrored((0.115, 0.45, 0.12), side)),
                          ((0.0, 0.04, 0.04), (1.0, 0.028, 0.028)), self.clay, rings=14, scales=self.limb_scales)
            sculptor.tube((self.mirrored((0.115, 0.45, 0.12), side), self.mirrored((0.105, 0.39, 0.14), side),
                           self.mirrored((0.09, 0.345, 0.16), side)),
                          ((0.0, 0.028, 0.028), (1.0, 0.02, 0.019)), self.clay, rings=14, scales=self.paw_scales)
            self.add_digits(self.mirrored((0.09, 0.338, 0.16), side), 0.035, 0.010, side)
            for joint, along, half_length, radius, scales in (
                    ((0.155, 0.475, 0.058), (0.0, -0.4, 1.0), 0.05, 0.046, self.limb_scales),
                    ((0.17, 0.36, -0.03), (0.0, -0.6, 1.0), 0.034, 0.03, self.paw_scales),
                    ((0.115, 0.452, 0.118), (0.0, 1.0, 0.4), 0.04, 0.034, self.limb_scales),
                    ((0.092, 0.346, 0.158), (0.0, -0.5, 1.0), 0.03, 0.024, self.paw_scales)):
                sculptor.ellipsoid(self.mirrored(joint, side), along, half_length, radius, radius * 0.95, self.clay,
                                   scales=scales)

    def add_digits(self, root, length, radius, side):
        for spread in (-1.0, 0.0, 1.0):
            tip = root + (side * spread * 0.022, -0.006, length)
            middle = (root + tip) / 2.0 + (0.0, 0.006, 0.0)
            self.sculptor.tube((root, middle, tip), ((0.0, radius, radius * 0.9), (1.0, radius * 0.7, radius * 0.6)),
                               self.clay, rings=8, segments=12, up_hint=(0.0, 1.0, 0.0), scales=self.paw_scales)
            self.sculptor.spike(tip, (side * spread * 0.4, -0.7, 1.0), 0.024, radius * 0.65, self.bone_clay,
                                curl=(0.0, -0.15, 0.0))

    def build_tail(self):
        tail = self.sculptor.tube(self.tail_points, self.tail_profile, self.clay, rings=64, segments=20,
                                  up_hint=(0.0, 1.0, 0.0), cap_start=False, scales=self.tail_scales)
        self.sculptor.ridge_spikes(tail, 0.05, 0.85, 11, 0.026, 0.008, 0.45, self.bone_clay)
        self.sculptor.ellipsoid((-0.085, 0.342, 0.255), (-1.0, 0.0, -0.25), 0.032, 0.022, 0.006, self.clay,
                                up_hint=(0.0, 1.0, 0.0))

    def build_wing(self, side):
        sculptor = self.sculptor
        shoulder, elbow, wrist, flank = (self.mirrored(point, side) for point in
                                         (self.wing_shoulder, self.wing_elbow, self.wing_wrist, self.wing_flank))
        fingers = [quadratic_curve(wrist, self.mirrored(control, side), self.mirrored(tip, side), self.membrane_rows)
                   for control, tip in self.wing_fingers]
        arm = catmull_rom((wrist, elbow, shoulder, flank), self.membrane_rows)
        edges = fingers + [arm]
        for leading, trailing in zip(edges[:-1], edges[1:]):
            self.add_membrane(wrist, leading, trailing)
        sculptor.tube((shoulder, (shoulder + elbow) / 2.0 + (side * 0.01, 0.0, -0.02), elbow),
                      ((0.0, 0.034, 0.034), (1.0, 0.024, 0.024)), self.clay, rings=14, segments=16,
                      scales=self.limb_scales)
        sculptor.tube((elbow, (elbow + wrist) / 2.0 + (side * 0.012, 0.0, 0.0), wrist),
                      ((0.0, 0.024, 0.024), (1.0, 0.018, 0.018)), self.clay, rings=14, segments=16,
                      scales=self.paw_scales)
        sculptor.ellipsoid(elbow, (0.0, 1.0, 0.0), 0.03, 0.026, 0.026, self.clay, scales=self.paw_scales)
        sculptor.ellipsoid(wrist, (side * 0.3, 1.0, 0.0), 0.026, 0.022, 0.022, self.clay, scales=self.paw_scales)
        for finger in fingers:
            sculptor.sweep(finger, numpy.linspace(0.013, 0.003, len(finger)), numpy.linspace(0.013, 0.003, len(finger)),
                           self.bone_clay, segments=10, cap_end=True, mottle=0.03)
        sculptor.spike(wrist, (side * -0.1, 1.0, 0.05), 0.10, 0.013, self.bone_clay, curl=(side * 0.1, 0.0, -0.1))
        for lean, length in ((-0.45, 0.045), (-0.15, 0.06), (0.25, 0.05)):
            sculptor.spike(wrist + (0.0, 0.01, 0.01), (side * lean, 1.0, 0.3), length, 0.007, self.bone_clay,
                           curl=(0.0, 0.0, 0.15))
        spur_index = int(self.membrane_rows * 0.35)
        sculptor.spike(fingers[0][spur_index], (side * 0.25, 1.0, 0.0), 0.04, 0.008, self.bone_clay)

    @staticmethod
    def edge_at(edge, along):
        samples = numpy.linspace(0.0, 1.0, len(edge))
        flat = along.ravel()
        points = numpy.stack([numpy.interp(flat, samples, edge[:, axis]) for axis in range(3)], axis=-1)
        return points.reshape(along.shape + (3,))

    def membrane_surface(self, wrist, leading, trailing, along, across):
        points = (self.edge_at(leading, along) * (1.0 - across)[..., None]
                  + self.edge_at(trailing, along) * across[..., None])
        belly = numpy.sin(math.pi * across)
        scallop = 1.0 - self.membrane_sag * belly * along ** 2
        points = wrist + (points - wrist) * scallop[..., None]
        span = numpy.linalg.norm(leading[-1] - trailing[-1])
        billow = self.membrane_billow * span * belly * numpy.sin(math.pi * along * 0.85)
        return points + numpy.array((0.0, 0.0, -1.0)) * billow[..., None]

    def add_membrane(self, wrist, leading, trailing):
        along, across = numpy.meshgrid(numpy.linspace(0.0, 1.0, len(leading)),
                                       numpy.linspace(0.0, 1.0, self.membrane_columns), indexing="ij")
        grid = self.membrane_surface(wrist, leading, trailing, along, across)
        forward = numpy.array((0.0, 0.0, 1.0))
        normals = unit_or_fallback(surface_normals(grid, grid - forward, False), forward)
        colors = numpy.asarray(self.membrane_clay) * (0.9 + 0.1 * along)[..., None] * mottling(grid, 0.04)[..., None]
        for sign in (1.0, -1.0):
            self.mesh.add_grid(grid + normals * self.membrane_half_thickness * sign, normals * sign, colors)
        self.membrane_sheets.append((grid + normals * self.membrane_half_thickness, normals))
        for path, (thick, thin) in self.vein_paths():
            points = self.membrane_surface(wrist, leading, trailing, path[:, 0], path[:, 1])
            centers = catmull_rom(points, len(points) * 3)
            radii = numpy.linspace(thick, thin, len(centers))
            self.sculptor.sweep(centers, radii, radii, self.vein_color, up_hint=(0.0, 0.0, 1.0), segments=6,
                                cap_start=True, cap_end=True, mottle=0.0)

    def vein_paths(self):
        generator = self.generator
        paths = []
        for rib in range(self.vein_ribs_per_panel):
            start = 0.22 + 0.72 * (rib + generator.uniform(0.2, 0.8)) / self.vein_ribs_per_panel
            drift = generator.uniform(-0.08, 0.12)
            phase = generator.uniform(0.0, 2.0 * math.pi)
            across = numpy.linspace(0.02, 0.98, 12)
            along = start + drift * across + 0.025 * numpy.sin(across * 7.0 + phase)
            rib_path = numpy.stack((numpy.clip(along, 0.08, 0.985), across), axis=-1)
            paths.append((rib_path, self.vein_rib_radius))
            for _ in range(self.vein_branches_per_rib):
                origin = rib_path[generator.integers(2, len(rib_path) - 2)]
                heading = generator.choice((-1.0, 1.0)) * generator.uniform(0.5, 1.2)
                branch = self.wandering_path(origin, heading)
                paths.append((branch, self.vein_branch_radius))
                fork_heading = heading + generator.choice((-1.0, 1.0)) * generator.uniform(0.5, 0.9)
                fork = self.wandering_path(branch[len(branch) // 2], fork_heading, self.vein_branch_steps // 2 + 1)
                paths.append((fork, (self.vein_branch_radius[1] * 1.3, self.vein_branch_radius[1] * 0.6)))
        return paths

    def wandering_path(self, origin, heading, steps=None):
        steps = steps or self.vein_branch_steps
        points = [numpy.asarray(origin, dtype=numpy.float64)]
        for _ in range(steps - 1):
            heading += self.generator.uniform(-self.vein_branch_turn, self.vein_branch_turn)
            step = numpy.array((math.cos(heading) * 0.6, math.sin(heading))) * self.vein_branch_step
            following = points[-1] + step
            following = numpy.array((min(max(following[0], 0.08), 0.985), min(max(following[1], 0.02), 0.98)))
            points.append(following)
        return numpy.array(points)


class Dragon:

    def __init__(self, height, model=None):
        self.model = model or DragonModel()
        self.height = height
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.sheen_light = (0.30, 0.28, 0.26, 1.0)
        self.sheen_material = (0.16, 0.14, 0.12, 1.0)
        self.sheen_shininess = 14.0
        self.eye_glow = 0.35
        self.flapping = True
        self.flap_degrees = 5.0
        self.flaps_per_second = 0.35
        self.flap_phase = 0.0
        self.wing_degrees = 0.0
        self.tail_strength = 1.0
        self.tail_swing = 0.014
        self.tail_waves_along = 1.6
        self.tail_wiggles_per_second = 0.5
        self.tail_phase = 0.0
        self.jaw_closing_degrees = 0.0
        self.tail_positions = self.model.tail[0].copy()

    def update(self, seconds):
        if self.flapping:
            self.flap_phase = (self.flap_phase + seconds * self.flaps_per_second * 2.0 * math.pi) % (2.0 * math.pi)
            self.wing_degrees = self.flap_degrees * math.sin(self.flap_phase)
        self.tail_phase = (self.tail_phase + seconds * self.tail_wiggles_per_second * 2.0 * math.pi) % (2.0 * math.pi)
        self.wiggle_tail()

    def wiggle_tail(self):
        along = self.model.tail_along
        sway = (self.tail_strength * self.tail_swing * along ** 1.5
                * numpy.sin(self.tail_phase - 2.0 * math.pi * self.tail_waves_along * along))
        self.tail_positions[:] = self.model.tail[0] + self.model.tail_sideways * sway[:, None]

    @staticmethod
    def draw(positions, normals, colors, indices, count=None):
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices) if count is None else count, GL_UNSIGNED_INT, indices)

    def draw_eyes(self, flash=None):
        if flash is None:
            glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (*(numpy.asarray(self.model.ember_color) * self.eye_glow), 1.0))
            self.draw(*self.model.eyes)
        else:
            glDisableClientState(GL_COLOR_ARRAY)
            glColor3f(*flash)
            glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (*flash, 1.0))
            positions, normals, _, indices = self.model.eyes
            glVertexPointer(3, GL_FLOAT, 0, positions)
            glNormalPointer(GL_FLOAT, 0, normals)
            glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
            glEnableClientState(GL_COLOR_ARRAY)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))

    def draw_wing(self, side, lettering_texture=None):
        shoulder = self.model.mirrored(self.model.wing_shoulder, side)
        glPushMatrix()
        glTranslatef(*shoulder)
        glRotatef(side * self.wing_degrees, 0.0, 0.0, 1.0)
        glTranslatef(*(-shoulder))
        self.draw(*self.model.wings[side])
        if lettering_texture is not None:
            self.draw_lettering(side, lettering_texture)
        glPopMatrix()

    def draw_lettering(self, side, texture):
        positions, normals, texture_points, indices = self.model.wing_decals[side]
        glDisableClientState(GL_COLOR_ARRAY)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glTexCoordPointer(2, GL_FLOAT, 0, texture_points)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEnableClientState(GL_COLOR_ARRAY)

    def draw_jaw(self):
        hinge = self.model.jaw_hinge
        glPushMatrix()
        glTranslatef(*hinge)
        glRotatef(-self.jaw_closing_degrees, 1.0, 0.0, 0.0)
        glTranslatef(*(-hinge))
        self.draw(*self.model.jaw)
        glPopMatrix()

    def draw_figure(self, lettering_textures=None, eye_flash=None):
        self.draw(*self.model.body)
        self.draw_jaw()
        self.draw_eyes(eye_flash)
        _, tail_normals, tail_colors, tail_indices = self.model.tail
        self.draw(self.tail_positions, tail_normals, tail_colors, tail_indices)
        for side in self.model.wings:
            self.draw_wing(side, (lettering_textures or {}).get(side))

    def begin(self):
        scale = self.height / self.model.total_height
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(math.degrees(self.yaw), 0.0, 1.0, 0.0)
        glScalef(scale, scale, scale)
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_SPECULAR, self.sheen_light)
        glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.sheen_material)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.sheen_shininess)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

    @staticmethod
    def end():
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
        glPopMatrix()

    def render(self):
        self.begin()
        self.draw(*self.model.rocky_base)
        self.draw(*self.model.solid_base)
        self.draw(*self.model.caption_letters)
        self.draw_figure()
        self.end()


class WingLettering:

    def __init__(self, font_path, lines):
        self.texture_size = (1024, 740)
        self.font_size = 230
        self.widest_fraction = 0.92
        self.line_heights = (0.3, 0.74)
        self.ink_color = (240, 190, 96)
        self.shadow_color = (46, 16, 8)
        self.shadow_offset = 6
        self.font = pygame.font.Font(font_path, self.font_size)
        self.lines = lines
        self.revealed = [0.0] * len(lines)
        self.texture = None
        self.uploaded_reveal = None

    def reveal(self, line, fraction):
        self.revealed[line] = fraction

    def visible(self):
        return any(fraction > 0.0 for fraction in self.revealed)

    def fitted(self, text, color):
        rendered = self.font.render(text, True, color)
        widest = self.texture_size[0] * self.widest_fraction
        if rendered.get_width() > widest:
            factor = widest / rendered.get_width()
            rendered = pygame.transform.smoothscale(rendered, (round(rendered.get_width() * factor),
                                                               round(rendered.get_height() * factor)))
        return rendered

    def surface(self):
        width, height = self.texture_size
        surface = pygame.Surface(self.texture_size, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        for text, fraction, line_height in zip(self.lines, self.revealed, self.line_heights):
            if fraction <= 0.0:
                continue
            ink = self.fitted(text, self.ink_color)
            shadow = self.fitted(text, self.shadow_color)
            left = (width - ink.get_width()) // 2
            top = round(line_height * height) - ink.get_height() // 2
            shown = pygame.Rect(0, 0, round(ink.get_width() * fraction), ink.get_height())
            surface.blit(shadow, (left + self.shadow_offset, top + self.shadow_offset), shown)
            surface.blit(ink, (left, top), shown)
        pygame.draw.rect(surface, (0, 0, 0, 0), surface.get_rect(), 2)
        return surface

    def bound_texture(self):
        reveal = tuple(self.revealed)
        if self.texture is None:
            self.texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        if reveal != self.uploaded_reveal:
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *self.texture_size, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                         pygame.image.tobytes(self.surface(), "RGBA", True))
            self.uploaded_reveal = reveal
        glBindTexture(GL_TEXTURE_2D, 0)
        return self.texture


class StatuePicture:

    def __init__(self, path):
        self.surface = pygame.image.load(path)
        self.size = self.surface.get_size()
        self.aspect = self.size[0] / self.size[1]
        self.right_pixels = 3
        self.down_pixels = 2
        self.texture = None

    def bound_texture(self):
        if self.texture is None:
            self.texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *self.size, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                         pygame.image.tobytes(self.surface, "RGBA", True))
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def render(self, height_fraction):
        _, _, viewport_width, viewport_height = glGetIntegerv(GL_VIEWPORT)
        half_height = height_fraction
        half_width = half_height * self.aspect * viewport_height / viewport_width
        shift_x = 2.0 * self.right_pixels / viewport_width
        shift_y = -2.0 * self.down_pixels / viewport_height
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        self.bound_texture()
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        for corner_x, corner_y in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
            glTexCoord2f(corner_x, corner_y)
            glVertex2f((2.0 * corner_x - 1.0) * half_width + shift_x, (2.0 * corner_y - 1.0) * half_height + shift_y)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()


class DragonFire:

    def __init__(self, model, seed=3):
        self.generator = numpy.random.default_rng(seed)
        self.particle_count = 1400
        self.source_count = 6000
        self.base_share = 0.35
        self.behind_depth = -0.30
        self.behind_base_depth = -0.46
        self.depth_jitter = 0.04
        self.figure_center = numpy.array((0.0, 0.62))
        self.outward_push = (0.0, 0.07)
        self.rise_speed = (0.16, 0.38)
        self.flicker = 0.35
        self.drift_damping = 2.0
        self.lifetime = (0.45, 1.05)
        self.size = (0.03, 0.08)
        self.flame_stretch = 1.6
        self.color_stops = (0.0, 0.2, 0.55, 1.0)
        self.color_reds = (1.0, 1.0, 0.85, 0.0)
        self.color_greens = (0.95, 0.6, 0.18, 0.0)
        self.color_blues = (0.7, 0.12, 0.03, 0.0)
        self.sprite_size = 64
        figure_points = numpy.concatenate([model.body[0]] + [wing[0] for wing in model.wings.values()])
        figure_points = figure_points[figure_points[:, 1] > model.plinth_top + 0.03]
        base_points = numpy.concatenate((model.rocky_base[0], model.solid_base[0]))
        base_count = round(self.source_count * self.base_share)
        figure_sources = figure_points[self.generator.integers(0, len(figure_points), self.source_count - base_count),
                                       :2].astype(numpy.float64)
        base_sources = base_points[self.generator.integers(0, len(base_points), base_count), :2].astype(numpy.float64)
        base_pushes = normalized(numpy.column_stack((numpy.sign(base_sources[:, 0]), numpy.full(base_count, 0.3))))
        self.sources = numpy.vstack((figure_sources, base_sources))
        self.source_depths = numpy.concatenate((numpy.full(len(figure_sources), self.behind_depth),
                                                numpy.full(base_count, self.behind_base_depth)))
        self.source_pushes = numpy.vstack((normalized(figure_sources - self.figure_center), base_pushes))
        self.positions = numpy.zeros((self.particle_count, 3))
        self.velocities = numpy.zeros((self.particle_count, 3))
        self.ages = numpy.zeros(self.particle_count)
        self.lifetimes = numpy.ones(self.particle_count)
        self.sizes = numpy.zeros(self.particle_count)
        self.respawn(numpy.ones(self.particle_count, dtype=bool))
        self.ages = self.generator.uniform(0.0, 1.0, self.particle_count) * self.lifetimes
        self.texture = None

    def respawn(self, mask):
        count = int(mask.sum())
        if count == 0:
            return
        chosen = self.generator.integers(0, len(self.sources), count)
        origins = (self.sources[chosen]
                   + self.source_pushes[chosen] * self.generator.uniform(*self.outward_push, count)[:, None])
        depths = self.source_depths[chosen] + self.generator.uniform(-self.depth_jitter, self.depth_jitter, count)
        self.positions[mask] = numpy.column_stack((origins, depths))
        self.velocities[mask] = numpy.column_stack((self.generator.normal(0.0, 0.03, count),
                                                    self.generator.uniform(*self.rise_speed, count),
                                                    numpy.zeros(count)))
        self.ages[mask] = 0.0
        self.lifetimes[mask] = self.generator.uniform(*self.lifetime, count)
        self.sizes[mask] = self.generator.uniform(*self.size, count)

    def update(self, seconds):
        self.ages += seconds
        self.velocities[:, 0] += (self.generator.normal(0.0, self.flicker, self.particle_count) * seconds
                                  - self.velocities[:, 0] * self.drift_damping * seconds)
        self.positions += self.velocities * seconds
        self.respawn(self.ages >= self.lifetimes)

    def sprite(self):
        span = numpy.linspace(-1.0, 1.0, self.sprite_size)
        distance = numpy.hypot(*numpy.meshgrid(span, span))
        alpha = numpy.clip(1.0 - distance, 0.0, 1.0) ** 1.8
        pixels = numpy.empty((self.sprite_size, self.sprite_size, 4), dtype=numpy.uint8)
        pixels[..., :3] = 255
        pixels[..., 3] = (alpha * 255.0).astype(numpy.uint8)
        return pixels

    def upload(self):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.sprite_size, self.sprite_size, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     numpy.ascontiguousarray(self.sprite()))
        glBindTexture(GL_TEXTURE_2D, 0)

    def quads(self, strength):
        view = numpy.array(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=numpy.float64).reshape(4, 4)
        right = normalized(view[:3, 0])
        up = normalized(view[:3, 1])
        age = numpy.clip(self.ages / self.lifetimes, 0.0, 1.0)
        size = self.sizes * (0.6 + 0.8 * numpy.sin(math.pi * numpy.sqrt(age)))
        across = right[None, :] * size[:, None]
        along = up[None, :] * (size * self.flame_stretch)[:, None]
        corners = numpy.stack((self.positions - across - along, self.positions + across - along,
                               self.positions + across + along, self.positions - across + along), axis=1)
        colors = numpy.stack((numpy.interp(age, self.color_stops, self.color_reds),
                              numpy.interp(age, self.color_stops, self.color_greens),
                              numpy.interp(age, self.color_stops, self.color_blues),
                              numpy.full(self.particle_count, strength * 0.8)), axis=-1)
        texture_points = numpy.tile(numpy.array(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))),
                                    (self.particle_count, 1))
        return (numpy.ascontiguousarray(corners.reshape(-1, 3), dtype=numpy.float32),
                numpy.ascontiguousarray(numpy.repeat(colors, 4, axis=0), dtype=numpy.float32),
                numpy.ascontiguousarray(texture_points, dtype=numpy.float32))

    def render(self, strength):
        if strength <= 0.0:
            return
        if self.texture is None:
            self.upload()
        corners, colors, texture_points = self.quads(strength)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glDisableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, corners)
        glColorPointer(4, GL_FLOAT, 0, colors)
        glTexCoordPointer(2, GL_FLOAT, 0, texture_points)
        glDrawArrays(GL_QUADS, 0, len(corners))
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)


class KnAdragonAnim:

    def __init__(self, height=1.0, model=None):
        self.dragon = Dragon(height, model)
        self.model = self.dragon.model
        self.dragon.flapping = False
        self.dragon.tail_strength = 0.0
        self.font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources",
                                      "Gadevoxpersonal.otf")
        self.phases = (("rocky base", 2.5), ("solid base", 2.5), ("sway", 1.5), ("descent", 3.0),
                       ("first eye flash", 1.4), ("tail wiggle", 1.5), ("wing flaps", 3.2), ("KOMODA", 1.8),
                       ("and", 0.9), ("AMIGA", 1.6), ("plus", 0.9), ("second eye flash", 1.4), ("caption", 2.5),
                       ("fire", 2.5), ("wing waves", 14.0))
        self.timeline_speed = 2.0
        self.phase_spans = {}
        start = 0.0
        for name, duration in self.phases:
            self.phase_spans[name] = (start, duration)
            start += duration
        self.jaw_snap_count = 4
        self.jaw_snap_degrees = 16.0
        self.phase_spans["jaw snaps"] = (self.phase_spans["fire"][0], 6.0)
        self.frozen_jaw_snap_count = 2
        self.frozen_jaw_snap_seconds = 1.5
        self.closing_eye_flash_seconds = 0.7
        self.sway_degrees = 22.0
        self.sway_period_seconds = 7.0
        self.descent_height = 1.5
        self.wing_flap_degrees = 9.0
        self.wing_flap_count = 2
        self.wing_wave_degrees = 12.0
        self.wing_wave_count = 5
        self.eye_flash_colors = ((1.0, 0.1, 0.04), (1.0, 0.85, 0.1), (1.0, 1.0, 1.0), (1.0, 0.85, 0.1),
                                 (1.0, 0.1, 0.04))
        self.lettering = {-1.0: WingLettering(self.font_path, ("KOMODA", "and")),
                          1.0: WingLettering(self.font_path, ("AMIGA", "plus"))}
        self.lettering_phases = ((-1.0, 0, "KOMODA"), (-1.0, 1, "and"), (1.0, 0, "AMIGA"), (1.0, 1, "plus"))
        self.fire = DragonFire(self.model)
        self.final_hold_seconds = 15.0
        self.hold_zoom_seconds = 1.2
        self.hold_zoom_margin = 0.97
        self.base_rim_radius = 0.405
        self.hold_zoom = 0.0
        self.picture = StatuePicture(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources",
                                                  "dragon.png"))
        self.picture_seconds = 3.0
        self.showing_picture = False
        self.seconds = 0.0
        self.sway_angle = 0.0
        self.sway_frozen = False
        self.held_seconds = 0.0
        self.descent_offset = self.descent_height
        self.eye_flash = None

    def restart(self):
        self.seconds = 0.0
        self.sway_angle = 0.0
        self.sway_frozen = False
        self.held_seconds = 0.0
        self.update(0.0)

    def swaying_angle(self):
        sway_start = self.phase_spans["sway"][0]
        ramp = self.progress("sway")
        return (self.sway_degrees * ramp * ramp * (3.0 - 2.0 * ramp)
                * math.sin(2.0 * math.pi * max(0.0, self.seconds - sway_start) / self.sway_period_seconds))

    def update_sway(self, seconds):
        if self.sway_frozen:
            self.held_seconds += seconds
            return
        angle = self.swaying_angle()
        waves_over = self.progress("wing waves") >= 1.0
        if waves_over and (angle == 0.0 or (angle > 0.0) != (self.sway_angle > 0.0)):
            self.sway_frozen = True
            angle = 0.0
        self.sway_angle = angle

    def progress(self, phase):
        start, duration = self.phase_spans[phase]
        return min(max((self.seconds - start) / duration, 0.0), 1.0)

    def started(self, phase):
        return self.seconds >= self.phase_spans[phase][0]

    def flash_color(self, progress):
        if not 0.0 < progress < 1.0:
            return None
        position = progress * (len(self.eye_flash_colors) - 1)
        index = min(int(position), len(self.eye_flash_colors) - 2)
        blend = position - index
        first, second = numpy.asarray(self.eye_flash_colors[index]), numpy.asarray(self.eye_flash_colors[index + 1])
        return tuple(first + (second - first) * blend)

    def update(self, seconds):
        self.seconds += seconds * self.timeline_speed
        self.update_sway(seconds)
        if self.held_seconds >= self.final_hold_seconds + self.picture_seconds:
            self.restart()
            return
        self.showing_picture = self.held_seconds >= self.final_hold_seconds
        self.descent_offset = self.descent_height * (1.0 - self.progress("descent")) ** 3
        self.dragon.tail_strength = self.progress("tail wiggle")
        flaps = self.progress("wing flaps")
        waves = self.progress("wing waves")
        self.dragon.wing_degrees = (self.wing_flap_degrees * math.sin(2.0 * math.pi * self.wing_flap_count * flaps)
                                    + self.wing_wave_degrees * math.sin(2.0 * math.pi * self.wing_wave_count * waves))
        snap_turns = self.jaw_snap_count * self.progress("jaw snaps")
        frozen_snaps = 0.0
        closing_flash = 0.0
        self.hold_zoom = 0.0
        if self.sway_frozen:
            ease = min(self.held_seconds / self.hold_zoom_seconds, 1.0)
            self.hold_zoom = ease * ease * (3.0 - 2.0 * ease)
            frozen_snaps = min(self.held_seconds / self.frozen_jaw_snap_seconds, 1.0)
            closing_flash = min(max((self.held_seconds - self.frozen_jaw_snap_seconds)
                                    / self.closing_eye_flash_seconds, 0.0), 1.0)
            snap_turns = self.frozen_jaw_snap_count * frozen_snaps
        self.dragon.jaw_closing_degrees = self.jaw_snap_degrees * 0.5 * (1.0 - math.cos(2.0 * math.pi * snap_turns))
        self.dragon.update(seconds)
        self.eye_flash = (self.flash_color(self.progress("first eye flash"))
                          or self.flash_color(self.progress("second eye flash"))
                          or self.flash_color(frozen_snaps)
                          or self.flash_color(closing_flash))
        for side, line, phase in self.lettering_phases:
            self.lettering[side].reveal(line, self.progress(phase))
        if self.started("fire"):
            self.fire.update(seconds)

    @staticmethod
    def revealed_count(arrays, fraction):
        return round(fraction * (len(arrays[3]) // 3)) * 3

    def statue_outline_points(self):
        dragon = self.dragon
        scale = dragon.height / self.model.total_height
        rim = self.base_rim_radius * scale
        x, y, z = dragon.position
        return numpy.array(((x, y, z + rim, 1.0), (x, y, z - rim, 1.0), (x + rim, y, z, 1.0), (x - rim, y, z, 1.0),
                            (x, y + dragon.height, z + rim, 1.0), (x, y + dragon.height, z - rim, 1.0)))

    def fitting_zoom(self, projection):
        clip = self.statue_outline_points() @ glGetDoublev(GL_MODELVIEW_MATRIX) @ projection
        screen = clip[:, :2] / clip[:, 3:4]
        lowest, highest = screen[:, 1].min(), screen[:, 1].max()
        center_x = 0.5 * (screen[:, 0].min() + screen[:, 0].max())
        full_zoom = 2.0 * self.hold_zoom_margin / (highest - lowest)
        zoom = 1.0 + (full_zoom - 1.0) * self.hold_zoom
        center = numpy.array((center_x, 0.5 * (lowest + highest))) * self.hold_zoom
        lens = numpy.identity(4)
        lens[0, 0] = lens[1, 1] = zoom
        lens[3, :2] = -zoom * center
        return lens

    def render(self):
        if self.hold_zoom <= 0.0:
            self.render_scene()
            return
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        lens = self.fitting_zoom(projection)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadMatrixd(projection @ lens)
        glMatrixMode(GL_MODELVIEW)
        self.render_scene()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        if self.showing_picture:
            self.picture.render(self.hold_zoom_margin)

    def render_scene(self):
        dragon = self.dragon
        if self.showing_picture:
            self.render_fire()
            return
        dragon.yaw = math.radians(self.sway_angle)
        dragon.begin()
        for phase, arrays in (("rocky base", self.model.rocky_base), ("solid base", self.model.solid_base),
                              ("caption", self.model.caption_letters)):
            if self.started(phase):
                dragon.draw(*arrays, count=self.revealed_count(arrays, self.progress(phase)))
        if self.started("descent"):
            glPushMatrix()
            glTranslatef(0.0, self.descent_offset, 0.0)
            textures = {side: lettering.bound_texture() for side, lettering in self.lettering.items()
                        if lettering.visible()}
            dragon.draw_figure(textures, self.eye_flash)
            glPopMatrix()
        dragon.end()
        self.render_fire()

    def render_fire(self):
        if self.started("fire"):
            dragon = self.dragon
            dragon.yaw = 0.0
            dragon.begin()
            self.fire.render(self.progress("fire"))
            dragon.end()
