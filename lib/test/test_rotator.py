import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.rotator import Rotator, AngleRotator, Edge

WIDTH, HEIGHT = 800, 600
FPS = 60
CAMERA_DISTANCE = 4.5
HALF_WIDTH = 1.5
TOTAL_DURATION = 2.5
TEXTURE_COORDS = ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))


def build_surface():
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill((16, 16, 32))
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surface, (48, 96, 96), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surface, (48, 96, 96), (0, y), (WIDTH, y))
    corner_size = 60
    pygame.draw.rect(surface, (220, 60, 60), (0, 0, corner_size, corner_size))
    pygame.draw.rect(surface, (60, 220, 60), (WIDTH - corner_size, 0, corner_size, corner_size))
    pygame.draw.rect(surface, (60, 120, 220), (WIDTH - corner_size, HEIGHT - corner_size, corner_size, corner_size))
    pygame.draw.rect(surface, (220, 210, 60), (0, HEIGHT - corner_size, corner_size, corner_size))
    return surface


def make_texture():
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return texture


def upload(texture, surface):
    data = pygame.image.tobytes(surface, "RGBA", True)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)


def draw_quad(corners):
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    for corner, (u, v) in zip(corners, TEXTURE_COORDS):
        glTexCoord2f(u, v)
        glVertex3f(*corner)
    glEnd()


def build_corner_rotator(surface):
    half_height = HALF_WIDTH * HEIGHT / WIDTH
    return Rotator(
        surface,
        destination_top_left=(-HALF_WIDTH, half_height, 0.0),
        destination_top_right=(HALF_WIDTH, half_height, -3.0),
        destination_bottom_left=(-HALF_WIDTH, -half_height, 0.0),
        destination_bottom_right=(HALF_WIDTH, -half_height, -3.0),
        total_duration=TOTAL_DURATION,
        fps=FPS,
        half_width=HALF_WIDTH,
    )


def build_angle_rotator(surface):
    return AngleRotator(
        surface,
        still_edge=Edge.LEFT,
        total_angle=70.0,
        total_duration=TOTAL_DURATION,
        fps=FPS,
        half_width=HALF_WIDTH,
    )


def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Rotator test - tab switches corner/angle, space replays, esc quits")
    clock = pygame.time.Clock()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    surface = build_surface()
    texture = make_texture()
    upload(texture, surface)
    rotators = (build_corner_rotator(surface), build_angle_rotator(surface))
    active_index = 0

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                rotators[active_index].reset()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                active_index = 1 - active_index
                rotators[active_index].reset()

        corners = rotators[active_index].rotate()

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -CAMERA_DISTANCE)
        draw_quad(corners)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
