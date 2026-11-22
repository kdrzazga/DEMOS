import math
import os
import sys

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.plants.mushroom import MushroomPalette
from lib.plants.mushroom_forest import MushroomForest


class MushroomForestPreview:
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.field_of_view = 50.0
        self.seed = 7
        self.schemes = {
            pygame.K_1: ["violet"],
            pygame.K_2: ["cyan"],
            pygame.K_3: ["reddish"],
            pygame.K_4: ["yellowish"],
            pygame.K_5: ["violet", "cyan", "reddish", "yellowish"],
        }
        self.scheme = self.schemes[pygame.K_1]
        pygame.init()
        pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.OPENGL)
        pygame.display.set_caption("Mushroom forest  [1-5 colors, R reseed, Esc quit]")
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.forest = self.grow()

    def palettes(self):
        return [MushroomPalette.named(name) for name in self.scheme]

    def grow(self):
        return MushroomForest(self.palettes(), self.seed)

    def regrow(self):
        self.forest = self.grow()
        self.clock.tick()

    def look(self, elapsed):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.width / self.height, 0.1, 120.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(math.sin(elapsed * 0.07) * 4.0,
                  2.4 + 0.3 * math.sin(elapsed * 0.11),
                  11.0 - 1.5 * math.sin(elapsed * 0.05),
                  0.0, 2.0, -6.0,
                  0.0, 1.0, 0.0)

    def handle(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in self.schemes:
                self.scheme = self.schemes[event.key]
                self.forest.recolor(self.palettes())
            if event.key == pygame.K_r:
                self.seed += 1
                self.regrow()
        return True

    def run(self):
        running = True
        while running:
            delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running = running and self.handle(event)
            self.forest.update(delta)
            glClearColor(*self.forest.sky_color)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.elapsed += delta
            self.look(self.elapsed)
            self.forest.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    MushroomForestPreview().run()
