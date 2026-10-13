"""Standalone viewer for the 3D Pixelove Ole logo.

Run from the DEMOS folder:  python -m lib.pixelove_ole.preview

    mouse drag   orbit            wheel   zoom
    SPACE        lower row LOVE <-> OLE (animated)
    ENTER        fade the floor out / back in
    A..Z         fade the details (triangle, frame, comet, star, pixels) out / back in
    F1           toggle the automatic sway
    F2           explode / assemble the parts along z
    ESC          quit
"""
import math
import os
import sys

import pygame
from pygame.locals import (DOUBLEBUF, K_ESCAPE, K_F1, K_F2, K_RETURN, K_SPACE, K_a, K_z, KEYDOWN,
                           MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL, OPENGL, QUIT)
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.pixelove_ole.logo import PixeloveOleLogo


class LogoPreview:

    def __init__(self, width=1280, height=720, fps=60):
        self.width = width
        self.height = height
        self.fps = fps
        self.yaw = 0.0
        self.pitch = 8.0
        self.distance = 13.0
        self.auto_sway = True
        self.explode_target = 0.0
        self.explode = 0.0
        self.dragging = False
        self.elapsed = 0.0

        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Pixelove Ole - 3D logo")
        self.clock = pygame.time.Clock()
        self.logo = PixeloveOleLogo(lower_word="LOVE")

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glClearColor(0.02, 0.0, 0.05, 1.0)

    def handle(self, event):
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            return False
        if event.type == KEYDOWN and event.key == K_SPACE:
            self.logo.lower_row.morph_to("OLE" if self.logo.lower_row.word == "LOVE" else "LOVE")
        elif event.type == KEYDOWN and event.key == K_RETURN:
            floor = self.logo.floor
            floor.fade_to(1.0 if floor.target_opacity == 0.0 else 0.0)
        elif event.type == KEYDOWN and K_a <= event.key <= K_z:
            details = self.logo.details
            details.fade_to(1.0 if details.target_opacity == 0.0 else 0.0)
        elif event.type == KEYDOWN and event.key == K_F2:
            self.explode_target = 0.0 if self.explode_target else 1.0
        elif event.type == KEYDOWN and event.key == K_F1:
            self.auto_sway = not self.auto_sway
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.auto_sway = False
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == MOUSEMOTION and self.dragging:
            self.yaw += event.rel[0] * 0.3
            self.pitch = max(-80.0, min(80.0, self.pitch + event.rel[1] * 0.3))
        elif event.type == MOUSEWHEEL:
            self.distance = max(4.0, min(40.0, self.distance - event.y * 0.6))
        return True

    def update(self, delta_seconds):
        self.elapsed += delta_seconds
        if self.auto_sway:
            self.yaw = 28.0 * math.sin(self.elapsed * 0.4)
            self.pitch = 8.0 + 6.0 * math.sin(self.elapsed * 0.27)
        self.logo.update(delta_seconds)
        self.explode += (self.explode_target - self.explode) * min(1.0, delta_seconds * 3.0)
        parts = self.logo.parts()
        for index, part in enumerate(parts):
            home_x, home_y, home_z = part.home
            part.z = home_z + self.explode * (index - len(parts) / 2) * 0.6

    def render(self):
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, self.width / self.height, 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        yaw, pitch = math.radians(self.yaw), math.radians(self.pitch)
        eye_x = self.distance * math.cos(pitch) * math.sin(yaw)
        eye_y = self.distance * math.sin(pitch)
        eye_z = self.distance * math.cos(pitch) * math.cos(yaw)
        gluLookAt(eye_x, eye_y - 0.3, eye_z, 0.0, -0.3, 0.0, 0.0, 1.0, 0.0)
        self.logo.draw()

    def run(self):
        running = True
        while running:
            delta_seconds = self.clock.tick(self.fps) / 1000.0
            for event in pygame.event.get():
                running = self.handle(event) and running
            self.update(delta_seconds)
            self.render()
            pygame.display.flip()
        self.logo.release()
        pygame.quit()


if __name__ == "__main__":
    LogoPreview().run()
