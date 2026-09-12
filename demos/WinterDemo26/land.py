import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Land:
    def __init__(self, extent=24.0, resolution=44, seed=7, height_amplitudes=(1.15, 0.7, 0.5, 0.35)):
        self.extent = extent
        self.resolution = resolution
        self.random_generator = random.Random(seed)
        self.height_amplitudes = height_amplitudes
        self.snow_white = (0.97, 0.98, 1.0)
        self.cyan_shades = ((0.60, 0.86, 0.95), (0.74, 0.92, 0.98), (0.53, 0.80, 0.93))
        self.vertices = self._build_vertices()
        self.display_list = self._compile()

    def surface_height(self, x, z):
        amplitude = self.height_amplitudes
        return (amplitude[0] * math.sin(0.35 * x + 0.6) * math.cos(0.32 * z)
                + amplitude[1] * math.sin(0.6 * z + 1.3)
                + amplitude[2] * math.sin(0.22 * (x + z))
                + amplitude[3] * math.cos(0.5 * x - 0.3 * z))

    def _normal_at(self, x, z):
        step = 0.05
        slope_x = self.surface_height(x + step, z) - self.surface_height(x - step, z)
        slope_z = self.surface_height(x, z + step) - self.surface_height(x, z - step)
        normal_x = -slope_x / (2.0 * step)
        normal_z = -slope_z / (2.0 * step)
        length = math.sqrt(normal_x * normal_x + 1.0 + normal_z * normal_z)
        return normal_x / length, 1.0 / length, normal_z / length

    def _color_at(self, height_value):
        lowest = -1.5
        highest = 1.7
        normalized = (height_value - lowest) / (highest - lowest)
        chance_of_cyan = max(0.0, 0.32 * (1.0 - normalized))
        if self.random_generator.random() < chance_of_cyan:
            cyan = self.cyan_shades[self.random_generator.randrange(len(self.cyan_shades))]
            blend = self.random_generator.uniform(0.35, 0.9)
            return (self.snow_white[0] * (1.0 - blend) + cyan[0] * blend,
                    self.snow_white[1] * (1.0 - blend) + cyan[1] * blend,
                    self.snow_white[2] * (1.0 - blend) + cyan[2] * blend)
        return self.snow_white

    def _build_vertices(self):
        grid = []
        count = self.resolution
        for row in range(count + 1):
            line = []
            for column in range(count + 1):
                x = -self.extent + (2.0 * self.extent) * column / count
                z = -self.extent + (2.0 * self.extent) * row / count
                y = self.surface_height(x, z)
                normal = self._normal_at(x, z)
                color = self._color_at(y)
                line.append((x, y, z, normal, color))
            grid.append(line)
        return grid

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glBegin(GL_QUADS)
        for row in range(self.resolution):
            for column in range(self.resolution):
                corners = (self.vertices[row][column],
                           self.vertices[row][column + 1],
                           self.vertices[row + 1][column + 1],
                           self.vertices[row + 1][column])
                for x, y, z, normal, color in corners:
                    glColor3f(*color)
                    glNormal3f(*normal)
                    glVertex3f(x, y, z)
        glEnd()
        glEndList()
        return display_list

    def draw(self):
        glCallList(self.display_list)


class FlattyLand(Land):

    def __init__(self, extent=24.0, resolution=44, seed=7):
        super().__init__(extent, resolution, seed, height_amplitudes=(0.15, 0.07, 0.05, 0.035))
