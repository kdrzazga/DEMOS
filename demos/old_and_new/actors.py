import math

import numpy
from OpenGL.GL import *

from demos.old_and_new.models3d.lesson5_ball import Ball
from demos.old_and_new.models3d.lesson8_mesh import MeshSurface
from demos.old_and_new.models3d.lesson12_bald_head import (
    HeadFront, ellipse_coordinates)
from demos.old_and_new.models3d.lesson14_sunglasses import (
    HeadWithSunglasses)


class StageBall:
    def __init__(self, home, radius):
        self.ball = Ball(1.0, (0.95, 0.95, 0.93))
        self.home = numpy.array(home)
        self.position = numpy.array(home)
        self.full_radius = radius
        self.radius = radius
        self.size = 0.0
        self.visible = False
        self.bob_height = 0.08
        self.bob_speed = 2.0
        self.bob_offset = home[0]

    def bob(self, time):
        rise = self.bob_height * math.sin(self.bob_speed * time
                                          + self.bob_offset)
        self.position = self.home + (0.0, rise, 0.0)

    def jump(self, target, target_radius, arc_height, progress):
        flight = progress * progress * (3.0 - 2.0 * progress)
        arc = arc_height * 4.0 * progress * (1.0 - progress)
        self.position = (self.home + (numpy.array(target) - self.home)
                         * flight + (0.0, arc, 0.0))
        self.radius = (self.full_radius
                       + (target_radius - self.full_radius) * flight)

    def draw(self):
        if not self.visible or self.size <= 0.0:
            return
        glPushMatrix()
        glTranslatef(*self.position)
        scale = self.radius * self.size
        glScalef(scale, scale, scale)
        glEnable(GL_NORMALIZE)
        self.ball.draw()
        glDisable(GL_NORMALIZE)
        glPopMatrix()


class SkinMesh:
    def __init__(self, skin_color, wire_color):
        self.surface = MeshSurface(4.0, 20)
        self.surface.base_height = 0.0
        self.surface.fill_color = skin_color
        self.surface.line_color = skin_color
        self.skin_color = skin_color
        self.wire_color = wire_color
        self.visible = False
        self.row_share = 0.0
        self.column_share = 0.0

    def set_wire_darkness(self, share):
        self.surface.line_color = tuple(
            skin + (wire - skin) * share
            for skin, wire in zip(self.skin_color, self.wire_color))

    def draw(self, pose):
        if not self.visible:
            return
        surface = self.surface
        line_count = surface.divisions + 1
        positions = surface.grid_positions()
        glPushMatrix()
        pose.apply()
        glLineWidth(1.0)
        surface.draw_rows(positions,
                          range(round(line_count * self.row_share)))
        surface.draw_columns(positions,
                             range(round(line_count * self.column_share)))
        if surface.fill_alpha > 0.0:
            surface.draw_fill(positions)
        glPopMatrix()


class MorphingFront(HeadFront):
    def __init__(self, size, divisions):
        self.oval_share = 0.0
        super().__init__(size, divisions)
        self.wire_spacing = 10
        self.wire_indices = self.create_wire_indices()

    def grid_coordinates(self):
        corners = numpy.linspace(-1.0, 1.0, self.divisions + 1)
        u, v = numpy.meshgrid(corners, corners)
        oval_x, oval_z = ellipse_coordinates(u, v, self.head_half_width,
                                             self.head_half_length)
        half_size = self.size / 2.0
        square_x = u * half_size
        square_z = v * half_size
        x = square_x + (oval_x - square_x) * self.oval_share
        z = square_z + (oval_z - square_z) * self.oval_share
        return x, z


class FaceGrowth:
    def __init__(self, front):
        self.front = front
        self.full_dome_height = front.dome_height
        self.full_heights = {feature: feature.height
                             for feature in front.features}
        self.groups = [front.eyes, front.nose, front.lips,
                       front.cheeks, front.chin]

    def apply(self, dome_share, group_shares):
        self.front.dome_height = self.full_dome_height * dome_share
        for features, share in zip(self.groups, group_shares):
            for feature in features:
                feature.height = self.full_heights[feature] * share
        self.front.build()


class DemoHead(HeadWithSunglasses):
    def __init__(self, pose):
        self.pose = pose
        super().__init__()
        self.back.divisions = 20
        self.visible = False
        self.show_back = False
        self.show_eyes = False
        self.show_ears = False
        self.show_hair = False
        self.show_sunglasses = False
        self.full_back_depth = self.back.back_depth
        self.full_iris_degrees = self.eyeballs[0].iris_degrees
        self.full_pupil_degrees = self.eyeballs[0].pupil_degrees
        self.growth = FaceGrowth(self.front)
        self.set_back_depth(0.0)
        self.set_eye_colors(0.0, 0.0)
        for ear in self.ears:
            ear.size = 0.01
        self.haircut.visible_count = 0

    def create_front(self):
        return MorphingFront(4.0, 200)

    def prepare_hair(self):
        for hair in self.haircut.hairs:
            hair.draw()

    def set_back_depth(self, share):
        depth = self.full_back_depth * share
        if depth != self.back.back_depth:
            self.back.back_depth = depth
            self.back.invalidate()

    def set_eye_colors(self, iris_share, pupil_share):
        iris = self.full_iris_degrees * iris_share
        pupil = self.full_pupil_degrees * pupil_share
        for eyeball in self.eyeballs:
            if (eyeball.iris_degrees, eyeball.pupil_degrees) != (iris,
                                                                 pupil):
                eyeball.iris_degrees = iris
                eyeball.pupil_degrees = pupil
                eyeball.invalidate()

    def eye_targets(self):
        return [self.pose.transform_point(self.eye_center(socket))
                for socket in self.sockets]

    def eye_world_radius(self):
        return self.eye_radius * self.pose.scale

    def draw(self):
        if not self.visible:
            return
        glPushMatrix()
        self.pose.apply()
        glEnable(GL_NORMALIZE)
        self.draw_parts()
        glDisable(GL_NORMALIZE)
        glPopMatrix()
