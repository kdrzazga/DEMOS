import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from demos.WinterDemo26.bonfire import Bonfire


class BonfireTest:
    def __init__(self, width=900, height=700):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Bonfire Test")
        self._init_gl()
        self.bonfire = Bonfire(0.0, 0.0, 0.0)

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.9, 0.75, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.28, 0.24, 0.22, 1.0))
        glClearColor(0.05, 0.06, 0.10, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _draw_ground(self):
        glColor3f(0.10, 0.12, 0.16)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        size = 20.0
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
            self.bonfire.update(delta_seconds)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            orbit = self.elapsed * 0.4
            gluLookAt(math.sin(orbit) * 5.0, 2.6, math.cos(orbit) * 5.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (2.0, 4.0, 2.0, 1.0))
            self._draw_ground()
            self.bonfire.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    BonfireTest().run()


if __name__ == "__main__":
    main()
