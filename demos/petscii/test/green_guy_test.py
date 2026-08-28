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
    glDeleteTextures,
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

from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.green_guy import GreenGuy

CHAR_SIZE = 24
FRAME_MS = 500            # each head+torso combination is held for half a second
GUY_WIDTH, GUY_HEIGHT = 13, 16  # cells the guy is stamped over
CAMERA_FIT = 1.4          # camera distance as a multiple of the surface -- fits it fully in view
SWAY_DEGREES = 10.0       # peak left/right tilt of the sway
SWAY_PERIOD = 5000.0      # milliseconds for a full left-right-left sway
ZOOM_STEP = 2.0           # units z moves each frame: z = z + 2 zooming out, z = z - 2 zooming in
ZOOM_NEAR = 0.6           # closest camera distance, as a fraction of the fit distance
ZOOM_FAR = 1.4            # farthest camera distance, as a fraction of the fit distance

# every head+torso combination, shown in turn: the guy as drawn (his default
# head) followed by each expression pasted over that head
FRAMES = (
    "draw_guy",
    "mouth_wide_open",
    "mouth_left",
    "smile",
    "dead",
    "sad",
    "confused",
    "mouth0",
    "mouth_o",
)


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


def render_frame(guy, name, surface, texture):
    """Build one head+torso combination and hand back its fresh texture."""
    getattr(guy, name)()
    guy.render(surface)
    if texture is not None:
        glDeleteTextures([texture])
    pygame.display.set_caption("Green Guy - " + name)
    return upload(surface)


def main():
    pygame.init()
    guy = GreenGuy(CHAR_SIZE)
    # centre the 13x16 guy in the 40x25 screen; head paste follows self.origin
    guy.origin = ((Constants.ROWS - GUY_HEIGHT) // 2, (Constants.COLUMNS - GUY_WIDTH) // 2)
    width, height = guy.size()
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)

    surface = pygame.Surface((width, height))
    frame = 0
    texture = render_frame(guy, FRAMES[frame], surface, None)

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    half_width, half_height = width / 2, height / 2
    distance = max(width, height) * CAMERA_FIT
    z = distance                          # camera distance, zoomed in and out each frame
    z_near, z_far = distance * ZOOM_NEAR, distance * ZOOM_FAR
    zoom_step = ZOOM_STEP

    clock = pygame.time.Clock()
    start = pygame.time.get_ticks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        step = ((pygame.time.get_ticks() - start) // FRAME_MS) % len(FRAMES)
        if step != frame:
            frame = step
            texture = render_frame(guy, FRAMES[frame], surface, texture)

        sway = SWAY_DEGREES * math.sin(2 * math.pi * pygame.time.get_ticks() / SWAY_PERIOD)
        z += zoom_step
        if z >= z_far:
            z, zoom_step = z_far, -ZOOM_STEP     # reached the far point, start zooming in
        elif z <= z_near:
            z, zoom_step = z_near, ZOOM_STEP      # reached the near point, start zooming out

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 1.0, 10000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -z)
        glRotatef(sway, 0.0, 1.0, 0.0)

        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, texture)
        draw_surface(half_width, half_height)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
