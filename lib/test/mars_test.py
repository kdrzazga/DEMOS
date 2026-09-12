import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.mars import Mars


class MarsTest:
    def __init__(self, width=900, height=750):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Mars Test")
        self._init_gl()
        self.mars = Mars(0.0, 0.0, 0.0, radius=6.0, spin_speed=7.0, seed=17)

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.96, 0.90, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.14, 0.13, 0.16, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.10, 0.10, 0.14, 1.0))
        glClearColor(0.01, 0.01, 0.04, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / self.height, 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

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
            self.mars.update(delta_seconds)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            orbit = self.elapsed * 0.11
            height = 3.0 + math.sin(self.elapsed * 0.19) * 9.0
            gluLookAt(math.sin(orbit) * 18.0, height, math.cos(orbit) * 18.0,
                      0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.65, 0.40, 1.0, 0.0))
            self.mars.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    MarsTest().run()


if __name__ == "__main__":
    main()
