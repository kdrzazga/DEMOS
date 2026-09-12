import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.saturn import Saturn


class SaturnTest:
    def __init__(self, width=1000, height=750):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Saturn Test")
        self._init_gl()
        self.saturn = Saturn(0.0, 0.0, 0.0, radius=6.0, spin_speed=8.0, seed=11)

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.97, 0.90, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.16, 0.16, 0.20, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.12, 0.12, 0.16, 1.0))
        glClearColor(0.01, 0.01, 0.04, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / self.height, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _camera_height(self):
        return 7.0 + math.sin(self.elapsed * 0.17) * 12.0

    def _camera_distance(self):
        return 75.0 + math.sin(self.elapsed * 0.21 - math.pi / 2.0) * 25.0

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
            self.saturn.update(delta_seconds)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            orbit = self.elapsed * 0.13
            reach = self._camera_distance()
            gluLookAt(math.sin(orbit) * reach, self._camera_height(), math.cos(orbit) * reach,
                      0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.7, 0.5, 1.0, 0.0))
            self.saturn.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    SaturnTest().run()


if __name__ == "__main__":
    main()
