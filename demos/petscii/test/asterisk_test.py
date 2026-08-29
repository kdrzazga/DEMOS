import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, K_SPACE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_TEXTURE_2D,
    glClear,
    glClearColor,
    glEnable,
)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from demos.petscii.files.globals import Constants
from demos.petscii.files.asterisk_animation import AsteriskAnimation


def main():
    """Preview the asterisk effect on its own: it flies in from the right, zooms to
    the front and sways, spirals, then exits left trailing a swarm of 200. Press
    SPACE to replay, ESC (or close the window) to quit."""
    pygame.init()
    pygame.display.set_mode((Constants.WIDTH, Constants.HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Asterisk (PETSCII)")

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)

    asterisk = AsteriskAnimation()
    asterisk.animate()

    # hold on a blank screen after the run; SPACE replays, ESC / close quits
    clock = pygame.time.Clock()
    running = asterisk.running
    while running:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
            elif event.type == KEYDOWN and event.key == K_SPACE:
                asterisk.animate()
                running = asterisk.running
        glClear(GL_COLOR_BUFFER_BIT)
        pygame.display.flip()
        clock.tick(Constants.FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
