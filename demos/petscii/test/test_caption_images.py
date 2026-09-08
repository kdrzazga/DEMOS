"""Windowed OpenGL viewer for the PETSCII caption images.

Walks every PetsciiImage subclass defined under
``demos/petscii/files/petscii/images`` and shows each one, centred, for one
second before moving on; it quits once the last image has been shown (or on ESC
/ window close). Space, Enter or any of A/B/C/M/N/V/X/Z pauses the current image
and the same keys resume it. As each image appears its file name and class name
are written to standard output.

Run it directly:  python -m demos.petscii.test.test_caption_images
"""

import importlib
import inspect
import os
import re
import sys

import pygame
from pygame.locals import (
    DOUBLEBUF,
    KEYDOWN,
    K_ESCAPE,
    K_KP_ENTER,
    K_RETURN,
    K_SPACE,
    K_a,
    K_b,
    K_c,
    K_m,
    K_n,
    K_v,
    K_x,
    K_z,
    OPENGL,
    QUIT,
)
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
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
    glOrtho,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2f,
)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from lib.multi_petscii_image import MultiPetsciiImage
from lib.petscii_image import PetsciiImage

CHAR_SIZE = 24
DISPLAY_MS = 1000     # hold each image for one second
MARGIN = 40           # blank border kept around the centred image

# any of these keys toggles a pause on the current image (ESC still quits)
PAUSE_KEYS = frozenset({K_SPACE, K_RETURN, K_KP_ENTER,
                        K_a, K_b, K_c, K_m, K_n, K_v, K_x, K_z})

IMAGES_DIR = os.path.join(_ROOT, "demos", "petscii", "files", "petscii", "images")
IMAGES_PACKAGE = "demos.petscii.files.petscii.images"


def _natural_key(file_name):
    """Sort key that orders caption1, caption2, ... caption10 numerically."""
    return [int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", file_name)]


def discover_images():
    """(file_name, class) for every PetsciiImage subclass defined in the images
    directory, in natural filename order. Modules that define no such class (the
    package marker, the caption manager) contribute nothing."""
    found = []
    for file_name in sorted(os.listdir(IMAGES_DIR), key=_natural_key):
        if not file_name.endswith(".py") or file_name == "__init__.py":
            continue
        module = importlib.import_module(IMAGES_PACKAGE + "." + file_name[:-3])
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, PetsciiImage) and cls.__module__ == module.__name__:
                found.append((file_name, cls))
    return found


def upload(surface):
    """Upload a pygame surface as a fresh nearest-filtered RGBA texture."""
    texture = glGenTextures(1)
    data = pygame.image.tobytes(surface, "RGBA")
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return texture


def render_image(picture):
    """Draw a caption onto a fresh black surface sized exactly to it."""
    width, height = picture.size()
    surface = pygame.Surface((width, height))
    surface.fill((0, 0, 0))
    picture.render(surface, transparent_space=True)
    return surface


def draw_centered(texture, width, height, window_width, window_height):
    """Draw the texture at its native size, centred in the window (top-left ortho)."""
    left = (window_width - width) / 2
    top = (window_height - height) / 2
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, texture)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(left, top)
    glTexCoord2f(1, 0); glVertex2f(left + width, top)
    glTexCoord2f(1, 1); glVertex2f(left + width, top + height)
    glTexCoord2f(0, 1); glVertex2f(left, top + height)
    glEnd()


def main():
    pygame.init()

    # each caption is wrapped in a MultiPetsciiImage so it renders at its own
    # row/column count -- PetsciiImage.render assumes the full 40x25 screen and
    # would overrun these shorter grids.
    pictures = [(file_name, cls, MultiPetsciiImage((cls(CHAR_SIZE),)))
                for file_name, cls in discover_images()]
    if not pictures:
        pygame.quit()
        return

    sizes = [picture.size() for _, _, picture in pictures]
    window_width = max(width for width, _ in sizes) + 2 * MARGIN
    window_height = max(height for _, height in sizes) + 2 * MARGIN
    pygame.display.set_mode((window_width, window_height), DOUBLEBUF | OPENGL)

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, window_width, window_height, 0, -1, 1)   # pixels, top-left origin
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    clock = pygame.time.Clock()
    running = True
    for file_name, cls, picture in pictures:
        if not running:
            break
        surface = render_image(picture)
        width, height = surface.get_width(), surface.get_height()
        texture = upload(surface)
        print(f"{file_name}\t{cls.__name__}", flush=True)
        pygame.display.set_caption(f"{file_name} - {cls.__name__}")

        paused = False
        elapsed = 0
        while running and elapsed < DISPLAY_MS:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
                elif event.type == KEYDOWN and event.key in PAUSE_KEYS:
                    paused = not paused
                    pygame.display.set_caption(
                        f"{file_name} - {cls.__name__}" + (" [paused]" if paused else ""))
            glClear(GL_COLOR_BUFFER_BIT)
            draw_centered(texture, width, height, window_width, window_height)
            pygame.display.flip()
            dt = clock.tick(60)
            if not paused:
                elapsed += dt          # frozen while paused, so the image holds
        glDeleteTextures([texture])

    pygame.quit()


if __name__ == "__main__":
    main()
