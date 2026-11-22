import math

import numpy
import pygame
from OpenGL.GL import (
    GL_CURRENT_BIT,
    GL_ENABLE_BIT,
    GL_LIGHTING,
    GL_LINEAR,
    GL_QUADS,
    GL_RGB,
    GL_TEXTURE_2D,
    GL_TEXTURE_BIT,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glPixelStorei,
    glPopAttrib,
    glPushAttrib,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTexSubImage2D,
    glVertex3f,
)


class LineItem:

    def __init__(self, points, width):
        self.points = [tuple(point) for point in numpy.asarray(points).tolist()]
        self.width = width
        self.unit_count = max(1, len(self.points) - 1)

    def draw_units(self, canvas, color, first_unit, last_unit):
        segment_points = self.points[first_unit:last_unit + 1]
        if len(segment_points) >= 2:
            pygame.draw.lines(canvas, color, False, segment_points, self.width)


class FilledCellItem:

    def __init__(self, cell_outline, ellipse_outline, hole_color, ellipse_width):
        self.cell_outline = [tuple(point) for point in numpy.asarray(cell_outline).tolist()]
        self.ellipse_outline = [tuple(point) for point in numpy.asarray(ellipse_outline).tolist()]
        self.hole_color = hole_color
        self.ellipse_width = ellipse_width
        self.unit_count = 1

    def draw_units(self, canvas, color, first_unit, last_unit):
        pygame.draw.polygon(canvas, color, self.cell_outline)
        pygame.draw.polygon(canvas, self.hole_color, self.ellipse_outline)
        pygame.draw.lines(canvas, color, True, self.ellipse_outline, self.ellipse_width)


class DrawingPhase:

    def __init__(self, items, seconds):
        self.items = items
        self.seconds = seconds
        self.total_units = sum(item.unit_count for item in items)
        self.drawn_units = 0
        self.item_index = 0
        self.units_into_item = 0

    def reset(self):
        self.drawn_units = 0
        self.item_index = 0
        self.units_into_item = 0

    def draw_up_to(self, canvas, color, progress):
        target_units = int(round(progress * self.total_units))
        while self.drawn_units < target_units and self.item_index < len(self.items):
            item = self.items[self.item_index]
            units_to_draw = min(item.unit_count - self.units_into_item, target_units - self.drawn_units)
            item.draw_units(canvas, color, self.units_into_item, self.units_into_item + units_to_draw)
            self.units_into_item += units_to_draw
            self.drawn_units += units_to_draw
            if self.units_into_item >= item.unit_count:
                self.item_index += 1
                self.units_into_item = 0


