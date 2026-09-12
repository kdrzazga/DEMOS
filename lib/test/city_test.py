import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_3, K_4, K_5
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.urban.city_factory import CityFactory


class CityTest:
    def __init__(self, width=1000, height=720):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.sky_color = (0.36, 0.42, 0.50)
        self.ground_color = (0.58, 0.62, 0.68)
        self.field_of_view = 50.0
        self.orbit_speed = 0.12
        self.height_ratio = 0.46
        self.selected = 0
        self.plans = (("seed 1", 1, "single"), ("seed 2", 2, "single"), ("seed 3", 3, "single"),
                      ("seed 1 tripled", 1, "triple"), ("big city 11 x 11", 1, "big"))
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("City Test")
        self._init_gl()
        self.cities = tuple(self._create_city(seed, kind) for _, seed, kind in self.plans)
        self._announce()

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.98, 0.92, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glClearColor(self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.width / self.height, 0.5, 2600.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _create_city(self, seed, kind):
        factory = CityFactory(seed=seed)
        if kind == "triple":
            return factory.create_with_dense_center_triple()
        if kind == "big":
            return factory.create_big_city()
        return factory.create_with_dense_center()

    def _announce(self):
        city = self.cities[self.selected]
        print("%s -- %.0f x %.0f, %d towns, %d quarters, %d houses"
              % (self.plans[self.selected][0], city.width, city.depth,
                 city.town_count(), city.quarter_count(), city.house_count()))
        for row in range(city.rows):
            line = []
            for column in range(city.columns):
                town = city.town_at(row, column)
                line.append("  .  " if town is None else "%5d" % town.house_count())
            print("   " + " ".join(line))

    def _half_width_angle(self):
        half_height = math.radians(self.field_of_view / 2.0)
        return math.atan(math.tan(half_height) * self.width / self.height)

    def _orbit_radius(self):
        city = self.cities[self.selected]
        reach = math.hypot(city.width, city.depth) / 2.0
        return reach / math.tan(self._half_width_angle()) + reach * 0.3

    def _draw_ground(self):
        size = max(city.width + city.depth for city in self.cities)
        glColor3f(*self.ground_color)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(-size, 0.0, -size)
        glVertex3f(-size, 0.0, size)
        glVertex3f(size, 0.0, size)
        glVertex3f(size, 0.0, -size)
        glEnd()

    def _select(self, index):
        if 0 <= index < len(self.cities) and index != self.selected:
            self.selected = index
            self._announce()

    def run(self):
        choices = (K_1, K_2, K_3, K_4, K_5)
        running = True
        while running:
            delta_seconds = self.clock.tick(60) / 1000.0
            self.elapsed += delta_seconds
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key in choices:
                        self._select(choices.index(event.key))
            city = self.cities[self.selected]
            radius = self._orbit_radius()
            orbit = self.elapsed * self.orbit_speed
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            gluLookAt(math.sin(orbit) * radius, radius * self.height_ratio,
                      math.cos(orbit) * radius, 0.0, city.tallest() * 0.4, 0.0, 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.6, 0.0))
            self._draw_ground()
            city.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    print('Press key 1, 2 or 3 to switch seed, 4 for the tripled city, 5 for the big one')
    CityTest().run()


if __name__ == "__main__":
    main()
