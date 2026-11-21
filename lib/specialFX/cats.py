import random

import numpy
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CURRENT_BIT,
    GL_ENABLE_BIT,
    GL_FLOAT,
    GL_LIGHTING,
    GL_LINE_BIT,
    GL_LINE_STRIP,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_VERTEX_ARRAY,
    glBlendFunc,
    glColor4f,
    glDisable,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glLineWidth,
    glPopAttrib,
    glPushAttrib,
    glVertexPointer,
)


class Cat:

    def __init__(self, bottom_center, size):
        self.bottom_center = numpy.array(tuple(bottom_center), dtype=numpy.float32)
        self.size = size
        self.head_top_height = 1.11
        self.color = (1.0, 1.0, 1.0, 1.0)
        self.line_width = 3.0
        self.samples_per_curve = 48
        self.outline_point_count = 240
        self.left_side = ((-0.52, 0.0), (-0.66, 0.45), (-0.62, 0.95), (-0.40, 1.40))
        self.left_ear_inner_corner = (-0.26, self.head_top_height)
        self.right_ear_inner_corner = (0.30, self.head_top_height)
        self.right_side = ((0.45, 1.38), (0.62, 0.95), (0.64, 0.45), (0.48, 0.0))
        self.outline_points = self._to_world(self._evenly_spaced(self._trace_outline()))
        self.face_line_width = 2.0
        self.arc_samples = 32
        self.line_samples = 12
        self.eye_height = 0.78
        self.eye_spread = 0.22
        self.nose_height = 0.6
        self.eyes1_strokes = self._to_world_strokes(self._round_eyes_with_pupils())
        self.eyes2_strokes = self._to_world_strokes(self._slanted_eyes())
        self.eyes3_strokes = self._to_world_strokes(self._small_dot_eyes())
        self.eyes4_strokes = self._to_world_strokes(self._closed_eyes())
        self.mouth1_strokes = self._to_world_strokes(self._nose_and_wide_smile())
        self.mouth2_strokes = self._to_world_strokes(self._open_mouth())
        self.mouth3_strokes = self._to_world_strokes(self._heart_nose_and_double_curve())
        self.mouth4_strokes = self._to_world_strokes(self._nose_line_and_small_smile())
        self.eye_drawings = (self.draw_eyes1, self.draw_eyes2, self.draw_eyes3, self.draw_eyes4)
        self.mouth_drawings = (self.draw_mouth1, self.draw_mouth2, self.draw_mouth3, self.draw_mouth4)
        self.whisker_root_x = 0.34
        self.whisker_group_center_height = 0.55
        self.whisker_gap = 0.03
        self.whisker_length = 0.32
        self.whisker_droop = 0.04
        self.whisker_height_jitter = 0.07
        self.whisker_fan_degrees = (-20.0, 18.0)
        self.whisker_line_width = 1.5
        self.whisker_strokes = []

    def draw(self, progress=1.0):
        self._draw_strokes((self.outline_points,), progress, self.line_width)

    def grow_whiskers(self, left_count, right_count, randomness):
        unit_strokes = (self._side_whiskers(-1.0, left_count, randomness)
                        + self._side_whiskers(1.0, right_count, randomness))
        self.whisker_strokes = self._to_world_strokes(unit_strokes)

    def draw_whiskers(self, progress=1.0):
        self._draw_strokes(self.whisker_strokes, progress, self.whisker_line_width)

    def _side_whiskers(self, side, count, randomness):
        group_base_height = (self.whisker_group_center_height
                             + randomness.uniform(-self.whisker_height_jitter, self.whisker_height_jitter)
                             - 0.5 * (count - 1) * self.whisker_gap)
        root_heights = group_base_height + self.whisker_gap * numpy.arange(count)
        fan_angles = numpy.radians(numpy.linspace(*self.whisker_fan_degrees, count))
        whiskers = []
        for root_height, fan_angle in zip(root_heights, fan_angles):
            root = numpy.array((side * self.whisker_root_x, root_height))
            direction = numpy.array((side * numpy.cos(fan_angle), numpy.sin(fan_angle)))
            tip = root + self.whisker_length * direction
            bend = 0.5 * (root + tip) + numpy.array((0.0, -self.whisker_droop))
            whiskers.append(self._quadratic_curve(root, bend, tip))
        return whiskers

    def _quadratic_curve(self, start, handle, end):
        t = numpy.linspace(0.0, 1.0, self.line_samples)[:, None]
        return (1 - t) ** 2 * start + 2 * (1 - t) * t * handle + t ** 2 * end

    def draw_eyes1(self, progress=1.0):
        self._draw_strokes(self.eyes1_strokes, progress, self.face_line_width)

    def draw_eyes2(self, progress=1.0):
        self._draw_strokes(self.eyes2_strokes, progress, self.face_line_width)

    def draw_eyes3(self, progress=1.0):
        self._draw_strokes(self.eyes3_strokes, progress, self.face_line_width)

    def draw_eyes4(self, progress=1.0):
        self._draw_strokes(self.eyes4_strokes, progress, self.face_line_width)

    def draw_mouth1(self, progress=1.0):
        self._draw_strokes(self.mouth1_strokes, progress, self.face_line_width)

    def draw_mouth2(self, progress=1.0):
        self._draw_strokes(self.mouth2_strokes, progress, self.face_line_width)

    def draw_mouth3(self, progress=1.0):
        self._draw_strokes(self.mouth3_strokes, progress, self.face_line_width)

    def draw_mouth4(self, progress=1.0):
        self._draw_strokes(self.mouth4_strokes, progress, self.face_line_width)

    def _round_eyes_with_pupils(self):
        strokes = []
        for side in (-1.0, 1.0):
            eye_center = (side * self.eye_spread, self.eye_height)
            pupil_center = (side * self.eye_spread - side * 0.04, self.eye_height - 0.03)
            strokes.append(self._arc(eye_center, 0.13, 0.13, 90.0, 450.0))
            strokes.append(self._arc(pupil_center, 0.035, 0.035, 90.0, 450.0))
        return strokes

    def _slanted_eyes(self):
        strokes = []
        for side in (-1.0, 1.0):
            eye_center = (side * self.eye_spread, self.eye_height - 0.02)
            strokes.append(self._arc(eye_center, 0.12, 0.065, 0.0, 360.0, tilt_degrees=-side * 25.0))
        return strokes

    def _small_dot_eyes(self):
        strokes = []
        for side in (-1.0, 1.0):
            eye_center = (side * 0.15, self.eye_height)
            strokes.append(self._arc(eye_center, 0.06, 0.06, 90.0, 450.0))
            strokes.append(self._arc(eye_center, 0.018, 0.018, 90.0, 450.0))
        return strokes

    def _closed_eyes(self):
        return [self._arc((side * self.eye_spread, self.eye_height + 0.04), 0.1, 0.07, 200.0, 340.0)
                for side in (-1.0, 1.0)]

    def _nose_and_wide_smile(self):
        nose = numpy.vstack((self._line((-0.04, self.nose_height), (0.04, self.nose_height)),
                             self._line((0.04, self.nose_height), (0.0, self.nose_height - 0.045)),
                             self._line((0.0, self.nose_height - 0.045), (-0.04, self.nose_height))))
        smile = self._arc((0.0, 0.52), 0.26, 0.17, 200.0, 340.0)
        return [nose, smile]

    def _open_mouth(self):
        top_edge = self._arc((0.0, 0.33), 0.2, 0.06, 55.0, 125.0)
        bottom_edge = self._arc((0.0, 0.43), 0.2, 0.11, 205.0, 335.0)
        return [numpy.vstack((bottom_edge, top_edge, bottom_edge[:1]))]

    def _heart_nose_and_double_curve(self):
        lobe_radius = 0.035
        heart_tip = (0.0, self.nose_height - 0.06)
        heart = numpy.vstack((self._line(heart_tip, (-2 * lobe_radius, self.nose_height)),
                              self._arc((-lobe_radius, self.nose_height), lobe_radius, lobe_radius, 180.0, 0.0),
                              self._arc((lobe_radius, self.nose_height), lobe_radius, lobe_radius, 180.0, 0.0),
                              self._line((2 * lobe_radius, self.nose_height), heart_tip)))
        philtrum = self._line(heart_tip, (0.0, 0.48))
        curve_radius = 0.07
        double_curve = numpy.vstack((self._arc((-curve_radius, 0.48), curve_radius, curve_radius * 0.8, 180.0, 360.0),
                                     self._arc((curve_radius, 0.48), curve_radius, curve_radius * 0.8, 180.0, 360.0)))
        return [heart, philtrum, double_curve]

    def _nose_line_and_small_smile(self):
        nose = self._line((-0.05, self.nose_height), (0.05, self.nose_height))
        philtrum = self._line((0.0, self.nose_height), (0.0, 0.5))
        left_tick = self._line((-0.09, 0.52), (-0.09, 0.46))
        smile = self._arc((0.0, 0.46), 0.09, 0.07, 180.0, 360.0)
        right_tick = self._line((0.09, 0.46), (0.09, 0.52))
        return [nose, philtrum, numpy.vstack((left_tick, smile, right_tick))]

    def _arc(self, center, radius_x, radius_y, start_degrees, end_degrees, tilt_degrees=0.0):
        angles = numpy.radians(numpy.linspace(start_degrees, end_degrees, self.arc_samples))
        tilt = numpy.radians(tilt_degrees)
        x = radius_x * numpy.cos(angles)
        y = radius_y * numpy.sin(angles)
        return numpy.column_stack((center[0] + x * numpy.cos(tilt) - y * numpy.sin(tilt),
                                   center[1] + x * numpy.sin(tilt) + y * numpy.cos(tilt)))

    def _line(self, start, end):
        return numpy.linspace(start, end, self.line_samples)

    def _to_world_strokes(self, unit_strokes):
        return [self._to_world(numpy.asarray(stroke, dtype=numpy.float64)) for stroke in unit_strokes]

    def _draw_strokes(self, strokes, progress, line_width):
        stroke_lengths = [numpy.linalg.norm(numpy.diff(stroke, axis=0), axis=1).sum() for stroke in strokes]
        length_left = progress * sum(stroke_lengths)
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_LINE_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(line_width)
        glColor4f(*self.color)
        glEnableClientState(GL_VERTEX_ARRAY)
        for stroke, stroke_length in zip(strokes, stroke_lengths):
            if length_left <= 0.0:
                break
            stroke_share = min(1.0, length_left / stroke_length) if stroke_length else 1.0
            point_count = int(round(stroke_share * len(stroke)))
            if point_count >= 2:
                glVertexPointer(3, GL_FLOAT, 0, stroke)
                glDrawArrays(GL_LINE_STRIP, 0, point_count)
            length_left -= stroke_length
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()

    def _trace_outline(self):
        return numpy.vstack((
            self._bezier(self.left_side),
            [self.left_ear_inner_corner, self.right_ear_inner_corner],
            self._bezier(self.right_side),
        ))

    def _bezier(self, control_points):
        start, first_handle, second_handle, end = (numpy.array(point) for point in control_points)
        t = numpy.linspace(0.0, 1.0, self.samples_per_curve)[:, None]
        return ((1 - t) ** 3 * start + 3 * (1 - t) ** 2 * t * first_handle
                + 3 * (1 - t) * t ** 2 * second_handle + t ** 3 * end)

    def _evenly_spaced(self, path_points):
        step_lengths = numpy.linalg.norm(numpy.diff(path_points, axis=0), axis=1)
        path_lengths = numpy.concatenate(([0.0], numpy.cumsum(step_lengths)))
        even_lengths = numpy.linspace(0.0, path_lengths[-1], self.outline_point_count)
        return numpy.column_stack([numpy.interp(even_lengths, path_lengths, path_points[:, axis])
                                   for axis in range(2)])

    def _to_world(self, unit_points):
        world_points = numpy.empty((len(unit_points), 3), dtype=numpy.float32)
        world_points[:, :2] = unit_points * self.size + self.bottom_center[:2]
        world_points[:, 2] = self.bottom_center[2]
        return world_points


