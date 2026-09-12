import math
from OpenGL.GL import *


class GroundPatch:
    def __init__(self, center_x, center_z, radius, height_provider,
                 rings=18, segments=48, height_offset=0.04):
        self.center_x = center_x
        self.center_z = center_z
        self.radius = radius
        self.height_provider = height_provider
        self.rings = rings
        self.segments = segments
        self.height_offset = height_offset
        self.cyan_inner = (0.85, 1.0, 1.0)
        self.cyan_outer = (0.95, 1.0, 1.0)
        self.gray_inner = (0.9, 0.9, 0.9)
        self.gray_outer = (0.97, 0.97, 0.97)
        self.display_list = self._compile()

    def _color(self, radial_fraction):
        cyan = tuple(self.cyan_inner[channel] + (self.cyan_outer[channel] - self.cyan_inner[channel]) * radial_fraction
                     for channel in range(3))
        gray = tuple(self.gray_inner[channel] + (self.gray_outer[channel] - self.gray_inner[channel]) * radial_fraction
                     for channel in range(3))
        return tuple((cyan[channel] + gray[channel]) * 0.5 for channel in range(3))

    def _point(self, radial_fraction, angle):
        distance = self.radius * radial_fraction
        x = self.center_x + math.cos(angle) * distance
        z = self.center_z + math.sin(angle) * distance
        y = self.height_provider.surface_height(x, z) + self.height_offset
        return x, y, z

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glDisable(GL_LIGHTING)
        for ring in range(self.rings):
            inner_fraction = ring / self.rings
            outer_fraction = (ring + 1) / self.rings
            glBegin(GL_QUAD_STRIP)
            for segment in range(self.segments + 1):
                angle = 2.0 * math.pi * segment / self.segments
                glColor3f(*self._color(outer_fraction))
                glVertex3f(*self._point(outer_fraction, angle))
                glColor3f(*self._color(inner_fraction))
                glVertex3f(*self._point(inner_fraction, angle))
            glEnd()
        glEnable(GL_LIGHTING)
        glEndList()
        return display_list

    def draw(self):
        glCallList(self.display_list)
