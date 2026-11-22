import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.animals.dragon import KnAdragonAnim


class DragonTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.background = (0.04, 0.04, 0.05, 1.0)
        self.field_of_view = 32.0
        self.orbit_yaw = 0.0
        self.orbit_pitch = 0.12
        self.orbit_distance = 3.4
        self.closest_distance = 1.4
        self.farthest_distance = 8.0
        self.zoom_step = 1.1
        self.look_at_height = 0.5
        self.spin_radians_per_second = 0.35
        self.drag_radians_per_pixel = 0.008
        self.spinning = False
        self.paused = False
        self.dragging = False
        self.key_light_direction = (-0.5, 0.8, 0.9, 0.0)
        self.key_light_color = (0.95, 0.88, 0.80, 1.0)
        self.fill_light_direction = (0.8, 0.2, 0.4, 0.0)
        self.fill_light_color = (0.30, 0.32, 0.38, 1.0)
        self.ambient_color = (0.22, 0.20, 0.20, 1.0)
        self.caption = "KnA dragon - {:.0f} fps, {:.1f} s  (drag to orbit, wheel zoom, SPACE spin, R restart, P pause, F fire, ESC quit)"
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.animation = KnAdragonAnim(1.0)
        self.fire_render = self.animation.fire.render
        self.fire_shown = True
        self.running = True
        self.setup_gl()

    def setup_gl(self):
        glClearColor(*self.background)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, self.key_light_color)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, self.fill_light_color)
        glLightfv(GL_LIGHT1, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient_color)
        glShadeModel(GL_SMOOTH)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.window_size[0] / self.window_size[1], 0.05, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def toggle_fire(self):
        self.fire_shown = not self.fire_shown
        fire = self.animation.fire
        fire.render = self.fire_render if self.fire_shown else lambda strength: None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.spinning = not self.spinning
                elif event.key == pygame.K_r:
                    self.animation.restart()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_f:
                    self.toggle_fire()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.orbit_yaw -= event.rel[0] * self.drag_radians_per_pixel
                self.orbit_pitch = max(-0.3, min(1.3, self.orbit_pitch + event.rel[1] * self.drag_radians_per_pixel))
            elif event.type == pygame.MOUSEWHEEL:
                self.orbit_distance *= self.zoom_step ** -event.y
                self.orbit_distance = max(self.closest_distance, min(self.farthest_distance, self.orbit_distance))

    def update(self, seconds):
        if not self.paused:
            self.animation.update(seconds)
        if self.spinning and not self.dragging:
            self.orbit_yaw += self.spin_radians_per_second * seconds

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        horizontal = self.orbit_distance * math.cos(self.orbit_pitch)
        eye = (horizontal * math.sin(self.orbit_yaw), self.look_at_height + self.orbit_distance * math.sin(self.orbit_pitch),
               horizontal * math.cos(self.orbit_yaw))
        gluLookAt(*eye, 0.0, self.look_at_height, 0.0, 0.0, 1.0, 0.0)
        glLightfv(GL_LIGHT0, GL_POSITION, self.key_light_direction)
        glLightfv(GL_LIGHT1, GL_POSITION, self.fill_light_direction)
        self.animation.render()
        pygame.display.flip()

    def run(self):
        while self.running:
            seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.handle_events()
            self.update(seconds)
            self.draw()
            pygame.display.set_caption(self.caption.format(self.clock.get_fps(), self.animation.seconds))
        pygame.quit()


if __name__ == "__main__":
    DragonTest().run()
