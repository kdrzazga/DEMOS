import math
import random
from OpenGL.GL import *


class Snowflake:
    def __init__(self, bounds, random_generator, dome=None):
        self.min_x, self.max_x, self.min_z, self.max_z, self.ground_y, self.ceiling_y = bounds
        self.random_generator = random_generator
        self.dome = dome
        self.size = random_generator.uniform(0.10, 0.24)
        self.fall_speed = random_generator.uniform(1.6, 3.4)
        self.sway_amplitude = random_generator.uniform(0.2, 0.8)
        self.sway_speed = random_generator.uniform(0.5, 1.5)
        self.sway_phase = random_generator.uniform(0.0, math.tau)
        self.spin_speed = random_generator.uniform(-90.0, 90.0)
        self.spin = random_generator.uniform(0.0, 360.0)
        self.base_x = 0.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.age = 0.0
        self._reset(random_generator.uniform(self.ground_y, self.ceiling_y))

    def _reset(self, start_y):
        self.base_x = self.random_generator.uniform(self.min_x, self.max_x)
        self.z = self.random_generator.uniform(self.min_z, self.max_z)
        self.y = start_y
        self.age = self.random_generator.uniform(0.0, math.tau)
        self.x = self.base_x

    def update(self, dt):
        self.age += dt
        self.y -= self.fall_speed * dt
        self.x = self.base_x + math.sin(self.age * self.sway_speed + self.sway_phase) * self.sway_amplitude
        self.spin += self.spin_speed * dt
        if self.y < self.ground_y or self._blocked_by_dome():
            self._reset(self.ceiling_y)

    def _blocked_by_dome(self):
        if self.dome is None:
            return False
        center_x, center_z, radius, base_y = self.dome
        offset_x = self.x - center_x
        offset_z = self.z - center_z
        distance_squared = offset_x * offset_x + offset_z * offset_z
        if distance_squared >= radius * radius:
            return False
        return self.y <= base_y + math.sqrt(radius * radius - distance_squared)


class Snow:
    def __init__(self, count, bounds, seed=99, dome=None):
        self.random_generator = random.Random(seed)
        self.bounds = bounds
        self.flake_color = (0.98, 0.99, 1.0)
        self.flakes = [Snowflake(bounds, self.random_generator, dome) for _ in range(count)]
        self.display_list = self._build_flake_display_list()

    def _build_flake_display_list(self):
        arms = 6
        arm_length = 1.0
        segments = []
        for arm_index in range(arms):
            angle = math.tau * arm_index / arms
            direction = (math.cos(angle), math.sin(angle))
            tip = (direction[0] * arm_length, direction[1] * arm_length)
            segments.append(((0.0, 0.0), tip))
            for branch_position in (0.45, 0.72):
                base = (direction[0] * arm_length * branch_position, direction[1] * arm_length * branch_position)
                branch_length = arm_length * 0.26 * (1.0 - branch_position * 0.4)
                for branch_sign in (-1.0, 1.0):
                    branch_angle = angle + branch_sign * math.radians(60.0)
                    branch_tip = (base[0] + math.cos(branch_angle) * branch_length,
                                  base[1] + math.sin(branch_angle) * branch_length)
                    segments.append((base, branch_tip))

        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glBegin(GL_LINES)
        for (start_x, start_y), (end_x, end_y) in segments:
            glVertex3f(start_x, start_y, 0.0)
            glVertex3f(end_x, end_y, 0.0)
        glEnd()
        glEndList()
        return display_list

    def update(self, dt):
        for flake in self.flakes:
            flake.update(dt)

    def _billboard_matrix(self):
        view = glGetFloatv(GL_MODELVIEW_MATRIX)
        return (view[0][0], view[1][0], view[2][0], 0.0,
                view[0][1], view[1][1], view[2][1], 0.0,
                view[0][2], view[1][2], view[2][2], 0.0,
                0.0, 0.0, 0.0, 1.0)

    def draw(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(1.6)
        glColor3f(*self.flake_color)
        billboard = self._billboard_matrix()
        for flake in self.flakes:
            glPushMatrix()
            glTranslatef(flake.x, flake.y, flake.z)
            glMultMatrixf(billboard)
            glScalef(flake.size, flake.size, flake.size)
            glRotatef(flake.spin, 0.0, 0.0, 1.0)
            glCallList(self.display_list)
            glPopMatrix()
        glDisable(GL_LINE_SMOOTH)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
