import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class ChristmasRobin:
    def __init__(self, x, z, ground_height, size=1.0, hue=0.5, facing=0.0, head_bob=True, seed=0):
        self.x = x
        self.z = z
        self.ground_height = ground_height
        self.size = size
        self.hue = max(0.0, min(1.0, hue))
        self.facing = facing
        self.head_bob = head_bob
        self.random_generator = random.Random(seed)
        self.time = 0.0
        self.bob_phase = self.random_generator.uniform(0.0, math.tau)
        self.bob_speed = self.random_generator.uniform(1.7, 2.7)
        self.bob_amount = 0.035

        self.deep_orange = (0.78, 0.22, 0.06)
        self.golden_orange = (0.90, 0.54, 0.12)
        self.belly_color = (0.70, 0.66, 0.58)
        self.back_color = (0.32, 0.24, 0.17)
        self.wing_color = (0.26, 0.19, 0.13)
        self.beak_color = (0.20, 0.17, 0.14)
        self.eye_color = (0.04, 0.04, 0.05)
        self.leg_color = (0.35, 0.24, 0.18)
        self.hat_color = (0.72, 0.09, 0.10)
        self.fur_color = (0.80, 0.80, 0.82)

        self.body_radius = 0.30
        self.head_radius = 0.19
        self.body_center_y = self.body_radius * 1.15
        self.head_center = (0.0, self.body_center_y + self.body_radius * 0.72, self.body_radius * 0.30)
        self.hat_radius = self.head_radius * 0.96
        self.hat_height = self.head_radius * 1.85
        self.hat_bend = self.head_radius * 1.55

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.body_list = self._compile_body()
        self.head_list = self._compile_head()

    def update(self, dt):
        self.time += dt

    def _mix(self, start, end, factor):
        factor = max(0.0, min(1.0, factor))
        return tuple(start[channel] + (end[channel] - start[channel]) * factor for channel in range(3))

    def _smoothstep(self, low, high, value):
        span = max(0.0, min(1.0, (value - low) / (high - low)))
        return span * span * (3.0 - 2.0 * span)

    def _breast_color(self):
        return self._mix(self.deep_orange, self.golden_orange, self.hue)

    def _body_color(self, normal_x, normal_y, normal_z):
        base = self._mix(self.back_color, self.belly_color, self._smoothstep(-0.25, 0.55, normal_z))
        band = max(0.0, 1.0 - abs(normal_y - 0.25) / 0.60)
        breast = max(0.0, normal_z) * band * band
        return self._mix(base, self._breast_color(), breast * 1.6)

    def _head_color(self, normal_x, normal_y, normal_z):
        crown = self._smoothstep(0.15, 0.85, normal_y)
        front = self._smoothstep(-0.50, 0.25, normal_z)
        base = self._mix(self.back_color, self.belly_color, front * 0.35)
        return self._mix(base, self._breast_color(), front * (1.0 - crown) * 1.6)

    def _sphere_surface(self, radius, rings, segments, colorer):
        glBegin(GL_QUADS)
        for ring in range(rings):
            latitude_low = math.pi * ring / rings - math.pi / 2.0
            latitude_high = math.pi * (ring + 1) / rings - math.pi / 2.0
            for segment in range(segments):
                longitude_low = math.tau * segment / segments
                longitude_high = math.tau * (segment + 1) / segments
                for latitude, longitude in ((latitude_low, longitude_low),
                                            (latitude_low, longitude_high),
                                            (latitude_high, longitude_high),
                                            (latitude_high, longitude_low)):
                    normal_x = math.cos(latitude) * math.sin(longitude)
                    normal_y = math.sin(latitude)
                    normal_z = math.cos(latitude) * math.cos(longitude)
                    glColor3f(*colorer(normal_x, normal_y, normal_z))
                    glNormal3f(normal_x, normal_y, normal_z)
                    glVertex3f(normal_x * radius, normal_y * radius, normal_z * radius)
        glEnd()

    def _draw_wings(self):
        glColor3f(*self.wing_color)
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * self.body_radius * 0.80, self.body_radius * 0.05, -self.body_radius * 0.05)
            glRotatef(side * -12.0, 0.0, 1.0, 0.0)
            glScalef(0.30, 0.85, 1.05)
            gluSphere(self.quadric, self.body_radius * 0.72, 12, 10)
            glPopMatrix()

    def _draw_tail(self):
        glColor3f(*self.wing_color)
        glPushMatrix()
        glTranslatef(0.0, -self.body_radius * 0.05, -self.body_radius * 0.80)
        glRotatef(160.0, 1.0, 0.0, 0.0)
        glScalef(1.0, 0.35, 1.0)
        gluCylinder(self.quadric, self.body_radius * 0.42, self.body_radius * 0.12, self.body_radius * 1.5, 10, 2)
        glPopMatrix()

    def _draw_legs(self):
        glColor3f(*self.leg_color)
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * self.body_radius * 0.30, 0.0, self.body_radius * 0.12)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(self.quadric, self.body_radius * 0.075, self.body_radius * 0.065, self.body_radius * 0.42, 8, 1)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(side * self.body_radius * 0.30, self.body_radius * 0.045, self.body_radius * 0.22)
            glScalef(1.0, 0.45, 1.6)
            gluSphere(self.quadric, self.body_radius * 0.13, 8, 6)
            glPopMatrix()

    def _draw_beak(self):
        glColor3f(*self.beak_color)
        glPushMatrix()
        glTranslatef(0.0, -self.head_radius * 0.05, self.head_radius * 0.80)
        glRotatef(-6.0, 1.0, 0.0, 0.0)
        glScalef(1.0, 0.62, 1.0)
        gluCylinder(self.quadric, self.head_radius * 0.26, 0.0, self.head_radius * 0.85, 10, 2)
        glPopMatrix()

    def _draw_eyes(self):
        glColor3f(*self.eye_color)
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * self.head_radius * 0.52, self.head_radius * 0.20, self.head_radius * 0.66)
            gluSphere(self.quadric, self.head_radius * 0.17, 10, 8)
            glPopMatrix()

    def _hat_center(self, fraction):
        lean = fraction * fraction
        return (self.hat_bend * lean,
                self.head_radius * 0.62 + self.hat_height * fraction * (1.0 - 0.22 * lean),
                -self.hat_height * 0.16 * lean)

    def _draw_hat(self):
        rings = 12
        segments = 14
        glColor3f(*self.hat_color)
        for ring in range(rings):
            low = ring / rings
            high = (ring + 1) / rings
            center_low = self._hat_center(low)
            center_high = self._hat_center(high)
            radius_low = self.hat_radius * (1.0 - low) ** 0.85
            radius_high = self.hat_radius * (1.0 - high) ** 0.85
            glBegin(GL_QUAD_STRIP)
            for segment in range(segments + 1):
                angle = math.tau * segment / segments
                around_x = math.cos(angle)
                around_z = math.sin(angle)
                glNormal3f(around_x, 0.35, around_z)
                glVertex3f(center_high[0] + around_x * radius_high, center_high[1], center_high[2] + around_z * radius_high)
                glVertex3f(center_low[0] + around_x * radius_low, center_low[1], center_low[2] + around_z * radius_low)
            glEnd()

        glColor3f(*self.fur_color)
        glPushMatrix()
        glTranslatef(0.0, self.head_radius * 0.50, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluCylinder(self.quadric, self.hat_radius * 1.14, self.hat_radius * 1.14, self.head_radius * 0.34, 16, 1)
        glPopMatrix()

        tip = self._hat_center(1.0)
        glPushMatrix()
        glTranslatef(tip[0], tip[1], tip[2])
        gluSphere(self.quadric, self.hat_radius * 0.42, 12, 10)
        glPopMatrix()

    def _compile_body(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glPushMatrix()
        glTranslatef(0.0, self.body_center_y, 0.0)
        glPushMatrix()
        glScalef(0.92, 1.0, 0.95)
        self._sphere_surface(self.body_radius, 16, 22, self._body_color)
        glPopMatrix()
        self._draw_wings()
        self._draw_tail()
        glPopMatrix()
        self._draw_legs()
        glEndList()
        return display_list

    def _compile_head(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._sphere_surface(self.head_radius, 14, 20, self._head_color)
        self._draw_beak()
        self._draw_eyes()
        self._draw_hat()
        glEndList()
        return display_list

    def _bob_offset(self):
        if not self.head_bob:
            return 0.0
        return math.sin(self.time * self.bob_speed + self.bob_phase) * self.bob_amount

    def draw(self):
        bob = self._bob_offset()
        glPushMatrix()
        glTranslatef(self.x, self.ground_height, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.body_list)
        glPushMatrix()
        glTranslatef(self.head_center[0], self.head_center[1] + bob, self.head_center[2] + bob * 0.55)
        glRotatef(bob * 90.0, 1.0, 0.0, 0.0)
        glCallList(self.head_list)
        glPopMatrix()
        glPopMatrix()
