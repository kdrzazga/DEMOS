import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.specialFX.spiral_cats import SpiralCatsAnim

WIDTH, HEIGHT = 1000, 800
FPS = 60
FIELD_OF_VIEW = 45.0
CAMERA_DISTANCE = 16.0


def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Spiral + cats test - r replays, esc quits")
    clock = pygame.time.Clock()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FIELD_OF_VIEW, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.02, 0.02, 0.06, 1.0)

    spiral_cats_anim = SpiralCatsAnim(CAMERA_DISTANCE, FIELD_OF_VIEW, WIDTH / HEIGHT)
    spiral_cats_anim.restart()

    running = True
    while running:
        spiral_cats_anim.update(clock.tick(FPS) / 1000.0)
        if spiral_cats_anim.is_finished():
            spiral_cats_anim.restart()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                spiral_cats_anim.restart()

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -CAMERA_DISTANCE)
        spiral_cats_anim.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
