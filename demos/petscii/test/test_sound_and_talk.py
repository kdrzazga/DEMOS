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

from demos.petscii.files.petscii.green_guy import GreenGuy
from demos.petscii.files.petscii.images.multi_petscii_image_manager import MultiPetsciiImageManager
from demos.petscii.files.petscii.images.caption_groups import CAPTION_GROUPS
from demos.petscii.files.outro.sound_and_talk import SoundAndTalk

CHAR_SIZE = 24
FRAME_MS = 200
PAUSE_MS = 333
CAMERA_FIT = 1.4
SWAY_DEGREES = 10.0
SWAY_PERIOD = 5000.0
TALKING_FRAMES = ("mouth_wide_open", "mouth_left", "mouth0", "mouth_o", "smile")

SOUND_FILES = ("outro1.mp3", "outro2.mp3", "outro3.mp3")
TALK = (
    "For the past 40+ years, PETSCII art has showcased the creativity of Commodore computers like the C64.",
    " Similar to ASCII art, it uses simple characters to create expressive images, but with a distinct retro style and limited palette.",
    " Even nowadays, it celebrates the ingenuity of early digital artists and the legacy of vintage computing.",
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


class GuyFace:

    def __init__(self, guy, surface):
        self.guy = guy
        self.surface = surface
        self.name = None
        self.texture = None

    def show(self, name):
        if name == self.name:
            return
        self.name = name
        getattr(self.guy, name)()
        self.guy.render_figure(self.surface)
        if self.texture is not None:
            glDeleteTextures([self.texture])
        self.texture = upload(self.surface)

    def draw(self, half_width, half_height, distance, sway):
        window_width, window_height = pygame.display.get_surface().get_size()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, window_width / window_height, 1.0, 100000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -distance)
        glRotatef(sway, 0.0, 1.0, 0.0)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-half_width, half_height, 0)
        glTexCoord2f(1, 0); glVertex3f(half_width, half_height, 0)
        glTexCoord2f(1, 1); glVertex3f(half_width, -half_height, 0)
        glTexCoord2f(0, 1); glVertex3f(-half_width, -half_height, 0)
        glEnd()


def build_segments():
    return [SoundAndTalk(sound_file, talk, MultiPetsciiImageManager(caption_types=captions))
            for sound_file, talk, captions in zip(SOUND_FILES, TALK, CAPTION_GROUPS)]


def announce(segment):
    print(f"{segment.outro_sound_file}\t{segment.talk}", flush=True)


def main():
    pygame.init()
    pygame.mixer.init()

    guy = GreenGuy(CHAR_SIZE)
    window_width, window_height = guy.size()
    figure_width, figure_height = guy.figure_size()
    pygame.display.set_mode((window_width, window_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Sound and Talk")

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    face = GuyFace(guy, pygame.Surface((figure_width, figure_height)))
    face.show("smile")

    segments = build_segments()
    distance = max(window_width, window_height) * CAMERA_FIT
    half_width, half_height = figure_width / 2, figure_height / 2
    clock = pygame.time.Clock()

    index = 0
    paused = False
    pause_start = 0
    segments[0].start()
    announce(segments[0])
    talk_start = pygame.time.get_ticks()

    running = True
    while running and index < len(segments):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
        now = pygame.time.get_ticks()
        segment = segments[index]

        if not paused:
            segment.update()
            if segment.talking():
                face.show(TALKING_FRAMES[((now - talk_start) // FRAME_MS) % len(TALKING_FRAMES)])
            else:
                face.show("smile")
            if segment.finished:
                if index + 1 < len(segments):
                    paused = True
                    pause_start = now
                else:
                    index += 1
        else:
            face.show("smile")
            if now - pause_start >= PAUSE_MS:
                paused = False
                index += 1
                if index < len(segments):
                    segments[index].start()
                    announce(segments[index])
                    talk_start = now

        sway = SWAY_DEGREES * math.sin(2 * math.pi * now / SWAY_PERIOD)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        face.draw(half_width, half_height, distance, sway)
        segments[min(index, len(segments) - 1)].draw()
        pygame.display.flip()
        clock.tick(60)

    for segment in segments:
        segment.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
