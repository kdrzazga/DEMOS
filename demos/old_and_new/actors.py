import math

import numpy
from OpenGL.GL import *

from demos.old_and_new.models3d.lesson5_ball import Ball
from demos.old_and_new.models3d.lesson8_mesh import MeshSurface
from demos.old_and_new.models3d.lesson12_bald_head import (
    HeadFront, ellipse_coordinates)
from demos.old_and_new.c64_animation import C64Animation
from demos.old_and_new.models3d.lesson14_sunglasses import (
    HeadWithSunglasses, Lens)


class StageBall:
    def __init__(self, home, radius):
        self.ball = Ball(1.0, (0.95, 0.95, 0.93))
        self.home = numpy.array(home)
        self.position = numpy.array(home)
        self.full_radius = radius
        self.radius = radius
        self.size = 1.0
        self.visible = False
        self.point_share = 1.0
        self.cover_share = 1.0
        self.shaded = True
        self.point_size = 4.0
        self.bob_height = 0.08
        self.bob_speed = 2.0
        self.bob_offset = home[0]

    def bob(self, time):
        rise = self.bob_height * math.sin(self.bob_speed * time
                                          + self.bob_offset)
        self.position = self.home + (0.0, rise, 0.0)

    def glide(self, start, end, start_radius, end_radius, arc_height,
              progress):
        flight = progress * progress * (3.0 - 2.0 * progress)
        arc = arc_height * 4.0 * progress * (1.0 - progress)
        start = numpy.array(start)
        self.position = (start + (numpy.array(end) - start) * flight
                         + (0.0, arc, 0.0))
        self.radius = start_radius + (end_radius - start_radius) * flight

    def jump(self, target, target_radius, arc_height, progress):
        self.glide(self.home, target, self.full_radius, target_radius,
                   arc_height, progress)

    def draw_unfinished(self):
        ball = self.ball
        covered_strips = round(ball.stacks * self.cover_share)
        visible_rings = round((ball.stacks + 1) * self.point_share)
        first_open_ring = covered_strips + 1 if covered_strips else 0
        glDisable(GL_LIGHTING)
        glColor3f(*ball.color)
        for stack_index in range(covered_strips):
            ball.draw_strip(stack_index)
        glPointSize(self.point_size)
        glBegin(GL_POINTS)
        for stack_index in range(first_open_ring, visible_rings):
            for slice_index in range(ball.slices):
                glVertex3f(*ball.direction(slice_index, stack_index))
        glEnd()

    def draw(self):
        if not self.visible or self.size <= 0.0:
            return
        glPushMatrix()
        glTranslatef(*self.position)
        scale = self.radius * self.size
        glScalef(scale, scale, scale)
        glEnable(GL_NORMALIZE)
        if self.shaded:
            self.ball.draw()
        else:
            self.draw_unfinished()
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


class SproutingHair:
    def __init__(self, hair, growth_duration):
        self.hair = hair
        self.root = hair.control_points[0]
        self.growth_duration = growth_duration
        self.age = 0.0

    def update(self, seconds):
        self.age += seconds

    def draw(self):
        growth = min(self.age / self.growth_duration, 1.0)
        if growth <= 0.0:
            return
        glPushMatrix()
        glTranslatef(*self.root)
        glScalef(growth, growth, growth)
        glTranslatef(*(-self.root))
        self.hair.draw()
        glPopMatrix()


class BorderColoredLens(Lens):
    def __init__(self, outline, screen):
        super().__init__(outline)
        self.screen = screen

    def lens_color(self):
        return self.screen.normal_border_color

    def draw(self):
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            self.emit_shape()
            glEndList()
        glDisable(GL_LIGHTING)
        glColor3f(*self.lens_color())
        glCallList(self.display_list)
        glEnable(GL_LIGHTING)


