import math
import random

import numpy
from OpenGL.GL import *

from .lesson5_ball import Ball
from .lesson12_bald_head import BaldHead, BaldHeadScene


class Eyeball(Ball):
    def __init__(self, radius):
        super().__init__(radius, (0.97, 0.97, 0.95))
        self.slices = 32
        self.stacks = 24
        self.iris_color = (0.15, 0.4, 0.9)
        self.pupil_color = (0.02, 0.02, 0.03)
        self.iris_degrees = 35.0
        self.pupil_degrees = 14.0

    def color_at(self, stack_index):
        degrees_from_front = 180.0 * (1.0 - stack_index / self.stacks)
        if degrees_from_front < self.pupil_degrees:
            return self.pupil_color
        if degrees_from_front < self.iris_degrees:
            return self.iris_color
        return self.color

    def emit_vertex(self, slice_index, stack_index):
        glColor3f(*self.color_at(stack_index))
        super().emit_vertex(slice_index, stack_index)

    def invalidate(self):
        if self.display_list is not None:
            glDeleteLists(self.display_list, 1)
            self.display_list = None


class Ear:
    def __init__(self, side, skin_color):
        self.side = side
        self.skin_color = skin_color
        self.half_length = 0.32
        self.half_width = 0.2
        self.tube_radius = 0.05
        self.flatness = 0.6
        self.flare_degrees = 20.0
        self.segments = 32
        self.tube_segments = 12
        self.bowl_scale = 0.85
        self.bowl_depth = 0.05
        self.bowl_sink = 0.02
        self.position = (0.0, 0.0, 0.0)
        self.size = 1.0
        self.bowl = Ball(1.0, skin_color)
        self.display_list = None

    def rim_point(self, angle, tube_angle):
        center_y = self.half_width * math.cos(angle)
        center_z = self.half_length * math.sin(angle)
        out_y = math.cos(angle) / self.half_width
        out_z = math.sin(angle) / self.half_length
        out_length = math.hypot(out_y, out_z)
        out_y /= out_length
        out_z /= out_length
        outward = math.cos(tube_angle)
        across = math.sin(tube_angle)
        tube = self.tube_radius
        position = (self.side * tube * self.flatness * across,
                    center_y + tube * outward * out_y,
                    center_z + tube * outward * out_z)
        normal = (self.side * across / self.flatness,
                  outward * out_y,
                  outward * out_z)
        return position, normal

    def emit_rim_vertex(self, segment, tube_segment):
        angle = 2.0 * math.pi * segment / self.segments
        tube_angle = 2.0 * math.pi * tube_segment / self.tube_segments
        position, normal = self.rim_point(angle, tube_angle)
        glNormal3f(*normal)
        glVertex3f(*position)

    def compile(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        glColor3f(*self.skin_color)
        for segment in range(self.segments):
            glBegin(GL_TRIANGLE_STRIP)
            for tube_segment in range(self.tube_segments + 1):
                self.emit_rim_vertex(segment + 1, tube_segment)
                self.emit_rim_vertex(segment, tube_segment)
            glEnd()
        glEndList()

    def draw_bowl(self):
        glPushMatrix()
        glTranslatef(-self.side * self.bowl_sink, 0.0, 0.0)
        glScalef(self.bowl_depth,
                 self.half_width * self.bowl_scale,
                 self.half_length * self.bowl_scale)
        self.bowl.draw()
        glPopMatrix()

    def draw(self):
        if self.display_list is None:
            self.compile()
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.side * self.flare_degrees, 0.0, 0.0, 1.0)
        glScalef(self.size, self.size, self.size)
        self.bowl.enable_lighting()
        glCallList(self.display_list)
        self.bowl.disable_lighting()
        self.draw_bowl()
        glPopMatrix()


