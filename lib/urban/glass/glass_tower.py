import random

from OpenGL.GL import (
    GL_COMPILE,
    GL_ENABLE_BIT,
    GL_LIGHTING,
    glCallList,
    glColor3f,
    glDisable,
    glEndList,
    glGenLists,
    glNewList,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glTranslatef,
)
from OpenGL.GLU import gluSphere

from lib.urban.glass.glass_facade import GlassFacade
from lib.urban.shapes import Shapes
from lib.vector3 import Vector3


class TowerTier:

    def __init__(self, width, depth, height):
        self.width = width
        self.depth = depth
        self.height = height


class GlassVolume:

    def __init__(self, center_x, base, center_z, tier, style, randomness):
        self.style = style
        self.left = center_x - tier.width / 2.0
        self.right = center_x + tier.width / 2.0
        self.back = center_z - tier.depth / 2.0
        self.front = center_z + tier.depth / 2.0
        self.base = base
        self.top = base + tier.height
        rows = max(1, round(tier.height / style.floor_height))
        width_columns = max(1, round(tier.width / style.column_width))
        depth_columns = max(1, round(tier.depth / style.column_width))
        rise = Vector3(0.0, tier.height, 0.0)
        self.facades = [
            GlassFacade(Vector3(self.left, base, self.front), Vector3(tier.width, 0.0, 0.0), rise,
                        width_columns, rows, style, randomness),
            GlassFacade(Vector3(self.right, base, self.front), Vector3(0.0, 0.0, -tier.depth), rise,
                        depth_columns, rows, style, randomness),
            GlassFacade(Vector3(self.right, base, self.back), Vector3(-tier.width, 0.0, 0.0), rise,
                        width_columns, rows, style, randomness),
            GlassFacade(Vector3(self.left, base, self.back), Vector3(0.0, 0.0, tier.depth), rise,
                        depth_columns, rows, style, randomness),
        ]

    def draw_structure(self, shapes):
        inset = self.style.core_inset
        overhang = self.style.slab_overhang
        shapes.box(self.left + inset, self.base, self.back + inset,
                   self.right - inset, self.top, self.front - inset, self.style.core_color)
        shapes.box(self.left - overhang, self.top, self.back - overhang,
                   self.right + overhang, self.top + self.style.slab_thickness, self.front + overhang,
                   self.style.slab_color)


class RoofBeacon:

    def __init__(self, position):
        self.position = position
        self.radius = 0.22
        self.blink_period = 1.6
        self.flash_length = 0.3
        self.flash_color = (1.0, 0.12, 0.08)
        self.idle_color = (0.25, 0.03, 0.02)
        self.clock = 0.0

    def update(self, seconds):
        self.clock = (self.clock + seconds) % self.blink_period

    def is_flashing(self):
        return self.clock < self.flash_length

    def draw(self, shapes):
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        glColor3f(*(self.flash_color if self.is_flashing() else self.idle_color))
        glPushMatrix()
        glTranslatef(*self.position)
        gluSphere(shapes.quadric, self.radius, 10, 8)
        glPopMatrix()
        glPopAttrib()


class GlassSkyscraper:

    def __init__(self, x, z, tiers, style, seed):
        self.x = x
        self.z = z
        self.style = style
        randomness = random.Random(seed)
        self.volumes = []
        base = 0.0
        for tier in tiers:
            self.volumes.append(GlassVolume(x, base, z, tier, style, randomness))
            base += tier.height + style.slab_thickness
        self.roof_height = base
        self.spire_height = 4.0
        self.spire_width = 0.18
        self.spire_color = (0.4, 0.42, 0.46)
        self.beacon = RoofBeacon(Vector3(x, self.roof_height + self.spire_height, z))
        self.shapes = None
        self.structure_list = None

    def reflectors(self):
        return [facade for volume in self.volumes for facade in volume.facades]

    def set_blur(self, blur):
        for facade in self.reflectors():
            facade.set_blur(blur)

    @property
    def blur(self):
        return self.volumes[0].facades[0].blur

    def update(self, seconds):
        self.beacon.update(seconds)

    def draw(self):
        if self.structure_list is None:
            self.shapes = Shapes()
            self.structure_list = glGenLists(1)
            glNewList(self.structure_list, GL_COMPILE)
            self._draw_structure()
            glEndList()
        glCallList(self.structure_list)
        self.beacon.draw(self.shapes)

    def _draw_structure(self):
        for volume in self.volumes:
            volume.draw_structure(self.shapes)
        half_spire = self.spire_width / 2.0
        self.shapes.box(self.x - half_spire, self.roof_height, self.z - half_spire,
                        self.x + half_spire, self.roof_height + self.spire_height, self.z + half_spire,
                        self.spire_color)
