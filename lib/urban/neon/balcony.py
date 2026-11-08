from OpenGL.GL import (
    GL_AMBIENT_AND_DIFFUSE,
    GL_COLOR_MATERIAL,
    GL_COMPILE,
    GL_ENABLE_BIT,
    GL_FRONT_AND_BACK,
    GL_LIGHTING,
    GL_QUADS,
    glBegin,
    glCallList,
    glColor3f,
    glColorMaterial,
    glDisable,
    glEnable,
    glEnd,
    glEndList,
    glGenLists,
    glNewList,
    glNormal3f,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluSphere

from lib.vector3 import Vector3


class Balcony:

    def __init__(self, palette, left, right, rail_z, floor_height):
        self.palette = palette
        self.left = left
        self.right = right
        self.rail_z = rail_z
        self.floor_height = floor_height
        self.floor_depth = 8.0
        self.slab_thickness = 0.35
        self.rail_height = 1.05
        self.rail_thickness = 0.06
        self.baluster_spacing = 0.3
        self.baluster_width = 0.025
        self.floor_color = (0.12, 0.11, 0.1)
        self.shape_list = None

    def prepare(self, shapes):
        self.shape_list = glGenLists(1)
        glNewList(self.shape_list, GL_COMPILE)
        self._emit(shapes)
        glEndList()

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glCallList(self.shape_list)
        glPopAttrib()

    def _emit(self, shapes):
        floor = self.floor_height
        shapes.box(self.left, floor - self.slab_thickness, self.rail_z - 0.15,
                   self.right, floor, self.rail_z + self.floor_depth, self.floor_color)
        half_rail = self.rail_thickness / 2.0
        top = floor + self.rail_height
        metal = self.palette.metal
        shapes.box(self.left, top - self.rail_thickness, self.rail_z - half_rail,
                   self.right, top, self.rail_z + half_rail, metal)
        shapes.box(self.left, floor + 0.08, self.rail_z - half_rail,
                   self.right, floor + 0.12, self.rail_z + half_rail, metal)
        x = self.left
        half_baluster = self.baluster_width / 2.0
        while x <= self.right:
            shapes.box(x - half_baluster, floor, self.rail_z - half_baluster,
                       x + half_baluster, top, self.rail_z + half_baluster, metal)
            x += self.baluster_spacing


class StreetCorner:

    def __init__(self, palette, wall_x, balcony_height, rail_z):
        self.palette = palette
        self.wall_x = wall_x
        self.balcony_height = balcony_height
        self.rail_z = rail_z
        self.awning_color = (0.32, 0.22, 0.13)
        self.box_color = (0.18, 0.19, 0.18)
        self.pipe_color = (0.1, 0.1, 0.1)
        self.lantern_color = (0.9, 0.08, 0.06)
        self.lantern_radius = 0.38
        self.signal_color = (0.05, 0.05, 0.05)
        self.lantern_center = Vector3(wall_x + 2.6, balcony_height + 1.9, rail_z - 1.2)
        self.pole_base = Vector3(wall_x + 0.7, 0.0, rail_z - 1.4)
        self.pole_height = balcony_height + 3.2
        self.shape_list = None
        self.lantern_list = None

    def glow_arrays(self):
        return ([tuple(self.lantern_center)], [1.4], [(1.0, 0.15, 0.1, 0.75)])

    def prepare(self, shapes):
        self.shape_list = glGenLists(1)
        glNewList(self.shape_list, GL_COMPILE)
        self._emit(shapes)
        glEndList()
        self.lantern_list = glGenLists(1)
        glNewList(self.lantern_list, GL_COMPILE)
        glColor3f(*self.lantern_color)
        glPushMatrix()
        glTranslatef(*self.lantern_center)
        gluSphere(shapes.quadric, self.lantern_radius, 18, 14)
        glPopMatrix()
        glEndList()

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glCallList(self.shape_list)
        glDisable(GL_LIGHTING)
        glCallList(self.lantern_list)
        glPopAttrib()

    def _emit(self, shapes):
        wall = self.wall_x
        floor = self.balcony_height
        self._awning(wall, floor - 1.2, self.rail_z - 1.0, self.rail_z - 9.0, 4.4)
        self._awning(wall, floor - 9.5, self.rail_z - 3.0, self.rail_z - 14.0, 3.6)
        for box_z, box_y in ((self.rail_z - 10.0, floor + 4.0), (self.rail_z - 16.0, floor - 4.5),
                             (self.rail_z - 21.0, floor + 9.0), (self.rail_z - 6.0, floor - 6.0)):
            shapes.box(wall, box_y, box_z, wall + 0.8, box_y + 0.9, box_z + 1.3, self.box_color)
        for pipe_z in (self.rail_z - 0.4, self.rail_z - 12.5):
            shapes.box(wall + 0.05, 0.0, pipe_z, wall + 0.2, floor + 14.0, pipe_z + 0.15, self.pipe_color)
        base = self.pole_base
        shapes.box(base.x - 0.1, 0.0, base.z - 0.1, base.x + 0.1, self.pole_height, base.z + 0.1, self.palette.metal)
        shapes.box(base.x - 0.25, self.pole_height - 1.6, base.z - 0.2, base.x + 0.25, self.pole_height - 0.2,
                   base.z + 0.2, self.signal_color)

    def _awning(self, wall, height, near_z, far_z, reach):
        drop = 1.1
        glColor3f(*self.awning_color)
        glNormal3f(0.24, 0.97, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(wall, height, near_z)
        glVertex3f(wall + reach, height - drop, near_z)
        glVertex3f(wall + reach, height - drop, far_z)
        glVertex3f(wall, height, far_z)
        glEnd()
