import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.specialFX.spiral import Spiral, SpiralAnim

WIDTH, HEIGHT = 1000, 800
FPS = 60
FIELD_OF_VIEW = 45.0
CAMERA_DISTANCE = 16.0
STEP_KEYS = {pygame.K_0: 0, pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4, pygame.K_5: 5,
             pygame.K_6: 6}


def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Spiral test - a replays movement, r still spiral replay, space next step, 0-6 show steps, esc quits")
    clock = pygame.time.Clock()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FIELD_OF_VIEW, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.02, 0.02, 0.06, 1.0)

    spiral = Spiral(center=(0.0, 0.0, 0.0), turn_spacing=1.0, turns=5)
    spiral_anim = SpiralAnim(spiral, CAMERA_DISTANCE, FIELD_OF_VIEW, WIDTH / HEIGHT)
    spiral_anim.restart()
    movement_playing = True

    running = True
    while running:
        delta_seconds = clock.tick(FPS) / 1000.0
        if movement_playing:
            spiral_anim.update(delta_seconds)
            if spiral_anim.is_finished():
                spiral_anim.restart()
        else:
            spiral.update(delta_seconds)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                spiral_anim.restart()
                movement_playing = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                movement_playing = False
                spiral.show_steps(6)
                spiral.restart()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                movement_playing = False
                spiral.show_next_step()
            elif event.type == pygame.KEYDOWN and event.key in STEP_KEYS:
                movement_playing = False
                spiral.show_steps(STEP_KEYS[event.key])

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -CAMERA_DISTANCE)
        if movement_playing:
            spiral_anim.draw()
        else:
            spiral.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
