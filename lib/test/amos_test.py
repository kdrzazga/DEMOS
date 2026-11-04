import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONDOWN
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.amiga.amos import Amos


class SurfaceTexture:
    def __init__(self, surface):
        self.width, self.height = surface.get_size()
        self.texture_id = glGenTextures(1)
        self.upload(surface)

    def upload(self, surface):
        pixels = pygame.image.tobytes(surface, "RGBA", True)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)

    def draw_fullscreen(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)


class AmosTest:
    def __init__(self):
        self.width = 1280
        self.height = 960
        self.clock = pygame.time.Clock()
        pygame.init()
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("AMOS Test")
        self.init_gl()
        self.code_path = os.path.join(os.path.dirname(__file__), "..", "resources", "amos-code.txt")
        self.amos = Amos()
        self.amos.type_code(self.code_path)
        self.texture = SurfaceTexture(self.amos.surface)

    def init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return False
            if event.type == MOUSEBUTTONDOWN:
                self.move_mouse_cursor(*event.pos)
        return True

    def move_mouse_cursor(self, window_x, window_y):
        screen_width, screen_height = self.amos.screen.size
        self.amos.mouse_cursor.move_to(window_x * screen_width // self.width,
                                       window_y * screen_height // self.height)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.texture.draw_fullscreen()
        pygame.display.flip()

    def run(self):
        while self.handle_events():
            seconds = self.clock.tick(60) / 1000.0
            self.amos.update(seconds)
            self.texture.upload(self.amos.surface)
            self.draw()
        pygame.quit()


def main():
    AmosTest().run()


if __name__ == "__main__":
    main()