class Hair:
    def __init__(self, root, normal, fall, length):
        self.root_radius = 0.012
        self.tip_radius = 0.001
        self.segments = 8
        self.sides = 6
        rise = root + normal * length * 0.45
        self.control_points = (root, rise, rise + fall * length * 0.6)
        self.display_list = None

    def point_at(self, t):
        start, middle, end = self.control_points
        return ((1.0 - t) ** 2 * start + 2.0 * (1.0 - t) * t * middle
                + t * t * end)

    def tangent_at(self, t):
        start, middle, end = self.control_points
        tangent = (2.0 * (1.0 - t) * (middle - start)
                   + 2.0 * t * (end - middle))
        return tangent / numpy.linalg.norm(tangent)

    def radius_at(self, t):
        return self.root_radius + (self.tip_radius
                                   - self.root_radius) * t

    def reference_for(self, tangent):
        if abs(tangent[0]) < 0.9:
            return numpy.array((1.0, 0.0, 0.0))
        return numpy.array((0.0, 1.0, 0.0))

    def ring(self, t):
        center = self.point_at(t)
        tangent = self.tangent_at(t)
        side = numpy.cross(tangent, self.reference_for(tangent))
        side /= numpy.linalg.norm(side)
        other_side = numpy.cross(tangent, side)
        radius = self.radius_at(t)
        ring = []
        for side_index in range(self.sides + 1):
            angle = 2.0 * math.pi * side_index / self.sides
            direction = (math.cos(angle) * side
                         + math.sin(angle) * other_side)
            ring.append((center + direction * radius, direction))
        return ring

    def emit_shape(self):
        rings = [self.ring(segment / self.segments)
                 for segment in range(self.segments + 1)]
        for lower, upper in zip(rings, rings[1:]):
            glBegin(GL_TRIANGLE_STRIP)
            for (low_point, low_normal), (up_point, up_normal) in zip(
                    lower, upper):
                glNormal3f(*up_normal)
                glVertex3f(*up_point)
                glNormal3f(*low_normal)
                glVertex3f(*low_point)
            glEnd()

    def draw(self):
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            self.emit_shape()
            glEndList()
        glCallList(self.display_list)


class Haircut:
    def __init__(self, back, front, bald_spots):
        self.back = back
        self.front = front
        self.bald_spots = bald_spots
        self.fringe_share = 0.15
        self.hairline = -1.05
        self.hairline_recession = 0.25
        self.slope_step = 0.01
        self.hair_count = 1000
        self.color = (0.25, 0.25, 0.25)
        self.nape_line = 0.7
        self.temple_line = -0.3
        self.cheek_clearance = 0.6
        self.ear_clearance = 0.4
        self.crown_boost = 2.0
        self.above_ear_boost = 2.0
        self.above_ear_lift = numpy.array((0.0, 0.0, 0.6))
        self.above_ear_reach = 0.45
        self.steepest_slope = 6.0
        self.max_density = self.steepest_slope * (
            1.0 + self.crown_boost + self.above_ear_boost)
        self.shortest = 0.35
        self.longest = 0.6
        self.messiness = 0.3
        self.fall_direction = numpy.array((0.0, 0.0, 1.0))
        self.random = random.Random(13)
        self.hairs = [self.grow_hair()
                      for _hair_index in range(self.hair_count)]
        self.visible_count = self.hair_count

    def is_bald_spot(self, point):
        distances = [numpy.linalg.norm(point - spot)
                     for spot in self.bald_spots]
        return min(distances) < self.ear_clearance

    def is_cheek(self, point):
        _x, y, z = point
        below_temples = z > self.temple_line
        return below_temples and y > -self.cheek_clearance

    def crown_share(self, z):
        top = -self.back.half_length
        share = (z - self.temple_line) / (top - self.temple_line)
        return min(max(share, 0.0), 1.0)

    def above_ear_share(self, point):
        distances = [numpy.linalg.norm(
                         point - (spot - self.above_ear_lift))
                     for spot in self.bald_spots]
        nearest = min(distances)
        return max(1.0 - nearest / self.above_ear_reach, 0.0)

    def density(self, root, normal):
        steepness = 1.0 / max(abs(normal[1]), 0.001)
        area_stretch = min(steepness, self.steepest_slope)
        boost = (1.0
                 + self.crown_boost * self.crown_share(root[2])
                 + self.above_ear_boost * self.above_ear_share(root))
        return area_stretch * boost

    def hairline_at(self, x):
        across = x / self.back.half_width
        return self.hairline - self.hairline_recession * across ** 2

    def front_normal(self, x, z):
        height = self.front.height
        step = self.slope_step
        slope_x = (height(x + step, z) - height(x - step, z)) / (
            2.0 * step)
        slope_z = (height(x, z + step) - height(x, z - step)) / (
            2.0 * step)
        normal = numpy.array((-slope_x, 1.0, -slope_z))
        return normal / numpy.linalg.norm(normal)

    def random_spot(self):
        back = self.back
        x = self.random.uniform(-back.half_width, back.half_width)
        z = self.random.uniform(-back.half_length, self.nape_line)
        return x, z

    def random_front_root(self):
        back = self.back
        x = self.random.uniform(-back.half_width, back.half_width)
        hairline = self.hairline_at(x)
        z = self.random.uniform(-back.half_length, hairline)
        if back.bulge(x, z) <= 0.0:
            return None
        root = numpy.array((x, float(self.front.height(x, z)), z))
        return root, self.front_normal(x, z)

    def random_back_root(self):
        x, z = self.random_spot()
        if self.back.bulge(x, z) <= 0.0:
            return None
        root = numpy.array((x, self.back.height(x, z), z))
        if self.is_bald_spot(root) or self.is_cheek(root):
            return None
        return root, numpy.array(self.back.normal_at(root))

    def random_root(self):
        while True:
            if self.random.random() < self.fringe_share:
                candidate = self.random_front_root()
            else:
                candidate = self.random_back_root()
            if candidate is None:
                continue
            root, normal = candidate
            chance = self.random.uniform(0.0, self.max_density)
            if chance < self.density(root, normal):
                return root, normal

    def grow_hair(self):
        root, normal = self.random_root()
        jitter = numpy.array([self.random.uniform(-self.messiness,
                                                  self.messiness)
                              for _axis in range(3)])
        fall = normal * 0.35 + self.fall_direction * 0.65 + jitter
        fall /= numpy.linalg.norm(fall)
        length = self.random.uniform(self.shortest, self.longest)
        return Hair(root, normal, fall, length)

    def draw(self):
        self.front.enable_lighting()
        glColor3f(*self.color)
        for hair in self.hairs[:self.visible_count]:
            hair.draw()
        glDisable(GL_LIGHTING)


