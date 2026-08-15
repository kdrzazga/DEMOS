import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

from lib.textwall import TextWallArray, PygameTextWall
from lib.test.corpus import load_text, build_lines

WIDTH, HEIGHT = 800, 600
GREEN = (51, 255, 102)
BLUE = (102, 204, 255)
PANEL_BG = (0, 0, 25, 255)
SWAY_DEGREES = 45.0
SWAY_PERIOD = 3.0
DISTANCE = 4.5
HALF_H = 1.5


def make_texture():
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return tex


def upload(tex, surface):
    data = pygame.image.tobytes(surface, "RGBA", True)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)


def set_projection():
    near, far = 0.1, 100.0
    top = near * math.tan(math.radians(45.0) / 2.0)
    right = top * (WIDTH / HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glFrustum(-right, right, -top, top, near, far)
    glMatrixMode(GL_MODELVIEW)


def draw_quad(half_w, half_h):
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex3f(-half_w, -half_h, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex3f(half_w, -half_h, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex3f(half_w, half_h, 0.0)
    glTexCoord2f(0.0, 1.0); glVertex3f(-half_w, half_h, 0.0)
    glEnd()


def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("TextWall - opengl swaying surface")
    clock = pygame.time.Clock()

    canvas = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    layout = dict(x=16, y=12, initial_screen_y=260, rows=25,
                  speed=20, loop=False, font_size=18)
    wall_a = PygameTextWall(build_lines(load_text("kaplus.txt")), surface=canvas, color=GREEN, **layout)
    wall_b = PygameTextWall(build_lines(load_text("karate.txt")), surface=canvas, color=BLUE, **layout)
    walls = TextWallArray()
    walls.add(wall_a, 0.0)
    walls.add(wall_b, 0.5)

    glViewport(0, 0, WIDTH, HEIGHT)
    set_projection()
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    tex = make_texture()
    half_w = HALF_H * WIDTH / HEIGHT

    elapsed = 0.0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        walls.update(dt)
        canvas.fill(PANEL_BG)
        walls.draw()
        upload(tex, canvas)

        angle = SWAY_DEGREES * math.sin(elapsed * (2.0 * math.pi / SWAY_PERIOD))

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -DISTANCE)
        glRotatef(angle, 0.0, 1.0, 0.0)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        draw_quad(half_w, HALF_H)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