class SineWebAnim:

    def __init__(self, size):
        self.width, self.height = size
        self.center = numpy.array((self.width / 2.0, self.height / 2.0))
        shorter_side = min(self.width, self.height)
        self.ink_color = (255, 255, 255)
        self.paper_color = (0, 0, 0)
        self.curve_count = 6
        self.wave_amplitude_share = 0.12
        self.wavelength = 0.22 * shorter_side
        self.web_radius = 0.46 * shorter_side
        self.ring_count = 7
        self.thread_sag = 0.82
        self.outer_line_spacing = 0.012 * shorter_side
        self.curve_width = 3
        self.ring_width = 2
        self.outer_line_width = 1
        self.shade_width = 1
        self.shade_spacing = 0.006 * shorter_side
        self.shade_depth_share = 0.22
        self.ellipse_length_share = 0.34
        self.ellipse_thickness_share = 0.3
        self.ellipse_samples = 28
        self.arc_samples = 18
        self.spoke_samples_per_ring = 8
        self.phase_seconds = (4.0, 5.0, 4.0, 3.0, 3.0, 4.0)
        self.time = 0.0
        self.canvas = pygame.Surface(size)
        self.spoke_count = 2 * self.curve_count
        self.outer_radius = math.hypot(self.width / 2.0, self.height / 2.0)
        self.ring_radii = [self.web_radius * ring_index / self.ring_count for ring_index in range(self.ring_count + 1)]
        self.phases = [
            DrawingPhase(self._sine_curve_items(), self.phase_seconds[0]),
            DrawingPhase(self._ring_items(), self.phase_seconds[1]),
            DrawingPhase(self._outer_line_items(), self.phase_seconds[2]),
            DrawingPhase(self._ellipse_items(), self.phase_seconds[3]),
            DrawingPhase(self._filled_cell_items(), self.phase_seconds[4]),
            DrawingPhase(self._shade_items(), self.phase_seconds[5]),
        ]
        self.restart()

    def restart(self):
        self.time = 0.0
        self.canvas.fill(self.paper_color)
        for phase in self.phases:
            phase.reset()

    def update(self, delta_seconds):
        self.time += delta_seconds
        phase_start = 0.0
        for phase in self.phases:
            progress = max(0.0, min(1.0, (self.time - phase_start) / phase.seconds))
            phase.draw_up_to(self.canvas, self.ink_color, progress)
            phase_start += phase.seconds

    def total_seconds(self):
        return sum(phase.seconds for phase in self.phases)

    def is_finished(self):
        return self.time >= self.total_seconds()

    def draw(self, target_surface, position=(0, 0)):
        target_surface.blit(self.canvas, position)

    def _spoke_point(self, spoke_index, radius):
        curve_index = spoke_index % self.curve_count
        side = 1.0 if spoke_index < self.curve_count else -1.0
        curve_angle = math.pi * curve_index / self.curve_count
        along = numpy.array((math.cos(curve_angle), math.sin(curve_angle)))
        across = numpy.array((-along[1], along[0]))
        signed_distance = side * radius
        wave_offset = self.wave_amplitude_share * radius * math.sin(2.0 * math.pi * signed_distance / self.wavelength)
        return self.center + signed_distance * along + wave_offset * across

    def _spoke_segment(self, spoke_index, inner_radius, outer_radius):
        radii = numpy.linspace(inner_radius, outer_radius, self.spoke_samples_per_ring + 1)
        return numpy.array([self._spoke_point(spoke_index, radius) for radius in radii])

    def _thread(self, first_spoke, radius):
        second_spoke = (first_spoke + 1) % self.spoke_count
        start = self._spoke_point(first_spoke, radius)
        end = self._spoke_point(second_spoke, radius)
        handle = self.center + self.thread_sag * (0.5 * (start + end) - self.center)
        t = numpy.linspace(0.0, 1.0, self.arc_samples)[:, None]
        return (1 - t) ** 2 * start + 2 * (1 - t) * t * handle + t ** 2 * end

    def _sine_curve_items(self):
        items = []
        samples_per_half_curve = int(self.outer_radius / 2.0)
        for curve_index in range(self.curve_count):
            radii = numpy.linspace(self.outer_radius, 0.0, samples_per_half_curve)
            first_half = [self._spoke_point(curve_index + self.curve_count, radius) for radius in radii]
            second_half = [self._spoke_point(curve_index, radius) for radius in radii[::-1][1:]]
            items.append(LineItem(first_half + second_half, self.curve_width))
        return items

    def _ring_items(self):
        return [LineItem(self._thread(spoke_index, radius), self.ring_width)
                for radius in self.ring_radii[1:]
                for spoke_index in range(self.spoke_count)]

    def _outer_line_items(self):
        items = []
        thread_middle_share = (0.5 + 0.5 * self.thread_sag) * math.cos(math.pi / self.spoke_count)
        radius = self.web_radius + self.outer_line_spacing
        while thread_middle_share * radius < self.outer_radius:
            items.extend(LineItem(self._thread(spoke_index, radius), self.outer_line_width)
                         for spoke_index in range(self.spoke_count))
            radius += self.outer_line_spacing
        return items

    def _cells(self, ring_parity):
        for ring_index in range(self.ring_count):
            if (ring_index + 1) % 2 != ring_parity:
                continue
            inner_radius = self.ring_radii[ring_index]
            outer_radius = self.ring_radii[ring_index + 1]
            for spoke_index in range(self.spoke_count):
                yield spoke_index, inner_radius, outer_radius

    def _cell_outline(self, spoke_index, inner_radius, outer_radius):
        next_spoke = (spoke_index + 1) % self.spoke_count
        inner_thread = self._thread(spoke_index, inner_radius) if inner_radius > 0.0 else self.center[None, :]
        return numpy.vstack((inner_thread,
                             self._spoke_segment(next_spoke, inner_radius, outer_radius),
                             self._thread(spoke_index, outer_radius)[::-1],
                             self._spoke_segment(spoke_index, outer_radius, inner_radius)))

    def _cell_frame(self, spoke_index, inner_radius, outer_radius):
        inner_middle = self._thread(spoke_index, inner_radius)[self.arc_samples // 2] if inner_radius > 0.0 \
            else self.center
        outer_middle = self._thread(spoke_index, outer_radius)[self.arc_samples // 2]
        cell_center = 0.5 * (inner_middle + outer_middle)
        middle_radius = 0.5 * (inner_radius + outer_radius)
        next_spoke = (spoke_index + 1) % self.spoke_count
        chord = self._spoke_point(next_spoke, middle_radius) - self._spoke_point(spoke_index, middle_radius)
        chord_length = float(numpy.linalg.norm(chord))
        cell_depth = float(numpy.linalg.norm(outer_middle - inner_middle))
        return cell_center, chord / chord_length, chord_length, cell_depth

    def _cell_ellipse(self, spoke_index, inner_radius, outer_radius):
        cell_center, along_chord, chord_length, cell_depth = self._cell_frame(spoke_index, inner_radius, outer_radius)
        across_chord = numpy.array((-along_chord[1], along_chord[0]))
        semi_length = self.ellipse_length_share * chord_length
        semi_thickness = self.ellipse_thickness_share * cell_depth
        angles = numpy.linspace(0.0, 2.0 * math.pi, self.ellipse_samples + 1)
        return (cell_center + numpy.cos(angles)[:, None] * semi_length * along_chord
                + numpy.sin(angles)[:, None] * semi_thickness * across_chord)

    def _ellipse_items(self):
        return [LineItem(self._cell_ellipse(*cell), self.ring_width) for cell in self._cells(ring_parity=0)]

    def _filled_cell_items(self):
        return [FilledCellItem(self._cell_outline(*cell), self._cell_ellipse(*cell), self.paper_color, self.ring_width)
                for cell in self._cells(ring_parity=0)]

    def _shade_items(self):
        items = []
        for spoke_index, inner_radius, outer_radius in self._cells(ring_parity=1):
            cell_center, _, chord_length, _ = self._cell_frame(spoke_index, inner_radius, outer_radius)
            shade_depth = self.shade_depth_share * chord_length
            next_spoke = (spoke_index + 1) % self.spoke_count
            for boundary_spoke in (spoke_index, next_spoke):
                items.extend(self._shades_along_spoke(boundary_spoke, inner_radius, outer_radius,
                                                      cell_center, shade_depth))
        return items

    def _shades_along_spoke(self, spoke_index, inner_radius, outer_radius, cell_center, shade_depth):
        shade_count = int(shade_depth / self.shade_spacing)
        shades = []
        for shade_index in range(1, shade_count + 1):
            offset = shade_index * self.shade_spacing
            reach_share = math.asin(min(1.0, offset / shade_depth)) / math.pi
            shares = numpy.linspace(reach_share, 1.0 - reach_share, self.spoke_samples_per_ring + 1)
            shade_points = []
            for share in shares:
                root = self._spoke_point(spoke_index, inner_radius + share * (outer_radius - inner_radius))
                toward_center = cell_center - root
                distance = float(numpy.linalg.norm(toward_center))
                if distance > 0.0:
                    shade_points.append(root + toward_center / distance * min(offset, 0.8 * distance))
            if len(shade_points) >= 2:
                shades.append(LineItem(shade_points, self.shade_width))
        return shades


class SineWebPanel:

    def __init__(self, center, half_size, canvas_pixels):
        self.center = tuple(float(value) for value in center)
        self.half_size = half_size
        self.sine_web = SineWebAnim((canvas_pixels, canvas_pixels))
        self.canvas_pixels = canvas_pixels
        self.texture = None
        self.texture_is_stale = True

    @property
    def time(self):
        return self.sine_web.time

    @time.setter
    def time(self, seconds):
        if seconds < self.sine_web.time:
            self.sine_web.restart()
        if seconds > self.sine_web.time:
            self.sine_web.update(seconds - self.sine_web.time)
            self.texture_is_stale = True

    def restart(self):
        self.sine_web.restart()
        self.texture_is_stale = True

    def total_seconds(self):
        return self.sine_web.total_seconds()

    def draw(self):
        self._refresh_texture()
        center_x, center_y, center_z = self.center
        left, right = center_x - self.half_size, center_x + self.half_size
        bottom, top = center_y - self.half_size, center_y + self.half_size
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(left, bottom, center_z)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(right, bottom, center_z)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(right, top, center_z)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(left, top, center_z)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glPopAttrib()

    def _refresh_texture(self):
        if self.texture is None:
            self.texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.canvas_pixels, self.canvas_pixels, 0, GL_RGB,
                         GL_UNSIGNED_BYTE, None)
            self.texture_is_stale = True
        if not self.texture_is_stale:
            return
        pixels = pygame.image.tobytes(self.sine_web.canvas, "RGB", True)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.canvas_pixels, self.canvas_pixels, GL_RGB, GL_UNSIGNED_BYTE,
                        pixels)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.texture_is_stale = False
