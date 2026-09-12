import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Land:
    def __init__(self, extent=24.0, resolution=44, seed=7, height_amplitudes=(1.15, 0.7, 0.5, 0.35),
                 stretch=1.0, clearings=(), flattenings=(), depth_extent=None):
        self.extent = extent
        self.depth_extent = extent if depth_extent is None else depth_extent
        self.resolution = resolution
        self.random_generator = random.Random(seed)
        self.height_amplitudes = height_amplitudes
        self.stretch = stretch
        self.clearings = clearings
        self.flattenings = flattenings
        self.flatten_levels = tuple(self._natural_height(spot[0], spot[1]) if spot[5] is None
                                    else spot[5] for spot in flattenings)
        self.snow_white = (0.60, 0.67, 0.63)
        self.cyan_shades = ((0.60, 0.86, 0.95), (0.74, 0.92, 0.98), (0.53, 0.80, 0.93))
        self.vertices = self._build_vertices()
        self.display_list = self._compile()

    def _natural_height(self, x, z):
        amplitude = self.height_amplitudes
        across = x / self.stretch
        along = z / self.stretch
        return (amplitude[0] * math.sin(0.35 * across + 0.6) * math.cos(0.32 * along)
                + amplitude[1] * math.sin(0.6 * along + 1.3)
                + amplitude[2] * math.sin(0.22 * (across + along))
                + amplitude[3] * math.cos(0.5 * across - 0.3 * along))

    def _flatten_blend(self, x, z, center_x, center_z, half_width, half_depth, falloff):
        beyond = max((abs(x - center_x) - half_width) / falloff,
                     (abs(z - center_z) - half_depth) / falloff)
        if beyond <= 0.0:
            return 1.0
        if beyond >= 1.0:
            return 0.0
        return 1.0 - beyond * beyond * (3.0 - 2.0 * beyond)

    def surface_height(self, x, z):
        height = self._natural_height(x, z)
        for index, spot in enumerate(self.flattenings):
            blend = self._flatten_blend(x, z, spot[0], spot[1], spot[2], spot[3], spot[4])
            if blend > 0.0:
                height += (self.flatten_levels[index] - height) * blend
        return height

    def _is_cleared(self, x, z):
        for center_x, center_z, half_width, half_depth in self.clearings:
            if abs(x - center_x) < half_width and abs(z - center_z) < half_depth:
                return True
        return False

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
                z = -self.depth_extent + (2.0 * self.depth_extent) * row / count
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
                if self._is_cleared((corners[0][0] + corners[2][0]) * 0.5,
                                    (corners[0][2] + corners[2][2]) * 0.5):
                    continue
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

    def __init__(self, extent=24.0, resolution=44, seed=7, depth_extent=None):
        super().__init__(extent, resolution, seed, height_amplitudes=(0.15, 0.07, 0.05, 0.035),
                         depth_extent=depth_extent)
