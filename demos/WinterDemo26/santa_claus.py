import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class SantaClaus:
    def __init__(self, x, y, z, size=1.0, facing=0.0, wave=True, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.facing = facing
        self.wave = wave
        self.random_generator = random.Random(seed)
        self.time = 0.0
        self.wave_speed = self.random_generator.uniform(2.6, 3.4)
        self.wave_phase = self.random_generator.uniform(0.0, math.tau)
        self.wave_swing = 15.0
        self.wave_base_angle = -38.0

        self.suit_color = (0.72, 0.11, 0.12)
        self.fur_color = (0.82, 0.82, 0.85)
        self.beard_color = (0.80, 0.81, 0.84)
        self.skin_color = (0.80, 0.62, 0.50)
        self.blush_color = (0.80, 0.48, 0.42)
        self.eye_color = (0.05, 0.05, 0.06)
        self.spark_color = (0.92, 0.92, 0.94)
        self.belt_color = (0.22, 0.14, 0.10)
        self.buckle_color = (0.85, 0.68, 0.16)
        self.boot_color = (0.18, 0.13, 0.11)

        self.torso_radius = 0.44
        self.torso_center_y = 0.58
        self.head_radius = 0.30
        self.head_center_y = 1.16
        self.shoulder = (0.34, 0.92, 0.0)
        self.arm_length = 0.34
        self.arm_radius = 0.105
        self.cuff_length = 0.09
        self.mitten_radius = 0.14
        self.hat_radius = self.head_radius * 1.0
        self.hat_height = self.head_radius * 1.85
        self.hat_bend = self.head_radius * 1.45

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.body_list = self._compile_body()
        self.arm_list = self._compile_arm()

    def update(self, dt):
        self.time += dt

    def _aim(self, direction):
        length = math.sqrt(direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2)
        unit = (direction[0] / length, direction[1] / length, direction[2] / length)
        glRotatef(math.degrees(math.atan2(unit[0], unit[2])), 0.0, 1.0, 0.0)
        glRotatef(math.degrees(-math.asin(max(-1.0, min(1.0, unit[1])))), 1.0, 0.0, 0.0)

    def _blob(self, radius, scale):
        glPushMatrix()
        glScalef(*scale)
        gluSphere(self.quadric, radius, 14, 12)
        glPopMatrix()

    def _draw_arm(self):
        glPushMatrix()
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        glColor3f(*self.suit_color)
        gluCylinder(self.quadric, self.arm_radius, self.arm_radius * 0.94, self.arm_length, 12, 2)
        glTranslatef(0.0, 0.0, self.arm_length)
        glColor3f(*self.fur_color)
        gluCylinder(self.quadric, self.arm_radius * 1.22, self.arm_radius * 1.22, self.cuff_length, 12, 1)
        glPopMatrix()
        glColor3f(*self.suit_color)
        glPushMatrix()
        glTranslatef(0.0, self.arm_length + self.cuff_length + self.mitten_radius * 0.55, 0.0)
        self._blob(self.mitten_radius, (1.0, 1.12, 0.88))
        glPopMatrix()

    def _draw_torso(self):
        glColor3f(*self.suit_color)
        glPushMatrix()
        glTranslatef(0.0, self.torso_center_y, 0.0)
        self._blob(self.torso_radius, (1.0, 1.02, 0.86))
        glPopMatrix()

        glColor3f(*self.fur_color)
        glPushMatrix()
        glTranslatef(0.0, self.torso_center_y - self.torso_radius * 0.78, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluCylinder(self.quadric, self.torso_radius * 0.82, self.torso_radius * 0.88, self.torso_radius * 0.26, 18, 1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, self.torso_center_y - self.torso_radius * 0.10, self.torso_radius * 0.80)
        self._blob(self.torso_radius * 0.30, (0.42, 1.75, 0.35))
        glPopMatrix()

        glColor3f(*self.belt_color)
        glPushMatrix()
        glTranslatef(0.0, self.torso_center_y - self.torso_radius * 0.40, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluCylinder(self.quadric, self.torso_radius * 0.98, self.torso_radius * 0.98, self.torso_radius * 0.30, 18, 1)
        glPopMatrix()

        glColor3f(*self.buckle_color)
        glPushMatrix()
        glTranslatef(0.0, self.torso_center_y - self.torso_radius * 0.28, self.torso_radius * 0.86)
        self._blob(self.torso_radius * 0.20, (1.15, 1.0, 0.35))
        glPopMatrix()

    def _draw_legs(self):
        thigh_length = 0.30
        shin_length = 0.26
        leg_radius = 0.095
        for side in (-1.0, 1.0):
            hip = (side * 0.19, 0.26, 0.10)
            glColor3f(*self.suit_color)
            glPushMatrix()
            glTranslatef(*hip)
            self._aim((side * 0.12, -0.30, 1.0))
            gluCylinder(self.quadric, leg_radius, leg_radius * 0.92, thigh_length, 10, 1)
            glPopMatrix()

            knee = (hip[0] + side * 0.035, hip[1] - 0.088, hip[2] + 0.29)
            glPushMatrix()
            glTranslatef(*knee)
            self._aim((0.0, -1.0, 0.16))
            gluCylinder(self.quadric, leg_radius * 0.92, leg_radius * 0.86, shin_length, 10, 1)
            glPopMatrix()

            glColor3f(*self.boot_color)
            glPushMatrix()
            glTranslatef(knee[0], knee[1] - shin_length + 0.02, knee[2] + 0.08)
            self._blob(0.125, (1.0, 0.78, 1.35))
            glPopMatrix()

    def _draw_face(self):
        glColor3f(*self.skin_color)
        gluSphere(self.quadric, self.head_radius, 18, 16)

        glColor3f(*self.beard_color)
        glPushMatrix()
        glTranslatef(0.0, -self.head_radius * 0.62, self.head_radius * 0.30)
        self._blob(self.head_radius * 0.86, (1.06, 1.10, 0.92))
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, -self.head_radius * 1.35, self.head_radius * 0.24)
        self._blob(self.head_radius * 0.46, (0.90, 0.95, 0.85))
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, -self.head_radius * 0.30, self.head_radius * 0.78)
        self._blob(self.head_radius * 0.30, (1.75, 0.72, 0.85))
        glPopMatrix()

        glColor3f(*self.blush_color)
        glPushMatrix()
        glTranslatef(0.0, -self.head_radius * 0.10, self.head_radius * 0.92)
        self._blob(self.head_radius * 0.20, (1.0, 0.95, 0.95))
        glPopMatrix()

        for side in (-1.0, 1.0):
            glColor3f(*self.eye_color)
            glPushMatrix()
            glTranslatef(side * self.head_radius * 0.38, self.head_radius * 0.20, self.head_radius * 0.80)
            self._blob(self.head_radius * 0.15, (0.85, 1.0, 0.7))
            glPopMatrix()

            glColor3f(*self.spark_color)
            glPushMatrix()
            glTranslatef(side * self.head_radius * 0.33, self.head_radius * 0.28, self.head_radius * 0.90)
            gluSphere(self.quadric, self.head_radius * 0.05, 8, 6)
            glPopMatrix()

            glColor3f(*self.beard_color)
            glPushMatrix()
            glTranslatef(side * self.head_radius * 0.40, self.head_radius * 0.46, self.head_radius * 0.74)
            self._blob(self.head_radius * 0.17, (1.25, 0.45, 0.6))
            glPopMatrix()

    def _hat_center(self, fraction):
        lean = fraction * fraction
        return (self.hat_bend * 0.28 * lean,
                self.head_radius * 0.56 + self.hat_height * fraction * (1.0 - 0.20 * lean),
                -self.hat_bend * lean)

    def _draw_hat(self):
        rings = 12
        segments = 14
        glColor3f(*self.suit_color)
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
        glTranslatef(0.0, self.head_radius * 0.42, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluCylinder(self.quadric, self.hat_radius * 1.12, self.hat_radius * 1.12, self.head_radius * 0.36, 18, 1)
        glPopMatrix()

        tip = self._hat_center(1.0)
        glPushMatrix()
        glTranslatef(tip[0], tip[1], tip[2])
        gluSphere(self.quadric, self.hat_radius * 0.40, 12, 10)
        glPopMatrix()

    def _compile_body(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_torso()
        self._draw_legs()

        glPushMatrix()
        glTranslatef(-self.shoulder[0], self.shoulder[1], self.shoulder[2])
        glRotatef(128.0, 0.0, 0.0, 1.0)
        glRotatef(-28.0, 1.0, 0.0, 0.0)
        self._draw_arm()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, self.head_center_y, 0.0)
        self._draw_face()
        self._draw_hat()
        glPopMatrix()
        glEndList()
        return display_list

    def _compile_arm(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_arm()
        glEndList()
        return display_list

    def _wave_angle(self):
        if not self.wave:
            return self.wave_base_angle
        return self.wave_base_angle + math.sin(self.time * self.wave_speed + self.wave_phase) * self.wave_swing

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.body_list)
        glPushMatrix()
        glTranslatef(self.shoulder[0], self.shoulder[1], self.shoulder[2])
        glRotatef(self._wave_angle(), 0.0, 0.0, 1.0)
        glRotatef(-14.0, 1.0, 0.0, 0.0)
        glCallList(self.arm_list)
        glPopMatrix()
        glPopMatrix()
