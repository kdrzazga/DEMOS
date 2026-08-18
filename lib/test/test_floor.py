import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.floor import JumpingLettersToCaption

WIDTH, HEIGHT = 800, 600
FPS = 60
CAMERA_DISTANCE = 4.0
DURATION = 150


def build_captions():
    return [
        JumpingLettersToCaption('LOAD "*",8,1', 0, DURATION, -1.5, 0.5, 0.0),
        JumpingLettersToCaption("LOADING", DURATION//2, DURATION, -1.5, -0.6, 0.0),
    ]


def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("JumpingLettersToCaption test - space replays, esc quits")
    clock = pygame.time.Clock()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    captions = build_captions()
    frame = 0
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                captions = build_captions()
                frame = 0

        for caption in captions:
            caption.update(frame)

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -CAMERA_DISTANCE)
        for caption in captions:
            caption.draw()

        pygame.display.flip()
        frame += 1

    pygame.quit()


if __name__ == "__main__":
    main()
