import math

import numpy
from OpenGL.GL import *


class Material:

    def __init__(self, specular, shininess):
        self.specular = specular
        self.shininess = shininess

    def apply(self):
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (self.specular, self.specular, self.specular, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.shininess)


class DisplayListShape:

    def __init__(self):
        self.display_list = None

    def emit(self):
        raise NotImplementedError

    def render(self):
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            self.emit()
            glEndList()
        glCallList(self.display_list)

    def destroy(self):
        if self.display_list is not None:
            glDeleteLists(self.display_list, 1)
            self.display_list = None


class QuadPainter:

    @staticmethod
    def quad(corners, texcoords=None):
        a, b, c, d = (numpy.asarray(corner, dtype=float) for corner in corners)
        normal = numpy.cross(c - a, d - b)
        glNormal3f(*(normal / numpy.linalg.norm(normal)))
        for index, corner in enumerate((a, b, c, d)):
            if texcoords is not None:
                glTexCoord2f(*texcoords[index])
            glVertex3f(*corner)


class ChamferedBlock(DisplayListShape):

    def __init__(self, width, height, depth, chamfer):
        super().__init__()
        self.width = width
        self.height = height
        self.depth = depth
        self.chamfer = chamfer

    def emit(self):
        half_width = self.width / 2.0
        half_height = self.height / 2.0
        shoulder = self.depth - self.chamfer
        outline = ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))
        outer = [(sx * half_width, sy * half_height) for sx, sy in outline]
        inner = [(sx * (half_width - self.chamfer), sy * (half_height - self.chamfer)) for sx, sy in outline]
        glBegin(GL_QUADS)
        QuadPainter.quad([(x, y, self.depth) for x, y in inner])
        for corner in range(4):
            following = (corner + 1) % 4
            QuadPainter.quad([(*outer[corner], shoulder), (*outer[following], shoulder),
                              (*inner[following], self.depth), (*inner[corner], self.depth)])
            QuadPainter.quad([(*outer[corner], 0.0), (*outer[following], 0.0),
                              (*outer[following], shoulder), (*outer[corner], shoulder)])
        glEnd()


class DishedCap(DisplayListShape):

    def __init__(self, radius, curvature):
        super().__init__()
        self.radius = radius
        self.curvature = curvature
        self.rings = 6
        self.segments = 32

    def vertex(self, ring_radius, angle):
        x = ring_radius * math.cos(angle)
        y = ring_radius * math.sin(angle)
        tilt = self.curvature / self.radius
        normal = numpy.array((-x * tilt, -y * tilt, 1.0))
        glNormal3f(*(normal / numpy.linalg.norm(normal)))
        glVertex3f(x, y, 0.0)

    def emit(self):
        for ring in range(self.rings):
            inner_radius = self.radius * ring / self.rings
            outer_radius = self.radius * (ring + 1) / self.rings
            glBegin(GL_QUAD_STRIP)
            for segment in range(self.segments + 1):
                angle = 2.0 * math.pi * segment / self.segments
                self.vertex(outer_radius, angle)
                self.vertex(inner_radius, angle)
            glEnd()


class Superellipse:

    def __init__(self, half_width, half_height, exponent):
        self.half_width = half_width
        self.half_height = half_height
        self.exponent = exponent

    def outline(self, segments):
        angles = numpy.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
        power = 2.0 / self.exponent
        cosines = numpy.cos(angles)
        sines = numpy.sin(angles)
        x = self.half_width * numpy.sign(cosines) * numpy.abs(cosines) ** power
        y = self.half_height * numpy.sign(sines) * numpy.abs(sines) ** power
        return numpy.stack((x, y), axis=1)


class SurfaceGrid(DisplayListShape):

    def __init__(self):
        super().__init__()
        self.positions = None
        self.texcoords = None

    def estimate_normals(self):
        along = numpy.roll(self.positions, -1, axis=1) - numpy.roll(self.positions, 1, axis=1)
        across = numpy.gradient(self.positions, axis=0)
        normals = numpy.cross(across, along)
        lengths = numpy.linalg.norm(normals, axis=2, keepdims=True)
        return numpy.where(lengths > 1e-9, normals / numpy.maximum(lengths, 1e-12), numpy.array((0.0, 0.0, 1.0)))

    def emit(self):
        normals = self.estimate_normals()
        rows, segments = self.positions.shape[:2]
        for row in range(rows - 1):
            glBegin(GL_QUAD_STRIP)
            for column in range(segments + 1):
                wrapped = column % segments
                for current in (row + 1, row):
                    glNormal3f(*normals[current, wrapped])
                    if self.texcoords is not None:
                        glTexCoord2f(*self.texcoords[current, wrapped])
                    glVertex3f(*self.positions[current, wrapped])
            glEnd()


