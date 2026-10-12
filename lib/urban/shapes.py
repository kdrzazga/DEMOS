import math
from contextlib import contextmanager

from OpenGL.GL import *
from OpenGL.GLU import *


class Shapes:
    def __init__(self):
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)

    @contextmanager
    def frame(self, x, y, z, yaw=0.0):
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(yaw, 0.0, 1.0, 0.0)
        try:
            yield
        finally:
            glPopMatrix()

    @contextmanager
    def textured(self, texture):
        if texture is None:
            yield
            return
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture)
        try:
            yield
        finally:
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

    def box(self, x0, y0, z0, x1, y1, z1, color):
        left, right = min(x0, x1), max(x0, x1)
        bottom, top = min(y0, y1), max(y0, y1)
        back, front = min(z0, z1), max(z0, z1)
        faces = (
            ((0.0, 0.0, 1.0), ((left, bottom, front), (right, bottom, front), (right, top, front), (left, top, front))),
            ((0.0, 0.0, -1.0), ((right, bottom, back), (left, bottom, back), (left, top, back), (right, top, back))),
            ((1.0, 0.0, 0.0), ((right, bottom, front), (right, bottom, back), (right, top, back), (right, top, front))),
            ((-1.0, 0.0, 0.0), ((left, bottom, back), (left, bottom, front), (left, top, front), (left, top, back))),
            ((0.0, 1.0, 0.0), ((left, top, front), (right, top, front), (right, top, back), (left, top, back))),
            ((0.0, -1.0, 0.0), ((left, bottom, back), (right, bottom, back), (right, bottom, front), (left, bottom, front))),
        )
        glColor3f(*color)
        glBegin(GL_QUADS)
        for normal, corners in faces:
            glNormal3f(*normal)
            for corner in corners:
                glVertex3f(*corner)
        glEnd()

    def normal_of(self, first, second, third):
        ux, uy, uz = second[0] - first[0], second[1] - first[1], second[2] - first[2]
        vx, vy, vz = third[0] - first[0], third[1] - first[1], third[2] - first[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        return nx / length, ny / length, nz / length

    def upward_normal(self, points):
        nx, ny, nz = self.normal_of(points[0], points[1], points[2])
        if ny < 0.0:
            return -nx, -ny, -nz
        return nx, ny, nz

    def polygon(self, points, color, normal=None, uvs=None):
        glColor3f(*color)
        glNormal3f(*(normal or self.normal_of(points[0], points[1], points[2])))
        glBegin(GL_POLYGON)
        for index, point in enumerate(points):
            if uvs:
                glTexCoord2f(*uvs[index])
            glVertex3f(*point)
        glEnd()

    def fan(self, center, rim, normal, color):
        glColor3f(*color)
        glNormal3f(*normal)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(*center)
        for point in rim:
            glVertex3f(*point)
        glEnd()

    def strip(self, pairs, normals, color, uvs=None):
        glColor3f(*color)
        glBegin(GL_QUAD_STRIP)
        for index, (first, second) in enumerate(pairs):
            glNormal3f(*normals[index])
            if uvs:
                glTexCoord2f(*uvs[index][0])
            glVertex3f(*first)
            if uvs:
                glTexCoord2f(*uvs[index][1])
            glVertex3f(*second)
        glEnd()

    def cylinder(self, x, y, z, bottom_radius, top_radius, height, color, slices=12):
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluCylinder(self.quadric, bottom_radius, top_radius, height, slices, 1)
        glPopMatrix()

    def sphere(self, x, y, z, radius, color, scale=(1.0, 1.0, 1.0), slices=10, stacks=8):
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(*scale)
        gluSphere(self.quadric, radius, slices, stacks)
        glPopMatrix()

    def beam(self, start, end, thickness, color):
        dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 1e-6:
            return
        ux, uy, uz = dx / length, dy / length, dz / length
        glPushMatrix()
        glTranslatef(*start)
        if abs(ux) + abs(uy) > 1e-6:
            glRotatef(math.degrees(math.acos(max(-1.0, min(1.0, uz)))), -uy, ux, 0.0)
        elif uz < 0.0:
            glRotatef(180.0, 1.0, 0.0, 0.0)
        half = thickness / 2.0
        self.box(-half, -half, 0.0, half, half, length, color)
        glPopMatrix()
