import math

import numpy
from OpenGL.GL import *

from .lesson13_head import Head, HeadScene


class RoundedRectangle:
    def __init__(self, center, half_width, half_length):
        self.center = numpy.array(center)
        self.half_width = half_width
        self.half_length = half_length
        self.squareness = 8.0

    def offset(self, angle):
        power = 2.0 / self.squareness
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        x = (self.half_width * math.copysign(1.0, cos_angle)
             * abs(cos_angle) ** power)
        z = (self.half_length * math.copysign(1.0, sin_angle)
             * abs(sin_angle) ** power)
        return numpy.array((x, 0.0, z))

    def outward(self, angle):
        power = 2.0 - 2.0 / self.squareness
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        x = (math.copysign(1.0, cos_angle) * abs(cos_angle) ** power
             / self.half_width)
        z = (math.copysign(1.0, sin_angle) * abs(sin_angle) ** power
             / self.half_length)
        direction = numpy.array((x, 0.0, z))
        return direction / numpy.linalg.norm(direction)


class Bar:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.display_list = None

    def frames(self):
        raise NotImplementedError

    def emit_face(self, frames, first, second):
        first_across, first_up = first
        second_across, second_up = second
        glBegin(GL_TRIANGLE_STRIP)
        for center, across, up in frames:
            half_across = across * self.width / 2.0
            half_up = up * self.height / 2.0
            normal = (across * (first_across + second_across)
                      + up * (first_up + second_up))
            glNormal3f(*(normal / numpy.linalg.norm(normal)))
            glVertex3f(*(center + half_across * first_across
                         + half_up * first_up))
            glVertex3f(*(center + half_across * second_across
                         + half_up * second_up))
        glEnd()

    def emit_shape(self):
        frames = self.frames()
        corners = ((1.0, 1.0), (-1.0, 1.0),
                   (-1.0, -1.0), (1.0, -1.0))
        for index, first in enumerate(corners):
            second = corners[(index + 1) % len(corners)]
            self.emit_face(frames, first, second)

    def draw(self):
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            self.emit_shape()
            glEndList()
        glCallList(self.display_list)


class FrameRim(Bar):
    def __init__(self, outline, width, height):
        super().__init__(width, height)
        self.outline = outline
        self.segments = 64

    def frames(self):
        up = numpy.array((0.0, 1.0, 0.0))
        frames = []
        for segment in range(self.segments + 1):
            angle = 2.0 * math.pi * segment / self.segments
            outward = self.outline.outward(angle)
            edge = self.outline.center + self.outline.offset(angle)
            center = edge + outward * self.width / 2.0
            frames.append((center, outward, up))
        return frames


class CurvedBar(Bar):
    def __init__(self, start, middle, end, width, height):
        super().__init__(width, height)
        self.control_points = (start, middle, end)
        self.segments = 16
        bend_plane = numpy.cross(middle - start, end - middle)
        self.bend_normal = bend_plane / numpy.linalg.norm(bend_plane)

    def point_at(self, t):
        start, middle, end = self.control_points
        return ((1.0 - t) ** 2 * start + 2.0 * (1.0 - t) * t * middle
                + t * t * end)

    def tangent_at(self, t):
        start, middle, end = self.control_points
        tangent = (2.0 * (1.0 - t) * (middle - start)
                   + 2.0 * t * (end - middle))
        return tangent / numpy.linalg.norm(tangent)

    def frames(self):
        frames = []
        for segment in range(self.segments + 1):
            t = segment / self.segments
            tangent = self.tangent_at(t)
            across = numpy.cross(tangent, self.bend_normal)
            center = self.point_at(t)
            frames.append((center, across, self.bend_normal))
        return frames


