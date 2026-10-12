import math

from OpenGL.GL import *


class Flag:
    def __init__(self, base, direction, pole_length=2.3, cloth_start=0.75, cloth_drop=0.9, phase=0.0,
                 columns=10, rows=4):
        length = math.sqrt(sum(component * component for component in direction))
        self.base = base
        self.direction = tuple(component / length for component in direction)
        self.pole_length = pole_length
        self.cloth_start = cloth_start
        self.cloth_drop = cloth_drop
        self.phase = phase
        self.columns = columns
        self.rows = rows
        self.white = (0.97, 0.97, 0.96)
        self.red = (0.86, 0.08, 0.17)
        self.pole_color = (0.86, 0.86, 0.84)
        side_x, side_z = -self.direction[2], self.direction[0]
        side_length = math.hypot(side_x, side_z) or 1.0
        self.side = (side_x / side_length, 0.0, side_z / side_length)

    def point_on_pole(self, distance):
        return tuple(self.base[axis] + self.direction[axis] * distance for axis in range(3))

    def draw_pole(self, shapes):
        tip = self.point_on_pole(self.pole_length)
        shapes.beam(self.base, tip, 0.06, self.pole_color)
        shapes.sphere(tip[0], tip[1], tip[2], 0.07, self.pole_color, slices=8, stacks=6)

    def draw_cloth(self, elapsed):
        glNormal3f(*self.side)
        for row in range(self.rows):
            glColor3f(*(self.white if row < self.rows // 2 else self.red))
            glBegin(GL_QUAD_STRIP)
            for column in range(self.columns + 1):
                along = column / self.columns
                for drop in (row / self.rows, (row + 1) / self.rows):
                    glVertex3f(*self._cloth_point(along, drop, elapsed))
            glEnd()

    def _cloth_point(self, along, drop, elapsed):
        anchor = self.point_on_pole(self.cloth_start + (self.pole_length - self.cloth_start - 0.08) * along)
        wave = 0.14 * (along + drop * 0.5) * math.sin(elapsed * 3.1 + self.phase - along * 5.0 - drop * 1.3)
        return (anchor[0] + self.side[0] * wave,
                anchor[1] - self.cloth_drop * drop,
                anchor[2] + self.side[2] * wave)
