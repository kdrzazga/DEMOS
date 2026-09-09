"""Viewer for the encoded PETSCII pictures in files/resources/petscii.

Each .txt there holds a PETSCII screen (screen codes, then colours, in two
";"-separated segments -- see :class:`PetsciiScreen`). This decodes every one,
renders it to a pygame surface, and shows each on a pyOpenGL surface for a
second in turn; once all have been shown it quits. ESC or closing the window
quits early.
"""

import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_NEAREST,
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
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex3f,
)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from lib.petscii_image import PetsciiImage
from lib.petscii_screen import PetsciiScreen

PETSCII_DIR = os.path.join(os.path.dirname(__file__), "..", "files", "resources", "petscii")
CHAR_SIZE = 24
SECONDS_PER_PICTURE = 1.5


def petscii_files(directory):
    """Every encoded PETSCII .txt in `directory`, in a stable order."""
    return sorted(os.path.join(directory, name) for name in os.listdir(directory)
                  if name.lower().endswith(".txt"))


def render_picture(path, char_size):
    """Decode one encoded PETSCII file into an opaque pygame surface."""
    screen = PetsciiScreen.from_file(path, uppercase=True)
    image = PetsciiImage.from_petscii_screen(screen, char_size=char_size)
    surface = pygame.Surface(image.size())
    image.render(surface)
    return surface


def upload(surface):
    """Upload a surface as a texture and return its id."""
    texture = glGenTextures(1)
    data = pygame.image.tobytes(surface, "RGBA")
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return texture


def draw_full_quad():
    """Draw the bound texture over the whole viewport (identity NDC quad)."""
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-1, 1, 0)
    glTexCoord2f(1, 0); glVertex3f(1, 1, 0)
    glTexCoord2f(1, 1); glVertex3f(1, -1, 0)
    glTexCoord2f(0, 1); glVertex3f(-1, -1, 0)
    glEnd()


def show_for(texture, seconds, clock):
    """Draw `texture` for `seconds`; return False if the user asked to quit."""
    end = pygame.time.get_ticks() + int(seconds * 1000)
    while pygame.time.get_ticks() < end:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return False
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, texture)
        draw_full_quad()
        pygame.display.flip()
        clock.tick(60)
    return True


def main():
    paths = petscii_files(PETSCII_DIR)
    if not paths:
        print("no .txt PETSCII pictures found in %s" % os.path.abspath(PETSCII_DIR))
        return

    pygame.init()
    pygame.display.set_mode(PetsciiImage(CHAR_SIZE).size(), DOUBLEBUF | OPENGL)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)

    clock = pygame.time.Clock()
    for path in paths:
        pygame.display.set_caption("PETSCII: %s" % os.path.basename(path))
        texture = upload(render_picture(path, CHAR_SIZE))
        shown = show_for(texture, SECONDS_PER_PICTURE, clock)
        glDeleteTextures([texture])
        if not shown:
            break
    pygame.quit()


if __name__ == "__main__":
    main()
