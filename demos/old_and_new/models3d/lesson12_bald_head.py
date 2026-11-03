import math

import numpy
from OpenGL.GL import *

from .lesson8_mesh import MeshSurface
from .lesson11_talking_face import LipShapes, Speech, TalkingFace


def ellipse_coordinates(u, v, half_width, half_length):
    x = u * numpy.sqrt(1.0 - v * v / 2.0)
    z = v * numpy.sqrt(1.0 - u * u / 2.0)
    return x * half_width, z * half_length


class HeadFront(TalkingFace):
    def grid_coordinates(self):
        corners = numpy.linspace(-1.0, 1.0, self.divisions + 1)
        u, v = numpy.meshgrid(corners, corners)
        return ellipse_coordinates(u, v, self.head_half_width,
                                   self.head_half_length)

    def build(self):
        x, z = self.grid_coordinates()
        y = self.height(x, z)
        points = numpy.stack((x, y, z), axis=-1)
        along_x = numpy.gradient(points, axis=1)
        along_z = numpy.gradient(points, axis=0)
        normals = numpy.cross(along_z, along_x)
        lengths = numpy.linalg.norm(normals, axis=-1,
                                    keepdims=True)
        self.positions = points.reshape(-1, 3).astype(
            numpy.float32)
        self.normals = (normals / lengths).reshape(-1, 3).astype(
            numpy.float32)
        self.colors = self.mouth_colors()


class BackOfHead(MeshSurface):
    def __init__(self, front, divisions):
        super().__init__(front.size, divisions)
        self.front = front
        self.base_height = front.base_height
        self.half_width = front.head_half_width
        self.half_length = front.head_half_length
        self.line_color = front.line_color
        self.skin_color = front.skin_color
        self.back_depth = 1.9
        self.display_list = None

    def bulge(self, x, z):
        across = (x / self.half_width) ** 2
        along = (z / self.half_length) ** 2
        return math.sqrt(max(1.0 - across - along, 0.0))

    def height(self, x, z):
        return self.base_height - self.back_depth * self.bulge(x, z)

    def grid_positions(self):
        positions = []
        for row in range(self.divisions + 1):
            v = 2.0 * row / self.divisions - 1.0
            row_positions = []
            for column in range(self.divisions + 1):
                u = 2.0 * column / self.divisions - 1.0
                x, z = ellipse_coordinates(u, v, self.half_width,
                                           self.half_length)
                row_positions.append((x, self.height(x, z), z))
            positions.append(row_positions)
        return positions

    def normal_at(self, position):
        x, _y, z = position
        normal = (self.back_depth * x / self.half_width ** 2,
                  -self.bulge(x, z),
                  self.back_depth * z / self.half_length ** 2)
        length = math.sqrt(sum(axis * axis for axis in normal))
        if length == 0.0:
            return (0.0, -1.0, 0.0)
        return tuple(axis / length for axis in normal)

    def draw_skin(self, positions):
        glColor3f(*self.skin_color)
        for row in range(self.divisions):
            glBegin(GL_TRIANGLE_STRIP)
            for column in range(self.divisions + 1):
                for strip_row in (row + 1, row):
                    position = positions[strip_row][column]
                    glNormal3f(*self.normal_at(position))
                    glVertex3f(*position)
            glEnd()

    def compile(self):
        positions = self.grid_positions()
        every_line = range(self.divisions + 1)
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self.front.enable_lighting()
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        self.draw_skin(positions)
        glDisable(GL_POLYGON_OFFSET_FILL)
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        self.draw_rows(positions, every_line)
        self.draw_columns(positions, every_line)
        glEndList()

    def invalidate(self):
        if self.display_list is not None:
            glDeleteLists(self.display_list, 1)
            self.display_list = None

    def draw(self):
        if self.display_list is None:
            self.compile()
        glCallList(self.display_list)


class BaldHead:
    def __init__(self):
        self.lift = 0.2
        self.scale = 0.7
        self.show_back = True
        self.front = self.create_front()
        self.front.base_height = 0.0
        self.front.light_position = (4.0, 3.0, -2.0, 0.0)
        self.front.build()
        self.back = BackOfHead(self.front, 40)

    def create_front(self):
        return HeadFront(4.0, 200)

    def draw_parts(self):
        self.front.draw()
        if self.show_back:
            self.back.draw()

    def draw(self):
        glPushMatrix()
        glTranslatef(0.0, self.lift, 0.0)
        glScalef(self.scale, self.scale, self.scale)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        glEnable(GL_NORMALIZE)
        self.draw_parts()
        glDisable(GL_NORMALIZE)
        glPopMatrix()


class BaldHeadScene:
    def __init__(self):
        self.head = self.create_head()
        self.words = [
            ("condition", ["con", "di", "tion"]),
            ("exited", ["ex", "i", "ed"]),
            ("deter", ["de", "ter"]),
            ("openly", ["o", "e", "ly"]),
            ("intercom", ["in", "ter", "com"]),
            ("happier", ["a", "y", "er"])]
        self.speech = Speech(LipShapes(), self.words)

    def create_head(self):
        return BaldHead()

    def update(self, seconds):
        self.speech.update(seconds)
        self.head.front.shape_lips(*self.speech.lip_pose())
        self.head.front.build()

    def draw(self):
        self.head.draw()

#    window.camera_tilt = 12.0
