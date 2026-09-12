import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.solar_system3 import SolarSystem3


class SolarSystem3Test:
    def __init__(self, width=1000, height=750):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.dwell = 10.0
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Solar System 3 Test")
        self._init_gl()
        self.system = SolarSystem3(0.0, 0.0, 0.0, planet_scale=1.0, orbit_scale=95.0, year_seconds=20.0)
        self.system.update(0.0)

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.06, 0.06, 0.09, 1.0))
        glClearColor(0.005, 0.005, 0.02, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / self.height, 0.5, 4000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _ease(self, value):
        return value * value * (3.0 - 2.0 * value)

    def _framing(self, planet):
        return max(planet.radius * 5.5, 8.0)

    def _focus(self):
        planets = self.system.planets()
        stride = self.elapsed / self.dwell
        index = int(stride) % len(planets)
        follow = (index + 1) % len(planets)
        blend = self._ease(min(1.0, max(0.0, (stride - int(stride)) * 2.0 - 1.0)))
        near = planets[index]
        far = planets[follow]
        target = (near.x + (far.x - near.x) * blend,
                  near.y + (far.y - near.y) * blend,
                  near.z + (far.z - near.z) * blend)
        reach = self._framing(near) + (self._framing(far) - self._framing(near)) * blend
        return target, reach

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
            self.system.update(delta_seconds)
            target, reach = self._focus()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            orbit = self.elapsed * 0.22
            gluLookAt(target[0] + math.sin(orbit) * reach,
                      target[1] + reach * 0.30,
                      target[2] + math.cos(orbit) * reach,
                      target[0], target[1], target[2], 0.0, 1.0, 0.0)
            self.system.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    SolarSystem3Test().run()


if __name__ == "__main__":
    main()
