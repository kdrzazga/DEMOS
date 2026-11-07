import os
import sys

LIB_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(LIB_DIRECTORY, "root-effect"))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

from pulse_show import PulseShow
from sine_roots3d_connected import ConnectedSineRoots3D


class SineRoots3DTest:
    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        glViewport(0, 0, *self.window_size)
        self.clock = pygame.time.Clock()
        self.roots = ConnectedSineRoots3D()
        self.roots.aspect_ratio = self.window_size[0] / self.window_size[1]
        self.pulse_show = PulseShow(self.roots)
        self.surface_colors = {
            pygame.K_3: (236, 226, 204),
            pygame.K_4: (38, 44, 54),
            pygame.K_5: (214, 232, 222),
        }
        self.root_colors = {
            pygame.K_6: (122, 52, 24),
            pygame.K_7: (24, 46, 110),
            pygame.K_8: (46, 82, 34),
            pygame.K_9: (240, 240, 236),
        }
        self.elapsed_seconds = 0.0
        self.tilt_degrees_per_second = 30.0
        self.tilt_up_keys = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
        self.tilt_down_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
        self.running = True

    def tilt_direction(self):
        pressed = pygame.key.get_pressed()
        tilting_up = any(pressed[key] for key in self.tilt_up_keys)
        tilting_down = any(pressed[key] for key in self.tilt_down_keys)
        return int(tilting_up) - int(tilting_down)

    def clock_text(self):
        minutes, seconds = divmod(self.elapsed_seconds, 60.0)
        return f"{int(minutes):02d}:{seconds:04.1f}"

    def handle_color_key(self, key):
        if key in self.surface_colors:
            self.roots.set_surface_color(self.surface_colors[key])
        elif key in self.root_colors:
            self.roots.set_root_color(self.root_colors[key])
        elif key == pygame.K_0:
            self.pulse_show.start()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.roots.restart()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                self.roots.toggle_connections()
            elif event.type == pygame.KEYDOWN:
                self.handle_color_key(event.key)

    def run(self):
        while self.running:
            self.handle_events()
            delta_seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.elapsed_seconds += delta_seconds
            self.roots.tilt_surface(self.tilt_direction() * self.tilt_degrees_per_second * delta_seconds)
            self.roots.update(delta_seconds)
            glClearColor(*self.roots.background_color, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.roots.draw()
            pygame.display.flip()
            pygame.display.set_caption(f"Sine roots 3D - {self.clock_text()} - {self.clock.get_fps():.0f} fps - 2 lines, 3-5 surface, 6-9 roots, 0 pulse, +/- tilt {self.roots.surface_tilt_degrees:.0f}, SPACE restart, ESC quit")
        pygame.quit()


if __name__ == "__main__":
    SineRoots3DTest().run()
