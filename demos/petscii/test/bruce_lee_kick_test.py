import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, K_SPACE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_TEXTURE_2D,
    glClear,
    glClearColor,
    glEnable,
)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from demos.petscii.files.globals import Constants
from demos.petscii.files.bruce_lee_kick_animation import BruceLeeKickAnimation


def main():
    """Preview the spinning 3D Bruce Lee kick model on its own: he flies up from
    the bottom into the bottom centre and turns slowly. Press SPACE to replay the
    fly-in, ESC (or close the window) to quit."""
    pygame.init()
    pygame.display.set_mode((Constants.WIDTH, Constants.HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Bruce Lee Kick PETSCII 3D")

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    bruce = BruceLeeKickAnimation()
    bruce.start()

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False
            elif event.type == KEYDOWN and event.key == K_SPACE:
                bruce.phase = BruceLeeKickAnimation.WAIT   # rewind, then fly in again
                bruce.start()

        bruce.update()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        bruce.draw()
        pygame.display.flip()
        clock.tick(Constants.FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
