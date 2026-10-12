import math
import random

from OpenGL.GL import *


class Sky:
    def __init__(self, zenith, horizon, seed=5, radius=1000.0, slices=24, stacks=8, cloud_count=34):
        self.zenith = zenith
        self.horizon = horizon
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        generator = random.Random(seed)
        self.clouds = [self._create_cloud(generator) for _ in range(cloud_count)]
        self.display_list = None

    def _create_cloud(self, generator):
        heading = generator.uniform(0.0, 2.0 * math.pi)
        distance = generator.uniform(420.0, 820.0)
        center_x = math.sin(heading) * distance
        center_z = -math.cos(heading) * distance
        altitude = generator.uniform(150.0, 320.0)
        size = generator.uniform(28.0, 60.0)
        puffs = []
        for _ in range(generator.randint(5, 9)):
            puffs.append((center_x + generator.uniform(-1.6, 1.6) * size,
                          altitude + generator.uniform(-0.2, 0.5) * size,
                          center_z + generator.uniform(-0.8, 0.8) * size,
                          size * generator.uniform(0.55, 1.0)))
        return puffs

    def _mix(self, blend):
        return tuple(self.horizon[index] + (self.zenith[index] - self.horizon[index]) * blend for index in range(3))

    def build(self, shapes):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self._draw_dome()
        self._draw_clouds(shapes)
        glEndList()

    def _draw_dome(self):
        for stack in range(self.stacks):
            low = -0.15 + (math.pi / 2.0 + 0.15) * stack / self.stacks
            high = -0.15 + (math.pi / 2.0 + 0.15) * (stack + 1) / self.stacks
            glBegin(GL_QUAD_STRIP)
            for slice_index in range(self.slices + 1):
                heading = 2.0 * math.pi * slice_index / self.slices
                for elevation in (low, high):
                    glColor3f(*self._mix(max(0.0, math.sin(elevation)) ** 0.6))
                    glVertex3f(self.radius * math.cos(elevation) * math.sin(heading),
                               self.radius * math.sin(elevation),
                               -self.radius * math.cos(elevation) * math.cos(heading))
            glEnd()

    def _draw_clouds(self, shapes):
        for puffs in self.clouds:
            for x, y, z, radius in puffs:
                shapes.sphere(x, y - radius * 0.18, z, radius * 0.95, (0.84, 0.86, 0.90), (1.0, 0.45, 1.0), 12, 8)
                shapes.sphere(x, y, z, radius, (0.98, 0.98, 0.99), (1.0, 0.45, 1.0), 12, 8)

    def draw(self, eye):
        glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glPushMatrix()
        glTranslatef(*eye)
        glCallList(self.display_list)
        glPopMatrix()
        glPopAttrib()
