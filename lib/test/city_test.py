import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_3, K_4, K_5, K_6
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.urban.city_builder import CityBuilder


class CityTest:
    def __init__(self, width=1000, height=720):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.sky_color = (0.36, 0.42, 0.50)
        self.ground_color = (0.58, 0.62, 0.68)
        self.field_of_view = 50.0
        self.orbit_speed = 0.16
        self.height_ratio = 0.42
        self.selected = 0
        self.layouts = (("compact 3 x 2", CityBuilder(seed=1)),
                        ("dense grid 12 x 9", CityBuilder(blocks_across=12, blocks_deep=9,
                                                         quarter_rows=4, quarter_columns=4,
                                                         floor_range=(1, 3), road_width=5.0, seed=2)),
                        ("tall downtown 2 x 2", CityBuilder(blocks_across=2, blocks_deep=2,
                                                            quarter_rows=3, quarter_columns=4,
                                                            floor_range=(3, 6), windows_range=(3, 5),
                                                            road_width=9.0, seed=3)),
                        ("wide suburb 4 x 2", CityBuilder(blocks_across=4, blocks_deep=2,
                                                          quarter_rows=1, quarter_columns=5,
                                                          floor_range=(1, 2), windows_range=(2, 3),
                                                          road_width=6.0, house_spacing=(2.6, 3.0),
                                                          seed=4)),
                        ("compact 3 x 2 at density 0.45", CityBuilder(density=0.45, seed=1)),
                        ("dense grid 12 x 9 at density 0.7",
                         CityBuilder(blocks_across=12, blocks_deep=9, quarter_rows=4,
                                     quarter_columns=4, floor_range=(1, 3), road_width=5.0,
                                     density=0.7, seed=2)))
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("City Test")
        self._init_gl()
        self.cities = tuple(builder.build() for _, builder in self.layouts)
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
        gluPerspective(self.field_of_view, self.width / self.height, 0.5, 900.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _announce(self):
        name, builder = self.layouts[self.selected]
        city = self.cities[self.selected]
        plots = sum(quarter.plot_count() for quarter in city.quarters)
        print("%d. %s -- %.0f x %.0f, %d quarters, %d roads, %d of %d plots built (density %.2f)"
              % (self.selected + 1, name, city.width, city.depth, len(city.quarters),
                 len(city.roads), city.house_count(), plots, builder.density))

    def _half_width_angle(self):
        half_height = math.radians(self.field_of_view / 2.0)
        return math.atan(math.tan(half_height) * self.width / self.height)

    def _orbit_radius(self):
        city = self.cities[self.selected]
        reach = math.hypot(city.width, city.depth) / 2.0
        return reach / math.tan(self._half_width_angle()) + reach * 0.35

    def _ground_reach(self):
        return max(city.width + city.depth for city in self.cities)

    def _draw_ground(self):
        size = self._ground_reach()
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
        choices = (K_1, K_2, K_3, K_4, K_5, K_6)
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
    print('Press key 1, 2, 3, 4, 5 or 6')
    CityTest().run()


if __name__ == "__main__":
    main()
