import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from demos.retro_glasses.graffiti.thanks_for_watching_graffiti import ThanksForWatchingGraffiti
from lib.graffitti.swaying_surface import SwayingSurface


class ThanksGraffitiTestApp:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.camera_distance = 7.2
        self.surface_height = 2.9
        self.hold_seconds = 4.0
        self.wave_stagger_seconds = 0.15
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        pygame.display.set_caption(
            "Graffiti - THANKS FOR WATCHING   [SPACE restart, P pause, G finished, B blink, W blink wave, ESC quit]")
        self.graffiti = ThanksForWatchingGraffiti()
        self.surface = SwayingSurface(self.surface_height * self.graffiti.aspect_ratio, self.surface_height)
        self.clock = pygame.time.Clock()
        self.elapsed_seconds = 0.0
        self.sway_seconds = 0.0
        self.paused = False
        self.showing_finished = False

    def _set_camera(self):
        glViewport(0, 0, *self.window_size)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.window_size[0] / self.window_size[1], 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.showing_finished = False
                    self._restart_graffiti()
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                if event.key == pygame.K_g:
                    self.showing_finished = True
                    self.elapsed_seconds = max(self.elapsed_seconds, self.graffiti.duration_seconds)
                if event.key == pygame.K_b:
                    self.graffiti.blink_all_outlines(self.elapsed_seconds)
                if event.key == pygame.K_w:
                    self.graffiti.blink_all_outlines(self.elapsed_seconds, self.wave_stagger_seconds)
        return True

    def _restart_graffiti(self):
        self.elapsed_seconds = 0.0
        self.graffiti.reset_outline_blinks()

    def _advance_graffiti(self, frame_seconds):
        self.elapsed_seconds += frame_seconds
        if self.showing_finished:
            return
        if self.elapsed_seconds > self.graffiti.duration_seconds + self.hold_seconds:
            self._restart_graffiti()

    def run(self):
        running = True
        while running:
            running = self._handle_events()
            frame_seconds = self.clock.tick(self.frames_per_second) / 1000.0
            if self.paused:
                frame_seconds = 0.0
            self._advance_graffiti(frame_seconds)
            self.sway_seconds += frame_seconds
            self.graffiti.render(self.elapsed_seconds)
            self.surface.update(self.sway_seconds)
            self._set_camera()
            glClearColor(0.05, 0.05, 0.09, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.surface.render(self.graffiti.texture)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    ThanksGraffitiTestApp().run()
