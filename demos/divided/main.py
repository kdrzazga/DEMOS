import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, FULLSCREEN, K_ESCAPE, KEYDOWN, MOUSEBUTTONDOWN, OPENGL, QUIT
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.divided.world import DividedWorld
from lib.base_demo import BaseDemo


class DividedDemo(BaseDemo):

    def __init__(self, width, height, title, fps=60, windowed=False, triggered=False):
        super().__init__(windowed=windowed, triggered=triggered)
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps
        self.field_of_view = 40.0
        self.near_clip = 0.05
        self.far_clip = 120.0
        self.longest_frame = 0.1
        pygame.init()
        pygame.mouse.set_visible(False)
        self.init_display()
        self.clock = pygame.time.Clock()
        self.world = DividedWorld()
        self.setup_gl()

    def init_display(self):
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        flags = DOUBLEBUF | OPENGL
        if self.windowed:
            pygame.display.set_mode((self.width, self.height), flags)
        else:
            pygame.display.set_mode((0, 0), flags | FULLSCREEN)
        self.width, self.height = pygame.display.get_surface().get_size()
        pygame.display.set_caption(self.title)

    def setup_gl(self):
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        glClearColor(*self.world.dead_land.fog_color)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.width / self.height, self.near_clip, self.far_clip)
        glMatrixMode(GL_MODELVIEW)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.paused:
            return
        glLoadIdentity()
        eye, target = self.world.camera_view()
        gluLookAt(*eye, *target, 0.0, 1.0, 0.0)
        self.world.render(eye)

    def run(self):
        running = True
        while running:
            seconds = min(self.longest_frame, self.clock.tick(self.fps) / 1000.0)
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    self.trigger()
            if not self.paused:
                self.world.update(seconds)
            self.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    DividedDemo(1280, 720, "World divided", windowed=True).run()
