import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Reindeer:
    def __init__(self, x, y, z, size=1.0, facing=0.0, gallop=True, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.facing = facing
        self.gallop = gallop
        self.random_generator = random.Random(seed)
        self.time = 0.0
        self.gallop_speed = self.random_generator.uniform(3.0, 3.8)
        self.gallop_swing = 22.0

        self.coat_color = (0.68, 0.44, 0.22)
        self.belly_color = (0.78, 0.57, 0.34)
        self.antler_color = (0.34, 0.21, 0.12)
        self.muzzle_color = (0.44, 0.27, 0.15)
        self.nose_color = (0.28, 0.17, 0.10)
        self.ear_color = (0.82, 0.55, 0.52)
        self.eye_color = (0.05, 0.05, 0.06)
        self.spark_color = (0.92, 0.92, 0.94)
        self.harness_color = (0.30, 0.19, 0.12)
        self.bell_color = (0.88, 0.68, 0.15)
        self.hoof_color = (0.24, 0.15, 0.09)

        self.head_center = (0.0, 1.80, 0.95)
        self.harness_offset = (0.0, 1.14, 0.46)
        self.legs = ((0.26, 0.98, 0.44, 16.0, 0.0),
                     (-0.26, 0.98, 0.44, -14.0, math.pi),
                     (0.26, 0.95, -0.48, -20.0, math.pi * 0.7),
                     (-0.26, 0.95, -0.48, 18.0, math.pi * 1.7))

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.body_list = self._compile_body()
        self.leg_list = self._compile_leg()

    def update(self, dt):
        self.time += dt

    def harness_position(self):
        angle = math.radians(self.facing)
        local_x = self.harness_offset[0] * self.size
        local_y = self.harness_offset[1] * self.size
        local_z = self.harness_offset[2] * self.size
        return (self.x + local_x * math.cos(angle) + local_z * math.sin(angle),
                self.y + local_y,
                self.z - local_x * math.sin(angle) + local_z * math.cos(angle))

    def _unit(self, direction):
        length = math.sqrt(direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2)
        return (direction[0] / length, direction[1] / length, direction[2] / length)

    def _aim(self, direction):
        unit = self._unit(direction)
        glRotatef(math.degrees(math.atan2(unit[0], unit[2])), 0.0, 1.0, 0.0)
        glRotatef(math.degrees(-math.asin(max(-1.0, min(1.0, unit[1])))), 1.0, 0.0, 0.0)

    def _branch(self, start, direction, length, radius_start, radius_end):
        glPushMatrix()
        glTranslatef(*start)
        self._aim(direction)
        gluCylinder(self.quadric, radius_start, radius_end, length, 8, 1)
        glPopMatrix()
        unit = self._unit(direction)
        return (start[0] + unit[0] * length,
                start[1] + unit[1] * length,
                start[2] + unit[2] * length)

    def _blob(self, center, radius, scale):
        glPushMatrix()
        glTranslatef(*center)
        glScalef(*scale)
        gluSphere(self.quadric, radius, 14, 12)
        glPopMatrix()

    def _draw_body(self):
        glColor3f(*self.coat_color)
        self._blob((0.0, 1.06, 0.34), 0.44, (0.88, 0.95, 1.05))
        self._blob((0.0, 1.02, -0.46), 0.42, (0.90, 0.96, 1.02))
        glColor3f(*self.belly_color)
        self._blob((0.0, 0.86, -0.06), 0.34, (0.80, 0.55, 1.45))
        glColor3f(*self.coat_color)
        self._blob((0.0, 1.16, -0.88), 0.13, (1.0, 1.0, 1.0))

    def _draw_neck(self):
        glColor3f(*self.coat_color)
        glPushMatrix()
        glTranslatef(0.0, 1.28, 0.58)
        self._aim((0.0, 0.52, 0.37))
        gluCylinder(self.quadric, 0.215, 0.175, 0.62, 14, 2)
        glPopMatrix()

    def _draw_head(self):
        glColor3f(*self.coat_color)
        self._blob(self.head_center, 0.24, (0.88, 0.92, 1.15))

        glColor3f(*self.muzzle_color)
        muzzle_start = (self.head_center[0], self.head_center[1] - 0.04, self.head_center[2] + 0.14)
        muzzle_end = self._branch(muzzle_start, (0.0, -0.30, 1.0), 0.30, 0.145, 0.105)
        glColor3f(*self.nose_color)
        self._blob(muzzle_end, 0.105, (1.0, 0.85, 0.85))

        for side in (-1.0, 1.0):
            glColor3f(*self.coat_color)
            self._blob((side * 0.21, self.head_center[1] + 0.11, self.head_center[2] - 0.10),
                       0.13, (1.45, 0.55, 0.80))
            glColor3f(*self.ear_color)
            self._blob((side * 0.25, self.head_center[1] + 0.10, self.head_center[2] - 0.06),
                       0.085, (1.35, 0.45, 0.70))

            glColor3f(*self.eye_color)
            self._blob((side * 0.175, self.head_center[1] + 0.06, self.head_center[2] + 0.12),
                       0.052, (0.85, 1.0, 0.8))
            glColor3f(*self.spark_color)
            self._blob((side * 0.155, self.head_center[1] + 0.10, self.head_center[2] + 0.16),
                       0.018, (1.0, 1.0, 1.0))

    def _draw_antlers(self):
        glColor3f(*self.antler_color)
        for side in (-1.0, 1.0):
            base = (side * 0.12, self.head_center[1] + 0.17, self.head_center[2] - 0.08)
            first = self._branch(base, (side * 0.35, 0.92, -0.22), 0.28, 0.048, 0.038)
            self._branch(first, (side * 0.22, 0.72, 0.66), 0.21, 0.032, 0.020)
            second = self._branch(first, (side * 0.52, 0.80, -0.32), 0.26, 0.038, 0.030)
            self._branch(second, (side * 0.78, 0.52, 0.34), 0.19, 0.026, 0.016)
            third = self._branch(second, (side * 0.30, 0.92, 0.16), 0.23, 0.030, 0.022)
            self._branch(third, (side * 0.62, 0.70, -0.28), 0.15, 0.022, 0.014)

    def _draw_harness(self):
        glColor3f(*self.harness_color)
        glPushMatrix()
        glTranslatef(0.0, 1.06, 0.40)
        gluCylinder(self.quadric, 0.455, 0.455, 0.15, 18, 1)
        glPopMatrix()
        glColor3f(*self.bell_color)
        self._blob((0.0, 0.66, 0.50), 0.075, (1.0, 1.0, 1.0))

    def _compile_leg(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glColor3f(*self.coat_color)
        knee = self._branch((0.0, 0.0, 0.0), (0.0, -1.0, 0.14), 0.44, 0.115, 0.092)
        hoof = self._branch(knee, (0.0, -1.0, -0.18), 0.40, 0.088, 0.066)
        glColor3f(*self.hoof_color)
        self._blob(hoof, 0.082, (1.0, 0.85, 1.25))
        glEndList()
        return display_list

    def _compile_body(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_body()
        self._draw_neck()
        self._draw_head()
        self._draw_antlers()
        self._draw_harness()
        glEndList()
        return display_list

    def _leg_angle(self, base_angle, phase):
        if not self.gallop:
            return base_angle
        return base_angle + math.sin(self.time * self.gallop_speed + phase) * self.gallop_swing

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.body_list)
        for hip_x, hip_y, hip_z, base_angle, phase in self.legs:
            glPushMatrix()
            glTranslatef(hip_x, hip_y, hip_z)
            glRotatef(self._leg_angle(base_angle, phase), 1.0, 0.0, 0.0)
            glCallList(self.leg_list)
            glPopMatrix()
        glPopMatrix()
