import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_r
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from demos.WinterDemo26.desk import Desk


class DeskTest:
    def __init__(self, width=1100, height=700, rows=4, columns=3, item_delay=0.1, desk_start_delay=0.3):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.build_started = 0.0
        self.item_delay = item_delay
        self.desk_start_delay = desk_start_delay
        self.background = (0.07, 0.03, 0.10)
        self.row_spacing = 1.9
        self.column_spacing = 2.8
        self.hall_view = True
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Desk Test")
        self._init_gl()
        self.single_desk = Desk(0.0, 0.0, 0.0, seed=1)
        self.desks = [Desk((column - (columns - 1) / 2.0) * self.column_spacing, 0.0, -row * self.row_spacing,
                           laptop_count=2 + (row + column) % 2, seed=row * 10 + column)
                      for row in range(rows) for column in range(columns)]

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.75, 0.45, 0.95, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.22, 0.12, 0.26, 1.0))
        glClearColor(self.background[0], self.background[1], self.background[2], 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.05, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _draw_floor(self):
        glColor3f(0.12, 0.08, 0.14)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        size = 20.0
        glVertex3f(-size, 0.0, -size)
        glVertex3f(-size, 0.0, size)
        glVertex3f(size, 0.0, size)
        glVertex3f(size, 0.0, -size)
        glEnd()

    def _camera(self):
        if self.hall_view:
            sway = math.sin(self.elapsed * 0.3) * 0.6
            eye = (sway, 1.5, self.single_desk.depth + 1.6)
            return eye, (sway * 0.5, 0.6, -4.0)
        orbit = self.elapsed * 0.4
        eye = (math.sin(orbit) * 3.2, 1.8, math.cos(orbit) * 3.2)
        return eye, (0.0, 0.6, 0.0)

    def _desk_visible(self, desk_index):
        return self.elapsed - self.build_started >= desk_index * self.desk_start_delay

    def _visible_items(self, desk_index):
        desk_elapsed = self.elapsed - self.build_started - desk_index * self.desk_start_delay
        return int(desk_elapsed // self.item_delay)

    def _draw_building_desk(self, desk, desk_index):
        if self._desk_visible(desk_index):
            desk.draw(self._screen_glow(desk_index), self._visible_items(desk_index))

    def _screen_glow(self, index):
        return 0.85 + 0.15 * math.sin(self.elapsed * 4.0 + index * 1.7)

    def run(self):
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
                    elif event.key == K_1:
                        self.hall_view = True
                        self.build_started = self.elapsed
                    elif event.key == K_2:
                        self.hall_view = False
                        self.build_started = self.elapsed
                    elif event.key == K_r:
                        self.build_started = self.elapsed
            for desk in self.desks:
                desk.update(delta_seconds)
            self.single_desk.update(delta_seconds)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            eye, target = self._camera()
            gluLookAt(eye[0], eye[1], eye[2], target[0], target[1], target[2], 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (1.0, 5.0, 2.0, 1.0))
            self._draw_floor()
            if self.hall_view:
                for index, desk in enumerate(self.desks):
                    self._draw_building_desk(desk, index)
            else:
                self._draw_building_desk(self.single_desk, 0)
            pygame.display.flip()
        pygame.quit()


def main():
    print("Press 1 for the rows of desks, 2 to orbit a single desk, R to rebuild")
    DeskTest().run()


if __name__ == "__main__":
    main()
