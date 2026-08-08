import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_MODELVIEW,
    GL_NEAREST,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glClear,
    glClearColor,
    glColor3f,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from demos.petscii.files.petscii.bruce_lee_stage1 import BruceLeeStage

CHAR_SIZE = 24
SWAY_DEGREES = 10.0   # peak left/right tilt
SWAY_PERIOD = 5000.0  # milliseconds for a full left-right-left cycle
ZOOM = 0.9            # camera distance as a multiple of width; smaller = closer/zoomed in


def upload(surface):
    texture = glGenTextures(1)
    data = pygame.image.tobytes(surface, "RGBA")
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return texture


def draw_surface(half_width, half_height):
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-half_width, half_height, 0)
    glTexCoord2f(1, 0); glVertex3f(half_width, half_height, 0)
    glTexCoord2f(1, 1); glVertex3f(half_width, -half_height, 0)
    glTexCoord2f(0, 1); glVertex3f(-half_width, -half_height, 0)
    glEnd()


def main():
    pygame.init()
    image = BruceLeeStage(CHAR_SIZE)
    width, height = image.size()
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Bruce Lee PETSCII 3D")

    surface = pygame.Surface((width, height))
    image.render(surface)
    texture = upload(surface)

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    half_width, half_height = width / 2, height / 2
    distance = width * ZOOM

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        sway = SWAY_DEGREES * math.sin(2 * math.pi * pygame.time.get_ticks() / SWAY_PERIOD)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 1.0, 10000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -distance)
        glRotatef(sway, 0.0, 1.0, 0.0)

        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, texture)
        draw_surface(half_width, half_height)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
