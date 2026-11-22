import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.specialFX.cats import CatAnim

WIDTH, HEIGHT = 1000, 800
FPS = 60
FIELD_OF_VIEW = 45.0
CAMERA_DISTANCE = 12.0
CAT_SIZE = 1.0


def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("CatDog test - r replays, esc quits")
    clock = pygame.time.Clock()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FIELD_OF_VIEW, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.02, 0.02, 0.06, 1.0)

    visible_height = 2.0 * CAMERA_DISTANCE * math.tan(math.radians(FIELD_OF_VIEW / 2.0))
    visible_width = visible_height * WIDTH / HEIGHT
    cat_dog_anim = CatAnim(area_center=(0.0, 0.0, 0.0), area_width=visible_width,
                           area_height=visible_height, cat_size=CAT_SIZE)

    running = True
    while running:
        cat_dog_anim.update(clock.tick(FPS) / 1000.0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                cat_dog_anim.restart()

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -CAMERA_DISTANCE)
        cat_dog_anim.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
