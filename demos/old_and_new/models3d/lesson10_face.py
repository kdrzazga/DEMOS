import numpy
from OpenGL.GL import *

from .lesson8_mesh import MeshSurface


class FaceFeature:
    def __init__(self, x, z, width_x, width_z, height):
        self.center_x = x
        self.center_z = z
        self.width_x = width_x
        self.width_z = width_z
        self.height = height

    def heights(self, x, z):
        spread_x = (x - self.center_x) / self.width_x
        spread_z = (z - self.center_z) / self.width_z
        return self.height * numpy.exp(-spread_x ** 2 - spread_z ** 2)


class FaceSurface(MeshSurface):
    def __init__(self, size, divisions):
        super().__init__(size, divisions)
        self.head_half_width = 1.15
        self.head_half_length = 1.55
        self.dome_height = 0.55
        self.wire_spacing = 5
        self.line_color = (0.45, 0.3, 0.25)
        self.skin_color = (0.92, 0.74, 0.62)
        self.light_position = (2.0, 5.0, 3.0, 0.0)
        self.ambient_light = (0.3, 0.3, 0.35, 1.0)
        self.eyes = [FaceFeature(-0.42, -0.3, 0.16, 0.11, -0.22),
                     FaceFeature(0.42, -0.3, 0.16, 0.11, -0.22),
                     FaceFeature(-0.42, -0.52, 0.28, 0.07, 0.06),
                     FaceFeature(0.42, -0.52, 0.28, 0.07, 0.06)]
        self.nose = [FaceFeature(0.0, -0.05, 0.08, 0.3, 0.12),
                     FaceFeature(0.0, 0.22, 0.11, 0.1, 0.28),
                     FaceFeature(-0.12, 0.25, 0.07, 0.06, 0.08),
                     FaceFeature(0.12, 0.25, 0.07, 0.06, 0.08)]
        self.lips = [FaceFeature(0.0, 0.55, 0.25, 0.06, 0.1),
                     FaceFeature(0.0, 0.7, 0.22, 0.07, 0.09),
                     FaceFeature(0.0, 0.62, 0.28, 0.025, -0.05)]
        self.cheeks = [FaceFeature(-0.55, 0.2, 0.25, 0.25, 0.06),
                       FaceFeature(0.55, 0.2, 0.25, 0.25, 0.06)]
        self.chin = [FaceFeature(0.0, 1.1, 0.28, 0.14, 0.15),
                     FaceFeature(0.0, 0.86, 0.22, 0.05, -0.04)]
        self.triangle_indices = self.create_triangle_indices()
        self.wire_indices = self.create_wire_indices()
        self.build()

    @property
    def features(self):
        return (self.eyes + self.nose + self.lips
                + self.cheeks + self.chin)

    def dome(self, x, z):
        across = (x / self.head_half_width) ** 2
        along = (z / self.head_half_length) ** 2
        inside = numpy.clip(1.0 - across - along, 0.0, None)
        return self.dome_height * numpy.sqrt(inside)

    def height(self, x, z):
        shape = self.dome(x, z)
        for feature in self.features:
            shape = shape + feature.heights(x, z)
        return self.base_height + shape

    def build(self):
        half_size = self.size / 2.0
        axis = numpy.linspace(-half_size, half_size,
                              self.divisions + 1)
        x, z = numpy.meshgrid(axis, axis)
        y = self.height(x, z)
        step = self.size / self.divisions
        slope_z, slope_x = numpy.gradient(y, step)
        normals = numpy.stack((-slope_x, numpy.ones_like(y),
                               -slope_z), axis=-1)
        lengths = numpy.linalg.norm(normals, axis=-1,
                                    keepdims=True)
        positions = numpy.stack((x, y, z), axis=-1)
        self.positions = positions.reshape(-1, 3).astype(
            numpy.float32)
        self.normals = (normals / lengths).reshape(-1, 3).astype(
            numpy.float32)

    def create_triangle_indices(self):
        row_length = self.divisions + 1
        cells = numpy.arange(self.divisions)
        top_left = cells[:, None] * row_length + cells[None, :]
        top_left = top_left.ravel()
        top_right = top_left + 1
        bottom_left = top_left + row_length
        bottom_right = bottom_left + 1
        corners = (top_left, bottom_left, top_right,
                   top_right, bottom_left, bottom_right)
        triangles = numpy.stack(corners, axis=1)
        return triangles.ravel().astype(numpy.uint32)

    def create_wire_indices(self):
        row_length = self.divisions + 1
        cells = numpy.arange(self.divisions)
        wires = numpy.arange(0, row_length, self.wire_spacing)
        row_starts = wires[:, None] * row_length + cells[None, :]
        column_starts = cells[:, None] * row_length + wires[None, :]
        row_starts = row_starts.ravel()
        column_starts = column_starts.ravel()
        segments = numpy.concatenate((
            numpy.stack((row_starts, row_starts + 1), axis=1),
            numpy.stack((column_starts, column_starts + row_length),
                        axis=1)))
        return segments.ravel().astype(numpy.uint32)

    def enable_lighting(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, self.ambient_light)

    def draw_skin(self):
        self.enable_lighting()
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        glEnableClientState(GL_NORMAL_ARRAY)
        glNormalPointer(GL_FLOAT, 0, self.normals)
        glColor3f(*self.skin_color)
        glDrawElements(GL_TRIANGLES, self.triangle_indices.size,
                       GL_UNSIGNED_INT, self.triangle_indices)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisable(GL_POLYGON_OFFSET_FILL)
        glDisable(GL_LIGHTING)

    def draw_wires(self):
        glLineWidth(1.0)
        glColor3f(*self.line_color)
        glDrawElements(GL_LINES, self.wire_indices.size,
                       GL_UNSIGNED_INT, self.wire_indices)

    def draw(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        self.draw_skin()
        self.draw_wires()
        glDisableClientState(GL_VERTEX_ARRAY)


class FaceScene:
    def __init__(self):
        self.face = FaceSurface(4.0, 200)

    def draw(self):
        self.face.draw()