class Lens:
    def __init__(self, outline):
        self.outline = outline
        self.bulge = 0.03
        self.rings = 6
        self.slices = 64
        self.color = (0.42, 0.37, 0.71)
        self.shine = (0.9, 0.9, 0.9, 1.0)
        self.no_shine = (0.4, 0.3, 0.66, 1.0)
        self.shininess = 60.0
        self.display_list = None

    def lens_point(self, ring, slice_index):
        reach = ring / self.rings
        angle = 2.0 * math.pi * slice_index / self.slices
        x, _y, z = reach * self.outline.offset(angle)
        y = self.bulge * (1.0 - reach * reach)
        half_width = self.outline.half_width
        half_length = self.outline.half_length
        slope_x = -2.0 * self.bulge * x / half_width ** 2
        slope_z = -2.0 * self.bulge * z / half_length ** 2
        normal = numpy.array((-slope_x, 1.0, -slope_z))
        normal /= numpy.linalg.norm(normal)
        return self.outline.center + numpy.array((x, y, z)), normal

    def emit_vertex(self, ring, slice_index):
        position, normal = self.lens_point(ring, slice_index)
        glNormal3f(*normal)
        glVertex3f(*position)

    def emit_shape(self):
        for ring in range(self.rings):
            glBegin(GL_TRIANGLE_STRIP)
            for slice_index in range(self.slices + 1):
                self.emit_vertex(ring + 1, slice_index)
                self.emit_vertex(ring, slice_index)
            glEnd()

    def draw(self):
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            self.emit_shape()
            glEndList()
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.shine)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.shininess)
        glColor3f(*self.color)
        glCallList(self.display_list)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.no_shine)


class Sunglasses:
    def __init__(self, head):
        self.light_source = head.front
        self.frame_color = (0.1, 0.6, 0.2)
        self.height = 0.68
        self.lens_half_width = 0.42
        self.lens_half_length = 0.17
        self.lens_spread = 0.15
        self.frame_width = 0.07
        self.frame_height = 0.06
        self.arm_width = 0.025
        self.arm_height = 0.06
        self.arm_bow = 0.16
        self.bridge_arch = 0.08
        self.lift = 0.0
        lens_centers = [self.lens_center(head.eye_center(socket))
                        for socket in head.sockets]
        self.outlines = [
            RoundedRectangle(center, self.lens_half_width,
                             self.lens_half_length)
            for center in lens_centers]
        self.lenses = [Lens(outline) for outline in self.outlines]
        self.rims = [FrameRim(outline, self.frame_width,
                              self.frame_height)
                     for outline in self.outlines]
        self.bridge = self.create_bridge()
        sides = zip(self.outlines, head.ears)
        self.arms = [self.create_arm(outline, ear)
                     for outline, ear in sides]

    def lens_center(self, eye_center):
        x, _y, z = eye_center
        spread_x = x + math.copysign(self.lens_spread, x)
        return (spread_x, self.height, z)

    def edge_offset(self):
        return self.lens_half_width + self.frame_width / 2.0

    def create_bridge(self):
        left, right = sorted(self.outlines,
                             key=lambda outline: outline.center[0])
        reach = numpy.array((self.edge_offset(), 0.0, 0.0))
        start = left.center + reach
        end = right.center - reach
        middle = (start + end) / 2.0 + (0.0, self.bridge_arch, 0.0)
        return CurvedBar(start, middle, end, self.frame_height,
                         self.frame_width)

    def create_arm(self, outline, ear):
        side = math.copysign(1.0, outline.center[0])
        start = outline.center + (side * self.edge_offset(), 0.0, 0.0)
        ear_x, ear_y, ear_z = ear.position
        end = numpy.array((ear_x + side * 0.03, ear_y,
                           ear_z - ear.half_length))
        bow = numpy.array((side * self.arm_bow, 0.0, 0.0))
        middle = (start + end) / 2.0 + bow
        return CurvedBar(start, middle, end, self.arm_width,
                         self.arm_height)

    def draw(self):
        glPushMatrix()
        glTranslatef(0.0, self.lift, 0.0)
        self.light_source.enable_lighting()
        glColor3f(*self.frame_color)
        for frame_part in self.rims + [self.bridge] + self.arms:
            frame_part.draw()
        for lens in self.lenses:
            lens.draw()
        glDisable(GL_LIGHTING)
        glPopMatrix()


class HeadWithSunglasses(Head):
    def __init__(self):
        super().__init__()
        self.show_sunglasses = True
        self.sunglasses = Sunglasses(self)

    def draw_parts(self):
        super().draw_parts()
        if self.show_sunglasses:
            self.sunglasses.draw()


class SunglassesScene(HeadScene):
    def create_head(self):
        return HeadWithSunglasses()