class ScreenLens(BorderColoredLens):
    def __init__(self, outline, screen):
        super().__init__(outline, screen)
        self.screen_share = 0.0
        self.screen_height_share = 0.9
        self.screen_lift = 0.004
        self.grid = 8
        self.screen_list = None
        self.interference_lift = 0.002
        self.interference_source = None

    def lens_color(self):
        return self.screen.border_color

    def screen_point(self, column, row):
        outline = self.outline
        half_length = outline.half_length * self.screen_height_share
        half_width = half_length * self.screen.aspect
        u = column / self.grid
        v = row / self.grid
        x = (2.0 * u - 1.0) * half_width
        z = (2.0 * v - 1.0) * half_length
        reach_squared = ((x / outline.half_width) ** 2
                         + (z / outline.half_length) ** 2)
        y = self.bulge * (1.0 - reach_squared) + self.screen_lift
        return (u, v), outline.center + numpy.array((x, y, z))

    def emit_screen_vertex(self, column, row):
        texture_point, position = self.screen_point(column, row)
        glTexCoord2f(*texture_point)
        glVertex3f(*position)

    def compile_screen(self):
        self.screen_list = glGenLists(1)
        glNewList(self.screen_list, GL_COMPILE)
        for row in range(self.grid):
            glBegin(GL_TRIANGLE_STRIP)
            for column in range(self.grid + 1):
                self.emit_screen_vertex(column, row + 1)
                self.emit_screen_vertex(column, row)
            glEnd()
        glEndList()

    def draw(self):
        super().draw()
        if self.screen_share <= 0.0:
            return
        if self.screen_list is None:
            self.compile_screen()
        self.screen.refresh()
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.screen.texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 1.0, self.screen_share)
        glCallList(self.screen_list)
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        if self.interference_source is not None:
            self.draw_interference()

    def draw_interference(self):
        """Flat interference over the screen, just above the top of the bulge, pixel rows towards +z."""
        half_length = self.outline.half_length * self.screen_height_share
        half_width = half_length * self.screen.aspect
        glPushMatrix()
        glTranslatef(*self.outline.center)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        corner = (-half_width, half_length, self.bulge + self.screen_lift + self.interference_lift)
        self.interference_source.draw_interference(corner, 2.0 * half_width / self.screen.width)
        glPopMatrix()


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
        self.sprouting = False
        self.sprout_interval = 0.02
        self.sprout_growth_duration = 0.1
        self.sprout_timer = 0.0
        self.sprouts = []
        self.c64_animation = C64Animation()
        self.c64_screen = self.c64_animation.c64screen
        self.c64_screen.hold_typing()
        self.screen_lens = self.create_lenses()
        self.screen_lens.interference_source = self.c64_animation

    def create_lenses(self):
        outlines = self.sunglasses.outlines
        right_index = max(range(len(outlines)),
                          key=lambda index: outlines[index].center[0])
        lenses = [BorderColoredLens(outline, self.c64_screen)
                  for outline in outlines]
        screen_lens = ScreenLens(outlines[right_index], self.c64_screen)
        lenses[right_index] = screen_lens
        self.sunglasses.lenses = lenses
        return screen_lens

    def screen_center(self):
        middle = self.screen_lens.grid // 2
        _texture_point, center = self.screen_lens.screen_point(middle,
                                                                middle)
        return self.pose.transform_point(center)

    def screen_height(self):
        lens = self.screen_lens
        return (2.0 * lens.outline.half_length * lens.screen_height_share
                * self.pose.scale)

    def create_front(self):
        return MorphingFront(4.0, 200)

    def prepare_hair(self):
        for hair in self.haircut.hairs:
            hair.draw()

    def update_sprouts(self, real_seconds):
        if not self.sprouting:
            return
        self.sprout_timer += real_seconds
        while self.sprout_timer >= self.sprout_interval:
            self.sprout_timer -= self.sprout_interval
            self.sprouts.append(SproutingHair(
                self.haircut.grow_hair(), self.sprout_growth_duration))
        for sprout in self.sprouts:
            sprout.update(real_seconds)

    def draw_hair(self):
        super().draw_hair()
        if not self.sprouts:
            return
        self.front.enable_lighting()
        glColor3f(*self.haircut.color)
        for sprout in self.sprouts:
            sprout.draw()
        glDisable(GL_LIGHTING)

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
