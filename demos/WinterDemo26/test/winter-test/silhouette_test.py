import colorsys
import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from demos.WinterDemo26.silhouette import Silhouette, FIGURES_IN_ROW


class SilhouetteTest:
    def __init__(self, width=1100, height=700):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.background = (0.10, 0.10, 0.14)
        self.spacing = 0.8
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Silhouette Test")
        self._init_gl()
        self.silhouettes = [Silhouette(number, self._color(number)) for number in range(FIGURES_IN_ROW)]

    def _color(self, number):
        hue = number / FIGURES_IN_ROW
        return colorsys.hsv_to_rgb(hue, 0.6, 1.0)

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
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.28, 0.34, 1.0))
        glClearColor(self.background[0], self.background[1], self.background[2], 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, self.width / self.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _camera(self):
        swing = math.sin(self.elapsed * 0.4) * 0.9
        eye = (math.sin(swing) * 9.0, 1.2, math.cos(swing) * 9.0)
        return eye, (0.0, 0.2, 0.0)

    def _draw_silhouettes(self):
        row_start = -(FIGURES_IN_ROW - 1) * self.spacing / 2.0
        for number, silhouette in enumerate(self.silhouettes):
            glPushMatrix()
            glTranslatef(row_start + number * self.spacing, -0.3, 0.0)
            silhouette.draw()
            glPopMatrix()

    def run(self):
        running = True
        while running:
            delta_seconds = self.clock.tick(60) / 1000.0
            self.elapsed += delta_seconds
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
            for silhouette in self.silhouettes:
                silhouette.update(delta_seconds)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            eye, target = self._camera()
            gluLookAt(eye[0], eye[1], eye[2], target[0], target[1], target[2], 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (0.4, 0.8, 1.0, 0.0))
            self._draw_silhouettes()
            pygame.display.flip()
        pygame.quit()


def main():
    SilhouetteTest().run()


if __name__ == "__main__":
    main()
