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
    glDisable,
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

from demos.petscii.files.petscii.asian import Asian

CHAR_SIZE = 12
DEPTH = 7  # pixels between the front and back faces

class Globals:
    hat_changed = False
    eyes_step = 0
    graphics_said = False
    three_d_said = False


EYE_STEPS = ((6000, "close_eyes"), (11000, "eyes_wide_open"), (15000, "eyes_default"))


def upload(surface):
    texture = glGenTextures(1)
    data = pygame.image.tobytes(surface, "RGBA")
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return texture


def draw_face(half_width, half_height, z):
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-half_width, half_height, z)
    glTexCoord2f(1, 0); glVertex3f(half_width, half_height, z)
    glTexCoord2f(1, 1); glVertex3f(half_width, -half_height, z)
    glTexCoord2f(0, 1); glVertex3f(-half_width, -half_height, z)
    glEnd()


def draw_sides(half_width, half_height, d):
    glBegin(GL_QUADS)
    glVertex3f(-half_width, half_height, d);   glVertex3f(half_width, half_height, d)
    glVertex3f(half_width, half_height, -d);   glVertex3f(-half_width, half_height, -d)
    glVertex3f(-half_width, -half_height, d);  glVertex3f(half_width, -half_height, d)
    glVertex3f(half_width, -half_height, -d);  glVertex3f(-half_width, -half_height, -d)
    glVertex3f(-half_width, half_height, d);   glVertex3f(-half_width, -half_height, d)
    glVertex3f(-half_width, -half_height, -d); glVertex3f(-half_width, half_height, -d)
    glVertex3f(half_width, half_height, d);    glVertex3f(half_width, -half_height, d)
    glVertex3f(half_width, -half_height, -d);  glVertex3f(half_width, half_height, -d)
    glEnd()


def main():
    pygame.init()
    image = Asian(CHAR_SIZE)
    width, height = image.size()
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Asian PETSCII 3D")

    surface = pygame.Surface((width, height))
    image.render(surface)
    texture = upload(surface)

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    half_width, half_height = width / 2, height / 2
    distance = width * 1.6
    clock = pygame.time.Clock()
    angle = 0.0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        texture = conditionally_change_hat(image, surface, texture)
        texture = conditionally_change_eyes(image, surface, texture)
        texture = conditionally_talk(image, surface, texture)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 1.0, 10000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -distance)
        glRotatef(angle, 0.0, 1.0, 0.0)

        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, texture)
        draw_face(half_width, half_height, DEPTH / 2)          # front
        draw_face(half_width, half_height, -DEPTH / 2)         # back: reverse, appears mirrored

        glDisable(GL_TEXTURE_2D)
        glColor3f(0.4, 0.4, 0.4)
        draw_sides(half_width, half_height, DEPTH / 2)         # closed edges

        pygame.display.flip()
        angle = (angle + 1.0) % 360
        clock.tick(30)
    pygame.quit()


def conditionally_change_hat(image, surface, texture):
    if not Globals.hat_changed and pygame.time.get_ticks() >= 9000:
        image.alternate_hat()
        image.render(surface)
        texture = upload(surface)
        Globals.hat_changed = True
        print("Hat changed")
    return texture


def conditionally_talk(image, surface, texture):
    if not Globals.graphics_said and pygame.time.get_ticks() >= 15000:
        image.say_all_graphics()
        Globals.graphics_said = True
        print("say_all_graphics")
    if not Globals.three_d_said and pygame.time.get_ticks() >= 20000:
        image.say_3d()
        Globals.three_d_said = True
        print("say_3d")
    if image.talk():
        image.render(surface)
        texture = upload(surface)
    return texture


def conditionally_change_eyes(image, surface, texture):
    if Globals.eyes_step < len(EYE_STEPS):
        when, method = EYE_STEPS[Globals.eyes_step]
        if pygame.time.get_ticks() >= when:
            getattr(image, method)()
            image.render(surface)
            texture = upload(surface)
            Globals.eyes_step += 1
            print(method)
    return texture


if __name__ == "__main__":
    main()
