import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.urban.house import House


class HouseTest:
    def __init__(self, width=900, height=700):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.sky_color = (0.36, 0.42, 0.50)
        self.ground_color = (0.62, 0.66, 0.72)
        self.street_gap = 1.4
        self.orbit_speed = 0.28
        self.orbit_radius = 27.0
        self.orbit_height = 9.5
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("House Test")
        self._init_gl()
        self.houses = self._create_houses()

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
        gluPerspective(50.0, self.width / self.height, 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _create_houses(self):
        placements = ((1, 2, (0.40, 0.38, 0.36)),
                      (2, 3, (0.60, 0.60, 0.60)),
                      (3, 4, (0.44, 0.30, 0.26)),
                      (4, 5, (0.30, 0.34, 0.40)))
        houses = []
        cursor = 0.0
        for floor_count, windows_per_floor, color in placements:
            house = House(0.0, 0.0, 0.0, floor_count, windows_per_floor=windows_per_floor, color=color)
            cursor += house.width / 2.0
            house.x = cursor
            cursor += house.width / 2.0 + self.street_gap
            houses.append(house)
        middle = (cursor - self.street_gap) / 2.0
        for house in houses:
            house.x -= middle
        return houses

    def _draw_ground(self):
        glColor3f(*self.ground_color)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        size = 40.0
        glVertex3f(-size, 0.0, -size)
        glVertex3f(-size, 0.0, size)
        glVertex3f(size, 0.0, size)
        glVertex3f(size, 0.0, -size)
        glEnd()

    def run(self):
        running = True
        while running:
            delta_seconds = self.clock.tick(60) / 1000.0
            self.elapsed += delta_seconds
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    running = False
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            orbit = self.elapsed * self.orbit_speed
            gluLookAt(math.sin(orbit) * self.orbit_radius, self.orbit_height,
                      math.cos(orbit) * self.orbit_radius, 0.0, 4.5, 0.0, 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.6, 0.0))
            self._draw_ground()
            for house in self.houses:
                house.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    HouseTest().run()


if __name__ == "__main__":
    main()
