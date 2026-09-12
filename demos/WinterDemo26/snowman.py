import math
from OpenGL.GL import *
from OpenGL.GLU import *


class Snowman:
    def __init__(self, x, z, ground_height, scale=1.0):
        self.x = x
        self.z = z
        self.ground_height = ground_height
        self.scale = scale
        self.snow_color = (0.97, 0.98, 1.0)
        self.coal_color = (0.06, 0.06, 0.08)
        self.nose_color = (0.95, 0.5, 0.12)
        self.stick_color = (0.32, 0.20, 0.09)
        self.hat_color = (0.09, 0.09, 0.12)
        self.bottom_radius = 1.0 * scale
        self.middle_radius = 0.72 * scale
        self.head_radius = 0.5 * scale
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.display_list = self._compile()

    def _sphere(self, radius):
        gluSphere(self.quadric, radius, 24, 24)

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)

        bottom_y = self.bottom_radius * 0.95
        middle_y = bottom_y + (self.bottom_radius + self.middle_radius) * 0.72
        head_y = middle_y + (self.middle_radius + self.head_radius) * 0.72

        glColor3f(*self.snow_color)
        for center_y, radius in ((bottom_y, self.bottom_radius),
                                 (middle_y, self.middle_radius),
                                 (head_y, self.head_radius)):
            glPushMatrix()
            glTranslatef(0.0, center_y, 0.0)
            self._sphere(radius)
            glPopMatrix()

        self._draw_face(head_y)
        self._draw_buttons(middle_y)
        self._draw_arms(middle_y)
        self._draw_hat(head_y)

        glEndList()
        return display_list

    def _draw_face(self, head_y):
        glColor3f(*self.coal_color)
        for sign in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(sign * self.head_radius * 0.35, head_y + self.head_radius * 0.22, self.head_radius * 0.85)
            self._sphere(self.head_radius * 0.09)
            glPopMatrix()

        smile_points = 5
        for index in range(smile_points):
            angle = math.pi * (0.25 + 0.5 * index / (smile_points - 1))
            point_x = math.cos(angle) * self.head_radius * 0.42
            point_y = head_y - self.head_radius * 0.16 - math.sin(angle) * self.head_radius * 0.14
            glPushMatrix()
            glTranslatef(point_x, point_y, self.head_radius * 0.82)
            self._sphere(self.head_radius * 0.05)
            glPopMatrix()

        glColor3f(*self.nose_color)
        glPushMatrix()
        glTranslatef(0.0, head_y, self.head_radius * 0.8)
        gluCylinder(self.quadric, self.head_radius * 0.12, 0.0, self.head_radius * 0.95, 12, 2)
        glPopMatrix()

    def _draw_buttons(self, middle_y):
        glColor3f(*self.coal_color)
        for index in range(3):
            glPushMatrix()
            glTranslatef(0.0, middle_y + self.middle_radius * (0.45 - index * 0.45), self.middle_radius * 0.92)
            self._sphere(self.middle_radius * 0.08)
            glPopMatrix()

    def _draw_arms(self, middle_y):
        glColor3f(*self.stick_color)
        arm_length = self.middle_radius * 1.7
        for sign in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(sign * self.middle_radius * 0.7, middle_y + self.middle_radius * 0.2, 0.0)
            glRotatef(sign * 90.0, 0.0, 1.0, 0.0)
            glRotatef(-28.0, 1.0, 0.0, 0.0)
            gluCylinder(self.quadric, self.middle_radius * 0.055, self.middle_radius * 0.02, arm_length, 8, 2)
            glPopMatrix()

    def _draw_hat(self, head_y):
        glColor3f(*self.hat_color)
        brim_y = head_y + self.head_radius * 0.72
        glPushMatrix()
        glTranslatef(0.0, brim_y, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluDisk(self.quadric, 0.0, self.head_radius * 0.95, 20, 1)
        gluCylinder(self.quadric, self.head_radius * 0.6, self.head_radius * 0.56, self.head_radius * 1.1, 20, 2)
        glTranslatef(0.0, 0.0, self.head_radius * 1.1)
        gluDisk(self.quadric, 0.0, self.head_radius * 0.6, 20, 1)
        glPopMatrix()

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.ground_height, self.z)
        glCallList(self.display_list)
        glPopMatrix()
