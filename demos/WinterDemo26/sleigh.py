import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Sleigh:
    def __init__(self, x, y, z, size=1.0, facing=0.0, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.facing = facing
        self.random_generator = random.Random(seed)

        self.body_color = (0.38, 0.045, 0.085)
        self.gold_color = (0.88, 0.68, 0.15)
        self.seat_color = (0.46, 0.30, 0.18)
        self.stud_color = (0.32, 0.20, 0.12)

        self.section_exponent = 0.65
        self.sections = ((-1.22, 0.88, 0.26, 0.58),
                         (-1.05, 0.66, 0.38, 0.54),
                         (-0.80, 0.50, 0.45, 0.46),
                         (-0.35, 0.44, 0.47, 0.40),
                         (0.25, 0.43, 0.47, 0.37),
                         (0.70, 0.47, 0.44, 0.34),
                         (1.02, 0.58, 0.37, 0.30),
                         (1.22, 0.76, 0.26, 0.23),
                         (1.32, 0.92, 0.14, 0.14))
        self.runner_path = ((-0.20, -1.20), (-0.22, -0.95), (-0.22, -0.40), (-0.22, 0.30),
                            (-0.22, 0.85), (-0.18, 1.10), (-0.06, 1.32), (0.14, 1.45),
                            (0.34, 1.42), (0.46, 1.25), (0.44, 1.06))
        self.runner_offset = 0.40
        self.seat_offset = (0.0, 0.60, -0.30)

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.display_list = self._compile()

    def seat_position(self):
        angle = math.radians(self.facing)
        local_x = self.seat_offset[0] * self.size
        local_y = self.seat_offset[1] * self.size
        local_z = self.seat_offset[2] * self.size
        return (self.x + local_x * math.cos(angle) + local_z * math.sin(angle),
                self.y + local_y,
                self.z - local_x * math.sin(angle) + local_z * math.cos(angle))

    def _section_point(self, angle, half_width, half_height):
        cos_value = math.cos(angle)
        sin_value = math.sin(angle)
        return (math.copysign(abs(cos_value) ** self.section_exponent, cos_value) * half_width,
                math.copysign(abs(sin_value) ** self.section_exponent, sin_value) * half_height)

    def _section_normal(self, angle):
        cos_value = math.cos(angle)
        sin_value = math.sin(angle)
        return (math.copysign(abs(cos_value) ** self.section_exponent, cos_value),
                math.copysign(abs(sin_value) ** self.section_exponent, sin_value))

    def _draw_hull(self):
        steps = 26
        glColor3f(*self.body_color)
        for index in range(len(self.sections) - 1):
            back_z, back_y, back_width, back_height = self.sections[index]
            front_z, front_y, front_width, front_height = self.sections[index + 1]
            glBegin(GL_QUAD_STRIP)
            for step in range(steps + 1):
                angle = math.tau * step / steps
                normal_x, normal_y = self._section_normal(angle)
                glNormal3f(normal_x, normal_y, 0.0)
                front_x, front_offset = self._section_point(angle, front_width, front_height)
                glVertex3f(front_x, front_y + front_offset, front_z)
                back_x, back_offset = self._section_point(angle, back_width, back_height)
                glVertex3f(back_x, back_y + back_offset, back_z)
            glEnd()

        for section, facing_z in ((self.sections[0], -1.0), (self.sections[-1], 1.0)):
            center_z, center_y, half_width, half_height = section
            glBegin(GL_TRIANGLE_FAN)
            glNormal3f(0.0, 0.0, facing_z)
            glVertex3f(0.0, center_y, center_z)
            for step in range(steps + 1):
                angle = math.tau * step * facing_z / steps
                point_x, point_y = self._section_point(angle, half_width, half_height)
                glVertex3f(point_x, center_y + point_y, center_z)
            glEnd()

    def _sweep_tube(self, path, radius, sides):
        count = len(path)
        frames = []
        for index in range(count):
            previous = path[max(0, index - 1)]
            following = path[min(count - 1, index + 1)]
            tangent_y = following[0] - previous[0]
            tangent_z = following[1] - previous[1]
            length = math.hypot(tangent_y, tangent_z)
            if length == 0.0:
                tangent_y, tangent_z, length = 0.0, 1.0, 1.0
            frames.append((path[index][0], path[index][1], -tangent_z / length, tangent_y / length))
        for index in range(count - 1):
            glBegin(GL_QUAD_STRIP)
            for step in range(sides + 1):
                angle = math.tau * step / sides
                across = math.cos(angle)
                along = math.sin(angle)
                for center_y, center_z, normal_y, normal_z in (frames[index + 1], frames[index]):
                    glNormal3f(across, along * normal_y, along * normal_z)
                    glVertex3f(across * radius,
                               center_y + along * normal_y * radius,
                               center_z + along * normal_z * radius)
            glEnd()

    def _scroll_path(self):
        path = []
        steps = 22
        center_y = 1.25
        center_z = -1.45
        for step in range(steps + 1):
            fraction = step / steps
            angle = math.radians(-80.0 + fraction * 330.0)
            radius = 0.50 * (1.0 - 0.62 * fraction)
            path.append((center_y + math.sin(angle) * radius, center_z + math.cos(angle) * radius))
        return path

    def _draw_scroll(self):
        glColor3f(*self.body_color)
        self._sweep_tube(self._scroll_path(), 0.085, 10)

    def _draw_runners(self):
        glColor3f(*self.gold_color)
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * self.runner_offset, 0.0, 0.0)
            self._sweep_tube(self.runner_path, 0.055, 8)
            glPopMatrix()
            for support_z in (-0.75, 0.55):
                glPushMatrix()
                glTranslatef(side * self.runner_offset, -0.20, support_z)
                glRotatef(-90.0, 1.0, 0.0, 0.0)
                gluCylinder(self.quadric, 0.042, 0.042, 0.30, 8, 1)
                glPopMatrix()

    def _draw_trim(self):
        glColor3f(*self.gold_color)
        trim = []
        for center_z, center_y, half_width, half_height in self.sections:
            trim.append((center_y + half_height * 0.92, center_z))
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * 0.40, 0.0, 0.0)
            self._sweep_tube(trim, 0.035, 8)
            glPopMatrix()

    def _draw_seat(self):
        glColor3f(*self.seat_color)
        glPushMatrix()
        glTranslatef(0.0, 0.80, -0.28)
        glScalef(1.08, 0.26, 1.20)
        gluSphere(self.quadric, 0.38, 16, 12)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, 1.02, -0.92)
        glRotatef(-14.0, 1.0, 0.0, 0.0)
        glScalef(0.98, 1.05, 0.26)
        gluSphere(self.quadric, 0.40, 16, 12)
        glPopMatrix()

        glColor3f(*self.stud_color)
        glPushMatrix()
        glTranslatef(0.0, 1.05, -0.80)
        gluSphere(self.quadric, 0.035, 8, 6)
        glPopMatrix()

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_hull()
        self._draw_scroll()
        self._draw_trim()
        self._draw_seat()
        self._draw_runners()
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.display_list)
        glPopMatrix()
