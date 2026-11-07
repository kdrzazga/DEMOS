import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pygame
from OpenGL.GL import *

from demos.retro_glasses.c64_animation import C64Animation


class C64AnimationViewer:
    def __init__(self):
        self.window_size = (1280, 800)
        self.background = (0.0, 0.0, 0.0, 1.0)
        self.frames_per_second = 60
        pygame.init()
        pygame.display.set_mode(self.window_size, pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption("C64Animation test")
        self.clock = pygame.time.Clock()
        self.animation = C64Animation()
        self.running = True

    @property
    def screen(self):
        return self.animation.c64screen

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.screen.restart_typing()

    def quad_half_size(self):
        window_width, window_height = self.window_size
        window_aspect = window_width / window_height
        if self.screen.aspect > window_aspect:
            return 1.0, window_aspect / self.screen.aspect
        return self.screen.aspect / window_aspect, 1.0

    def draw(self):
        glClearColor(*self.background)
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.screen.refresh()
        half_width, half_height = self.quad_half_size()
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.screen.texture_id)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-half_width, -half_height)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(half_width, -half_height)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(half_width, half_height)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-half_width, half_height)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def run(self):
        while self.running:
            seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.handle_events()
            self.screen.update(seconds)
            self.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    C64AnimationViewer().run()
