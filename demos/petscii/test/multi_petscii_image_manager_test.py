import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, OPENGL, QUIT
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
from demos.petscii.files.petscii.images.multi_petscii_image_manager import MultiPetsciiImageManager


def main():
    pygame.init()
    pygame.display.set_mode((Constants.WIDTH, Constants.HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Captions on a curved surface")

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    manager = MultiPetsciiImageManager()

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        manager.draw()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
