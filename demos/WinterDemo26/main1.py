import math
import os
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.WinterDemo26.land import Land
from demos.WinterDemo26.tree import Tree
from demos.WinterDemo26.snowman import Snowman
from demos.WinterDemo26.snow import Snow


class WinterScene:
    def __init__(self, width=1100, height=700):
        self.width = width
        self.height = height
        self.sky_color = (0.66, 0.76, 0.86)
        self.tree_positions = ((-8.0, -4.0), (-5.5, 3.0), (6.5, -6.0), (9.0, 2.5),
                               (-10.0, -9.0), (3.0, 8.0), (-2.0, -11.0), (11.0, -1.0),
                               (-12.0, -14.0), (1.0, 13.0), (-4.0, -14.0), (12.0, -12.0))
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self._init_display()
        self._init_gl()
        self.land = Land(extent=80.0, resolution=144, seed=7)
        self.trees = self._create_trees()
        self.snowman = Snowman(1.7, 0.0, self.land.surface_height(1.7, 0.0) - 0.6)
        self.snow = Snow(220, (-22.0, 22.0, -20.0, 20.0, -1.5, 18.0))

    def _init_display(self):
        pygame.init()
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Winter")

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
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, (self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0))
        glFogf(GL_FOG_START, 30.0)
        glFogf(GL_FOG_END, 80.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.1, 220.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _create_trees(self):
        trees = []
        for index, (x, z) in enumerate(self.tree_positions):
            ground = self.land.surface_height(x, z)
            trees.append(Tree(x, z, ground, snow_top=index % 3 != 0, seed=index + 1))
        return trees

    def _place_camera(self):
        orbit = math.radians(35.0 * math.sin(self.elapsed * 0.25))
        radius = 26.0
        eye_x = math.sin(orbit) * radius
        eye_z = math.cos(orbit) * radius
        gluLookAt(eye_x, 10.0, eye_z, 0.0, 3.0, 0.0, 0.0, 1.0, 0.0)

    def _draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self._place_camera()
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.6, 0.0))
        self.land.draw()
        for tree in self.trees:
            tree.draw()
        self.snowman.draw()
        self.snow.draw()

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
            self.snow.update(delta_seconds)
            self._draw()
            pygame.display.flip()
        pygame.quit()


def main():
    WinterScene().run()


if __name__ == "__main__":
    main()
