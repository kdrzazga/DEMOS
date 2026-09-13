import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_1, K_2
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from demos.WinterDemo26.hall import Hall


class HallTest:
    def __init__(self, width=1100, height=700):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.background = (0.10, 0.10, 0.14)
        self.inside_view = True
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Hall Test")
        self._init_gl()
        self.hall = Hall(0.0, 0.0, 0.0)

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.98, 0.92, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glClearColor(self.background[0], self.background[1], self.background[2], 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0, self.width / self.height, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _camera(self):
        if self.inside_view:
            sway = math.sin(self.elapsed * 0.4) * 4.0
            eye = (sway, 2.4, self.hall.length / 2.0 - 3.0)
            target = (sway * 0.3, 6.0 + math.sin(self.elapsed * 0.25) * 2.5, -self.hall.length / 2.0)
            return eye, target
        orbit = self.elapsed * 0.2
        eye = (math.sin(orbit) * 45.0, 30.0, math.cos(orbit) * 45.0)
        return eye, (0.0, 5.0, 0.0)

    def run(self):
        running = True
        while running:
            self.elapsed += self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_1:
                        self.inside_view = True
                    elif event.key == K_2:
                        self.inside_view = False
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            eye, target = self._camera()
            gluLookAt(eye[0], eye[1], eye[2], target[0], target[1], target[2], 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.3, 1.0, 0.5, 0.0))
            self.hall.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    print("Press 1 for the inside view, 2 to orbit outside")
    HallTest().run()


if __name__ == "__main__":
    main()
