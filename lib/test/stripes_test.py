import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.specialFX.stripes import StripeEffects
from lib.specialFX.unsynced import UnsyncedPicture

WIDTH, HEIGHT = 1000, 600
FPS = 60
CAMERA_DISTANCE = 9.0
PICTURE_WIDTH = 8.0
PICTURE_PIXELS = (1024, 576)
AMBER = (1.0, 0.6, 0.1)
BLUE_STRIPES_COUNT = 12
MIDDLE_BAND = (360, 40, AMBER)
BOTTOM_BAND = (500, 90)
SHADING_COLORS = (None, (0.2, 1.0, 0.4), AMBER, (1.0, 1.0, 1.0))
ODYSSEY = ("Tell me, O muse, of that ingenious hero who travelled far and wide after he had sacked "
           "the famous town of Troy. Many cities did he visit, and many were the nations with whose "
           "manners and customs he was acquainted; moreover he suffered much by sea while trying to "
           "save his own life and bring his men safely home; but do what he might he could not save "
           "his men, for they perished through their own sheer folly in eating the cattle of the "
           "Sun-god Hyperion; so the god prevented them from ever reaching home.")
TEXT_SIZE = 84
TEXT_MARGIN = 24
TEXT_COLOR = (230, 230, 210)
TEXT_AREA_HEIGHT = PICTURE_PIXELS[1] * 3 // 4


def pixel_size():
    return PICTURE_WIDTH / PICTURE_PIXELS[0]


def picture_corner():
    picture_height = PICTURE_PIXELS[1] * pixel_size()
    return -PICTURE_WIDTH / 2.0, picture_height / 2.0, 0.0


def draw_rectangle(left, top, right, bottom, z, color):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex3f(left, bottom, z)
    glVertex3f(right, bottom, z)
    glVertex3f(right, top, z)
    glVertex3f(left, top, z)
    glEnd()


def draw_picture():
    left, top, z = picture_corner()
    draw_rectangle(left, top, left + PICTURE_WIDTH, top - PICTURE_PIXELS[1] * pixel_size(), z, (0.04, 0.06, 0.16))


def wrap_words(text, text_font, usable_width):
    lines = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if line and text_font.size(candidate)[0] > usable_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    return lines


def make_text_texture():
    area_size = (PICTURE_PIXELS[0], TEXT_AREA_HEIGHT)
    surface = pygame.Surface(area_size, pygame.SRCALPHA)
    text_font = pygame.font.Font(None, TEXT_SIZE)
    line_top = TEXT_MARGIN
    for line in wrap_words(ODYSSEY, text_font, area_size[0] - 2 * TEXT_MARGIN):
        if line_top + text_font.get_height() > area_size[1]:
            break
        surface.blit(text_font.render(line, True, TEXT_COLOR), (TEXT_MARGIN, line_top))
        line_top += text_font.get_linesize()
    pixels = pygame.image.tobytes(surface, "RGBA", True)
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, area_size[0], area_size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
    glBindTexture(GL_TEXTURE_2D, 0)
    return texture


def draw_text(texture, brightness):
    left, top, z = picture_corner()
    right = left + PICTURE_WIDTH
    bottom = top - TEXT_AREA_HEIGHT * pixel_size()
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBindTexture(GL_TEXTURE_2D, texture)
    glColor4f(brightness, brightness, brightness, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(left, bottom, z + 0.001)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(right, bottom, z + 0.001)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(right, top, z + 0.001)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(left, top, z + 0.001)
    glEnd()
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)


def is_blinking(seconds, period, duration):
    return seconds % period < duration


def visible_bands(seconds):
    bands = [BOTTOM_BAND]
    if is_blinking(seconds, 3.0, 0.8):
        bands.append(MIDDLE_BAND)
    return bands


def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Stripes test - space switches shading color, up/down brightness, "
                               "u toggles unsynced picture, esc quits")
    clock = pygame.time.Clock()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    text_texture = make_text_texture()
    left, top, z = picture_corner()
    stripe_effects = StripeEffects()
    stripe_effects.place_picture((left, top, z + 0.002), pixel_size())
    stripe_effects.blue_height_share = tuple(share * 3 for share in stripe_effects.blue_height_share)
    unsynced_picture = UnsyncedPicture()
    unsynced_enabled = False
    shading_index = 0
    brightness = 1.0
    seconds = 0.0

    running = True
    while running:
        delta_seconds = clock.tick(FPS) / 1000.0
        seconds += delta_seconds
        stripe_effects.update(delta_seconds)
        unsynced_picture.update(delta_seconds)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                shading_index = (shading_index + 1) % len(SHADING_COLORS)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_u:
                unsynced_enabled = not unsynced_enabled
                unsynced_picture.restart()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                brightness = min(1.0, brightness + 0.1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                brightness = max(0.0, brightness - 0.1)

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -CAMERA_DISTANCE)
        glDisable(GL_LIGHTING)
        draw_picture()
        draw_text(text_texture, brightness)
        stripe_effects.interference((left, top, z + 0.002), pixel_size(), PICTURE_PIXELS[0], visible_bands(seconds),
                                    brightness, SHADING_COLORS[shading_index], transparency=0.5)
        stripe_effects.blue_interference(0, 0, PICTURE_PIXELS[0], MIDDLE_BAND[0], BLUE_STRIPES_COUNT, brightness,
                                         transparency=0.1)
        if unsynced_enabled:
            unsynced_picture.draw()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