class Head(BaldHead):
    def __init__(self):
        super().__init__()
        self.eye_radius = 0.16
        self.eye_rise = 0.03
        self.ear_height = -0.45
        self.ear_along = 0.0
        self.ear_offset = 0.02
        self.show_eyes = True
        self.show_ears = True
        self.sockets = self.front.eyes[:2]
        self.eyeballs = [Eyeball(self.eye_radius)
                         for _socket in self.sockets]
        for eyeball in self.eyeballs:
            eyeball.light_position = self.front.light_position
        self.ears = [Ear(side, self.front.skin_color)
                     for side in (-1.0, 1.0)]
        for ear in self.ears:
            ear.bowl.light_position = self.front.light_position
            ear.position = self.ear_position(ear.side)
        self.show_hair = True
        ear_spots = [numpy.array(ear.position) for ear in self.ears]
        self.haircut = Haircut(self.back, self.front, ear_spots)

    def eye_center(self, socket):
        x = socket.center_x
        z = socket.center_z
        y = float(self.front.height(x, z)) + self.eye_rise
        return (x, y, z)

    def ear_position(self, side):
        back = self.back
        depth_share = self.ear_height / back.back_depth
        length_share = self.ear_along / back.half_length
        inside = 1.0 - depth_share ** 2 - length_share ** 2
        x = back.half_width * math.sqrt(inside)
        return (side * (x + self.ear_offset), self.ear_height,
                self.ear_along)

    def draw_eyes(self):
        for socket, eyeball in zip(self.sockets, self.eyeballs):
            glPushMatrix()
            glTranslatef(*self.eye_center(socket))
            eyeball.draw()
            glPopMatrix()

    def draw_ears(self):
        for ear in self.ears:
            ear.draw()

    def draw_hair(self):
        self.haircut.draw()

    def draw_parts(self):
        super().draw_parts()
        if self.show_eyes:
            self.draw_eyes()
        if self.show_ears:
            self.draw_ears()
        if self.show_hair:
            self.draw_hair()


class HeadScene(BaldHeadScene):
    def create_head(self):
        return Head()

