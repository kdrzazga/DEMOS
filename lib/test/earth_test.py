import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.earth import Earth


class EarthTest:
    def __init__(self, width=900, height=750):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Earth Test")
        self._init_gl()
        self.earth = Earth(0.0, 0.0, 0.0, radius=6.0, spin_speed=26.0)

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
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.12, 0.14, 0.20, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.10, 0.12, 0.18, 1.0))
        glClearColor(0.01, 0.01, 0.04, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / self.height, 0.1, 1200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _camera_distance(self):
        return 232.0 + math.sin(self.elapsed * 0.16 - math.pi / 2.0) * 210.0

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
            self.earth.update(delta_seconds)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            orbit = self.elapsed * 0.12
            reach = self._camera_distance()
            gluLookAt(math.sin(orbit) * reach, reach * 0.17, math.cos(orbit) * reach,
                      0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.6, 0.45, 1.0, 0.0))
            self.earth.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    EarthTest().run()


if __name__ == "__main__":
    main()