class CrtGlass(SurfaceGrid):

    def __init__(self, center, outline, rim_height, bulge):
        super().__init__()
        self.rings = 24
        self.segments = 160
        edge = outline.outline(self.segments)
        scales = numpy.linspace(0.0, 1.0, self.rings + 1)[:, None, None]
        flat = edge[None, :, :] * scales
        heights = numpy.broadcast_to(rim_height + bulge * (1.0 - scales[..., 0] ** 2), flat.shape[:2])
        self.positions = numpy.dstack((flat[..., 0] + center[0], flat[..., 1] + center[1], heights))
        self.texcoords = numpy.dstack((0.5 + flat[..., 0] / (2.0 * outline.half_width),
                                       0.5 - flat[..., 1] / (2.0 * outline.half_height)))


class CrtBezel(SurfaceGrid):

    def __init__(self, center, inner, outer, profile):
        super().__init__()
        self.segments = 160
        inner_edge = inner.outline(self.segments)
        outer_edge = outer.outline(self.segments)
        rows = []
        for blend, height in profile:
            ring = inner_edge * (1.0 - blend) + outer_edge * blend
            rows.append(numpy.column_stack((ring[:, 0] + center[0], ring[:, 1] + center[1],
                                            numpy.full(self.segments, height))))
        self.positions = numpy.stack(rows)


class WoodenBox(DisplayListShape):

    def __init__(self, half_width, half_height, depth, wood):
        super().__init__()
        self.half_width = half_width
        self.half_height = half_height
        self.depth = depth
        self.wood = wood

    def mapped(self, corners, horizontal, vertical):
        return [(horizontal(corner) / self.wood.world_width, vertical(corner) / self.wood.world_height)
                for corner in corners]

    def emit(self):
        w, h, d = self.half_width, self.half_height, self.depth
        across = lambda corner: corner[0] + w
        upward = lambda corner: corner[1] + h
        backward = lambda corner: -corner[2]
        faces = (([(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)], across, upward),
                 ([(w, -h, 0), (w, -h, -d), (w, h, -d), (w, h, 0)], backward, upward),
                 ([(-w, -h, -d), (-w, -h, 0), (-w, h, 0), (-w, h, -d)], backward, upward),
                 ([(-w, h, 0), (w, h, 0), (w, h, -d), (-w, h, -d)], backward, across),
                 ([(-w, -h, -d), (w, -h, -d), (w, -h, 0), (-w, -h, 0)], backward, across))
        glBegin(GL_QUADS)
        for corners, horizontal, vertical in faces:
            QuadPainter.quad(corners, self.mapped(corners, horizontal, vertical))
        glEnd()


class RearHood(DisplayListShape):

    def __init__(self, half_width, half_height, depth, hood_depth, hood_center, hood_shrink):
        super().__init__()
        self.half_width = half_width
        self.half_height = half_height
        self.depth = depth
        self.hood_depth = hood_depth
        self.hood_center = hood_center
        self.hood_shrink = hood_shrink
        self.back_color = (0.11, 0.085, 0.065)
        self.hood_color = (0.07, 0.06, 0.055)
        self.base_margin = 0.06

    def emit(self):
        w, h, d = self.half_width, self.half_height, self.depth
        center_x, center_y = self.hood_center
        base_w = w - self.base_margin
        base_h = h - self.base_margin
        end_w = w * self.hood_shrink[0]
        end_h = h * self.hood_shrink[1]
        end_z = -d - self.hood_depth
        outline = ((1.0, -1.0), (-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))
        base = [(sx * base_w, sy * base_h, -d) for sx, sy in outline]
        tip = [(center_x + sx * end_w, center_y + sy * end_h, end_z) for sx, sy in outline]
        glBegin(GL_QUADS)
        glColor3f(*self.back_color)
        QuadPainter.quad([(sx * w, sy * h, -d) for sx, sy in outline])
        glColor3f(*self.hood_color)
        for corner in range(4):
            following = (corner + 1) % 4
            QuadPainter.quad([base[corner], base[following], tip[following], tip[corner]])
        QuadPainter.quad(tip)
        glEnd()
