import math
import random

import numpy
from OpenGL.GL import (
    GL_ALWAYS,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CURRENT_BIT,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_FLOAT,
    GL_KEEP,
    GL_LIGHTING,
    GL_LINE_BIT,
    GL_LINE_STRIP,
    GL_NOTEQUAL,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_REPLACE,
    GL_SRC_ALPHA,
    GL_STENCIL_BUFFER_BIT,
    GL_STENCIL_TEST,
    GL_TEXTURE_2D,
    GL_TRIANGLE_FAN,
    GL_TRIANGLE_STRIP,
    GL_TRUE,
    GL_VERTEX_ARRAY,
    glBlendFunc,
    glClear,
    glColor4f,
    glColorMask,
    glDisable,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glLineWidth,
    glPopAttrib,
    glPushAttrib,
    glStencilFunc,
    glStencilOp,
    glVertexPointer,
)

from lib.specialFX.travelling_surface import TravellingSurface


class Spiral:

    def __init__(self, center, turn_spacing, turns):
        self.center = numpy.array(tuple(center), dtype=numpy.float32)
        self.turn_spacing = turn_spacing
        self.turns = turns
        self.inner_radius = 0.5 * turn_spacing
        self.samples_per_turn = 600
        self.sine_amplitude = 0.3 * turn_spacing
        self.sine_wavelength = 1.6 * turn_spacing
        self.circles_per_gap_choices = (3, 4)
        self.circle_radius_share = 0.4
        self.circle_neighbour_clearance = 0.45
        self.circle_segments = 24
        self.band_circle_fit_share = 0.8
        self.band_circle_min_radius = 0.05 * turn_spacing
        self.band_circle_gap = 0.06 * turn_spacing
        self.band_circle_search_length = 1.5 * turn_spacing
        self.color = (1.0, 1.0, 1.0, 1.0)
        self.line_width = 2.0
        self.step_durations = (4.0, 4.0, 4.0, 4.0, 4.0, 4.0)
        self.outward_acceleration = 2.0
        self.next_step_drawn_share = 0.5
        self.completed_steps = 0
        self.randomness = random.Random(7)
        self.steps = (self.draw_spiral, self.draw_sine_curve, self.draw_gap_circles, self.draw_gap_fill,
                      self.draw_band_circles, self.draw_band_fill)
        self.shown_steps = len(self.steps)
        self.time = 0.0

        self.spiral_angles, self.spiral_points, self.spiral_normals, self.arc_lengths = self._trace_spiral()
        self.spiral_world_points = self._to_world(self.spiral_points)
        self.sine_points = self._trace_sine_curve()
        self.gap_circles, self.gap_circle_disks = self._place_gap_circles()
        self.gap_fill_strip = self._interleave(self.spiral_world_points, self.sine_points)
        band_inner_edge, band_outer_edge = self._trace_turn_band()
        self.band_circles, self.band_circle_disks = self._place_band_circles(band_inner_edge, band_outer_edge)
        self.band_fill_strip = self._interleave(self._to_world(band_inner_edge), self._to_world(band_outer_edge))

    def update(self, delta_seconds):
        self.time += delta_seconds

    def restart(self):
        self.time = 0.0
        self.completed_steps = 0

    def show_next_step(self):
        self.show_steps(self.shown_steps % len(self.steps) + 1)

    def show_steps(self, step_count):
        self.shown_steps = max(0, min(step_count, len(self.steps)))
        self.completed_steps = max(0, self.shown_steps - 1)
        self.time = self._step_start(self.completed_steps)

    def is_finished(self):
        return self.time >= self._steps_end(self.shown_steps)

    def total_seconds(self):
        return self._steps_end(len(self.steps))

    def _steps_end(self, step_count):
        if not step_count:
            return 0.0
        last_step_index = step_count - 1
        return self._step_start(last_step_index) + self.step_durations[last_step_index]

    def draw(self):
        for step_index, step in enumerate(self.steps[:self.shown_steps]):
            step(self._step_progress(step_index))

    def draw_spiral(self, progress=1.0):
        self._draw_partial_line(self.spiral_world_points, progress)

    def draw_sine_curve(self, progress=1.0):
        self._draw_partial_line(self.sine_points, progress)

    def draw_gap_circles(self, progress=1.0):
        self._draw_circles_one_by_one(self.gap_circles, progress)

    def draw_gap_fill(self, progress=1.0):
        self._draw_filled_strip(self.gap_fill_strip, self.gap_circle_disks, progress)

    def draw_band_circles(self, progress=1.0):
        self._draw_circles_one_by_one(self.band_circles, progress)

    def draw_band_fill(self, progress=1.0):
        self._draw_filled_strip(self.band_fill_strip, self.band_circle_disks, progress)

    def _draw_circles_one_by_one(self, circles, progress):
        drawn_circles = progress * len(circles)
        for circle_index, circle_points in enumerate(circles):
            circle_progress = min(1.0, drawn_circles - circle_index)
            if circle_progress <= 0.0:
                break
            self._draw_partial_line(circle_points, circle_progress)

    def _draw_filled_strip(self, strip, hole_disks, progress):
        vertex_count = 2 * int(round(progress * len(strip) / 2))
        if vertex_count < 4:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_STENCIL_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_STENCIL_TEST)
        glClear(GL_STENCIL_BUFFER_BIT)
        glEnableClientState(GL_VERTEX_ARRAY)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        for disk_points in hole_disks:
            glVertexPointer(3, GL_FLOAT, 0, disk_points)
            glDrawArrays(GL_TRIANGLE_FAN, 0, len(disk_points))
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glStencilFunc(GL_NOTEQUAL, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*self.color)
        glVertexPointer(3, GL_FLOAT, 0, strip)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, vertex_count)
        glDisableClientState(GL_VERTEX_ARRAY)
        glClear(GL_STENCIL_BUFFER_BIT)
        glPopAttrib()

    def _step_start(self, step_index):
        time_share_at_handover = self.next_step_drawn_share ** (1.0 / self.outward_acceleration)
        return time_share_at_handover * sum(self.step_durations[:max(0, step_index)])

    def _step_progress(self, step_index):
        if step_index < self.completed_steps:
            return 1.0
        elapsed = self.time - self._step_start(step_index)
        linear_progress = max(0.0, min(1.0, elapsed / self.step_durations[step_index]))
        return linear_progress ** self.outward_acceleration

    def _spiral_points_at(self, angles):
        radii = self.inner_radius + self.turn_spacing * angles / (2.0 * math.pi)
        return numpy.column_stack((radii * numpy.cos(angles), radii * numpy.sin(angles)))

    def _evenly_spaced_angles(self, sample_count):
        dense_angles = numpy.linspace(0.0, 2.0 * math.pi * self.turns, 8 * sample_count)
        dense_step_lengths = numpy.linalg.norm(numpy.diff(self._spiral_points_at(dense_angles), axis=0), axis=1)
        dense_arc_lengths = numpy.concatenate(([0.0], numpy.cumsum(dense_step_lengths)))
        even_arc_lengths = numpy.linspace(0.0, dense_arc_lengths[-1], sample_count)
        return numpy.interp(even_arc_lengths, dense_arc_lengths, dense_angles)

    def _trace_spiral(self):
        sample_count = int(self.samples_per_turn * self.turns) + 1
        angles = self._evenly_spaced_angles(sample_count)
        flat_points = self._spiral_points_at(angles)
        tangents = numpy.gradient(flat_points, axis=0)
        tangents /= numpy.linalg.norm(tangents, axis=1, keepdims=True)
        outward_normals = numpy.column_stack((tangents[:, 1], -tangents[:, 0]))
        step_lengths = numpy.linalg.norm(numpy.diff(flat_points, axis=0), axis=1)
        arc_lengths = numpy.concatenate(([0.0], numpy.cumsum(step_lengths)))
        return angles, flat_points, outward_normals, arc_lengths

    def _sine_offset(self, arc_length):
        return self.sine_amplitude * numpy.sin(2.0 * math.pi * arc_length / self.sine_wavelength)

    def _trace_sine_curve(self):
        offsets = self._sine_offset(self.arc_lengths)
        return self._to_world(self.spiral_points + self.spiral_normals * offsets[:, None])

    def _spiral_frame_at(self, arc_length):
        point = numpy.array([numpy.interp(arc_length, self.arc_lengths, self.spiral_points[:, axis])
                             for axis in range(2)])
        normal = numpy.array([numpy.interp(arc_length, self.arc_lengths, self.spiral_normals[:, axis])
                              for axis in range(2)])
        return point, normal / numpy.linalg.norm(normal)

    def _place_gap_circles(self):
        centers, gap_fit_radii = self._gap_circle_candidates()
        radii = self._separate_circle_radii(centers, gap_fit_radii)
        return self._circle_shapes(centers, radii)

    def _trace_turn_band(self):
        full_turn = 2.0 * math.pi
        has_outer_turn = self.spiral_angles <= self.spiral_angles[-1] - full_turn
        inner_offsets = numpy.maximum(0.0, self._sine_offset(self.arc_lengths[has_outer_turn]))
        inner_edge = self.spiral_points[has_outer_turn] + self.spiral_normals[has_outer_turn] * inner_offsets[:, None]
        outer_angles = self.spiral_angles[has_outer_turn] + full_turn
        outer_arc_lengths = numpy.interp(outer_angles, self.spiral_angles, self.arc_lengths)
        outer_normals = numpy.column_stack([numpy.interp(outer_angles, self.spiral_angles, self.spiral_normals[:, axis])
                                            for axis in range(2)])
        outer_normals /= numpy.linalg.norm(outer_normals, axis=1, keepdims=True)
        outer_offsets = numpy.minimum(0.0, self._sine_offset(outer_arc_lengths))
        outer_edge = self._spiral_points_at(outer_angles) + outer_normals * outer_offsets[:, None]
        return inner_edge, outer_edge

    def _place_band_circles(self, inner_edge, outer_edge):
        midline = 0.5 * (inner_edge + outer_edge)
        search_samples = int(self.band_circle_search_length / self.arc_lengths[1])
        centers = []
        radii = []
        for sample_index, candidate_center in enumerate(midline):
            window = slice(max(0, sample_index - search_samples), sample_index + search_samples + 1)
            edge_distance = min(numpy.linalg.norm(inner_edge[window] - candidate_center, axis=1).min(),
                                numpy.linalg.norm(outer_edge[window] - candidate_center, axis=1).min())
            candidate_radius = self.band_circle_fit_share * edge_distance
            if candidate_radius < self.band_circle_min_radius:
                continue
            if centers and numpy.linalg.norm(candidate_center - centers[-1]) < (
                    radii[-1] + candidate_radius + self.band_circle_gap):
                continue
            centers.append(candidate_center)
            radii.append(candidate_radius)
        return self._circle_shapes(numpy.array(centers), numpy.array(radii))

    def _circle_shapes(self, centers, radii):
        circle_angles = numpy.linspace(0.0, 2.0 * math.pi, self.circle_segments + 1)
        unit_circle = numpy.column_stack((numpy.cos(circle_angles), numpy.sin(circle_angles)))
        outlines = [self._to_world(circle_center + unit_circle * circle_radius)
                    for circle_center, circle_radius in zip(centers, radii)]
        disks = [self._to_world(numpy.vstack((circle_center, circle_center + unit_circle * circle_radius)))
                 for circle_center, circle_radius in zip(centers, radii)]
        return outlines, disks

    def _interleave(self, first_points, second_points):
        interleaved = numpy.empty((2 * len(first_points), 3), dtype=numpy.float32)
        interleaved[0::2] = first_points
        interleaved[1::2] = second_points
        return interleaved

    def _gap_circle_candidates(self):
        gap_length = 0.5 * self.sine_wavelength
        gap_count = int(self.arc_lengths[-1] // gap_length)
        centers = []
        gap_fit_radii = []
        for gap_index in range(gap_count):
            gap_start = gap_index * gap_length
            circle_count = self.randomness.choice(self.circles_per_gap_choices)
            for circle_index in range(circle_count):
                arc_length = gap_start + gap_length * (circle_index + 1) / (circle_count + 1)
                curve_offset = float(self._sine_offset(arc_length))
                point, normal = self._spiral_frame_at(arc_length)
                centers.append(point + normal * 0.5 * curve_offset)
                gap_fit_radii.append(self.circle_radius_share * abs(curve_offset))
        return numpy.array(centers), numpy.array(gap_fit_radii)

    def _separate_circle_radii(self, centers, gap_fit_radii):
        if len(centers) < 2:
            return gap_fit_radii
        center_distances = numpy.linalg.norm(centers[:, None, :] - centers[None, :, :], axis=2)
        numpy.fill_diagonal(center_distances, numpy.inf)
        nearest_neighbour_distances = center_distances.min(axis=1)
        return numpy.minimum(gap_fit_radii, self.circle_neighbour_clearance * nearest_neighbour_distances)

    def _to_world(self, flat_points):
        world_points = numpy.empty((len(flat_points), 3), dtype=numpy.float32)
        world_points[:, :2] = flat_points + self.center[:2]
        world_points[:, 2] = self.center[2]
        return world_points

    def _draw_partial_line(self, points, progress):
        point_count = int(round(progress * len(points)))
        if point_count < 2:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_LINE_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(self.line_width)
        glColor4f(*self.color)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, points)
        glDrawArrays(GL_LINE_STRIP, 0, point_count)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()


class SpiralAnim(TravellingSurface):

    def __init__(self, spiral, camera_distance, field_of_view_degrees, aspect_ratio):
        spiral_extent = spiral.inner_radius + spiral.turn_spacing * spiral.turns + spiral.sine_amplitude
        super().__init__(spiral, spiral.center, spiral_extent, camera_distance, field_of_view_degrees, aspect_ratio)
        self.spiral = spiral
        self.sway_bob_height = 0.25 * spiral.turn_spacing
        self.surface_margin = 0.4 * spiral.turn_spacing
        self.surface_depth_offset = 0.01 * spiral.turn_spacing

    def restart(self):
        self.spiral.show_steps(len(self.spiral.steps))
        super().restart()