class CatAnim:

    def __init__(self, area_center, area_width, area_height, cat_size):
        self.area_center = numpy.array(tuple(area_center), dtype=numpy.float32)
        self.area_width = area_width
        self.area_height = area_height
        self.cat_size = cat_size
        self.horizontal_spacing = 1.35 * cat_size
        self.outline_phase_seconds = 8.0
        self.eyes_phase_seconds = 4.0
        self.mouth_phase_seconds = 4.0
        self.whiskers_phase_seconds = 4.0
        self.outline_seconds_per_cat = 1.2
        self.eyes_seconds_per_cat = 0.6
        self.mouth_seconds_per_cat = 0.6
        self.whiskers_seconds_per_cat = 0.6
        self.whiskers_per_side = (3, 5)
        self.randomness = random.Random()
        self.time = 0.0
        self.stacked_cats = self._tile_cats()
        self.cat_eye_drawings = [self.randomness.choice(cat.eye_drawings) for cat in self.stacked_cats]
        self.cat_mouth_drawings = [self.randomness.choice(cat.mouth_drawings) for cat in self.stacked_cats]
        for cat in self.stacked_cats:
            cat.grow_whiskers(self.randomness.randint(*self.whiskers_per_side),
                              self.randomness.randint(*self.whiskers_per_side), self.randomness)
        self.phases = (self.draw_outlines, self.draw_eyes, self.draw_mouths, self.draw_whiskers)
        self.phase_durations = (self.outline_phase_seconds, self.eyes_phase_seconds,
                                self.mouth_phase_seconds, self.whiskers_phase_seconds)

    def update(self, delta_seconds):
        self.time += delta_seconds

    def restart(self):
        self.time = 0.0

    def total_seconds(self):
        return sum(self.phase_durations)

    def is_finished(self):
        return self.time >= self.total_seconds()

    def draw(self):
        phase_start = 0.0
        for phase, phase_duration in zip(self.phases, self.phase_durations):
            phase(max(0.0, self.time - phase_start), phase_duration)
            phase_start += phase_duration

    def draw_outlines(self, phase_time, phase_seconds):
        self._draw_cat_by_cat(phase_time, phase_seconds, [cat.draw for cat in self.stacked_cats],
                              self.outline_seconds_per_cat)

    def draw_eyes(self, phase_time, phase_seconds):
        self._draw_cat_by_cat(phase_time, phase_seconds, self.cat_eye_drawings, self.eyes_seconds_per_cat)

    def draw_mouths(self, phase_time, phase_seconds):
        self._draw_cat_by_cat(phase_time, phase_seconds, self.cat_mouth_drawings, self.mouth_seconds_per_cat)

    def draw_whiskers(self, phase_time, phase_seconds):
        self._draw_cat_by_cat(phase_time, phase_seconds, [cat.draw_whiskers for cat in self.stacked_cats],
                              self.whiskers_seconds_per_cat)

    def _draw_cat_by_cat(self, phase_time, phase_seconds, cat_drawings, seconds_per_cat):
        drawing_seconds = min(seconds_per_cat, phase_seconds)
        cat_start_interval = (phase_seconds - drawing_seconds) / max(1, len(cat_drawings) - 1)
        for cat_index, cat_drawing in enumerate(cat_drawings):
            cat_progress = (phase_time - cat_index * cat_start_interval) / drawing_seconds
            if cat_progress <= 0.0:
                break
            cat_drawing(min(1.0, cat_progress))

    def _tile_cats(self):
        probe_cat = Cat((0.0, 0.0, 0.0), self.cat_size)
        cat_half_width = max(float(numpy.abs(probe_cat.outline_points[:, 0]).max()),
                             (probe_cat.whisker_root_x + probe_cat.whisker_length) * self.cat_size)
        cat_height = float(probe_cat.outline_points[:, 1].max())
        row_height = probe_cat.head_top_height * self.cat_size
        center_x, center_y, center_z = (float(value) for value in self.area_center)
        row_count = max(1, int((self.area_height - cat_height) // row_height) + 1)
        lowest_row_y = center_y - 0.5 * ((row_count - 1) * row_height + cat_height)
        leftmost_x = center_x - 0.5 * self.area_width + cat_half_width
        rightmost_x = center_x + 0.5 * self.area_width - cat_half_width
        lattice_reach = int(self.area_width // self.horizontal_spacing) + 2
        cats = []
        for row_index in range(row_count):
            row_y = lowest_row_y + row_index * row_height
            row_shift = 0.5 * self.horizontal_spacing * (row_index % 2)
            for lattice_index in range(-lattice_reach, lattice_reach + 1):
                cat_x = center_x + lattice_index * self.horizontal_spacing + row_shift
                if leftmost_x <= cat_x <= rightmost_x:
                    cats.append(Cat((cat_x, row_y, center_z), self.cat_size))
        return cats
